"""Project Agent - Specialist for project management domain.

Responsible ONLY for:
- Project status and metadata
- Milestones and deliverables
- Customer information
- Project timeline overview
- Deployment information

This agent does NOT handle:
- Financial data (see FinanceAgent)
- Risks/blockers (see RiskAgent)
- Detailed schedules (see ScheduleAgent)
- Documents (see DocumentAgent)
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base_agent import Agent, AgentResponse, Citation
from app.ai.guardrails import Guardrails
from app.tools.project_lookup_tool import ProjectLookupTool
from app.execution_studio import auto_trace, emit_event

logger = logging.getLogger(__name__)


class ProjectAgent(Agent):
    """Specialist agent for project management domain."""

    DOMAIN = "project_management"
    DESCRIPTION = "Answers questions about project status, milestones, customer info, and deployment"
    VERSION = "2.0"

    def __init__(self, *args, **kwargs):
        """Initialize ProjectAgent."""
        super().__init__(*args, **kwargs)
        self.guardrails = Guardrails(strict_mode=False)

    def _register_tools(self) -> None:
        """Register tools for project domain."""
        self.tool_manager.register(ProjectLookupTool())

    def get_system_prompt(self) -> str:
        """Return system prompt for project management domain."""
        return """You are an expert project manager providing business intelligence.

Your expertise:
- Project status and health
- Timeline and schedule overview
- Customer relationships and satisfaction
- Deployment and rollout readiness
- Key metrics and KPIs

Guidelines:
1. Be concise and business-focused
2. Always ground answers in project data
3. Use current/accurate project status
4. Highlight risks only if they impact project status
5. For detailed schedules or budgets, defer to specialists

Answer only questions about project management.
For financial data, recommend the Finance Agent.
For risk analysis, recommend the Risk Agent.
For detailed schedules, recommend the Schedule Agent.
For documents, recommend the Document Agent.
"""

    @auto_trace(component="ProjectAgent", action="answer_query")
    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        context_data: Optional[dict] = None,
    ) -> AgentResponse:
        """Answer a question about project management.

        Args:
            query: User question
            project_id: Optional project to focus on
            context_data: Optional additional context

        Returns:
            AgentResponse with answer, citations, confidence
        """
        start_time = time.time()
        logger.info(f"ProjectAgent.answer: {query[:100]}...")

        try:
            # Step 1: Determine tools to use
            emit_event("ProjectAgent", "determine_tools")
            tool_calls = await self._determine_tools(query, project_id)
            logger.debug(f"Tool calls: {[t['tool'] for t in tool_calls]}")
            emit_event("ProjectAgent", "tools_selected", metadata={"tool_count": len(tool_calls)})

            # Step 2: Execute tools
            emit_event("ProjectAgent", "execute_tools")
            tool_results = await self._execute_tools(tool_calls)
            tool_names = [t["tool"] for t in tool_calls]
            logger.debug(f"Tool results: {len(tool_results)} tools executed")
            emit_event("ProjectAgent", "tools_executed", metadata={"tool_count": len(tool_names)})

            if not tool_results:
                # No tools returned data
                answer = (
                    "I don't have access to project data right now. "
                    "Please provide a specific project ID."
                )
                return await self.create_response(
                    answer=answer,
                    citations=[],
                    confidence=0.0,
                    tool_calls=tool_names,
                    context_length=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Step 3: Build context from tool results
            emit_event("ProjectAgent", "build_context")
            context = self._build_context(tool_results, query)
            context_length = len(context)
            emit_event("ProjectAgent", "context_built", metadata={"context_length": context_length})

            # Step 4: Generate response with LLM
            emit_event("ProjectAgent", "invoke_llm")
            system_prompt = self.get_system_prompt()
            llm_response = await self.llm_client.generate(
                messages=[
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {query}",
                    }
                ],
                system_prompt=system_prompt,
            )
            emit_event("ProjectAgent", "llm_response_received", metadata={"response_length": len(llm_response)})

            # Step 5: Extract citations
            emit_event("ProjectAgent", "extract_citations")
            citations = self._extract_citations(tool_results, llm_response)
            emit_event("ProjectAgent", "citations_extracted", metadata={"citation_count": len(citations)})

            # Step 6: Apply guardrails
            emit_event("ProjectAgent", "apply_guardrails")
            grounding_ok, grounding_score, _ = self.guardrails.ground_response(
                llm_response, context
            )
            hallucination_risk, _ = self.guardrails.check_hallucination(llm_response, context)
            confidence = self._calculate_confidence(hallucination_risk, grounding_ok, len(tool_names))
            emit_event("ProjectAgent", "guardrails_applied", metadata={
                "grounding_ok": grounding_ok,
                "hallucination_risk": hallucination_risk,
                "confidence": confidence
            })

            logger.info(
                f"ProjectAgent response: grounding={grounding_ok}, "
                f"hallucination_risk={hallucination_risk:.2f}, confidence={confidence:.2f}"
            )

            # Step 7: Return response
            return await self.create_response(
                answer=llm_response,
                citations=citations,
                confidence=confidence,
                tool_calls=tool_names,
                context_length=context_length,
                hallucination_risk=hallucination_risk,
                grounding_ok=grounding_ok,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"ProjectAgent.answer failed: {e}", exc_info=True)
            return await self.create_response(
                answer=f"Error: {str(e)}",
                citations=[],
                confidence=0.0,
                tool_calls=[],
                context_length=0,
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
            )

    async def _determine_tools(
        self,
        query: str,
        project_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Determine which tools to use.

        Args:
            query: User query
            project_id: Optional project ID

        Returns:
            List of tool calls
        """
        tool_calls = []

        # Project lookup: needed for status, metadata, customer info
        if any(
            word in query.lower()
            for word in ["project", "status", "customer", "summary", "overview", "deployment"]
        ):
            if project_id:
                tool_calls.append(
                    {
                        "tool": "project_lookup",
                        "params": {"project_id": project_id},
                    }
                )

        return tool_calls or [{"tool": "project_lookup", "params": {"project_id": project_id}}]

    def _build_context(self, tool_results, query: str) -> str:
        """Build context string from tool results.

        Args:
            tool_results: List of ToolResult or Dict of tool -> ToolResult
            query: Original query

        Returns:
            Context string for LLM
        """
        context_parts = []

        # Handle both list and dict formats
        items = tool_results if isinstance(tool_results, list) else tool_results.values()

        for i, result in enumerate(items):
            if result.success and result.data:
                tool_name = f"Tool {i}" if isinstance(tool_results, list) else "Result"
                context_parts.append(f"From {tool_name}:\n{result.data}")

        return "\n\n".join(context_parts)
