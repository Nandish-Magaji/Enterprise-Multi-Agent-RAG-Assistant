import json
from typing import Any
from config.settings import settings
from config.logging_config import get_logger
from database.models import (
    create_workflow,
    save_artifact,
    update_workflow_state,
)
from adk.executor import executor
from services.rag_engine import build_context, rag_engine
from tools.tavily_mcp import build_tavily_context, extract_tavily_sources

logger = get_logger(__name__)

class ResearchPipeline:
    def run(
        self,
        owner_id: str,
        user_query: str,
        title: str | None = None,
        target_audience: str | None = None,
        writing_method: str | None = None,
        top_k: int = settings.DEFAULT_TOP_K,
        max_retries: int = settings.MAX_RETRIES,
    ) -> dict[str, Any]:
        logger.info("Starting Research Pipeline")
        (
            workflow_title,
            workflow_id,
            context,
            sources,
        ) = self._prepare_workflow(
            user_query=user_query,
            title=title,
            top_k=top_k,
            owner_id=owner_id,
        )
        research_notes = self._perform_research(
            workflow_id=workflow_id,
            user_query=user_query,
            context=context,
            target_audience=target_audience,
            writing_method=writing_method,
            sources=sources,
            owner_id=owner_id,
        )
        web_sources = extract_tavily_sources(research_notes)
        sources.extend(web_sources)
        verification_context = "\n\n".join(
            part for part in (context, build_tavily_context(web_sources)) if part
        )
        draft = self._generate_draft(
            workflow_id=workflow_id,
            user_query=user_query,
            research_notes=research_notes,
            target_audience=target_audience,
            writing_method=writing_method,
            owner_id=owner_id,
        )
        draft, verification, attempts = self._verify_and_correct(
            workflow_id=workflow_id,
            user_query=user_query,
            context=verification_context,
            draft=draft,
            max_retries=max_retries,
            owner_id=owner_id,
        )
        save_artifact(
            workflow_id,
            "writer",
            draft,
            {
                "attempts": attempts + 1,
            },
        )
        logger.info("Draft saved successfully.")
        save_artifact(
            workflow_id,
            "fact_checker",
            json.dumps(verification, indent=2),
            {
                "sources": sources,
            },
        )
        logger.info("Fact checking completed.")
        update_workflow_state(
            workflow_id,
            "EDITING",
            owner_id,
        )
        logger.info("Running Editor Agent")
        final_document = self._edit(
            draft=draft,
        )
        save_artifact(
            workflow_id,
            "editor",
            final_document,
            {
                "verification_verdict": verification.get("verdict"),
            },
        )
        logger.info("Final document created.")
        update_workflow_state(
            workflow_id,
            "HITL_APPROVAL",
            owner_id,
        )
        logger.info(
            "Workflow %s completed successfully (%s).",
            workflow_id,
            verification.get("verdict")
        )
        return {
            "workflow_id": workflow_id,
            "state": "HITL_APPROVAL",
            "title": workflow_title,
            "research_notes": research_notes,
            "draft": draft,
            "final_document": final_document,
            "verification": verification,
            "sources": sources,
            "attempts_made": attempts + 1,
        }
    def _verify_and_correct(
        self,
        workflow_id: str,
        user_query: str,
        context: str,
        draft: str,
        max_retries: int,
        owner_id: str,
    ) -> tuple[str, dict[str, Any], int]:
        verification = {}
        attempts = 0
        while attempts < max_retries:
            update_workflow_state(
                workflow_id,
                "CHECKING",
                owner_id,
            )
            logger.info("Running Fact Checker")
            verification = self._verify(
                context=context,
                generated_answer=draft,
                user_query=user_query,
                verification_mode="general_knowledge",
            )
            if verification.get("verdict") == "PASS":
                break
            attempts += 1
            unsupported_claims = (
                verification.get("unsupported_claims")
                or verification.get("unsupported_statements")
                or []
            )
            if not unsupported_claims:
                break
            update_workflow_state(
                workflow_id,
                "WRITING",
                owner_id,
            )
            draft = self._correct(
                context=context,
                draft=draft,
                unsupported_claims=unsupported_claims,
                user_query=user_query,
            )
        return draft, verification, attempts
    def _prepare_workflow(
        self,
        user_query: str,
        title: str | None,
        top_k: int,
        owner_id: str,
    ) -> tuple[str, str, str, list[dict]]:
        workflow_title = (
            title.strip()
            if title and title.strip()
            else user_query[:80]
        )
        workflow_id = create_workflow(
            workflow_title,
            user_query,
            owner_id,
        )
        retrieval_results = rag_engine.search(
            user_query,
            top_k=top_k,
            owner_id=owner_id,
        )

        context = build_context(retrieval_results)

        if not retrieval_results:
            logger.info(
                "No relevant source chunks retrieved. "
                "Continuing without retrieved context."
            )
        sources = [
            {
                "source_id": result["source_id"],
                "source_title": result["source_title"],
                "citation": result["citation"],
                "chunk_index": result["chunk_index"],
            }
            for result in retrieval_results
        ]
        return (
            workflow_title,
            workflow_id,
            context,
            sources,
        )
    def _perform_research(
        self,
        workflow_id: str,
        user_query: str,
        context: str,
        target_audience: str | None,
        writing_method: str | None,
        sources: list[dict[str, Any]],
        owner_id: str,
    ) -> str:
        update_workflow_state(
            workflow_id,
            "RESEARCH",
            owner_id,
        )
        logger.info("Stage: RESEARCH")
        research_notes = self._research(
            user_query=user_query,
            context=context,
            target_audience=target_audience,
            writing_method=writing_method,
            sources=sources,
        )
        save_artifact(
            workflow_id,
            "researcher",
            research_notes,
            {
                "sources": sources,
            },
        )
        logger.info("Research completed successfully.")
        return research_notes
    def _generate_draft(
        self,
        workflow_id: str,
        user_query: str,
        research_notes: str,
        target_audience: str | None,
        writing_method: str | None,
        owner_id: str,
    ) -> str:
        update_workflow_state(
            workflow_id,
            "WRITING",
            owner_id,
        )
        logger.info("Stage: WRITING")
        draft = self._write(
            user_query=user_query,
            research_notes=research_notes,
            target_audience=target_audience,
            writing_method=writing_method,
        )
        logger.info("Draft generated successfully.")
        return draft
    def _research(
        self,
        user_query: str,
        context: str,
        target_audience: str | None,
        writing_method: str | None,
        sources: list[dict[str, Any]],
    ) -> str:
        return executor.execute(
            agent_name="researcher",
            inputs={
                "user_query": user_query,
                "context": context,
                "target_audience": target_audience,
                "writing_method": writing_method,
                "sources": sources,
            },
        )
    def _write(
        self,
        user_query: str,
        research_notes: str,
        target_audience: str | None,
        writing_method: str | None,
)    -> str:
        return executor.execute(
            agent_name="writer",
            inputs={
                "user_query": user_query,
                "research_notes": research_notes,
                "target_audience": target_audience,
                "writing_method": writing_method,
            },
        )
    def _verify(
        self,
        context: str,
        generated_answer: str,
        user_query: str,
        verification_mode: str = "general_knowledge",
    ) -> dict[str, Any]:
        raw = executor.execute(
            agent_name="fact_checker",
            inputs={
                "user_query": user_query,
                "context": context,
                "generated_answer": generated_answer,
                "verification_mode": verification_mode
            },
            json_output=True,
        )
        try:
            report = json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Fact Checker returned invalid JSON.")
            report = {
                "has_hallucination": True,
                "unsupported_claims": [
                    "Fact Checker returned invalid JSON."
                ],
                "relevance_issue": True,
                "reasoning": raw,
                "verdict": "FAIL",
            }
        unsupported = (
            report.get("unsupported_claims")
            or report.get("unsupported_statements")
            or []
        )
        report["unsupported_claims"] = unsupported
        report["has_hallucination"] = bool(
            report.get("has_hallucination")
            or unsupported
        )
        report["verdict"] = (
            "FAIL"
            if report["has_hallucination"]
            or report.get("relevance_issue")
            else "PASS"
        )
        return report
    def _correct(
        self,
        context: str,
        draft: str,
        unsupported_claims: list[str],
        user_query: str,
    ) -> str:
        logger.info("Writer Agent correcting unsupported claims.")
        return executor.execute(
            agent_name="writer",
            inputs={
                "user_query": user_query,
                "context": context,
                "unsupported_claims": unsupported_claims,
                "draft": draft,
            },
        )
    def _edit(
        self,
        draft: str,
    ) -> str:
        return executor.execute(
            agent_name="editor",
            inputs={
                "draft": draft,
            },
        )
