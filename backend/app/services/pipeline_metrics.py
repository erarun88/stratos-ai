"""Pipeline metrics and monitoring.

Enables visibility into pipeline performance:
- Per-stage timing
- Success/failure rates
- Bottleneck identification
- Cost aggregation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.embedding import EmbeddingOperation

logger = logging.getLogger(__name__)


class PipelineMetrics:
    """Query and analyze embedding pipeline metrics."""

    def __init__(self, session: Session):
        self.session = session

    def get_stage_stats(self, stage: str = None, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for a stage or all stages.

        Args:
            stage: Specific stage to query (None = all stages)
            hours: Time window (default: last 24 hours)

        Returns:
            {
                "extraction": {
                    "total": 100,
                    "completed": 98,
                    "failed": 2,
                    "avg_duration_ms": 450,
                    "total_tokens": 1500000,
                    "total_cost": 45.00,
                },
                ...
            }
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        query = (
            self.session.query(
                EmbeddingOperation.operation_type,
                EmbeddingOperation.status,
                func.count().label("count"),
                func.avg(EmbeddingOperation.duration_ms).label("avg_duration_ms"),
                func.sum(EmbeddingOperation.tokens_used).label("total_tokens"),
                func.sum(EmbeddingOperation.cost_usd).label("total_cost"),
            )
            .where(EmbeddingOperation.created_at >= since)
            .group_by(EmbeddingOperation.operation_type, EmbeddingOperation.status)
        )

        if stage:
            query = query.where(EmbeddingOperation.operation_type == stage)

        rows = query.all()

        # Organize results
        results = {}
        for row in rows:
            op_type = row.operation_type
            if op_type not in results:
                results[op_type] = {
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "avg_duration_ms": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                }

            results[op_type]["total"] += row.count
            if row.status == "completed":
                results[op_type]["completed"] = row.count
            elif row.status == "failed":
                results[op_type]["failed"] = row.count

            if row.avg_duration_ms:
                results[op_type]["avg_duration_ms"] = int(row.avg_duration_ms)
            if row.total_tokens:
                results[op_type]["total_tokens"] = row.total_tokens
            if row.total_cost:
                results[op_type]["total_cost"] = float(row.total_cost)

        return results

    def get_bottlenecks(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Identify slowest stages.

        Returns stages ranked by average duration (slowest first).
        """
        stats = self.get_stage_stats(hours=hours)

        bottlenecks = [
            {
                "stage": stage,
                "avg_duration_ms": data["avg_duration_ms"],
                "failure_rate": (
                    data["failed"] / data["total"] * 100
                    if data["total"] > 0
                    else 0
                ),
                "completed": data["completed"],
            }
            for stage, data in stats.items()
        ]

        return sorted(bottlenecks, key=lambda x: x["avg_duration_ms"], reverse=True)

    def get_cost_breakdown(self, hours: int = 24) -> Dict[str, Any]:
        """Get cost breakdown by stage.

        Shows where the money is going in the pipeline.
        """
        stats = self.get_stage_stats(hours=hours)

        total_cost = sum(data["total_cost"] for data in stats.values())
        breakdown = {}

        for stage, data in stats.items():
            cost = data["total_cost"]
            pct = (cost / total_cost * 100) if total_cost > 0 else 0
            breakdown[stage] = {
                "cost_usd": cost,
                "percentage": pct,
                "cost_per_doc": (
                    cost / data["completed"] if data["completed"] > 0 else 0
                ),
            }

        return {
            "total_cost_usd": total_cost,
            "breakdown": breakdown,
        }

    def get_document_stats(self, document_id: int) -> Dict[str, Any]:
        """Get detailed stats for a specific document.

        Shows the journey through the pipeline.
        """
        doc = self.session.get(Document, document_id)
        if not doc:
            return {}

        operations = (
            self.session.query(EmbeddingOperation)
            .where(EmbeddingOperation.document_id == document_id)
            .order_by(EmbeddingOperation.created_at)
            .all()
        )

        stages = {}
        total_duration = 0

        for op in operations:
            stage = op.operation_type
            if stage not in stages:
                stages[stage] = []

            stages[stage].append({
                "status": op.status,
                "duration_ms": op.duration_ms,
                "tokens_used": op.tokens_used,
                "cost_usd": float(op.cost_usd) if op.cost_usd else None,
                "error": op.error_message,
                "timestamp": op.created_at.isoformat(),
            })

            if op.duration_ms:
                total_duration += op.duration_ms

        return {
            "document_id": document_id,
            "title": doc.title,
            "embedding_status": doc.embedding_status,
            "total_tokens": doc.token_count,
            "total_cost": doc.embedding_cost,
            "embedded_at": doc.embedded_at.isoformat() if doc.embedded_at else None,
            "total_duration_ms": total_duration,
            "stages": stages,
        }

    def get_health_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get overall pipeline health summary.

        Good for dashboards and monitoring.
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        # Overall stats
        total_docs = (
            self.session.query(func.count(Document.id))
            .where(Document.created_at >= since)
            .scalar() or 0
        )

        completed = (
            self.session.query(func.count(Document.id))
            .where(
                (Document.embedding_status == "completed")
                & (Document.created_at >= since)
            )
            .scalar() or 0
        )

        failed = (
            self.session.query(func.count(Document.id))
            .where(
                (Document.embedding_status == "failed")
                & (Document.created_at >= since)
            )
            .scalar() or 0
        )

        processing = (
            self.session.query(func.count(Document.id))
            .where(
                (Document.embedding_status == "processing")
                & (Document.created_at >= since)
            )
            .scalar() or 0
        )

        # Cost
        total_cost = (
            self.session.query(func.sum(Document.embedding_cost))
            .where(
                (Document.embedding_status == "completed")
                & (Document.created_at >= since)
            )
            .scalar() or 0.0
        )

        # Calculate rates
        success_rate = (completed / total_docs * 100) if total_docs > 0 else 0
        failure_rate = (failed / total_docs * 100) if total_docs > 0 else 0

        # Identify bottlenecks
        bottlenecks = self.get_bottlenecks(hours=hours)
        slowest_stage = bottlenecks[0] if bottlenecks else None

        return {
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_documents": total_docs,
                "completed": completed,
                "failed": failed,
                "processing": processing,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2),
            },
            "costs": {
                "total_cost_usd": round(total_cost, 4),
                "cost_per_document": (
                    round(total_cost / completed, 4) if completed > 0 else 0
                ),
            },
            "performance": {
                "slowest_stage": slowest_stage,
                "bottlenecks": bottlenecks[:3],
            },
        }
