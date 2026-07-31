"""Abstract base class for all tools.

Tools are agents' interface to backend systems: data retrieval, calculations, API calls.
Each tool describes itself and executes a single responsibility.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Result of a tool execution."""

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        if self.success:
            return f"ToolResult(success=True, data={type(self.data).__name__})"
        return f"ToolResult(success=False, error={self.error})"


class ToolError(Exception):
    """Base exception for tool execution errors."""

    pass


class Tool(ABC):
    """Abstract base class for all tools.

    Agents call tools to retrieve data, execute queries, or perform actions.
    Each tool handles a single responsibility and is independent.

    Example:
        class SemanticSearchTool(Tool):
            name = "semantic_search"
            description = "Search project documents by semantic meaning"

            async def execute(self, query: str, limit: int = 5, **kwargs):
                # Implement search logic
                pass
    """

    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with success status, data, and optional error message
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    async def call(self, **kwargs) -> ToolResult:
        """Public interface to execute tool. Wraps with error handling."""
        try:
            logger.debug(f"Executing tool: {self.name} with kwargs: {list(kwargs.keys())}")
            result = await self.execute(**kwargs)
            if result.success:
                logger.info(f"Tool {self.name} succeeded")
            else:
                logger.warning(f"Tool {self.name} failed: {result.error}")
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} raised exception: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__},
            )
