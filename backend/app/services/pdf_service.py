"""PDF text extraction service.

Safely extracts text from PDF documents with error handling.
"""

import logging
from io import BytesIO
from pypdf import PdfReader

logger = logging.getLogger(__name__)


class PdfExtractionError(Exception):
    """Raised when PDF text extraction fails."""
    pass


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF.

    Args:
        pdf_bytes: Raw PDF file content

    Returns:
        Combined text from all pages

    Raises:
        PdfExtractionError: If extraction fails
    """
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        if not reader.pages:
            raise PdfExtractionError("PDF has no pages")

        text_parts = []
        for page_num, page in enumerate(reader.pages):
            try:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num}: {e}")
                # Continue with other pages

        full_text = "\n\n".join(text_parts)

        if not full_text or not full_text.strip():
            raise PdfExtractionError("No text found in PDF")

        logger.info(f"Extracted text from {len(reader.pages)} pages, {len(full_text)} chars")
        return full_text

    except PdfExtractionError:
        raise
    except Exception as e:
        raise PdfExtractionError(f"PDF extraction failed: {e}")


def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Get the number of pages in a PDF."""
    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Failed to get page count: {e}")
        return 0
