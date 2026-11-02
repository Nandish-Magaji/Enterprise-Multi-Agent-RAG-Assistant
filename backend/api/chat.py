from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.gemini_service import generate_response

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/chat")
async def chat(request: ChatRequest) -> dict[str, str]:
    return {"response": generate_response(request.message)}
