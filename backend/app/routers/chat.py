"""Chat router - HTTP endpoints for AI Project Assistant.

PHASE B: Refactored to use Supervisor Agent orchestration

Provides:
- POST /chat - Synchronous chat endpoint
- POST /chat/stream - Streaming chat endpoint
- GET /chat/health - Health check
- GET /chat/agents - List available agents

Backward compatible with existing API.
Internal architecture uses Supervisor Agent + Specialist Agents.
"""

import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents import (
    DocumentAgent,
    FinanceAgent,
    ProjectAgent,
    RiskAgent,
    ScheduleAgent,
    SupervisorAgent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Chat request."""

    query: str = Field(..., description="Question or query", min_length=1, max_length=500)
    project_id: Optional[int] = Field(None, description="Optional project ID to scope the query")
    response_mode: str = Field(
        "concise",
        description="Response mode: concise, detailed, or executive",
        pattern="^(concise|detailed|executive)$",
    )
    conversation_id: Optional[str] = Field(
        None, description="Optional conversation ID for context history"
    )


class Citation(BaseModel):
    """Citation in response."""

    source: str
    content: Optional[str] = None
    relevance: Optional[float] = None
    tool: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response."""

    answer: str = Field(description="The answer to the query")
    citations: list[Citation] = Field(default_factory=list, description="Source citations")
    confidence: float = Field(
        description="Confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    response_mode: str = Field(description="Mode used to generate response")
    agents_used: list[str] = Field(
        default_factory=list, description="Agents that contributed to answer"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


# Global supervisor instance
_supervisor = None


def get_supervisor() -> SupervisorAgent:
    """Get or create the global Supervisor instance.

    Initializes all specialist agents on first call.
    """
    global _supervisor
    if _supervisor is None:
        logger.info("Initializing Supervisor Agent with Specialist Agents...")

        supervisor = SupervisorAgent()

        # Register specialist agents
        supervisor.register_agent("project_management", ProjectAgent())
        supervisor.register_agent("risk_management", RiskAgent())
        supervisor.register_agent("schedule", ScheduleAgent())
        supervisor.register_agent("document_management", DocumentAgent())

        # FinanceAgent not fully implemented yet, but registered for future use
        # supervisor.register_agent("finance", FinanceAgent())

        _supervisor = supervisor
        logger.info(f"Supervisor initialized with {len(supervisor.list_agents())} agents")

    return _supervisor


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Answer a question using Supervisor Agent orchestration.

    The Supervisor:
    1. Understands the user intent
    2. Routes to appropriate specialist agents
    3. Executes agents in parallel
    4. Merges results
    5. Returns unified response

    Args:
        request: ChatRequest with query and optional filters

    Returns:
        ChatResponse with answer, citations, confidence, and agents used
    """
    start_time = time.time()
    logger.info(f"Chat endpoint: {request.query[:100]}... (project_id={request.project_id})")

    try:
        supervisor = get_supervisor()

        # Route through Supervisor (orchestrates specialist agents)
        supervisor_response = await supervisor.answer(
            query=request.query,
            project_id=request.project_id,
        )

        # Convert to API response format (backward compatible)
        citations = [
            Citation(
                source=c["source"] if isinstance(c, dict) else c.source,
                content=c.get("content") if isinstance(c, dict) else c.content,
                relevance=c.get("relevance") if isinstance(c, dict) else c.relevance,
                tool=c.get("tool") if isinstance(c, dict) else c.tool,
            )
            for c in supervisor_response.get("citations", [])
        ]

        elapsed_ms = (time.time() - start_time) * 1000

        response = ChatResponse(
            answer=supervisor_response.get("answer", ""),
            citations=citations,
            confidence=supervisor_response.get("confidence", 0.0),
            response_mode=request.response_mode,
            agents_used=supervisor_response.get("agents_used", []),
            metadata={
                **supervisor_response.get("metadata", {}),
                "elapsed_ms": elapsed_ms,
            },
        )

        logger.info(
            f"Chat endpoint complete: agents={len(response.agents_used)} "
            f"confidence={response.confidence:.2f} elapsed_ms={elapsed_ms:.0f}"
        )

        return response

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}",
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """Stream a chat response (Server-Sent Events).

    Streams answer and metadata in real-time.

    Args:
        request: ChatRequest with query and optional filters

    Returns:
        StreamingResponse with SSE events
    """
    from fastapi.responses import StreamingResponse

    async def generate():
        """Generate SSE events."""
        try:
            supervisor = get_supervisor()

            # Route through Supervisor
            supervisor_response = await supervisor.answer(
                query=request.query,
                project_id=request.project_id,
            )

            # Stream start
            yield 'data: {"type": "start"}\n\n'

            # Stream answer character by character
            answer = supervisor_response.get("answer", "")
            for char in answer:
                yield f'data: {{"type": "text", "content": "{json.dumps(char)}"}}\n\n'

            # Stream citations
            citations = supervisor_response.get("citations", [])
            citations_data = [
                {
                    "source": c["source"] if isinstance(c, dict) else c.source,
                    "content": c.get("content") if isinstance(c, dict) else c.content,
                    "relevance": c.get("relevance") if isinstance(c, dict) else c.relevance,
                }
                for c in citations
            ]
            yield 'data: {"type": "citations", "citations": '
            yield json.dumps(citations_data)
            yield '}\n\n'

            # Stream metadata
            yield 'data: {"type": "metadata", '
            yield json.dumps({
                "confidence": supervisor_response.get("confidence", 0.0),
                "agents_used": supervisor_response.get("agents_used", []),
            })
            yield '}\n\n'

            # Stream end
            yield 'data: {"type": "end"}\n\n'

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield f'data: {{"type": "error", "error": "{json.dumps(str(e))}"}}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.get("/agents")
async def list_agents() -> dict:
    """List available specialist agents."""
    try:
        supervisor = get_supervisor()
        agents = supervisor.list_agents()
        return {
            "agents": agents,
            "count": len(agents),
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health() -> dict:
    """Health check for chat endpoint."""
    try:
        supervisor = get_supervisor()
        agents = supervisor.list_agents()

        return {
            "status": "healthy",
            "supervisor": "operational",
            "agents": agents,
            "agent_count": len(agents),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
