"""Context Builder - Assembles and formats retrieved context for LLM.

Responsibilities:
- Merge results from multiple tools
- Remove duplicates
- Order by relevance
- Trim to token limit
- Format for LLM consumption
"""

import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build coherent context from tool results."""

    def __init__(self, max_tokens: int = 8000):
        """Initialize context builder.

        Args:
            max_tokens: Maximum tokens to include in context
        """
        self.max_tokens = max_tokens

    def build(
        self,
        tool_results: List[dict],
        max_tokens: Optional[int] = None,
    ) -> str:
        """Build context from tool results.

        Args:
            tool_results: List of tool result dicts with 'tool', 'data', and 'success' keys
            max_tokens: Override max tokens (uses instance default if not provided)

        Returns:
            Formatted context string for LLM
        """
        max_tokens = max_tokens or self.max_tokens

        # Extract and validate results
        valid_results = []
        for result in tool_results:
            if isinstance(result, dict) and result.get("success") and result.get("data"):
                valid_results.append(result)

        if not valid_results:
            logger.warning("No valid tool results to build context from")
            return "No context available."

        # Format each result
        formatted_sections = []

        for result in valid_results:
            tool_name = result.get("tool", "unknown")
            data = result.get("data")

            section = self._format_section(tool_name, data)
            if section:
                formatted_sections.append(section)

        # Merge and trim
        merged_context = "\n\n".join(formatted_sections)
        trimmed_context = self._trim_to_tokens(merged_context, max_tokens)

        logger.info(f"Context built: {len(formatted_sections)} sections, ~{len(trimmed_context) // 4} tokens")
        return trimmed_context

    def _format_section(self, tool_name: str, data: Any) -> Optional[str]:
        """Format a single tool result section.

        Args:
            tool_name: Name of the tool that produced this result
            data: The data from the tool

        Returns:
            Formatted section string or None if data is invalid
        """
        if isinstance(data, list):
            return self._format_list_section(tool_name, data)
        elif isinstance(data, dict):
            return self._format_dict_section(tool_name, data)
        elif isinstance(data, str):
            return f"### {tool_name}\n{data}"
        else:
            return f"### {tool_name}\n{str(data)}"

    def _format_list_section(self, tool_name: str, items: List[Any]) -> str:
        """Format a list of items."""
        if not items:
            return ""

        lines = [f"### {tool_name} ({len(items)} items)"]

        # Try to intelligently format items
        for i, item in enumerate(items[:10], 1):  # Limit to first 10 items
            if isinstance(item, dict):
                # Format dict as key-value pairs
                item_str = self._format_dict_inline(item)
                lines.append(f"{i}. {item_str}")
            else:
                lines.append(f"{i}. {str(item)[:200]}")

        if len(items) > 10:
            lines.append(f"... and {len(items) - 10} more items")

        return "\n".join(lines)

    def _format_dict_section(self, tool_name: str, data: dict) -> str:
        """Format a dictionary."""
        lines = [f"### {tool_name}"]

        for key, value in data.items():
            if isinstance(value, (list, dict)):
                lines.append(f"**{key}:**")
                if isinstance(value, list):
                    for item in value[:5]:  # Limit nested lists
                        lines.append(f"  - {str(item)[:100]}")
                    if len(value) > 5:
                        lines.append(f"  - ... and {len(value) - 5} more")
                else:
                    for k, v in list(value.items())[:5]:
                        lines.append(f"  - {k}: {str(v)[:100]}")
            else:
                lines.append(f"**{key}:** {str(value)}")

        return "\n".join(lines)

    def _format_dict_inline(self, data: dict) -> str:
        """Format a dict as a single inline string."""
        parts = []
        for key, value in data.items():
            if not isinstance(value, (list, dict)):
                parts.append(f"{key}: {str(value)[:50]}")
        return " | ".join(parts) if parts else str(data)

    def _trim_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trim text to approximate token limit.

        Simple approach: rough estimate of 4 chars per token.

        Args:
            text: Text to trim
            max_tokens: Maximum token count

        Returns:
            Trimmed text
        """
        max_chars = max_tokens * 4 - 200  # Leave buffer for safety

        if len(text) <= max_chars:
            return text

        # Trim and add ellipsis
        trimmed = text[:max_chars].rsplit("\n", 1)[0]  # Break at paragraph
        return trimmed + "\n\n[... context trimmed to token limit]"

    def remove_duplicates(self, items: List[dict], key_fields: List[str]) -> List[dict]:
        """Remove duplicate items from a list.

        Args:
            items: List of items (typically dicts)
            key_fields: Fields to use for deduplication

        Returns:
            List with duplicates removed
        """
        seen = set()
        unique_items = []

        for item in items:
            if isinstance(item, dict):
                key_tuple = tuple(item.get(field) for field in key_fields)
            else:
                key_tuple = str(item)

            if key_tuple not in seen:
                seen.add(key_tuple)
                unique_items.append(item)

        logger.debug(f"Removed {len(items) - len(unique_items)} duplicates")
        return unique_items
