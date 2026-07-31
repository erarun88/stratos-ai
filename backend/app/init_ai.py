"""Initialize AI infrastructure.

Runs migrations, downloads NLTK data, verifies OpenAI API connection.

Usage:
    python -m app.init_ai
"""

import logging
import sys

from app.config import settings
from app.migrate_embeddings import migrate

logger = logging.getLogger(__name__)

# Configure logging for startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def download_nltk_data():
    """Download required NLTK datasets."""
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        logger.info("✓ NLTK punkt tokenizer downloaded")
    except Exception as e:
        logger.error(f"Failed to download NLTK data: {e}")
        return False
    return True


def verify_openai_api():
    """Verify OpenAI API key is configured and working."""
    if not settings.openai_api_key:
        logger.warning("⚠ OPENAI_API_KEY not configured")
        logger.warning("  AI features will not work until you set OPENAI_API_KEY in .env")
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        # Quick test: get model info
        models = client.models.list()
        logger.info(f"✓ OpenAI API verified ({len(list(models))} models available)")
        return True
    except Exception as e:
        logger.error(f"Failed to verify OpenAI API: {e}")
        logger.error("  Check your OPENAI_API_KEY and API quota")
        return False


def main():
    """Run all initialization steps."""
    logger.info("Initializing StratOS AI - Document Intelligence")
    logger.info(f"  Embedding model: {settings.embedding_model}")
    logger.info(f"  Max chunk tokens: {settings.embedding_max_chunk_tokens}")
    logger.info(f"  Embedding worker: {'enabled' if settings.embedding_worker_enabled else 'disabled'}")

    # Step 1: Run database migrations
    logger.info("\n[1/3] Running database migrations...")
    try:
        migrate()
        logger.info("✓ Database migrations complete")
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False

    # Step 2: Download NLTK data
    logger.info("\n[2/3] Downloading NLTK data...")
    if not download_nltk_data():
        logger.error("✗ NLTK setup failed")
        return False

    # Step 3: Verify OpenAI API
    logger.info("\n[3/3] Verifying OpenAI API...")
    if not verify_openai_api():
        logger.error("✗ OpenAI API verification failed")
        logger.info("  Run this again after configuring OPENAI_API_KEY")
        return False

    logger.info("\n✓ AI infrastructure initialized successfully!")
    logger.info("  You can now:")
    logger.info("    1. Upload documents (embeddings will be generated automatically)")
    logger.info("    2. Search documents semantically (POST /search/semantic)")
    logger.info("    3. Monitor embedding progress (GET /documents/{id}/embedding-status)")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
