"""Chat router - HTTP endpoints for AI Project Assistant.

Provides:
- POST /chat - Synchronous chat endpoint
- POST /chat/stream - Streaming chat endpoint
"""

import logging
import time
from typing import AsyncIterator, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.project_agent import ProjectAgent

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
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context history")


class Citation(BaseModel):
    """Citation in response."""

    source: str
    content: Optional[str] = None
    relevance: Optional[str] = None
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
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


# Global agent instance (create once, reuse)
_agent = None


def get_agent() -> ProjectAgent:
    """Get or create the global ProjectAgent instance."""
    global _agent
    if _agent is None:
        logger.info("Initializing ProjectAgent...")
        _agent = ProjectAgent()
    return _agent


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Answer a question about projects.

    Args:
        request: ChatRequest with query and optional filters

    Returns:
        ChatResponse with answer, citations, and confidence
    """
    start_time = time.time()

    try:
        agent = get_agent()

        # Get agent response
        agent_response = await agent.answer(
            query=request.query,
            conversation_id=request.conversation_id,
            project_id=request.project_id,
            response_mode=request.response_mode,
        )

        # Convert to API response
        citations = [
            Citation(
                source=c.get("source"),
                content=c.get("content"),
                relevance=c.get("relevance"),
                tool=c.get("tool"),
            )
            for c in agent_response.citations
        ]

        elapsed_ms = (time.time() - start_time) * 1000

        response = ChatResponse(
            answer=agent_response.answer,
            citations=citations,
            confidence=agent_response.confidence,
            response_mode=agent_response.mode,
            metadata={
                **agent_response.metadata,
                "elapsed_ms": elapsed_ms,
            },
        )

        logger.info(
            f"Chat endpoint: query={request.query[:50]}... "
            f"mode={request.response_mode} "
            f"confidence={response.confidence:.2f} "
            f"elapsed_ms={elapsed_ms:.0f}"
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

    Streams answer tokens in real-time for better UX.

    Args:
        request: ChatRequest with query and optional filters

    Returns:
        StreamingResponse with SSE events
    """
    from fastapi.responses import StreamingResponse

    async def generate():
        """Generate SSE events."""
        try:
            agent = get_agent()

            # Execute agent (but get tools results without LLM streaming for MVP)
            # Future: implement full streaming through LLM
            agent_response = await agent.answer(
                query=request.query,
                conversation_id=request.conversation_id,
                project_id=request.project_id,
                response_mode=request.response_mode,
            )

            # Stream answer character by character
            yield 'data: {"type": "start"}\n\n'

            for i, char in enumerate(agent_response.answer):
                yield f'data: {{"type": "text", "content": "{char}"}}\n\n'
                # Yield every 10 characters for efficiency
                if i % 10 == 0:
                    pass

            # Stream citations
            yield 'data: {"type": "citations", "citations": '
            import json

            citations_data = [
                {
                    "source": c.get("source"),
                    "content": c.get("content"),
                    "relevance": c.get("relevance"),
                }
                for c in agent_response.citations
            ]
            yield json.dumps(citations_data)
            yield '}\n\n'

            # Stream metadata
            yield 'data: {"type": "metadata", '
            yield json.dumps({
                "confidence": agent_response.confidence,
                "mode": agent_response.mode,
            })
            yield '}\n\n'

            # Stream end
            yield 'data: {"type": "end"}\n\n'

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield f'data: {{"type": "error", "error": "{str(e)}"}}\n\n'

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.get("/health")
async def chat_health() -> dict:
    """Health check for chat endpoint."""
    try:
        agent = get_agent()
        tools = agent.tool_manager.list_tools()
        return {
            "status": "healthy",
            "tools": tools,
            "tool_count": len(tools),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
