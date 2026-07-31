"""Semantic text chunking service.

Splits documents into semantically meaningful chunks for embedding.
Uses sentence-level splitting with token-aware merging.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Approximate tokens per word (English, average)
TOKENS_PER_WORD = 1.3


def estimate_tokens(text: str) -> int:
    """Rough estimate of token count (for OpenAI API).

    OpenAI's tokenizer is precise, but this gives a quick estimate
    without requiring the tiktoken library.

    Args:
        text: The text to estimate

    Returns:
        Approximate token count
    """
    words = len(text.split())
    return int(words * TOKENS_PER_WORD)


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences.

    Simple heuristic: split on periods, exclamation marks, question marks
    followed by whitespace and uppercase letter.

    Args:
        text: Text to split

    Returns:
        List of sentences (stripped)
    """
    # Replace newlines with spaces for smoother splitting
    text = re.sub(r'\n+', ' ', text)

    # Split on sentence boundaries
    # Matches: punctuation + (space + uppercase) or end of string
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    # Clean up and filter empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def create_semantic_chunks(
    text: str,
    max_chunk_tokens: int = 800,
    min_chunk_tokens: int = 100,
) -> List[dict]:
    """Split text into semantic chunks.

    Groups sentences into chunks that:
    - Don't exceed max_chunk_tokens
    - Are at least min_chunk_tokens (to avoid tiny chunks)
    - Break at sentence boundaries (preserve meaning)

    Args:
        text: Text to chunk
        max_chunk_tokens: Maximum tokens per chunk (default: 800)
        min_chunk_tokens: Minimum tokens per chunk (default: 100)

    Returns:
        List of chunks: [{"text": "...", "token_count": N}, ...]
    """
    if not text or not text.strip():
        return []

    sentences = split_into_sentences(text)
    if not sentences:
        return []

    chunks = []
    current_chunk_sentences = []
    current_chunk_tokens = 0

    for sentence in sentences:
        sentence_tokens = estimate_tokens(sentence)

        # Check if adding this sentence would exceed the limit
        would_exceed = current_chunk_tokens + sentence_tokens > max_chunk_tokens

        if would_exceed and current_chunk_sentences:
            # Finalize current chunk and start a new one
            chunk_text = " ".join(current_chunk_sentences).strip()
            chunk_tokens = estimate_tokens(chunk_text)

            # Only include chunks that meet minimum size
            if chunk_tokens >= min_chunk_tokens:
                chunks.append({
                    "text": chunk_text,
                    "token_count": chunk_tokens,
                })

            current_chunk_sentences = []
            current_chunk_tokens = 0

        # Add sentence to current chunk
        current_chunk_sentences.append(sentence)
        current_chunk_tokens += sentence_tokens

    # Finalize last chunk
    if current_chunk_sentences:
        chunk_text = " ".join(current_chunk_sentences).strip()
        chunk_tokens = estimate_tokens(chunk_text)
        if chunk_tokens >= min_chunk_tokens:
            chunks.append({
                "text": chunk_text,
                "token_count": chunk_tokens,
            })

    logger.info(
        f"Created {len(chunks)} semantic chunks from {len(sentences)} sentences, "
        f"total {sum(c['token_count'] for c in chunks)} tokens"
    )

    return chunks
