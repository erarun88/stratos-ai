"""Execution Studio API - HTTP endpoints for visualization and tracing.

Provides:
- GET /execution-studio/requests - Recent requests
- GET /execution-studio/requests/{id} - Trace for request
- GET /execution-studio/requests/{id}/events - Events with pagination
- GET /execution-studio/requests/{id}/metrics - Aggregated metrics
- GET /execution-studio/explanations/{component} - Learning content
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.execution_studio import get_event_store, get_component_explanation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/execution-studio", tags=["execution-studio"])

store = get_event_store()


@router.get("/requests")
async def get_recent_requests(
    limit: int = Query(50, ge=1, le=100),
    hours: int = Query(24, ge=1, le=168),
) -> dict:
    """Get recent request IDs.

    Args:
        limit: Max requests to return (default 50, max 100)
        hours: Only include requests from last N hours (default 24)

    Returns:
        Dict with list of request IDs
    """
    try:
        request_ids = store.get_recent_requests(limit=limit, hours=hours)
        return {
            "requests": request_ids,
            "count": len(request_ids),
        }
    except Exception as e:
        logger.error(f"Failed to get recent requests: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}")
async def get_request_trace(request_id: str) -> dict:
    """Get complete trace for a request.

    Args:
        request_id: Request ID to retrieve

    Returns:
        Dict with all events for the request
    """
    try:
        events = store.get_request_trace(request_id)

        if not events:
            raise HTTPException(status_code=404, detail="Request not found")

        return {
            "request_id": request_id,
            "event_count": len(events),
            "events": [e.to_dict() for e in events],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get request trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}/events")
async def get_request_events(
    request_id: str,
    component: Optional[str] = Query(None, description="Filter by component"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
) -> dict:
    """Get paginated events for a request.

    Args:
        request_id: Request ID
        component: Optional component filter
        skip: Number of events to skip
        limit: Max events to return

    Returns:
        Dict with paginated events
    """
    try:
        if component:
            events = store.get_component_events(request_id, component)
        else:
            events = store.get_request_trace(request_id)

        if not events:
            raise HTTPException(status_code=404, detail="Request not found")

        # Paginate
        paginated = events[skip : skip + limit]

        return {
            "request_id": request_id,
            "component_filter": component,
            "total_count": len(events),
            "skip": skip,
            "limit": limit,
            "returned": len(paginated),
            "events": [e.to_dict() for e in paginated],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get request events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/requests/{request_id}/metrics")
async def get_request_metrics(request_id: str) -> dict:
    """Get aggregated metrics for a request trace.

    Args:
        request_id: Request ID

    Returns:
        Dict with trace metrics
    """
    try:
        metrics = store.get_trace_metrics(request_id)

        if metrics.event_count == 0:
            raise HTTPException(status_code=404, detail="Request not found")

        return metrics.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get request metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/explanations/{component}")
async def get_component_info(component: str) -> dict:
    """Get educational explanation for a component.

    Args:
        component: Component name

    Returns:
        Dict with component explanation or 404
    """
    try:
        explanation = get_component_explanation(component)

        if not explanation:
            raise HTTPException(
                status_code=404,
                detail=f"No explanation found for component: {component}",
            )

        return {
            "component": component,
            "purpose": explanation.purpose,
            "problem_solves": explanation.problem_solves,
            "can_skip": explanation.can_skip,
            "design_pattern": explanation.design_pattern,
            "advantages": explanation.advantages,
            "tradeoffs": explanation.tradeoffs,
            "related_components": explanation.related_components,
            "docs_link": explanation.docs_link,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get component explanation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def execution_studio_health() -> dict:
    """Health check for Execution Studio."""
    try:
        # Try to query recent requests as a health check
        store.get_recent_requests(limit=1)
        return {
            "status": "healthy",
            "component": "execution-studio",
            "message": "Event system operational",
        }
    except Exception as e:
        logger.error(f"Execution Studio health check failed: {e}")
        return {
            "status": "unhealthy",
            "component": "execution-studio",
            "error": str(e),
        }
