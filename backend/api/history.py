from fastapi import APIRouter, Depends

from database.models import get_workflow_artifacts, list_workflows
from security.auth import get_current_user

router = APIRouter(tags=["history"])


@router.get("/workflows")
async def workflows(user: dict = Depends(get_current_user)) -> dict[str, object]:
    return {"workflows": list_workflows(user["sub"])}


@router.get("/workflows/{workflow_id}/artifacts")
async def workflow_artifacts(workflow_id: str, user: dict = Depends(get_current_user)) -> dict[str, object]:
    return {"artifacts": get_workflow_artifacts(workflow_id, user["sub"])}
