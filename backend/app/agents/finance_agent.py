"""Finance Agent - Specialist for financial domain.

Responsible ONLY for:
- Project budgets and allocation
- Cost tracking and variance analysis
- Revenue and profitability
- Financial forecasts
- Financial KPIs and metrics
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base_agent import Agent, AgentResponse, Citation
from app.ai.guardrails import Guardrails
from app.execution_studio import auto_trace, emit_event

logger = logging.getLogger(__name__)


class FinanceAgent(Agent):
    """Specialist agent for financial domain."""

    DOMAIN = "finance"
    DESCRIPTION = "Answers questions about budgets, costs, revenue, and financial KPIs"
    VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        """Initialize FinanceAgent."""
        super().__init__(*args, **kwargs)
        self.guardrails = Guardrails(strict_mode=False)

    def _register_tools(self) -> None:
        """Register tools for finance domain.

        TODO: Implement BudgetLookupTool, CostVarianceTool, ForecastTool
        For now, this is a placeholder.
        """
        # self.tool_manager.register(BudgetLookupTool())
        # self.tool_manager.register(CostVarianceTool())
        # self.tool_manager.register(ForecastTool())
        pass

    def get_system_prompt(self) -> str:
        """Return system prompt for finance domain."""
        return """You are a senior financial analyst specializing in project finance.

Your expertise:
- Project budgets and financial planning
- Cost tracking and variance analysis
- Revenue projections and profitability
- Financial forecasts and scenarios
- KPIs and financial health metrics

Guidelines:
1. Focus on financial metrics and data
2. Always provide actual vs. budgeted comparisons
3. Flag cost overruns and financial risks
4. Use clear formatting for financial data
5. Provide actionable financial insights

For project status, refer to the Project Agent.
For risks, refer to the Risk Agent.
For schedules, refer to the Schedule Agent.
"""

    @auto_trace(component="FinanceAgent", action="answer_query")
    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        context_data: Optional[dict] = None,
    ) -> AgentResponse:
        """Answer a question about project finances.

        Args:
            query: User question
            project_id: Optional project to focus on
            context_data: Optional additional context

        Returns:
            AgentResponse with answer, citations, confidence
        """
        start_time = time.time()
        logger.info(f"FinanceAgent.answer: {query[:100]}...")

        try:
            # Step 1: Determine tools to use
            emit_event("FinanceAgent", "determine_tools")
            tool_calls = await self._determine_tools(query, project_id)
            emit_event("FinanceAgent", "tools_selected", metadata={"tool_count": len(tool_calls)})

            # Step 2: Execute tools
            emit_event("FinanceAgent", "execute_tools")
            tool_results = await self._execute_tools(tool_calls)
            tool_names = [t["tool"] for t in tool_calls]
            emit_event("FinanceAgent", "tools_executed", metadata={"tool_count": len(tool_names)})

            if not tool_results:
                # TODO: Implement full logic similar to ProjectAgent
                # For now, return a placeholder response
                answer = (
                    "Finance Agent is not yet fully implemented. "
                    "Please check back soon for budget, cost, and financial analysis."
                )
                emit_event("FinanceAgent", "no_tool_results")
                return await self.create_response(
                    answer=answer,
                    citations=[],
                    confidence=0.0,
                    tool_calls=tool_names,
                    context_length=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    metadata={"status": "placeholder"},
                )

            # Step 3: Build context from tool results
            emit_event("FinanceAgent", "build_context")
            context = self._build_context(tool_results, query)
            context_length = len(context)
            emit_event("FinanceAgent", "context_built", metadata={"context_length": context_length})

            # Step 4: Generate response with LLM
            emit_event("FinanceAgent", "invoke_llm")
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
            emit_event("FinanceAgent", "llm_response_received", metadata={"response_length": len(llm_response)})

            # Step 5: Extract citations
            emit_event("FinanceAgent", "extract_citations")
            citations = self._extract_citations(tool_results, llm_response)
            emit_event("FinanceAgent", "citations_extracted", metadata={"citation_count": len(citations)})

            # Step 6: Apply guardrails
            emit_event("FinanceAgent", "apply_guardrails")
            grounding_ok, grounding_score, _ = self.guardrails.ground_response(
                llm_response, context
            )
            hallucination_risk, _ = self.guardrails.check_hallucination(llm_response, context)
            confidence = self._calculate_confidence(hallucination_risk, grounding_ok, len(tool_names))
            emit_event("FinanceAgent", "guardrails_applied", metadata={
                "grounding_ok": grounding_ok,
                "hallucination_risk": hallucination_risk,
                "confidence": confidence
            })

            logger.info(
                f"FinanceAgent response: grounding={grounding_ok}, "
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
            logger.error(f"FinanceAgent.answer failed: {e}", exc_info=True)
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
        # TODO: Implement tool determination
        return []

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
