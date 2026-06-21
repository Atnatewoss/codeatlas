from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from agents.state import Evidence

router = APIRouter(prefix="/api/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    citations: List[str] = []

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Interact with the codebase using the context gathered during the ToT exploration.
    This simulates an LLM response grounded in the repository evidence.
    """
    # In a real implementation, you'd use LangChain/LangGraph to route the query,
    # retrieve from a vector store, and generate an answer with citations.
    
    last_msg = request.messages[-1].content.lower()
    
    if "architecture" in last_msg:
        return ChatResponse(
            content="Based on the structure analysis, the architecture uses a decoupled service layer. The authentication mechanisms are isolated from the core logic.",
            citations=["src/auth/jwt.py", "docs/architecture.md"]
        )
    elif "run" in last_msg or "flow" in last_msg:
        return ChatResponse(
            content="The execution flow begins at the ASGI entry point in `server.py`, routing through the middleware before hitting the designated endpoints.",
            citations=["src/server.py", "src/middleware/auth.py"]
        )
    else:
        return ChatResponse(
            content="I can help you understand the codebase. You can ask about its architecture, execution flow, or any specific files cited in the evidence panel.",
            citations=[]
        )
