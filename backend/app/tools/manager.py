"""Tool manager for orchestrating tool calls.

Responsible for:
- Registering tools
- Describing tools to LLM
- Executing tool calls
- Handling tool results
"""

import json
import logging
from typing import Any, Dict, List, Optional

from app.tools.base import Tool, ToolError, ToolResult

logger = logging.getLogger(__name__)


class ToolManager:
    """Orchestrates tool registration, description, and execution."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool for use by agents.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool name is empty or already registered
        """
        if not tool.name:
            raise ValueError(f"Tool {tool.__class__.__name__} has no name")
        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name} already registered")

        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a registered tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())

    def get_tools_description(self) -> str:
        """Get LLM-friendly description of all tools.

        Format suitable for including in LLM system prompt:
        "You have access to the following tools:
         - tool_name: description
         - another_tool: description"
        """
        if not self.tools:
            return "No tools available."

        descriptions = ["You have access to the following tools:\n"]
        for name, tool in self.tools.items():
            descriptions.append(f"  • {name}: {tool.description}")

        return "\n".join(descriptions)

    async def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Parameters to pass to the tool

        Returns:
            ToolResult with execution results

        Raises:
            ToolError: If tool not found or execution fails
        """
        tool = self.get_tool(tool_name)
        if not tool:
            error = f"Tool '{tool_name}' not found"
            logger.error(error)
            return ToolResult(success=False, error=error)

        logger.info(f"Executing tool: {tool_name}")
        return await tool.call(**kwargs)

    async def execute_parallel(self, tool_calls: List[Dict[str, Any]]) -> List[ToolResult]:
        """Execute multiple tools in parallel.

        Args:
            tool_calls: List of dicts with 'tool' and 'params' keys
                       [{"tool": "semantic_search", "params": {"query": "..."}}, ...]

        Returns:
            List of ToolResult objects
        """
        import asyncio

        async def _execute_one(call: Dict[str, Any]) -> ToolResult:
            tool_name = call.get("tool")
            params = call.get("params", {})
            return await self.execute_tool(tool_name, **params)

        results = await asyncio.gather(*[_execute_one(call) for call in tool_calls])
        return results

    def format_tool_call_for_llm(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Format a tool call for LLM context.

        Useful for including in conversation history to show what tools were used.
        """
        return f"Tool: {tool_name}\nParameters: {json.dumps(params, indent=2)}"
