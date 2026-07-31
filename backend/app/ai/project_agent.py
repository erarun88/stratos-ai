"""ProjectAgent - Main AI orchestrator for project intelligence.

Responsibilities:
1. Route user queries to appropriate tools
2. Execute tools and retrieve context
3. Build coherent context from results
4. Generate response via LLM
5. Apply guardrails (grounding, hallucination checks)
6. Format response for delivery

This is the first specialized agent. Future agents (DocumentAgent, FinanceAgent, etc.)
will follow the same pattern.
"""

import logging
from typing import List, Optional

from app.ai.context_builder import ContextBuilder
from app.ai.guardrails import Guardrails
from app.ai.llm_client import LLMClient
from app.ai.memory.service import MemoryService, Message
from app.ai.prompts import get_system_prompt
from app.ai.response_formatter import ResponseFormatter
from app.tools.manager import ToolManager
from app.tools.project_lookup_tool import ProjectLookupTool
from app.tools.risk_lookup_tool import RiskLookupTool
from app.tools.schedule_lookup_tool import ScheduleLookupTool
from app.tools.semantic_search_tool import SemanticSearchTool

logger = logging.getLogger(__name__)


class ProjectAgentResponse:
    """Structured response from ProjectAgent."""

    def __init__(
        self,
        answer: str,
        citations: List[dict],
        confidence: float,
        mode: str = "concise",
        metadata: dict = None,
    ):
        self.answer = answer
        self.citations = citations
        self.confidence = confidence
        self.mode = mode
        self.metadata = metadata or {}


class ProjectAgent:
    """AI Agent for project management intelligence.

    Answers questions about projects using semantic search and project data.
    First specialized agent in a future multi-agent ecosystem.
    """

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        """Initialize ProjectAgent.

        Args:
            llm_provider: "anthropic" or "openai" (defaults to config)
            llm_model: Model name (defaults to config)
        """
        # Initialize components
        self.llm_client = LLMClient(provider=llm_provider, model=llm_model)
        self.context_builder = ContextBuilder(max_tokens=8000)
        self.guardrails = Guardrails(strict_mode=False)
        self.formatter = ResponseFormatter()
        self.memory = MemoryService()

        # Initialize tools
        self.tool_manager = ToolManager()
        self._register_tools()

        logger.info(f"ProjectAgent initialized with {len(self.tool_manager.list_tools())} tools")

    def _register_tools(self) -> None:
        """Register all available tools."""
        self.tool_manager.register(SemanticSearchTool())
        self.tool_manager.register(ProjectLookupTool())
        self.tool_manager.register(RiskLookupTool())
        self.tool_manager.register(ScheduleLookupTool())

    async def answer(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        project_id: Optional[int] = None,
        response_mode: str = "concise",
    ) -> ProjectAgentResponse:
        """Answer a question about projects.

        Args:
            query: User question (natural language)
            conversation_id: Optional conversation ID for context history
            project_id: Optional project ID to scope the query
            response_mode: "concise", "detailed", or "executive"

        Returns:
            ProjectAgentResponse with answer, citations, and confidence
        """
        logger.info(f"ProjectAgent.answer: {query[:100]}... (mode={response_mode})")

        try:
            # Step 1: Determine which tools to use
            tool_calls = await self._determine_tools(query, project_id)
            logger.info(f"Selected tools: {[t['tool'] for t in tool_calls]}")

            # Step 2: Execute tools in parallel
            tool_results = await self.tool_manager.execute_parallel(tool_calls)
            logger.info(f"Tool execution complete: {len(tool_results)} results")

            # Step 3: Build context from tool results
            context_data = self._prepare_tool_results(tool_results, tool_calls)
            context = self.context_builder.build(context_data)
            logger.debug(f"Context built: {len(context)} characters")

            # Step 4: Generate response from LLM
            system_prompt = get_system_prompt("default")
            response_text = await self.llm_client.generate(
                messages=[{"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}],
                system_prompt=system_prompt,
            )
            logger.info(f"LLM response generated: {len(response_text)} characters")

            # Step 5: Extract and format citations
            citations = self._extract_citations(context_data, response_text)

            # Step 6: Apply guardrails
            grounding_ok, grounding_score, _ = self.guardrails.ground_response(response_text, context)
            hallucination_risk, _ = self.guardrails.check_hallucination(response_text, context)
            confidence = self.guardrails.score_confidence(grounding_score, hallucination_risk)

            logger.info(
                f"Guardrails check: grounding={grounding_ok}, "
                f"hallucination_risk={hallucination_risk:.2f}, confidence={confidence:.2f}"
            )

            # Step 7: Format response
            formatted_answer = self.formatter.format(
                response_text,
                mode=response_mode,
                citations=citations,
            )

            # Step 8: Save to memory (if conversation_id provided)
            if conversation_id:
                await self.memory.save(
                    conversation_id,
                    Message(
                        role="user",
                        content=query,
                        tokens=self.llm_client.count_tokens(query),
                    ),
                )
                await self.memory.save(
                    conversation_id,
                    Message(
                        role="assistant",
                        content=formatted_answer,
                        tokens=self.llm_client.count_tokens(formatted_answer),
                    ),
                )

            return ProjectAgentResponse(
                answer=formatted_answer,
                citations=citations,
                confidence=confidence,
                mode=response_mode,
                metadata={
                    "grounding_ok": grounding_ok,
                    "hallucination_risk": hallucination_risk,
                    "tool_calls": len(tool_calls),
                    "context_length": len(context),
                },
            )

        except Exception as e:
            logger.error(f"ProjectAgent.answer failed: {e}", exc_info=True)
            return ProjectAgentResponse(
                answer=f"Error processing query: {e}",
                citations=[],
                confidence=0.0,
                mode=response_mode,
                metadata={"error": str(e)},
            )

    async def _determine_tools(
        self,
        query: str,
        project_id: Optional[int] = None,
    ) -> List[dict]:
        """Determine which tools to use based on query.

        Let LLM decide based on available tools.

        Args:
            query: User query
            project_id: Optional project ID

        Returns:
            List of tool calls: [{"tool": "name", "params": {...}}, ...]
        """
        # For MVP: heuristic-based tool selection
        # In future: let LLM decide via function calling

        tool_calls = []

        # Always do semantic search for document context
        tool_calls.append({
            "tool": "semantic_search",
            "params": {
                "query": query,
                "limit": 5,
                "project_id": project_id,
            },
        })

        # Add project lookup if query mentions project or status
        if any(word in query.lower() for word in ["project", "status", "summary", "overview"]):
            if project_id:
                tool_calls.append({
                    "tool": "project_lookup",
                    "params": {"project_id": project_id},
                })

        # Add risk lookup if query mentions risks/issues/blockers
        if any(word in query.lower() for word in ["risk", "issue", "blocker", "problem", "escalat"]):
            if project_id:
                tool_calls.append({
                    "tool": "risk_lookup",
                    "params": {"project_id": project_id},
                })

        # Add schedule lookup if query mentions dates/timeline/schedule
        if any(word in query.lower() for word in ["schedule", "date", "timeline", "delay", "milestone"]):
            if project_id:
                tool_calls.append({
                    "tool": "schedule_lookup",
                    "params": {"project_id": project_id},
                })

        return tool_calls

    def _prepare_tool_results(
        self,
        tool_results: list,
        tool_calls: List[dict],
    ) -> List[dict]:
        """Prepare tool results for context building.

        Maps tool results back to tool names and success status.

        Args:
            tool_results: List of ToolResult objects from tool execution
            tool_calls: Original tool call requests

        Returns:
            List of dicts with 'tool', 'success', 'data' keys
        """
        prepared = []

        for i, result in enumerate(tool_results):
            tool_name = tool_calls[i]["tool"] if i < len(tool_calls) else "unknown"
            prepared.append({
                "tool": tool_name,
                "success": result.success,
                "data": result.data,
                "error": result.error,
            })

        return prepared

    def _extract_citations(
        self,
        context_data: List[dict],
        response: str,
    ) -> List[dict]:
        """Extract citations from tool results.

        Args:
            context_data: Prepared tool results
            response: LLM response text

        Returns:
            List of citation dicts with 'source' and 'relevance' keys
        """
        citations = []

        for result in context_data:
            if not result["success"]:
                continue

            tool_name = result["tool"]
            data = result["data"]

            # Extract source information based on tool type
            if tool_name == "semantic_search" and isinstance(data, list):
                for item in data[:3]:  # Top 3 results
                    citations.append({
                        "source": f"Document: {item.get('title', 'Unknown')}",
                        "content": item.get("chunk_text", "")[:100],
                        "relevance": f"{item.get('similarity_score', 0):.2f}",
                        "tool": tool_name,
                    })
            elif tool_name == "project_lookup" and isinstance(data, dict):
                citations.append({
                    "source": f"Project: {data.get('name', 'Unknown')}",
                    "content": f"Status: {data.get('status', 'Unknown')}",
                    "relevance": "1.00",
                    "tool": tool_name,
                })

        return citations[:5]  # Limit to top 5 citations
