"""Base agent class - foundation for all specialist agents.

Every specialist agent inherits from this base class.
Provides standardized interface, lifecycle management, and instrumentation.

Design principles:
- Single responsibility per agent
- Stateless execution
- Standard response format
- Pluggable tools
- Comprehensive logging
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.llm_client import LLMClient
from app.tools.base import ToolResult
from app.tools.manager import ToolManager

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """A single citation with source and relevance."""

    source: str
    content: Optional[str] = None
    relevance: Optional[float] = None
    tool: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "source": self.source,
            "content": self.content,
            "relevance": self.relevance,
            "tool": self.tool,
        }


@dataclass
class AgentResponse:
    """Standardized response from any agent.

    All agents return this format. Supervisor can compose multiple responses.
    """

    # Core response
    answer: str
    confidence: float  # 0.0-1.0

    # Provenance
    citations: List[Citation] = field(default_factory=list)

    # Execution details
    agent_name: str = ""
    execution_time_ms: float = 0.0
    tool_calls: List[str] = field(default_factory=list)
    context_length: int = 0

    # Quality signals
    hallucination_risk: float = 0.0
    grounding_ok: bool = True
    approval_required: bool = False
    approval_reason: Optional[str] = None

    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for API responses."""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "citations": [c.to_dict() for c in self.citations],
            "agent_name": self.agent_name,
            "execution_time_ms": self.execution_time_ms,
            "tool_calls": self.tool_calls,
            "context_length": self.context_length,
            "hallucination_risk": self.hallucination_risk,
            "grounding_ok": self.grounding_ok,
            "approval_required": self.approval_required,
            "approval_reason": self.approval_reason,
            "metadata": self.metadata,
        }


class Agent(ABC):
    """Abstract base class for all specialist agents.

    Every agent (Project, Finance, Risk, Schedule, Document) inherits from this.
    Agents are stateless and reusable. No internal state except configuration.

    Key responsibilities:
    1. Define domain (what this agent handles)
    2. Register tools it needs
    3. Generate domain-specific prompts
    4. Execute query using tools
    5. Validate and format response
    6. Report confidence/quality metrics

    Example:
        class ProjectAgent(Agent):
            DOMAIN = "project_management"

            def register_tools(self):
                self.tool_manager.register(ProjectLookupTool())
                self.tool_manager.register(ScheduleLookupTool())

            def get_system_prompt(self):
                return "You are an expert in project management..."

            async def answer(self, query: str):
                # Determine tools, execute, format response
                pass
    """

    # Each subclass must define these
    DOMAIN: str = ""  # e.g., "project_management", "finance", "risk"
    DESCRIPTION: str = ""  # e.g., "Answers questions about project status and timelines"
    VERSION: str = "1.0"

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize agent.

        Args:
            llm_client: Optional custom LLM client. If None, creates default.
        """
        self.llm_client = llm_client or LLMClient()
        self.tool_manager = ToolManager()
        self._register_tools()

        logger.info(
            f"{self.__class__.__name__} initialized "
            f"(domain={self.DOMAIN}, tools={len(self.tool_manager.list_tools())})"
        )

    @abstractmethod
    def _register_tools(self) -> None:
        """Register tools this agent uses.

        Called during __init__. Each subclass registers its own tool set.

        Example:
            def _register_tools(self):
                self.tool_manager.register(ProjectLookupTool())
                self.tool_manager.register(ScheduleLookupTool())
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return system prompt for this agent's domain.

        Called before each LLM invocation.

        Returns:
            System prompt as string

        Example:
            def get_system_prompt(self):
                return '''You are an expert project manager...
                Answer questions about project status, timelines, and milestones.
                Be concise and grounded in project data.
                '''
        """
        pass

    @abstractmethod
    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        context_data: Optional[dict] = None,
    ) -> AgentResponse:
        """Answer a question in this agent's domain.

        Args:
            query: User question (natural language)
            project_id: Optional project context
            context_data: Optional additional context from supervisor

        Returns:
            AgentResponse with answer, citations, confidence, metadata

        This is the only public interface agents expose.
        Supervisor calls this method on agents.
        """
        pass

    # =========================================================================
    # COMMON UTILITIES - Subclasses can use these
    # =========================================================================

    async def _determine_tools(
        self,
        query: str,
        project_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Determine which tools to use for this query.

        Subclasses can override for custom logic.
        Default: Let LLM decide based on query semantics.

        Args:
            query: User query
            project_id: Optional project context

        Returns:
            List of tool calls: [{"tool": "name", "params": {...}}, ...]
        """
        # Default implementation: heuristic-based
        # Subclasses can override with LLM-based selection
        return []

    async def _execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
    ) -> Dict[str, ToolResult]:
        """Execute tools in parallel.

        Args:
            tool_calls: List of tool calls with parameters

        Returns:
            Dict mapping tool names to results
        """
        results = await self.tool_manager.execute_parallel(tool_calls)
        return results

    def _extract_citations(
        self,
        tool_results,
        llm_response: str,
    ) -> List[Citation]:
        """Extract citations from tool results and LLM response.

        Subclasses can override for domain-specific citation logic.

        Args:
            tool_results: Results from executed tools (list or dict)
            llm_response: LLM-generated response

        Returns:
            List of Citation objects
        """
        citations = []

        items = tool_results if isinstance(tool_results, list) else tool_results.values()

        for i, result in enumerate(items):
            if result.success and result.data:
                # Create citation for each tool result
                citation = Citation(
                    source=f"Tool {i}" if isinstance(tool_results, list) else "Tool Result",
                    content=str(result.data)[:200],  # First 200 chars
                    tool=f"Tool {i}" if isinstance(tool_results, list) else "Tool",
                )
                citations.append(citation)

        return citations

    def _calculate_confidence(
        self,
        hallucination_risk: float,
        grounding_ok: bool,
        tool_count: int,
    ) -> float:
        """Calculate confidence score for response.

        Simple formula:
        - Base: 0.5
        - +0.3 if grounded
        - -hallucination_risk
        - +0.1 per tool (capped at 0.95)

        Args:
            hallucination_risk: 0.0-1.0
            grounding_ok: Boolean
            tool_count: Number of tools used

        Returns:
            Confidence score 0.0-1.0
        """
        confidence = 0.5

        if grounding_ok:
            confidence += 0.3

        confidence -= hallucination_risk
        confidence += min(tool_count * 0.1, 0.2)

        # Clamp to 0-1
        return max(0.0, min(1.0, confidence))

    async def create_response(
        self,
        answer: str,
        citations: List[Citation],
        confidence: float,
        tool_calls: List[str],
        context_length: int,
        hallucination_risk: float = 0.0,
        grounding_ok: bool = True,
        approval_required: bool = False,
        approval_reason: Optional[str] = None,
        execution_time_ms: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> AgentResponse:
        """Create standardized response.

        Helper method for subclasses to build response objects consistently.

        Args:
            answer: The answer text
            citations: List of Citation objects
            confidence: Confidence score (0.0-1.0)
            tool_calls: List of tool names that were invoked
            context_length: Length of context used
            hallucination_risk: Hallucination risk score
            grounding_ok: Whether response is grounded in data
            approval_required: Whether this action needs approval
            approval_reason: If approval needed, why
            execution_time_ms: How long execution took
            metadata: Additional metadata

        Returns:
            AgentResponse ready for serialization
        """
        return AgentResponse(
            answer=answer,
            confidence=confidence,
            citations=citations,
            agent_name=self.__class__.__name__,
            execution_time_ms=execution_time_ms,
            tool_calls=tool_calls,
            context_length=context_length,
            hallucination_risk=hallucination_risk,
            grounding_ok=grounding_ok,
            approval_required=approval_required,
            approval_reason=approval_reason,
            metadata=metadata or {},
        )
