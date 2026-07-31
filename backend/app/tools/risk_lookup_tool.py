"""Tool for looking up project risks and issues.

Retrieves risks, blockers, and escalation items from project documents and metadata.
"""

import logging
from typing import Optional

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.database import engine
from app.models.project import Project
from app.tools.base import Tool, ToolResult

logger = logging.getLogger(__name__)


class RiskLookupTool(Tool):
    """Look up risks, blockers, and issues for a project."""

    name = "risk_lookup"
    description = "Retrieve project risks, blockers, and escalation items. Searches project documents for risk-related content. Provide project_id."

    async def execute(
        self,
        project_id: int,
    ) -> ToolResult:
        """Look up risks for a project.

        Args:
            project_id: Project ID

        Returns:
            ToolResult with list of risks from project documents
        """
        try:
            if not project_id:
                return ToolResult(success=False, error="project_id is required")

            with Session(engine) as session:
                project = session.get(Project, project_id)
                if not project:
                    return ToolResult(success=False, error=f"Project {project_id} not found")

                # Search documents for risk-related content using semantic search
                risk_keywords = ["risk", "blocker", "issue", "escalation", "delay", "problem"]

                all_risks = []

                for keyword in risk_keywords:
                    query_sql = f"""
                        SELECT
                            de.document_id,
                            d.title,
                            de.chunk_text,
                            de.chunk_index
                        FROM document_embeddings de
                        JOIN documents d ON de.document_id = d.id
                        WHERE d.deleted_at IS NULL
                            AND d.project_id = {project_id}
                            AND de.chunk_text ILIKE '%{keyword}%'
                        LIMIT 3
                    """
                    try:
                        results = session.execute(text(query_sql)).fetchall()
                        for doc_id, doc_title, chunk_text, chunk_idx in results:
                            all_risks.append({
                                "keyword": keyword,
                                "document": doc_title,
                                "content": chunk_text[:300],  # First 300 chars
                                "severity": "unknown",
                            })
                    except Exception:
                        # Silently skip if query fails
                        pass

                logger.info(f"Risk lookup: found {len(all_risks)} risks for project {project_id}")

                # Remove duplicates (same content from different keywords)
                unique_risks = []
                seen_content = set()
                for risk in all_risks:
                    content_hash = hash(risk["content"])
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        unique_risks.append(risk)

                return ToolResult(
                    success=True,
                    data={
                        "project_id": project_id,
                        "project_name": project.name,
                        "risk_count": len(unique_risks),
                        "risks": unique_risks[:10],  # Top 10
                    },
                    metadata={"risk_count": len(unique_risks)},
                )

        except Exception as e:
            logger.error(f"Risk lookup error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))
