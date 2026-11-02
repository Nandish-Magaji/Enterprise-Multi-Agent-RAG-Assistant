from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

import adk.register_agents
from config.logging_config import get_logger

logger = get_logger(__name__)

from database.models import get_source_count, init_db, save_artifact, update_workflow_state
from orchestrator.research_pipeline import ResearchPipeline
from services.rag_engine import extract_text_from_upload, rag_engine
from security.auth import get_current_user, require_reviewer
from api.export import router as export_router
from api.chat import router as chat_router
from api.history import router as history_router
from config.settings import settings

load_dotenv()
init_db()

app = FastAPI(title="Enterprise Multi-Agent RAG Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(export_router)
app.include_router(chat_router)
app.include_router(history_router)


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


@app.post("/rag/ingest-text")
async def ingest_text(request: IngestTextRequest, user: dict = Depends(get_current_user)) -> dict[str, object]:
    try:
        result = rag_engine.ingest_text(
            title=request.title,
            content=request.content,
            owner_id=user["sub"],
            source_type=request.source_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG ingestion failed: {exc}") from exc
    return result


@app.post("/rag/ingest-file")
async def ingest_file(file: UploadFile = File(...), user: dict = Depends(get_current_user)) -> dict[str, object]:
    filename = file.filename or "uploaded-document"
    content = await file.read()
    try:
        text, source_type = extract_text_from_upload(filename, content)
        result = rag_engine.ingest_text(
            title=filename,
            content=text,
            owner_id=user["sub"],
            source_type=source_type,
            metadata={"filename": filename},
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RAG ingestion failed: {exc}") from exc
    return result


@app.post("/workflow/run")
async def run_workflow(request: WorkflowRunRequest, user: dict = Depends(get_current_user)) -> dict[str, object]:
    pipeline = ResearchPipeline()
    try:
        return pipeline.run(
            owner_id=user["sub"],
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


@app.post("/workflow/approve")
async def approve_workflow(request: HitlDecisionRequest, user: dict = Depends(require_reviewer)) -> dict[str, str]:
    if not update_workflow_state(request.workflow_id, "COMPLETED", user["sub"]):
        raise HTTPException(status_code=404, detail="Workflow not found.")
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
async def reject_workflow(request: HitlDecisionRequest, user: dict = Depends(require_reviewer)) -> dict[str, str]:
    if not update_workflow_state(request.workflow_id, "REJECTED", user["sub"]):
        raise HTTPException(status_code=404, detail="Workflow not found.")
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
