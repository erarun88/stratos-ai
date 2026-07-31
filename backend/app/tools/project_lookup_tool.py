"""Tool for looking up project information.

Retrieves project metadata, status, dates, and team information.
"""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine
from app.models.engineer import Engineer
from app.models.project import Project
from app.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class ProjectLookupTool(Tool):
    """Look up project information by ID or name."""

    name = "project_lookup"
    description = "Retrieve project information: status, dates, manager, customer, team members. Provide project_id or project_name."

    async def execute(
        self,
        project_id: Optional[int] = None,
        project_name: Optional[str] = None,
    ) -> ToolResult:
        """Look up project information.

        Args:
            project_id: Project ID to look up
            project_name: Project name to look up (if ID not provided)

        Returns:
            ToolResult with project data
        """
        try:
            if not project_id and not project_name:
                return ToolResult(success=False, error="Must provide project_id or project_name")

            with Session(engine) as session:
                project = None

                if project_id:
                    project = session.get(Project, project_id)
                elif project_name:
                    statement = select(Project).where(Project.name.ilike(f"%{project_name}%"))
                    project = session.execute(statement).scalar_one_or_none()

                if not project:
                    return ToolResult(
                        success=False,
                        error=f"Project not found (id={project_id}, name={project_name})",
                    )

                # Fetch project engineers
                engineers_statement = select(Engineer).where(Engineer.project_id == project.id)
                engineers = session.execute(engineers_statement).scalars().all()

                project_data = {
                    "id": project.id,
                    "name": project.name,
                    "customer": project.customer,
                    "status": project.status,
                    "project_manager": project.project_manager,
                    "start_date": project.start_date.isoformat() if project.start_date else None,
                    "end_date": project.end_date.isoformat() if project.end_date else None,
                    "description": project.description,
                    "budget": float(project.budget) if project.budget else None,
                    "team_size": len(engineers),
                    "team_members": [
                        {
                            "id": e.id,
                            "name": e.name,
                            "email": e.email,
                            "role": e.role,
                            "status": e.status,
                        }
                        for e in engineers
                    ],
                }

                logger.info(f"Project lookup: {project.name} (id={project.id})")
                return ToolResult(
                    success=True,
                    data=project_data,
                    metadata={"project_id": project.id},
                )

        except Exception as e:
            logger.error(f"Project lookup error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))
