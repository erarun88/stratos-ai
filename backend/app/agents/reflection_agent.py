"""Reflection Agent - Post-generation quality review and improvement.

The Reflection Agent reviews responses BEFORE returning them to users.

Responsibilities:
1. Detect hallucinations (claims not supported by evidence)
2. Verify citations exist and match claims
3. Identify unsupported statements
4. Suggest clarity improvements
5. Improve executive wording
6. One-pass refinement (no infinite loops)

Design: Reflection is AFTER generation, so response quality is verified before delivery.
"""

import logging
import time
from typing import Dict, Optional, Tuple

from app.ai.guardrails import Guardrails
from app.ai.llm_client import LLMClient
from app.execution_studio import auto_trace, emit_event

logger = logging.getLogger(__name__)


class ReflectionResult:
    """Result of reflection review."""

    def __init__(
        self,
        original_answer: str,
        improved_answer: Optional[str] = None,
        issues_found: bool = False,
        hallucination_risk: float = 0.0,
        citation_gaps: list = None,
        clarity_score: float = 0.8,
        reflection_applied: bool = False,
        reflection_reasoning: str = "",
    ):
        self.original_answer = original_answer
        self.improved_answer = improved_answer or original_answer
        self.issues_found = issues_found
        self.hallucination_risk = hallucination_risk
        self.citation_gaps = citation_gaps or []
        self.clarity_score = clarity_score
        self.reflection_applied = reflection_applied
        self.reflection_reasoning = reflection_reasoning


class ReflectionAgent:
    """Reviews and improves generated responses for quality assurance.

    One-pass reflection: if improvements needed, apply once and return.
    Never creates loops (no "reflect on reflection").

    Usage:
        reflection = ReflectionAgent()
        result = await reflection.review(
            answer="Original response...",
            citations=[Citation(...), ...],
            context="Project data..."
        )
        # Use result.improved_answer instead of original
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """Initialize Reflection Agent.

        Args:
            llm_client: Optional custom LLM client
        """
        self.llm_client = llm_client or LLMClient()
        self.guardrails = Guardrails(strict_mode=True)
        logger.info("ReflectionAgent initialized")

    @auto_trace(component="ReflectionAgent", action="review_response")
    async def review(
        self,
        answer: str,
        citations: list = None,
        context: str = "",
        confidence: float = 0.7,
    ) -> ReflectionResult:
        """Review and improve a generated response.

        Args:
            answer: Generated response to review
            citations: Citations supporting the answer
            context: Context used to generate answer
            confidence: Original response confidence

        Returns:
            ReflectionResult with original/improved answers and issues found
        """
        start_time = time.time()
        logger.info(f"Reflecting on response: {answer[:100]}...")

        try:
            # Step 1: Detect hallucinations
            emit_event("ReflectionAgent", "check_hallucinations")
            hallucination_risk, _ = self.guardrails.check_hallucination(answer, context)
            emit_event("ReflectionAgent", "hallucinations_checked", metadata={
                "hallucination_risk": hallucination_risk
            })

            # Step 2: Verify citations
            emit_event("ReflectionAgent", "verify_citations")
            citation_gaps = self._verify_citations(answer, citations or [])
            emit_event("ReflectionAgent", "citations_verified", metadata={
                "citation_gaps": len(citation_gaps)
            })

            # Step 3: Check clarity
            emit_event("ReflectionAgent", "assess_clarity")
            clarity_score = self._assess_clarity(answer)
            emit_event("ReflectionAgent", "clarity_assessed", metadata={
                "clarity_score": clarity_score
            })

            # Step 4: Determine if improvement needed
            needs_improvement = (
                hallucination_risk > 0.3 or len(citation_gaps) > 0 or clarity_score < 0.7
            )

            # Step 5: Apply one-pass improvement if needed
            improved_answer = answer
            improvement_reasoning = ""

            if needs_improvement:
                logger.info(f"Issues found: hallucination={hallucination_risk:.2f}, "
                           f"gaps={len(citation_gaps)}, clarity={clarity_score:.2f}")

                emit_event("ReflectionAgent", "improve_answer")
                improved_answer, improvement_reasoning = await self._improve_answer(
                    answer, citation_gaps, clarity_score, context
                )
                emit_event("ReflectionAgent", "answer_improved", metadata={
                    "improvement_length": len(improved_answer) - len(answer)
                })
            else:
                improvement_reasoning = "Response is high quality, no improvements needed"

            elapsed_ms = (time.time() - start_time) * 1000

            result = ReflectionResult(
                original_answer=answer,
                improved_answer=improved_answer,
                issues_found=needs_improvement,
                hallucination_risk=hallucination_risk,
                citation_gaps=citation_gaps,
                clarity_score=clarity_score,
                reflection_applied=needs_improvement,
                reflection_reasoning=improvement_reasoning,
            )

            logger.info(
                f"Reflection complete: applied={needs_improvement}, "
                f"elapsed_ms={elapsed_ms:.0f}"
            )

            return result

        except Exception as e:
            logger.error(f"Reflection failed: {e}", exc_info=True)
            # On error, return original answer unchanged
            return ReflectionResult(
                original_answer=answer,
                improved_answer=answer,
                issues_found=False,
                reflection_applied=False,
                reflection_reasoning=f"Reflection error: {str(e)}",
            )

    def _verify_citations(self, answer: str, citations: list) -> list:
        """Verify that citations support the claims in the answer.

        Args:
            answer: The generated answer
            citations: List of citations

        Returns:
            List of gaps (unsupported claims)
        """
        if not citations:
            # If no citations but answer has claims, that's a gap
            if any(word in answer.lower() for word in ["according", "found", "shows", "indicates"]):
                return ["No citations provided for evidence-based claims"]
            return []

        gaps = []

        # Check if citations cover major claims
        citation_text = " ".join(str(c.content or c.source) for c in citations)

        # Simple heuristic: if answer makes specific claims without supporting citations
        key_claims = ["budget", "timeline", "risk", "milestone", "status"]
        for claim in key_claims:
            if claim in answer.lower() and claim not in citation_text.lower():
                gaps.append(f"Claim about '{claim}' lacks citation")

        return gaps

    def _assess_clarity(self, answer: str) -> float:
        """Assess clarity of the answer (0.0-1.0).

        Args:
            answer: The answer to assess

        Returns:
            Clarity score
        """
        score = 0.8  # Default reasonable score

        # Reduce for very long answers
        if len(answer) > 1000:
            score -= 0.1

        # Reduce for jargon-heavy answers (simple heuristic)
        jargon_terms = ["herein", "aforementioned", "notwithstanding"]
        jargon_count = sum(1 for term in jargon_terms if term in answer.lower())
        score -= jargon_count * 0.05

        # Boost for clear structure
        if "\n" in answer:  # Has line breaks, likely structured
            score += 0.1

        return max(0.0, min(1.0, score))

    async def _improve_answer(
        self, answer: str, citation_gaps: list, clarity_score: float, context: str
    ) -> Tuple[str, str]:
        """Improve the answer based on identified issues.

        One-pass only - no reflecting on the reflection.

        Args:
            answer: Original answer
            citation_gaps: Gaps found in citations
            clarity_score: Clarity assessment
            context: Context used to generate answer

        Returns:
            Tuple of (improved_answer, reasoning)
        """
        improvements = []

        if citation_gaps:
            improvements.append(
                f"Address citation gaps: {', '.join(citation_gaps[:2])}"
            )

        if clarity_score < 0.7:
            improvements.append("Improve clarity and reduce jargon")

        improvement_prompt = f"""Review this response and make ONE PASS of improvements.

Original response:
{answer}

Issues to address:
{chr(10).join(f'- {i}' for i in improvements)}

Provide an improved version that:
1. Addresses the issues above
2. Maintains factual accuracy
3. Keeps the same length/scope
4. Does NOT add new claims without evidence

IMPORTANT: This is a one-pass review. Return ONLY the improved response, no preamble.
"""

        try:
            improved = await self.llm_client.generate(
                messages=[{"role": "user", "content": improvement_prompt}],
                system_prompt="You are a quality reviewer improving AI-generated responses.",
            )

            reasoning = f"Applied improvements: {', '.join(improvements)}"
            return improved, reasoning

        except Exception as e:
            logger.warning(f"Improvement failed, using original: {e}")
            return answer, f"Improvement attempted but failed: {str(e)}"
