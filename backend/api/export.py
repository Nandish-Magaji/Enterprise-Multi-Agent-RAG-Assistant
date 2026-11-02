from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response

from database.models import get_workflow_artifacts
from security.auth import get_current_user
from services.markdown_service import render_markdown
from services.pdf_service import render_pdf

router = APIRouter(prefix="/workflows", tags=["export"])


def _export_data(workflow_id: str, owner_id: str) -> tuple[str, str, list[dict[str, Any]]]:
    artifacts = get_workflow_artifacts(workflow_id, owner_id)
    editor = next((artifact for artifact in reversed(artifacts) if artifact["agent_name"] == "editor"), None)
    if editor is None:
        raise HTTPException(status_code=404, detail="Final document is not available for export.")

    sources: list[dict[str, Any]] = []
    for artifact in artifacts:
        if artifact["agent_name"] == "fact_checker":
            sources = artifact.get("metadata", {}).get("sources", []) or []
            break
    title = next(
        (source.get("source_title") for source in sources if source.get("source_title")),
        "Generated document",
    )
    return title, editor["content"], sources


def _filename(workflow_id: str, extension: str) -> str:
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", workflow_id)
    return f"workflow-{safe_id}.{extension}"


@router.get("/{workflow_id}/export/markdown", dependencies=[Depends(get_current_user)])
async def export_markdown(workflow_id: str, user: dict = Depends(get_current_user)) -> Response:
    title, content, sources = _export_data(workflow_id, user["sub"])
    document = render_markdown(title, content, sources)
    return Response(
        content=document,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{_filename(workflow_id, "md")}"'},
    )


@router.get("/{workflow_id}/export/pdf", dependencies=[Depends(get_current_user)])
async def export_pdf(workflow_id: str, user: dict = Depends(get_current_user)) -> Response:
    title, content, sources = _export_data(workflow_id, user["sub"])
    document = render_pdf(title, content, sources)
    return Response(
        content=document,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_filename(workflow_id, "pdf")}"'},
    )
