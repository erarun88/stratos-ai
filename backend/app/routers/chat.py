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
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.agents import (
    DocumentAgent,
    FinanceAgent,
    ProjectAgent,
    RiskAgent,
    ScheduleAgent,
    SupervisorAgent,
)
from app.agents.agent_registry import get_agent_registry, init_default_agents
from app.execution_studio import ExecutionEvent, get_event_bus, get_event_store

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
    """Chat response with Phase D (Reflection) and Phase E (Approval) support."""

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

    # Phase D - Reflection
    reflection_applied: bool = Field(
        default=False, description="Whether reflection improved the response"
    )

    # Phase E - Approval
    approval_required: bool = Field(
        default=False, description="Whether action requires approval before execution"
    )
    approval_id: Optional[str] = Field(
        default=None, description="Approval request ID if approval required"
    )
    approval_reason: Optional[str] = Field(
        default=None, description="Reason why approval is required"
    )

    metadata: dict = Field(default_factory=dict, description="Additional metadata")


# Global supervisor instance
_supervisor = None


def get_supervisor() -> SupervisorAgent:
    """Get or create the global Supervisor instance.

    Initializes all specialist agents from the Agent Registry.
    If registry is empty, initializes with default agents.
    """
    global _supervisor
    if _supervisor is None:
        logger.info("Initializing Supervisor Agent with registered agents...")

        # Get agent registry (create if doesn't exist)
        registry = get_agent_registry()

        # If no agents registered, initialize defaults
        if registry.count() == 0:
            logger.info("No agents in registry, initializing defaults...")
            init_default_agents()

        # Create supervisor
        supervisor = SupervisorAgent()

        # Register all enabled agents from registry
        enabled_domains = registry.get_enabled_domains()
        logger.info(f"Registering {len(enabled_domains)} enabled agents...")

        for domain in enabled_domains:
            agent = registry.get(domain)
            if agent:
                supervisor.register_agent(domain, agent)
                logger.info(f"  Registered: {domain}")

        _supervisor = supervisor
        logger.info(
            f"Supervisor initialized with {len(supervisor.list_agents())} agents "
            f"from registry"
        )

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
    request_id = str(uuid.uuid4())
    bus = get_event_bus()
    store = get_event_store()

    logger.info(f"Chat endpoint: {request.query[:100]}... (request_id={request_id[:8]}..., project_id={request.project_id})")

    # Publish start event
    start_event = ExecutionEvent(
        request_id=request_id,
        component="ChatEndpoint",
        action="receive_query",
        metadata={"query": request.query, "project_id": request.project_id}
    )
    bus.publish(start_event)

    try:
        supervisor = get_supervisor()

        # Route through Supervisor (orchestrates specialist agents)
        # Pass request_id so Supervisor can publish events
        supervisor_response = await supervisor.answer(
            query=request.query,
            project_id=request.project_id,
            request_id=request_id,  # NEW: Pass request_id for tracing
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
            reflection_applied=supervisor_response.get("reflection_applied", False),
            approval_required=supervisor_response.get("approval_required", False),
            approval_id=supervisor_response.get("approval_id"),
            approval_reason=supervisor_response.get("approval_reason"),
            metadata={
                **supervisor_response.get("metadata", {}),
                "elapsed_ms": elapsed_ms,
                "request_id": request_id,
            },
        )

        # Publish completion event
        end_event = ExecutionEvent(
            request_id=request_id,
            component="ChatEndpoint",
            action="return_response",
            status="completed",
            duration_ms=elapsed_ms,
            metadata={"agents_used": response.agents_used}
        )
        bus.publish(end_event)
        store.store_event(end_event)

        logger.info(
            f"Chat endpoint complete: request_id={request_id[:8]}..., agents={len(response.agents_used)} "
            f"confidence={response.confidence:.2f} elapsed_ms={elapsed_ms:.0f}"
        )

        return response

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)

        # Publish error event
        error_event = ExecutionEvent(
            request_id=request_id,
            component="ChatEndpoint",
            action="return_response",
            status="failed",
            error=str(e),
            duration_ms=(time.time() - start_time) * 1000
        )
        bus.publish(error_event)
        store.store_event(error_event)

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

            # Stream metadata (including Phase D and E)
            yield 'data: {"type": "metadata", '
            yield json.dumps({
                "confidence": supervisor_response.get("confidence", 0.0),
                "agents_used": supervisor_response.get("agents_used", []),
                "reflection_applied": supervisor_response.get("reflection_applied", False),
                "approval_required": supervisor_response.get("approval_required", False),
                "approval_id": supervisor_response.get("approval_id"),
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
    """List available specialist agents with metadata.

    Returns both the supervisor's active agents and the full registry metadata.
    """
    try:
        supervisor = get_supervisor()
        registry = get_agent_registry()

        agents = supervisor.list_agents()
        metadata = registry.list_metadata()

        return {
            "agents": agents,
            "count": len(agents),
            "registry": {
                "total": registry.count(),
                "enabled": len(registry.get_enabled_domains()),
                "metadata": metadata,
            },
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/status")
async def get_registry_status() -> dict:
    """Get Agent Registry status and configuration."""
    try:
        registry = get_agent_registry()
        metadata = registry.list_metadata()

        return {
            "total_agents": registry.count(),
            "enabled_agents": len(registry.get_enabled_domains()),
            "disabled_agents": registry.count() - len(registry.get_enabled_domains()),
            "enabled_domains": registry.get_enabled_domains(),
            "metadata": metadata,
        }
    except Exception as e:
        logger.error(f"Error getting registry status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/registry/agents/{domain}/enable")
async def enable_agent(domain: str) -> dict:
    """Enable an agent in the registry.

    Args:
        domain: Agent domain name

    Returns:
        Updated registry status
    """
    try:
        registry = get_agent_registry()
        success = registry.enable(domain)

        if not success:
            raise HTTPException(status_code=404, detail=f"Agent not found: {domain}")

        logger.info(f"Enabled agent: {domain}")

        return {
            "success": True,
            "domain": domain,
            "enabled": True,
            "message": f"Agent '{domain}' enabled",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/registry/agents/{domain}/disable")
async def disable_agent(domain: str) -> dict:
    """Disable an agent in the registry.

    Args:
        domain: Agent domain name

    Returns:
        Updated registry status
    """
    try:
        registry = get_agent_registry()
        success = registry.disable(domain)

        if not success:
            raise HTTPException(status_code=404, detail=f"Agent not found: {domain}")

        logger.info(f"Disabled agent: {domain}")

        return {
            "success": True,
            "domain": domain,
            "enabled": False,
            "message": f"Agent '{domain}' disabled",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health() -> dict:
    """Health check for chat endpoint."""
    try:
        supervisor = get_supervisor()
        registry = get_agent_registry()
        agents = supervisor.list_agents()

        return {
            "status": "healthy",
            "supervisor": "operational",
            "agents_active": len(agents),
            "agents_registered": registry.count(),
            "agents": agents,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }
