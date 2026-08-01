"""Supervisor Agent - Orchestration entry point for all specialist agents.

The Supervisor is the single point of contact for routing user queries.

Responsibilities:
1. Understand user intent
2. Determine which specialist agents are needed
3. Route queries to agents
4. Execute agents in parallel when independent
5. Merge results intelligently
6. Apply reflection for quality improvement (Phase D)
7. Check for approval requirements (Phase E)
8. Return unified response

The Supervisor NEVER contains domain business logic.
All domain logic lives in specialist agents.

Design: Supervisor is stateless orchestrator, not a domain expert.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional

from app.agents.base_agent import Agent, AgentResponse, Citation
from app.agents.reflection_agent import ReflectionAgent
from app.approvals import get_approval_manager, ApprovalType
from app.ai.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Orchestrates specialist agents to answer complex queries.

    Supervisor's job:
    - Parse user query
    - Determine which agents can help
    - Invoke them in parallel
    - Merge their responses
    - Return one unified answer

    Supervisor is NOT an agent itself. It coordinates agents.
    """

    def __init__(self, agents: Optional[Dict[str, Agent]] = None):
        """Initialize Supervisor with specialist agents.

        Args:
            agents: Dict mapping domain -> Agent instance
                   If None, supervisor starts empty and agents added dynamically
        """
        self.agents: Dict[str, Agent] = agents or {}
        self.llm_client = LLMClient()
        self.reflection_agent = ReflectionAgent()  # Phase D
        self.approval_manager = get_approval_manager()  # Phase E

        logger.info(f"Supervisor initialized with {len(self.agents)} agents "
                   f"(with Reflection and Approval frameworks)")

    def register_agent(self, domain: str, agent: Agent) -> None:
        """Register a specialist agent.

        Args:
            domain: Domain name (e.g., "project_management", "finance")
            agent: Agent instance
        """
        self.agents[domain] = agent
        logger.info(f"Supervisor registered agent for domain: {domain}")

    def list_agents(self) -> Dict[str, str]:
        """List available agents and their descriptions."""
        return {domain: agent.DESCRIPTION for domain, agent in self.agents.items()}

    async def answer(
        self,
        query: str,
        project_id: Optional[int] = None,
        required_domains: Optional[List[str]] = None,
    ) -> Dict:
        """Answer a complex query by coordinating specialist agents.

        Args:
            query: User query (natural language)
            project_id: Optional project context
            required_domains: Optional list of domains to query.
                             If None, supervisor determines automatically.

        Returns:
            Dict with:
            - answer: Unified response
            - citations: Merged citations from all agents
            - confidence: Overall confidence (avg of agent confidences)
            - agents_used: List of agents that contributed
            - execution_time_ms: Total time
            - metadata: Orchestration details
        """
        start_time = time.time()
        logger.info(f"Supervisor.answer: {query[:100]}... (project_id={project_id})")

        try:
            # Step 1: Determine which agents to invoke
            agent_domains = required_domains or await self._select_agents(query)
            logger.info(f"Selected agents: {agent_domains}")

            if not agent_domains:
                return {
                    "answer": "I don't have enough context to answer this question. "
                    "Could you provide more details?",
                    "citations": [],
                    "confidence": 0.0,
                    "agents_used": [],
                    "execution_time_ms": 0,
                    "metadata": {"no_agents_selected": True},
                }

            # Step 2: Invoke selected agents in parallel
            responses = await self._invoke_agents_parallel(
                agent_domains, query, project_id
            )

            # Step 3: Merge responses
            merged = self._merge_responses(responses, query)

            # Step 4: Apply Phase D - Reflection for quality improvement
            reflection_result = await self.reflection_agent.review(
                answer=merged["answer"],
                citations=merged["citations"],
                context=query,
                confidence=merged["confidence"],
            )

            # Use improved answer if reflection found and fixed issues
            final_answer = reflection_result.improved_answer
            reflection_applied = reflection_result.reflection_applied

            # Step 5: Check Phase E - Approval requirements
            approval_required = False
            approval_id = None
            approval_reason = None

            # Detect if response suggests dangerous actions
            dangerous_keywords = {
                "delete": ApprovalType.DELETE_PROJECT,
                "remove project": ApprovalType.DELETE_PROJECT,
                "cancel project": ApprovalType.CHANGE_STATUS,
                "close project": ApprovalType.CHANGE_STATUS,
                "approve budget": ApprovalType.APPROVE_BUDGET,
                "assign": ApprovalType.ASSIGN_CREWS,
                "escalate": ApprovalType.ESCALATE_RISK,
            }

            for keyword, approval_type in dangerous_keywords.items():
                if keyword in final_answer.lower():
                    if self.approval_manager.requires_approval(approval_type):
                        approval_req = self.approval_manager.create_approval_request(
                            action_type=approval_type,
                            action_description=final_answer[:200],
                            requester_id="system",
                            metadata={"query": query, "project_id": project_id},
                        )
                        approval_required = True
                        approval_id = approval_req.id
                        approval_reason = approval_req.reason
                        logger.info(f"Approval required for {approval_type}: {approval_id}")
                        break

            # Step 6: Return unified response
            elapsed_ms = (time.time() - start_time) * 1000

            result = {
                "answer": final_answer,
                "citations": merged["citations"],
                "confidence": merged["confidence"],
                "agents_used": list(responses.keys()),
                "execution_time_ms": elapsed_ms,
                "reflection_applied": reflection_applied,
                "approval_required": approval_required,
                "approval_id": approval_id,
                "approval_reason": approval_reason,
                "metadata": {
                    "agent_count": len(responses),
                    "merge_strategy": "consensus",
                    "reflection_reasoning": reflection_result.reflection_reasoning,
                },
            }

            logger.info(
                f"Supervisor.answer complete: "
                f"agents={len(responses)}, confidence={merged['confidence']:.2f}, "
                f"elapsed_ms={elapsed_ms:.0f}"
            )

            return result

        except Exception as e:
            logger.error(f"Supervisor.answer failed: {e}", exc_info=True)
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "agents_used": [],
                "execution_time_ms": 0,
                "metadata": {"error": str(e)},
            }

    async def _select_agents(self, query: str) -> List[str]:
        """Determine which agents to invoke based on query.

        Current: Heuristic-based pattern matching
        Future: LLM-based intent classification

        Args:
            query: User query

        Returns:
            List of domain names to invoke
        """
        query_lower = query.lower()
        selected = []

        # Project-related queries
        if any(
            word in query_lower
            for word in ["project", "status", "timeline", "milestone", "schedule", "scope"]
        ):
            if "project_management" in self.agents:
                selected.append("project_management")

        # Finance-related queries
        if any(
            word in query_lower
            for word in ["budget", "cost", "revenue", "profit", "financial", "expense"]
        ):
            if "finance" in self.agents:
                selected.append("finance")

        # Risk-related queries
        if any(
            word in query_lower
            for word in ["risk", "blocker", "issue", "problem", "escalat", "dependency"]
        ):
            if "risk_management" in self.agents:
                selected.append("risk_management")

        # Schedule-related queries
        if any(
            word in query_lower
            for word in [
                "schedule",
                "delay",
                "date",
                "timeline",
                "critical path",
                "completion",
            ]
        ):
            if "schedule" in self.agents:
                selected.append("schedule")

        # Document-related queries
        if any(
            word in query_lower
            for word in [
                "document",
                "search",
                "find",
                "retrieve",
                "spec",
                "requirement",
            ]
        ):
            if "document_management" in self.agents:
                selected.append("document_management")

        # Default: always include document search for context
        if "document_management" in self.agents and "document_management" not in selected:
            selected.append("document_management")

        return list(set(selected))  # Remove duplicates

    async def _invoke_agents_parallel(
        self,
        agent_domains: List[str],
        query: str,
        project_id: Optional[int],
    ) -> Dict[str, AgentResponse]:
        """Invoke multiple agents in parallel.

        Args:
            agent_domains: List of domain names
            query: User query to send to each agent
            project_id: Optional project context

        Returns:
            Dict mapping domain -> AgentResponse
        """
        tasks = {}

        for domain in agent_domains:
            if domain not in self.agents:
                logger.warning(f"Agent not found for domain: {domain}")
                continue

            agent = self.agents[domain]
            task = agent.answer(query=query, project_id=project_id)
            tasks[domain] = task

        # Execute all in parallel
        if not tasks:
            return {}

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        # Map results back to domains
        responses = {}
        for domain, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Agent {domain} failed: {result}", exc_info=result)
            else:
                responses[domain] = result

        return responses

    def _merge_responses(
        self,
        responses: Dict[str, AgentResponse],
        query: str,
    ) -> Dict:
        """Merge multiple agent responses into one unified response.

        Strategy: Consensus merging
        - Take answers that address query
        - Merge citations
        - Average confidence
        - Combine metadata

        Args:
            responses: Dict of agent -> AgentResponse
            query: Original query (for relevance)

        Returns:
            Dict with merged answer, citations, confidence
        """
        if not responses:
            return {
                "answer": "No agents available to answer this query.",
                "citations": [],
                "confidence": 0.0,
            }

        if len(responses) == 1:
            # Single agent: return as-is
            resp = list(responses.values())[0]
            return {
                "answer": resp.answer,
                "citations": resp.citations,
                "confidence": resp.confidence,
            }

        # Multiple agents: merge answers
        answers = [r.answer for r in responses.values()]
        all_citations = []
        confidences = []

        for resp in responses.values():
            all_citations.extend(resp.citations)
            confidences.append(resp.confidence)

        # Remove duplicate citations
        unique_citations = self._deduplicate_citations(all_citations)

        # Merge answers: concatenate with agent labels
        merged_answer = self._merge_answers(answers, responses)

        # Average confidence
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "answer": merged_answer,
            "citations": unique_citations,
            "confidence": avg_confidence,
        }

    def _merge_answers(self, answers: List[str], responses: Dict) -> str:
        """Merge multiple answers into one coherent response.

        Args:
            answers: List of answer texts
            responses: Dict mapping domain -> response (for context)

        Returns:
            Merged answer text
        """
        if not answers:
            return ""

        if len(answers) == 1:
            return answers[0]

        # Multi-answer: organize by domain
        merged_parts = []

        for domain, response in responses.items():
            # Format: "From Project Agent: ..."
            agent_name = response.agent_name.replace("Agent", "").replace("_", " ")
            merged_parts.append(f"\n**{agent_name}:**\n{response.answer}")

        return "\n".join(merged_parts)

    def _deduplicate_citations(self, citations: List[Citation]) -> List[Citation]:
        """Remove duplicate citations.

        Args:
            citations: List of Citation objects

        Returns:
            Deduplicated list
        """
        seen = set()
        unique = []

        for citation in citations:
            key = (citation.source, citation.tool)
            if key not in seen:
                seen.add(key)
                unique.append(citation)

        return unique
