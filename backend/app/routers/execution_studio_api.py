"""Execution Studio API - HTTP endpoints for visualization and tracing.

Provides:
- GET /execution-studio/requests - Recent requests
- GET /execution-studio/requests/{id} - Trace for request
- GET /execution-studio/requests/{id}/events - Events with pagination
- GET /execution-studio/requests/{id}/metrics - Aggregated metrics
- GET /execution-studio/requests/{id}/download - Download event log as JSON
- DELETE /execution-studio/history - Clear old events
- GET /execution-studio/explanations/{component} - Learning content
"""

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.execution_studio import (
    get_event_store,
    get_component_explanation,
    get_semantic_event_store,
)
from app.execution_studio.component_registry import get_component_metadata, get_all_components
from app.execution_studio.component_learning import get_component_learning, get_all_learning

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


@router.get("/requests/{request_id}/download")
async def download_event_log(request_id: str) -> StreamingResponse:
    """Download event log for a request as JSON file.

    Args:
        request_id: Request ID to download

    Returns:
        JSON file with all events
    """
    try:
        events = store.get_request_trace(request_id)

        if not events:
            raise HTTPException(status_code=404, detail="Request not found")

        # Create JSON export
        export_data = {
            "request_id": request_id,
            "exported_at": datetime.utcnow().isoformat(),
            "event_count": len(events),
            "events": [e.to_dict() for e in events],
        }

        # Stream as JSON file download
        json_str = json.dumps(export_data, indent=2, default=str)

        return StreamingResponse(
            iter([json_str]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=execution_{request_id}.json"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download event log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def clear_old_events(days: int = Query(7, ge=1, le=90)) -> dict:
    """Delete old execution events to save storage.

    Args:
        days: Delete events older than this many days (default 7, max 90)

    Returns:
        Dict with count of deleted events
    """
    try:
        deleted_count = store.delete_old_events(days=days)

        logger.info(f"Cleared {deleted_count} events older than {days} days")

        return {
            "status": "success",
            "deleted_count": deleted_count,
            "days_retained": days,
            "message": f"Deleted {deleted_count} events older than {days} days"
        }
    except Exception as e:
        logger.error(f"Failed to clear event history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic/requests/{request_id}/trace")
async def get_semantic_request_trace(request_id: str) -> dict:
    """Get complete semantic execution trace for a request.

    Returns rich, self-describing events with:
    - Purpose and reason for each event
    - Input/output summaries
    - Component relationships
    - Decision rationale
    - Complete execution narrative

    Args:
        request_id: Request ID to retrieve

    Returns:
        Dict with semantic events forming the execution narrative
    """
    try:
        semantic_store = get_semantic_event_store()
        events = semantic_store.get_request_trace(request_id)

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
        logger.error(f"Failed to get semantic request trace: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic/requests/{request_id}/graph")
async def get_execution_graph(request_id: str) -> dict:
    """Get execution graph reconstructed from semantic events.

    Builds a complete DAG showing:
    - Parent-child relationships
    - Parallel execution paths
    - Component dependencies
    - Data flow
    - Decision branches

    Args:
        request_id: Request ID

    Returns:
        Graph structure with nodes and edges
    """
    try:
        semantic_store = get_semantic_event_store()
        events = semantic_store.get_request_trace(request_id)

        if not events:
            raise HTTPException(status_code=404, detail="Request not found")

        # Build graph from events
        nodes = []
        edges = []
        event_map = {str(e.event_id): e for e in events}

        for event in events:
            # Create node
            node = {
                "id": str(event.event_id),
                "label": f"{event.component}::{event.action}",
                "component": event.component,
                "component_type": event.component_type.value,
                "purpose": event.purpose,
                "status": event.status.value,
                "duration_ms": event.duration_ms,
            }
            nodes.append(node)

            # Parent-child edge
            if event.parent_event_id:
                edges.append({
                    "source": event.parent_event_id,
                    "target": str(event.event_id),
                    "relationship": "parent-child",
                    "label": f"{event.sequence_in_parent}",
                })

            # Related events
            for related in event.related_events:
                edges.append({
                    "source": str(event.event_id),
                    "target": related.event_id,
                    "relationship": related.relationship.value,
                    "label": related.description,
                })

            # Dependencies (component-level)
            for dep in event.dependencies:
                # Find events from that component
                for other_event in events:
                    if other_event.component == dep.component:
                        edges.append({
                            "source": str(other_event.event_id),
                            "target": str(event.event_id),
                            "relationship": "dependency",
                            "label": dep.reason,
                        })
                        break

        return {
            "request_id": request_id,
            "nodes": nodes,
            "edges": edges,
            "event_count": len(events),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/architecture/{request_id}/diagram")
async def get_architecture_diagram(request_id: str) -> dict:
    """Get architecture diagram for a request.

    Returns component layout, connections, and real-time metrics.

    Args:
        request_id: Request ID to get architecture for

    Returns:
        Dict with components, connections, and statistics
    """
    try:
        # Try semantic events first, fall back to old events
        semantic_store = get_semantic_event_store()
        events = semantic_store.get_request_trace(request_id)

        # If no semantic events, try old event store
        if not events:
            events = store.get_request_trace(request_id)

        if not events:
            raise HTTPException(status_code=404, detail="Request not found")

        # Build component status map
        components = {}
        connections = []
        event_indices = {}

        for idx, event in enumerate(events):
            event_indices[str(event.event_id)] = idx

            # Get component type (handle both old and new events)
            component_type = "unknown"
            if hasattr(event, "component_type"):
                component_type = event.component_type.value if hasattr(event.component_type, "value") else str(event.component_type)

            # Get metadata
            metadata = get_component_metadata(event.component)

            # Create or update component
            component_id = event.component
            if component_id not in components:
                components[component_id] = {
                    "id": event.component,
                    "display_name": metadata.display_name,
                    "type": component_type,
                    "icon": metadata.icon,
                    "color": metadata.color,
                    "position": list(metadata.position),
                    "status": event.status.value if hasattr(event.status, "value") else event.status,
                    "duration_ms": event.duration_ms,
                    "metrics": {
                        "tokens": 0,
                        "cost": 0.0,
                        "errors": 0,
                    }
                }
            else:
                # Update status if this event is more recent and different
                status_val = event.status.value if hasattr(event.status, "value") else event.status
                if status_val != "started":
                    components[component_id]["status"] = status_val
                components[component_id]["duration_ms"] += event.duration_ms

            # Aggregate metrics
            components[component_id]["metrics"]["tokens"] += event.tokens_used
            components[component_id]["metrics"]["cost"] += event.cost
            status_val = event.status.value if hasattr(event.status, "value") else event.status
            if status_val == "failed":
                components[component_id]["metrics"]["errors"] += 1

            # Add parent-child connection
            if hasattr(event, "parent_event_id") and event.parent_event_id:
                parent_event = next(
                    (e for e in events if str(e.event_id) == event.parent_event_id),
                    None
                )
                if parent_event and parent_event.component != event.component:
                    # Only add connection if not already present
                    conn_key = (parent_event.component, event.component)
                    if not any(
                        c["from"] == conn_key[0] and c["to"] == conn_key[1]
                        for c in connections
                    ):
                        connections.append({
                            "from": parent_event.component,
                            "to": event.component,
                            "type": "parent-child",
                            "flow_type": "direct",
                        })

        # Calculate statistics
        total_duration = max((e.duration_ms for e in events), default=0)
        total_tokens = sum(e.tokens_used for e in events)
        total_cost = sum(e.cost for e in events)
        active_components = sum(1 for c in components.values() if c["status"] == "completed")
        errors = sum(c["metrics"]["errors"] for c in components.values())

        return {
            "components": list(components.values()),
            "connections": connections,
            "statistics": {
                "total_duration_ms": total_duration,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "components_active": active_components,
                "total_components": len(components),
                "errors": errors,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get architecture diagram: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/components")
async def list_all_components() -> dict:
    """Get metadata for all registered components.

    Useful for Learn Mode and understanding system architecture.

    Returns:
        Dict with all component metadata
    """
    try:
        all_components = get_all_components()
        return {
            "count": len(all_components),
            "components": {
                name: {
                    "display_name": meta.display_name,
                    "type": meta.component_type,
                    "icon": meta.icon,
                    "description": meta.description,
                    "color": meta.color,
                }
                for name, meta in all_components.items()
            }
        }
    except Exception as e:
        logger.error(f"Failed to list components: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learn/components/{component_name}")
async def get_component_learning_info(component_name: str) -> dict:
    """Get learning content for a specific component.

    Provides educational information, design patterns, tips, and best practices.

    Args:
        component_name: Component name to learn about

    Returns:
        Dict with component learning content
    """
    try:
        learning = get_component_learning(component_name)
        return {
            "component": learning.component,
            "purpose": learning.purpose,
            "description": learning.description,
            "design_pattern": learning.design_pattern,
            "workflow_steps": learning.workflow_steps,
            "when_to_use": learning.when_to_use,
            "when_not_to_use": learning.when_not_to_use,
            "performance_tips": learning.performance_tips,
            "common_mistakes": learning.common_mistakes,
            "related_components": learning.related_components,
        }
    except Exception as e:
        logger.error(f"Failed to get component learning: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/before-after/{request_id}")
async def get_before_after_visualization(request_id: str) -> dict:
    """Get before/after state transformations for each component.

    Shows what data came in and what was produced for every step in execution.
    Useful for understanding data flow and debugging.

    Args:
        request_id: Request ID to visualize

    Returns:
        Dict with component transformations
    """
    try:
        # Try semantic events first (have structured I/O)
        semantic_store = get_semantic_event_store()
        events = semantic_store.get_request_trace(request_id)

        # Fallback to old events if no semantic events
        if not events:
            events = store.get_request_trace(request_id)

        if not events:
            raise HTTPException(status_code=404, detail="Request not found")

        # Build before/after data for each component
        transformations = []

        for event in events:
            # Handle semantic events
            if hasattr(event, 'input') and hasattr(event, 'output'):
                transformations.append({
                    "component": event.component,
                    "component_type": getattr(event, 'component_type', 'unknown'),
                    "action": getattr(event, 'action', 'unknown'),
                    "status": event.status.value if hasattr(event.status, 'value') else event.status,
                    "input": {
                        "type": event.input.type if hasattr(event.input, 'type') else "unknown",
                        "description": event.input.description if hasattr(event.input, 'description') else "",
                        "key_fields": event.input.key_fields if hasattr(event.input, 'key_fields') else {},
                    },
                    "output": {
                        "type": event.output.type if hasattr(event.output, 'type') else "unknown",
                        "description": event.output.description if hasattr(event.output, 'description') else "",
                        "key_fields": event.output.key_fields if hasattr(event.output, 'key_fields') else {},
                        "confidence": getattr(event.output, 'confidence', 0.5) if hasattr(event, 'output') else 0.5,
                    },
                    "duration_ms": event.duration_ms,
                    "tokens_used": event.tokens_used,
                    "cost": event.cost,
                    "error": event.error if hasattr(event, 'error') else None,
                })
            else:
                # Fallback for old event format
                input_data = event.metadata.get('query') or event.metadata.get('input') or {}
                output_data = event.metadata.get('result') or event.metadata.get('output') or event.metadata.get('response') or {}

                transformations.append({
                    "component": event.component,
                    "component_type": "unknown",
                    "action": event.action,
                    "status": event.status.value if hasattr(event.status, 'value') else event.status,
                    "input": {
                        "type": "data",
                        "description": f"Input to {event.component}",
                        "key_fields": input_data if isinstance(input_data, dict) else {"value": str(input_data)},
                    },
                    "output": {
                        "type": "data",
                        "description": f"Output from {event.component}",
                        "key_fields": output_data if isinstance(output_data, dict) else {"value": str(output_data)},
                        "confidence": 0.5,
                    },
                    "duration_ms": event.duration_ms,
                    "tokens_used": event.tokens_used,
                    "cost": event.cost,
                    "error": event.error if hasattr(event, 'error') else None,
                })

        return {
            "request_id": request_id,
            "transformation_count": len(transformations),
            "transformations": transformations,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get before/after visualization: {e}", exc_info=True)
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
