"""Document Agent - Specialist for document management and RAG domain.

Responsible ONLY for:
- Semantic document search
- RAG (Retrieval-Augmented Generation)
- Document summaries and analysis
- Document comparisons
- Citation and evidence retrieval
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.agents.base_agent import Agent, AgentResponse
from app.ai.guardrails import Guardrails
from app.tools.semantic_search_tool import SemanticSearchTool
from app.execution_studio import auto_trace, emit_event

logger = logging.getLogger(__name__)


class DocumentAgent(Agent):
    """Specialist agent for document management and semantic search domain."""

    DOMAIN = "document_management"
    DESCRIPTION = "Answers questions using project documents, semantic search, and RAG"
    VERSION = "1.0"

    def __init__(self, *args, **kwargs):
        """Initialize DocumentAgent."""
        super().__init__(*args, **kwargs)
        self.guardrails = Guardrails(strict_mode=True)  # Stricter for document grounding

    def _register_tools(self) -> None:
        """Register tools for document domain."""
        self.tool_manager.register(SemanticSearchTool())

    def get_system_prompt(self) -> str:
        """Return system prompt for document domain."""
        return """You are an expert document analyst specializing in project documentation.

Your expertise:
- Semantic document search and retrieval
- Document summarization
- Evidence-based analysis
- Document comparison and synthesis
- Citation and traceability

Guidelines:
1. ALWAYS cite your sources from documents
2. Only answer based on document content
3. Quote relevant passages when helpful
4. Highlight contradictions between documents
5. Be explicit about what documents DON'T say

If documents don't contain the answer, say so directly.
For project status, refer to the Project Agent.
For financial analysis, refer to the Finance Agent.
For risk assessment, refer to the Risk Agent.
"""

    @auto_trace(component="DocumentAgent", action="answer_query")
    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        context_data: Optional[dict] = None,
    ) -> AgentResponse:
        """Answer a question using document search and RAG.

        Args:
            query: User question
            project_id: Optional project to focus on
            context_data: Optional additional context

        Returns:
            AgentResponse with answer, citations, confidence
        """
        start_time = time.time()
        logger.info(f"DocumentAgent.answer: {query[:100]}...")

        try:
            # Step 1: Determine tools to use
            emit_event("DocumentAgent", "determine_tools")
            tool_calls = await self._determine_tools(query, project_id)
            logger.debug(f"Tool calls: {[t['tool'] for t in tool_calls]}")
            emit_event("DocumentAgent", "tools_selected", metadata={"tool_count": len(tool_calls)})

            # Step 2: Execute semantic search
            emit_event("DocumentAgent", "execute_tools")
            tool_results = await self._execute_tools(tool_calls)
            tool_names = [t["tool"] for t in tool_calls]
            logger.debug(f"Tool results: {len(tool_results)} tools executed")
            emit_event("DocumentAgent", "tools_executed", metadata={"tool_count": len(tool_names)})

            if not tool_results:
                answer = "No relevant documents found for this query."
                return await self.create_response(
                    answer=answer,
                    citations=[],
                    confidence=0.0,
                    tool_calls=tool_names,
                    context_length=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Step 3: Build context from documents
            emit_event("DocumentAgent", "build_context")
            context = self._build_context(tool_results)
            context_length = len(context)
            emit_event("DocumentAgent", "context_built", metadata={"context_length": context_length})

            # Step 4: Generate response grounded in documents
            emit_event("DocumentAgent", "invoke_llm")
            system_prompt = self.get_system_prompt()
            llm_response = await self.llm_client.generate(
                messages=[
                    {
                        "role": "user",
                        "content": f"Documents:\n{context}\n\nQuestion: {query}",
                    }
                ],
                system_prompt=system_prompt,
            )
            emit_event("DocumentAgent", "llm_response_received", metadata={"response_length": len(llm_response)})

            # Step 5: Extract citations (critical for document agent)
            emit_event("DocumentAgent", "extract_citations")
            citations = self._extract_document_citations(tool_results, llm_response)
            emit_event("DocumentAgent", "citations_extracted", metadata={"citation_count": len(citations)})

            # Step 6: Apply strict guardrails
            emit_event("DocumentAgent", "apply_guardrails")
            grounding_ok, grounding_score, _ = self.guardrails.ground_response(
                llm_response, context
            )
            hallucination_risk, _ = self.guardrails.check_hallucination(llm_response, context)
            confidence = self._calculate_confidence(hallucination_risk, grounding_ok, len(tool_names))
            emit_event("DocumentAgent", "guardrails_applied", metadata={
                "grounding_ok": grounding_ok,
                "hallucination_risk": hallucination_risk,
                "confidence": confidence
            })

            logger.info(
                f"DocumentAgent response: grounding={grounding_ok}, "
                f"hallucination_risk={hallucination_risk:.2f}, confidence={confidence:.2f}"
            )

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
            logger.error(f"DocumentAgent.answer failed: {e}", exc_info=True)
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
        # Always do semantic search for document queries
        return [
            {
                "tool": "semantic_search",
                "params": {
                    "query": query,
                    "limit": 5,
                    "project_id": project_id,
                },
            }
        ]

    def _build_context(self, tool_results) -> str:
        """Build context from document search results."""
        context_parts = []

        items = tool_results if isinstance(tool_results, list) else tool_results.values()

        for result in items:
            if result.success and result.data:
                # Format document results
                if isinstance(result.data, list):
                    for i, doc in enumerate(result.data, 1):
                        doc_text = str(doc)
                        context_parts.append(f"Document {i}:\n{doc_text}")
                else:
                    context_parts.append(str(result.data))

        return "\n\n---\n\n".join(context_parts)

    def _extract_document_citations(self, tool_results, llm_response: str) -> List:
        """Extract citations from document search results.

        For document agent, we create citations for each retrieved document.

        Args:
            tool_results: Results from semantic search (list or dict)
            llm_response: LLM response text

        Returns:
            List of Citation objects
        """
        from app.agents.base_agent import Citation

        citations = []

        items = tool_results if isinstance(tool_results, list) else tool_results.values()

        for result in items:
            if result.success and result.data:
                if isinstance(result.data, list):
                    for doc in result.data:
                        # Extract document metadata if available
                        doc_id = getattr(doc, "id", "unknown")
                        doc_title = getattr(doc, "title", "Document")

                        citation = Citation(
                            source=f"Document: {doc_title}",
                            content=str(doc)[:300],
                            relevance=getattr(doc, "relevance_score", None),
                            tool="semantic_search",
                        )
                        citations.append(citation)

        return citations
