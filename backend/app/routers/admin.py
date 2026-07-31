"""Admin endpoints for monitoring and debugging the embedding pipeline.

Exposes metrics, pipeline health, bottleneck analysis, and diagnostic tools.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_session
from app.services.pipeline_metrics import PipelineMetrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# Response models
class StageStats(BaseModel):
    """Statistics for a single pipeline stage."""
    completed: int
    failed: int
    avg_duration_ms: int
    total_tokens: Optional[int]
    total_cost: float


class PipelineHealth(BaseModel):
    """Overall pipeline health."""
    total_documents: int
    completed: int
    failed: int
    processing: int
    success_rate: float
    failure_rate: float


class CostBreakdown(BaseModel):
    """Cost breakdown by stage."""
    cost_usd: float
    percentage: float
    cost_per_doc: float


class HealthSummary(BaseModel):
    """Complete health summary for dashboard."""
    period_hours: int
    summary: PipelineHealth
    costs: dict
    performance: dict


@router.get("/pipeline/health", response_model=HealthSummary)
def get_pipeline_health(
    hours: int = Query(24, ge=1, le=720),
    session: Session = Depends(get_session),
):
    """Get overall pipeline health and metrics.

    Shows:
    - Documents processed, completed, failed, processing
    - Success/failure rates
    - Total costs and per-document costs
    - Bottleneck analysis (slowest stages)
    """
    metrics = PipelineMetrics(session)
    return metrics.get_health_summary(hours=hours)


@router.get("/pipeline/stages")
def get_stage_stats(
    stage: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),
    session: Session = Depends(get_session),
):
    """Get detailed statistics for each pipeline stage.

    Shows per-stage:
    - Success/failure counts
    - Average duration
    - Total tokens processed
    - Total costs

    Use ?stage=extraction to filter to one stage.
    """
    metrics = PipelineMetrics(session)
    return metrics.get_stage_stats(stage=stage, hours=hours)


@router.get("/pipeline/bottlenecks")
def get_bottlenecks(
    hours: int = Query(24, ge=1, le=720),
    session: Session = Depends(get_session),
):
    """Identify bottlenecks in the pipeline.

    Returns stages ranked by average duration (slowest first),
    plus their failure rates.

    Use this to find optimization opportunities.
    """
    metrics = PipelineMetrics(session)
    return {
        "period_hours": hours,
        "bottlenecks": metrics.get_bottlenecks(hours=hours),
    }


@router.get("/pipeline/costs")
def get_cost_breakdown(
    hours: int = Query(24, ge=1, le=720),
    session: Session = Depends(get_session),
):
    """Get cost breakdown by stage.

    Shows where the OpenAI API costs are coming from.

    Use this to:
    - Budget for OpenAI usage
    - Identify cost-saving opportunities
    - Track spending trends
    """
    metrics = PipelineMetrics(session)
    return metrics.get_cost_breakdown(hours=hours)


@router.get("/documents/{document_id}/pipeline")
def get_document_pipeline(
    document_id: int,
    session: Session = Depends(get_session),
):
    """Get detailed pipeline stats for a specific document.

    Shows the journey through the pipeline:
    - Which stages completed
    - Which stages failed (and why)
    - Duration of each stage
    - Tokens and costs for each stage

    Use this for debugging a specific document's processing.
    """
    metrics = PipelineMetrics(session)
    stats = metrics.get_document_stats(document_id)
    if not stats:
        return {"error": f"Document {document_id} not found"}
    return stats


@router.post("/pipeline/retry/{document_id}")
def retry_document(
    document_id: int,
    session: Session = Depends(get_session),
):
    """Manually retry a failed document.

    Sets embedding_status back to 'queued' so the embedding scheduler
    will pick it up on the next run.

    Smart retry: If the checkpoint system is enabled, retries resume
    from the last completed stage (not from the beginning).
    """
    from app.models.document import Document

    doc = session.get(Document, document_id)
    if not doc:
        return {"error": f"Document {document_id} not found"}

    old_status = doc.embedding_status
    doc.embedding_status = "queued"
    doc.embedding_error = None
    session.commit()

    logger.info(
        f"Manually retried document {document_id} "
        f"(was: {old_status}, now: queued)"
    )

    return {
        "document_id": document_id,
        "previous_status": old_status,
        "new_status": "queued",
        "message": "Document will be reprocessed on next scheduler run",
    }


@router.get("/pipeline/diagnostics")
def get_diagnostics(
    session: Session = Depends(get_session),
):
    """Pipeline diagnostics and system health.

    Returns:
    - Database connectivity
    - Total documents by status
    - Pending vs. completed
    - Orphaned documents (stuck in 'processing')
    """
    from sqlalchemy import func, select, text
    from app.models.document import Document

    try:
        # Test DB connection
        session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {e}"

    # Document status breakdown
    statuses = {}
    for status in ["queued", "processing", "completed", "failed"]:
        count = (
            session.query(func.count(Document.id))
            .where(Document.embedding_status == status)
            .scalar() or 0
        )
        statuses[status] = count

    # Identify orphans (processing > 10 minutes)
    from datetime import timedelta, datetime
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    orphans = (
        session.query(func.count(Document.id))
        .where(
            (Document.embedding_status == "processing")
            & (Document.updated_at < cutoff)
        )
        .scalar() or 0
    )

    return {
        "database": db_status,
        "document_status": statuses,
        "orphaned_documents": orphans,
        "notes": (
            "Orphaned documents are stuck in 'processing'. "
            "This can happen if a worker crashes. Use /retry to restart them."
        ),
    }
