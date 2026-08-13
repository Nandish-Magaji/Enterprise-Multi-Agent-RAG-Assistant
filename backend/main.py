from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import adk.register_agents
from config.logging_config import get_logger

logger = get_logger(__name__)

from database.models import (
    get_source_count,
    get_workflow_artifacts,
    init_db,
    list_workflows,
    save_artifact,
    update_workflow_state,
)
from orchestrator.research_pipeline import ResearchPipeline
from services.gemini_service import generate_response
from services.rag_engine import extract_text_from_upload, rag_engine

load_dotenv()
init_db()

app = FastAPI(title="Enterprise Multi-Agent RAG Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class IngestTextRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source_type: str = "text"


class WorkflowRunRequest(BaseModel):
    user_query: str = Field(..., min_length=1)
    title: str | None = None
    target_audience: str | None = None
    writing_method: str | None = None
    top_k: int = Field(default=6, ge=1, le=12)


class HitlDecisionRequest(BaseModel):
    workflow_id: str
    feedback: str | None = None


@app.get("/health")
async def health() -> dict[str, int | str]:
    return {
        "status": "ok",
        "rag_sources": get_source_count(),
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    reply = generate_response(request.message)
    return {"response": reply}


@app.post("/rag/ingest-text")
async def ingest_text(request: IngestTextRequest) -> dict[str, object]:
    try:
        result = rag_engine.ingest_text(
            title=request.title,
            content=request.content,
            source_type=request.source_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG ingestion failed: {exc}") from exc
    return result


@app.post("/rag/ingest-file")
async def ingest_file(file: UploadFile = File(...)) -> dict[str, object]:
    filename = file.filename or "uploaded-document"
    content = await file.read()
    try:
        text, source_type = extract_text_from_upload(filename, content)
        result = rag_engine.ingest_text(
            title=filename,
            content=text,
            source_type=source_type,
            metadata={"filename": filename},
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG ingestion failed: {exc}") from exc
    return result


@app.post("/workflow/run")
async def run_workflow(request: WorkflowRunRequest) -> dict[str, object]:
    pipeline = ResearchPipeline()
    try:
        return pipeline.run(
            user_query=request.user_query,
            title=request.title,
            target_audience=request.target_audience,
            writing_method=request.writing_method,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Workflow execution failed.")

        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


@app.get("/workflows")
async def workflows() -> dict[str, object]:
    return {"workflows": list_workflows()}


@app.get("/workflows/{workflow_id}/artifacts")
async def workflow_artifacts(workflow_id: str) -> dict[str, object]:
    return {"artifacts": get_workflow_artifacts(workflow_id)}


@app.post("/workflow/approve")
async def approve_workflow(request: HitlDecisionRequest) -> dict[str, str]:
    update_workflow_state(request.workflow_id, "COMPLETED")
    save_artifact(
        request.workflow_id,
        "human",
        request.feedback or "Approved by human reviewer.",
        {"decision": "approve"},
    )
    return {
        "workflow_id": request.workflow_id,
        "state": "COMPLETED",
    }


@app.post("/workflow/reject")
async def reject_workflow(request: HitlDecisionRequest) -> dict[str, str]:
    update_workflow_state(request.workflow_id, "REJECTED")
    save_artifact(
        request.workflow_id,
        "human",
        request.feedback or "Rejected by human reviewer.",
        {"decision": "reject"},
    )
    return {
        "workflow_id": request.workflow_id,
        "state": "REJECTED",
    }
