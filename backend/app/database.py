from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Import all models so they're registered with SQLAlchemy's Base
# This ensures create_all() and migrations work correctly
from app.models.project import Project  # noqa: F401, E402
from app.models.engineer import Engineer  # noqa: F401, E402
from app.models.document import Document  # noqa: F401, E402
from app.models.embedding import DocumentEmbedding, EmbeddingOperation  # noqa: F401, E402


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a database session per request.

    The session is closed when the request finishes, including on error.
    """
    with Session(engine) as session:
        yield session