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
            # TODO: Implement full logic similar to ProjectAgent
            # For now, return a placeholder response

            answer = (
                "Finance Agent is not yet fully implemented. "
                "Please check back soon for budget, cost, and financial analysis."
            )

            return await self.create_response(
                answer=answer,
                citations=[],
                confidence=0.0,
                tool_calls=[],
                context_length=0,
                execution_time_ms=(time.time() - start_time) * 1000,
                metadata={"status": "placeholder"},
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
