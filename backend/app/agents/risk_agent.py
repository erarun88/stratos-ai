"""Risk Agent - Specialist for risk management domain.

Responsible ONLY for:
- Project blockers and issues
- Risk identification and analysis
- Dependency risks
- Escalation and mitigation strategies
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base_agent import Agent, AgentResponse
from app.ai.guardrails import Guardrails
from app.tools.risk_lookup_tool import RiskLookupTool
from app.execution_studio import auto_trace, emit_event

logger = logging.getLogger(__name__)


class RiskAgent(Agent):
    """Specialist agent for risk management domain."""

    DOMAIN = "risk_management"
    DESCRIPTION = "Answers questions about project risks, blockers, issues, and escalations"
    VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        """Initialize RiskAgent."""
        super().__init__(*args, **kwargs)
        self.guardrails = Guardrails(strict_mode=False)

    def _register_tools(self) -> None:
        """Register tools for risk domain."""
        self.tool_manager.register(RiskLookupTool())

    def get_system_prompt(self) -> str:
        """Return system prompt for risk management domain."""
        return """You are a senior risk manager specializing in project risk management.

Your expertise:
- Identifying and analyzing project risks
- Assessing impact and likelihood
- Mitigation strategies
- Escalation management
- Dependency risk analysis
- Blocker resolution strategies

Guidelines:
1. Be clear about risk severity and impact
2. Always recommend mitigation actions
3. Escalate critical issues appropriately
4. Focus on actionable insights
5. Provide risk prioritization

For project status, refer to the Project Agent.
For financial impact, refer to the Finance Agent.
For schedule impact, refer to the Schedule Agent.
"""

    @auto_trace(component="RiskAgent", action="answer_query")
    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        context_data: Optional[dict] = None,
    ) -> AgentResponse:
        """Answer a question about project risks.

        Args:
            query: User question
            project_id: Optional project to focus on
            context_data: Optional additional context

        Returns:
            AgentResponse with answer, citations, confidence
        """
        start_time = time.time()
        logger.info(f"RiskAgent.answer: {query[:100]}...")

        try:
            # Step 1: Determine tools to use
            emit_event("RiskAgent", "determine_tools")
            tool_calls = await self._determine_tools(query, project_id)
            emit_event("RiskAgent", "tools_selected", metadata={"tool_count": len(tool_calls)})

            # Step 2: Execute tools
            emit_event("RiskAgent", "execute_tools")
            tool_results = await self._execute_tools(tool_calls)
            tool_names = [t["tool"] for t in tool_calls]
            emit_event("RiskAgent", "tools_executed", metadata={"tool_count": len(tool_names)})

            if not tool_results:
                answer = "No risk data available. Please provide a specific project ID."
                return await self.create_response(
                    answer=answer,
                    citations=[],
                    confidence=0.0,
                    tool_calls=tool_names,
                    context_length=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Check if any actual risk data was found
            has_risk_data = False
            for result in (tool_results if isinstance(tool_results, list) else tool_results.values()):
                if result.success and result.data:
                    if isinstance(result.data, dict) and result.data.get("risk_count", 0) > 0:
                        has_risk_data = True
                        break

            if not has_risk_data:
                answer = "No risks have been documented for this project yet. Please add risk information through the project management interface if you have identified any risks."
                return await self.create_response(
                    answer=answer,
                    citations=[],
                    confidence=0.95,
                    tool_calls=tool_names,
                    context_length=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Step 3: Build context
            emit_event("RiskAgent", "build_context")
            context = self._build_context(tool_results)
            emit_event("RiskAgent", "context_built", metadata={"context_length": len(context)})

            # Step 4: Generate response
            emit_event("RiskAgent", "invoke_llm")
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
            emit_event("RiskAgent", "llm_response_received", metadata={"response_length": len(llm_response)})

            # Step 5: Extract citations
            emit_event("RiskAgent", "extract_citations")
            citations = self._extract_citations(tool_results, llm_response)
            emit_event("RiskAgent", "citations_extracted", metadata={"citation_count": len(citations)})

            # Step 6: Apply guardrails
            emit_event("RiskAgent", "apply_guardrails")
            grounding_ok, grounding_score, _ = self.guardrails.ground_response(
                llm_response, context
            )
            hallucination_risk, _ = self.guardrails.check_hallucination(llm_response, context)
            confidence = self._calculate_confidence(hallucination_risk, grounding_ok, len(tool_names))
            emit_event("RiskAgent", "guardrails_applied", metadata={
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
            logger.error(f"RiskAgent.answer failed: {e}", exc_info=True)
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

        if any(word in query.lower() for word in ["risk", "blocker", "issue", "problem", "escalat"]):
            if project_id:
                tool_calls.append(
                    {
                        "tool": "risk_lookup",
                        "params": {"project_id": project_id},
                    }
                )

        return tool_calls or [{"tool": "risk_lookup", "params": {"project_id": project_id}}]

    def _build_context(self, tool_results) -> str:
        """Build context from tool results."""
        context_parts = []
        items = tool_results if isinstance(tool_results, list) else tool_results.values()
        for result in items:
            if result.success and result.data:
                context_parts.append(f"{result.data}")
        return "\n\n".join(context_parts)
