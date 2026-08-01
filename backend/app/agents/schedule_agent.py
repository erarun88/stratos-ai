"""Schedule Agent - Specialist for schedule and timeline domain.

Responsible ONLY for:
- Project schedules and timelines
- Milestone tracking
- Delay analysis and impact
- Critical path analysis
- Completion forecasts
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base_agent import Agent, AgentResponse
from app.ai.guardrails import Guardrails
from app.tools.schedule_lookup_tool import ScheduleLookupTool
from app.execution_studio import auto_trace, emit_event

logger = logging.getLogger(__name__)


class ScheduleAgent(Agent):
    """Specialist agent for schedule and timeline domain."""

    DOMAIN = "schedule"
    DESCRIPTION = "Answers questions about project schedules, milestones, delays, and timelines"
    VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        """Initialize ScheduleAgent."""
        super().__init__(*args, **kwargs)
        self.guardrails = Guardrails(strict_mode=False)

    def _register_tools(self) -> None:
        """Register tools for schedule domain."""
        self.tool_manager.register(ScheduleLookupTool())

    def get_system_prompt(self) -> str:
        """Return system prompt for schedule domain."""
        return """You are a senior project scheduler and timeline expert.

Your expertise:
- Project schedules and critical path analysis
- Milestone planning and tracking
- Delay analysis and impact assessment
- Schedule forecasting
- Resource allocation timeline planning

Guidelines:
1. Always provide concrete dates and timelines
2. Highlight critical path items
3. Assess delay impact
4. Suggest schedule optimization
5. Use clear timeline formatting

For project status, refer to the Project Agent.
For financial impact of delays, refer to the Finance Agent.
For risk mitigation, refer to the Risk Agent.
"""

    @auto_trace(component="ScheduleAgent", action="answer_query")
    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        context_data: Optional[dict] = None,
    ) -> AgentResponse:
        """Answer a question about project schedule.

        Args:
            query: User question
            project_id: Optional project to focus on
            context_data: Optional additional context

        Returns:
            AgentResponse with answer, citations, confidence
        """
        start_time = time.time()
        logger.info(f"ScheduleAgent.answer: {query[:100]}...")

        try:
            # Step 1: Determine tools to use
            emit_event("ScheduleAgent", "determine_tools")
            tool_calls = await self._determine_tools(query, project_id)
            logger.debug(f"Tool calls: {[t['tool'] for t in tool_calls]}")
            emit_event("ScheduleAgent", "tools_selected", metadata={"tool_count": len(tool_calls)})

            # Step 2: Execute tools
            emit_event("ScheduleAgent", "execute_tools")
            tool_results = await self._execute_tools(tool_calls)
            tool_names = [t["tool"] for t in tool_calls]
            logger.debug(f"Tool results: {len(tool_results)} tools executed")
            emit_event("ScheduleAgent", "tools_executed", metadata={"tool_count": len(tool_names)})

            if not tool_results:
                answer = "No schedule data available. Please provide a specific project ID."
                return await self.create_response(
                    answer=answer,
                    citations=[],
                    confidence=0.0,
                    tool_calls=tool_names,
                    context_length=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Step 3: Build context from tool results
            emit_event("ScheduleAgent", "build_context")
            context = self._build_context(tool_results)
            context_length = len(context)
            emit_event("ScheduleAgent", "context_built", metadata={"context_length": context_length})

            # Step 4: Generate response with LLM
            emit_event("ScheduleAgent", "invoke_llm")
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
            emit_event("ScheduleAgent", "llm_response_received", metadata={"response_length": len(llm_response)})

            # Step 5: Extract citations
            emit_event("ScheduleAgent", "extract_citations")
            citations = self._extract_citations(tool_results, llm_response)
            emit_event("ScheduleAgent", "citations_extracted", metadata={"citation_count": len(citations)})

            # Step 6: Apply guardrails
            emit_event("ScheduleAgent", "apply_guardrails")
            grounding_ok, grounding_score, _ = self.guardrails.ground_response(
                llm_response, context
            )
            hallucination_risk, _ = self.guardrails.check_hallucination(llm_response, context)
            confidence = self._calculate_confidence(hallucination_risk, grounding_ok, len(tool_names))
            emit_event("ScheduleAgent", "guardrails_applied", metadata={
                "grounding_ok": grounding_ok,
                "hallucination_risk": hallucination_risk,
                "confidence": confidence
            })

            return await self.create_response(
                answer=llm_response,
                citations=citations,
                confidence=confidence,
                tool_calls=tool_names,
                context_length=len(context),
                hallucination_risk=hallucination_risk,
                grounding_ok=grounding_ok,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            logger.error(f"ScheduleAgent.answer failed: {e}", exc_info=True)
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
        """Determine which tools to use."""
        tool_calls = []

        if any(
            word in query.lower()
            for word in ["schedule", "timeline", "milestone", "delay", "date", "completion"]
        ):
            if project_id:
                tool_calls.append(
                    {
                        "tool": "schedule_lookup",
                        "params": {"project_id": project_id},
                    }
                )

        return tool_calls or [{"tool": "schedule_lookup", "params": {"project_id": project_id}}]

    def _build_context(self, tool_results) -> str:
        """Build context from tool results."""
        context_parts = []
        items = tool_results if isinstance(tool_results, list) else tool_results.values()
        for result in items:
            if result.success and result.data:
                context_parts.append(f"{result.data}")
        return "\n\n".join(context_parts)
