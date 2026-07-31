"""Response formatter - Format LLM responses for different audiences.

Supports multiple output modes:
- concise: Brief answer (2-3 sentences)
- detailed: Full analysis with evidence
- executive: Structured for C-suite (summary, metrics, risks, actions)
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Format responses for different audiences and use cases."""

    def format(
        self,
        answer: str,
        mode: str = "concise",
        citations: Optional[List[dict]] = None,
    ) -> str:
        """Format response based on mode.

        Args:
            answer: LLM-generated answer text
            mode: "concise", "detailed", or "executive"
            citations: Optional list of citations

        Returns:
            Formatted response string
        """
        if mode == "concise":
            return self._format_concise(answer, citations)
        elif mode == "detailed":
            return self._format_detailed(answer, citations)
        elif mode == "executive":
            return self._format_executive(answer, citations)
        else:
            logger.warning(f"Unknown response mode: {mode}, using concise")
            return self._format_concise(answer, citations)

    def _format_concise(
        self,
        answer: str,
        citations: Optional[List[dict]] = None,
    ) -> str:
        """Format as concise summary.

        Args:
            answer: Answer text
            citations: Citations

        Returns:
            Formatted response
        """
        # Truncate to first 2-3 sentences
        sentences = answer.split(". ")
        concise_answer = ". ".join(sentences[:2]) + ("." if sentences else "")

        if citations:
            citations_section = self._format_citations_section(citations)
            return f"{concise_answer}\n\n{citations_section}"

        return concise_answer

    def _format_detailed(
        self,
        answer: str,
        citations: Optional[List[dict]] = None,
    ) -> str:
        """Format as detailed analysis.

        Args:
            answer: Answer text
            citations: Citations

        Returns:
            Formatted response
        """
        response = answer

        if citations:
            citations_section = self._format_citations_section(citations)
            response = f"{answer}\n\n{citations_section}"

        return response

    def _format_executive(
        self,
        answer: str,
        citations: Optional[List[dict]] = None,
    ) -> str:
        """Format for executive consumption.

        Structured format with:
        - Executive summary (1 sentence)
        - Key points (bullets)
        - Risks (if any)
        - Recommendations
        - Citations

        Args:
            answer: Answer text
            citations: Citations

        Returns:
            Formatted response
        """
        lines = [answer]

        if citations:
            lines.append("")
            lines.append("**Sources:**")
            for i, citation in enumerate(citations[:3], 1):
                source = citation.get("source", "Unknown")
                relevance = citation.get("relevance", "")
                lines.append(f"  {i}. {source}{f' (relevance: {relevance})' if relevance else ''}")

        return "\n".join(lines)

    def _format_citations_section(self, citations: List[dict]) -> str:
        """Format citations section.

        Args:
            citations: List of citations

        Returns:
            Formatted citations text
        """
        if not citations:
            return ""

        lines = ["**Sources:**"]
        for i, citation in enumerate(citations[:5], 1):
            source = citation.get("source", "Unknown")
            lines.append(f"  {i}. {source}")

        return "\n".join(lines)

    def format_for_json(
        self,
        answer: str,
        citations: Optional[List[dict]] = None,
        confidence: float = 0.0,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Format response as JSON-serializable dict.

        Args:
            answer: Answer text
            citations: Citations
            confidence: Confidence score 0.0-1.0
            metadata: Optional metadata dict

        Returns:
            Dict suitable for JSON response
        """
        return {
            "answer": answer,
            "citations": citations or [],
            "confidence": float(confidence),
            "metadata": metadata or {},
        }
