"""OpenAI embedding service with retry logic.

Generates embeddings for document chunks using OpenAI API.
Handles rate limiting, retries, and cost tracking.
"""

import json
import logging
from typing import List

from openai import OpenAI, RateLimitError, APIError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

# Cost per 1M tokens for text-embedding-3-small (2024 pricing)
EMBEDDING_COST_PER_1M_TOKENS = 0.02


class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass


def _init_openai_client() -> OpenAI:
    """Initialize OpenAI client with API key from settings."""
    if not settings.openai_api_key:
        raise EmbeddingError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=settings.openai_api_key)


@retry(
    stop=stop_after_attempt(4),  # Retry up to 3 times (4 total attempts)
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
def _call_openai_embedding_api(client: OpenAI, texts: List[str]) -> dict:
    """Call OpenAI embedding API with automatic retry on rate limits.

    Args:
        client: OpenAI client instance
        texts: List of text chunks to embed

    Returns:
        Response dict with embeddings and usage info

    Raises:
        EmbeddingError: If all retries fail
    """
    try:
        response = client.embeddings.create(
            input=texts,
            model=settings.embedding_model,
        )
        return {
            "embeddings": [item.embedding for item in response.data],
            "usage_tokens": response.usage.total_tokens if response.usage else 0,
        }
    except RateLimitError as e:
        logger.warning(f"Rate limited by OpenAI API: {e}")
        raise  # tenacity will retry
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise  # tenacity will retry
    except Exception as e:
        logger.error(f"Unexpected error during embedding: {e}")
        raise EmbeddingError(f"Embedding API call failed: {e}")


def generate_embeddings(texts: List[str]) -> dict:
    """Generate embeddings for a list of texts.

    Batches texts into reasonable sizes and handles rate limiting.

    Args:
        texts: List of text chunks to embed

    Returns:
        {
            "embeddings": [[float, ...], ...],  # One per text
            "total_tokens": int,
            "total_cost": float,
        }

    Raises:
        EmbeddingError: If embedding fails after retries
    """
    if not texts:
        return {"embeddings": [], "total_tokens": 0, "total_cost": 0.0}

    try:
        client = _init_openai_client()

        all_embeddings = []
        total_tokens = 0

        # Batch texts to avoid overwhelming the API
        batch_size = settings.embedding_batch_size
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(f"Embedding batch {i // batch_size + 1}: {len(batch)} texts")

            result = _call_openai_embedding_api(client, batch)
            all_embeddings.extend(result["embeddings"])
            total_tokens += result["usage_tokens"]

        # Calculate cost
        total_cost = (total_tokens / 1_000_000) * EMBEDDING_COST_PER_1M_TOKENS

        logger.info(
            f"Generated {len(all_embeddings)} embeddings, "
            f"{total_tokens} tokens, cost: ${total_cost:.4f}"
        )

        return {
            "embeddings": all_embeddings,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
        }

    except EmbeddingError:
        raise
    except Exception as e:
        raise EmbeddingError(f"Embedding generation failed: {e}")


def embedding_to_json(embedding: List[float]) -> str:
    """Serialize embedding vector to JSON string."""
    return json.dumps(embedding)


def embedding_from_json(json_str: str) -> List[float]:
    """Deserialize embedding vector from JSON string."""
    return json.loads(json_str)
