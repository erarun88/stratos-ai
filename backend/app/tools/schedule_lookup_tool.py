"""Tool for looking up project schedule and milestones.

Retrieves project timeline, key dates, and schedule status.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.database import engine
from app.models.project import Project
from app.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class ScheduleLookupTool(Tool):
    """Look up project schedule and milestone dates."""

    name = "schedule_lookup"
    description = "Retrieve project timeline, key dates, and schedule status. Calculate schedule variance (ahead/behind). Provide project_id."

    async def execute(
        self,
        project_id: int,
    ) -> ToolResult:
        """Look up schedule for a project.

        Args:
            project_id: Project ID

        Returns:
            ToolResult with project timeline and schedule status
        """
        try:
            if not project_id:
                return ToolResult(success=False, error="project_id is required")

            with Session(engine) as session:
                project = session.get(Project, project_id)
                if not project:
                    return ToolResult(success=False, error=f"Project {project_id} not found")

                today = datetime.now().date()
                schedule_data = {
                    "project_id": project.id,
                    "project_name": project.name,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "status": project.status,
                }

                # Calculate schedule variance if dates exist
                if project.start_date and project.end_date:
                    total_duration = (project.end_date - project.start_date).days
                    elapsed_duration = (today - project.start_date).days
                    remaining_duration = (project.end_date - today).days

                    schedule_data.update({
                        "total_duration_days": total_duration,
                        "elapsed_duration_days": max(0, elapsed_duration),
                        "remaining_duration_days": max(0, remaining_duration),
                        "progress_percent": min(
                            100,
                            max(0, int((elapsed_duration / total_duration * 100) if total_duration > 0 else 0))
                        ),
                        "on_schedule": remaining_duration >= 0,
                        "days_ahead_behind": remaining_duration,  # positive = ahead, negative = behind
                    })

                logger.info(f"Schedule lookup: project {project_id} ({project.name})")

                return ToolResult(
                    success=True,
                    data=schedule_data,
                    metadata={
                        "project_id": project.id,
                        "on_schedule": schedule_data.get("on_schedule", None),
                    },
                )

        except Exception as e:
            logger.error(f"Schedule lookup error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))
