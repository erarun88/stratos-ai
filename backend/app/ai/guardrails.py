"""Guardrails - Enterprise safety checks for AI responses.

Responsibilities:
- Grounding verification (answer supported by context)
- Hallucination detection
- Citation validation
- Confidence scoring
"""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class Guardrails:
    """Enterprise guardrails for AI responses."""

    def __init__(self, strict_mode: bool = False):
        """Initialize guardrails.

        Args:
            strict_mode: If True, stricter grounding and hallucination checks
        """
        self.strict_mode = strict_mode

    def ground_response(
        self,
        answer: str,
        context: str,
        min_overlap: float = 0.1,
    ) -> Tuple[bool, float, str]:
        """Verify response is grounded in provided context.

        Args:
            answer: LLM-generated answer
            context: Retrieved context from tools
            min_overlap: Minimum token overlap required (0.0-1.0)

        Returns:
            Tuple of (is_grounded, confidence_score, explanation)
        """
        if not context:
            return False, 0.0, "No context provided for grounding check"

        # Extract key terms from answer
        answer_terms = set(self._extract_terms(answer))
        context_terms = set(self._extract_terms(context))

        # Calculate overlap
        overlap = answer_terms & context_terms
        overlap_ratio = len(overlap) / len(answer_terms) if answer_terms else 1.0

        is_grounded = overlap_ratio >= min_overlap
        confidence = overlap_ratio

        if self.strict_mode and overlap_ratio < 0.5:
            confidence = confidence * 0.5  # Penalize in strict mode

        explanation = (
            f"Answer contains {len(answer_terms)} key terms, "
            f"{len(overlap)} found in context ({overlap_ratio:.1%} overlap)"
        )

        logger.info(f"Grounding check: {is_grounded} (confidence: {confidence:.2f})")
        return is_grounded, confidence, explanation

    def check_hallucination(
        self,
        answer: str,
        context: str,
    ) -> Tuple[float, str]:
        """Detect potential hallucinations in response.

        Hallucination indicators:
        - Specific numbers/dates not in context
        - Named entities not in context
        - Confident statements about unknown facts

        Args:
            answer: LLM-generated answer
            context: Retrieved context

        Returns:
            Tuple of (hallucination_score, explanation)
            Score: 0.0 = no hallucination risk, 1.0 = high risk
        """
        risk_score = 0.0

        # Check for specific numbers
        answer_numbers = re.findall(r"\d+(?:\.\d+)?", answer)
        context_numbers = set(re.findall(r"\d+(?:\.\d+)?", context))
        unverified_numbers = [n for n in answer_numbers if n not in context_numbers]
        if unverified_numbers:
            risk_score += 0.2 * min(1.0, len(unverified_numbers) / 5)

        # Check for confident language
        confident_phrases = ["definitely", "certainly", "absolutely", "proven", "fact"]
        confident_count = sum(1 for phrase in confident_phrases if phrase in answer.lower())
        if confident_count > 0:
            risk_score += 0.1 * min(1.0, confident_count / 5)

        # Check context size - small context = higher hallucination risk
        if len(context) < 200:
            risk_score += 0.1

        # Cap at 1.0
        risk_score = min(1.0, risk_score)

        explanation = f"Hallucination risk score: {risk_score:.2f}"
        if unverified_numbers:
            explanation += f" ({len(unverified_numbers)} unverified numbers)"
        if confident_count > 0:
            explanation += f" ({confident_count} high-confidence claims)"

        logger.info(f"Hallucination check: risk={risk_score:.2f}")
        return risk_score, explanation

    def validate_citations(
        self,
        answer: str,
        citations: List[dict],
    ) -> Tuple[bool, str]:
        """Validate that claims are cited.

        Args:
            answer: LLM-generated answer
            citations: List of citation dicts with 'content' and 'source' keys

        Returns:
            Tuple of (citations_valid, explanation)
        """
        if not citations:
            logger.warning("No citations provided for validation")
            return False, "No citations provided"

        citation_contents = [c.get("content", "").lower() for c in citations]

        # Check if key statements are cited
        sentences = re.split(r"[.!?]+", answer)
        uncited_sentences = []

        for sentence in sentences:
            sentence = sentence.strip().lower()
            if len(sentence) < 10:
                continue

            is_cited = any(
                citation_content and citation_content in sentence
                for citation_content in citation_contents
            )

            if not is_cited:
                uncited_sentences.append(sentence[:50])

        is_valid = len(uncited_sentences) == 0
        explanation = (
            f"All {len(sentences)} major statements cited"
            if is_valid
            else f"{len(uncited_sentences)} statements not directly cited"
        )

        logger.info(f"Citation validation: {is_valid} - {explanation}")
        return is_valid, explanation

    def score_confidence(
        self,
        grounding_score: float,
        hallucination_risk: float,
        context_quality: float = 1.0,
    ) -> float:
        """Calculate overall confidence score for response.

        Args:
            grounding_score: Grounding confidence (0.0-1.0)
            hallucination_risk: Hallucination risk (0.0-1.0)
            context_quality: Quality of retrieved context (0.0-1.0)

        Returns:
            Overall confidence score (0.0-1.0)
        """
        # Formula: grounding * (1 - hallucination) * context_quality
        confidence = grounding_score * (1.0 - hallucination_risk) * context_quality
        return min(1.0, max(0.0, confidence))

    def _extract_terms(self, text: str) -> List[str]:
        """Extract key terms from text.

        Removes common words, splits on non-alphanumeric.

        Args:
            text: Text to extract terms from

        Returns:
            List of terms
        """
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "is", "are", "be", "been", "was", "were", "have", "has", "do", "does",
            "will", "would", "could", "should", "may", "might", "can", "must",
        }

        # Extract alphanumeric terms
        terms = re.findall(r"\b\w+\b", text.lower())
        return [t for t in terms if t not in stop_words and len(t) > 2]
