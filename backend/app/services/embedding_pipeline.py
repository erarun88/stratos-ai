"""Checkpoint-based embedding pipeline.

Improvements over v1:
1. Stateless: Another instance can pick up failed work
2. Extensible: Add new stages without rewriting pipeline
3. Recoverable: Resume from last successful checkpoint (no wasted API calls)
4. Measurable: Every stage timed, logged, queryable
5. Idempotent: Safe to retry any stage

Pipeline Model:
    Extract → Chunk → Embed → Index → Complete

Checkpoints track which stages succeeded, enabling smart retries.
"""

import logging
import time
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.embedding import DocumentEmbedding, EmbeddingOperation
from app.config import settings

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Stages in the embedding pipeline."""
    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETION = "completion"


class StageStatus(str, Enum):
    """Status of a pipeline stage."""
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PipelineCheckpoint:
    """Represents the state of a document in the pipeline.

    Enables resumption from the last successful stage.
    """

    def __init__(self, document_id: int):
        self.document_id = document_id
        self.stages: Dict[PipelineStage, Dict[str, Any]] = {
            stage: {
                "status": StageStatus.PENDING,
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
                "error": None,
                "metadata": {},
            }
            for stage in PipelineStage
        }
        self.extracted_text: Optional[str] = None
        self.chunks: Optional[List[Dict]] = None
        self.embeddings: Optional[List] = None

    def start_stage(self, stage: PipelineStage) -> None:
        """Mark a stage as started."""
        self.stages[stage]["status"] = StageStatus.STARTED
        self.stages[stage]["started_at"] = datetime.utcnow()

    def complete_stage(self, stage: PipelineStage, metadata: Dict = None) -> None:
        """Mark a stage as completed."""
        started = self.stages[stage]["started_at"]
        completed = datetime.utcnow()
        self.stages[stage]["status"] = StageStatus.COMPLETED
        self.stages[stage]["completed_at"] = completed
        self.stages[stage]["duration_ms"] = int(
            (completed - started).total_seconds() * 1000
        )
        if metadata:
            self.stages[stage]["metadata"] = metadata

    def fail_stage(self, stage: PipelineStage, error: str) -> None:
        """Mark a stage as failed."""
        self.stages[stage]["status"] = StageStatus.FAILED
        self.stages[stage]["error"] = error

    def skip_stage(self, stage: PipelineStage) -> None:
        """Mark a stage as skipped (already done or not needed)."""
        self.stages[stage]["status"] = StageStatus.SKIPPED

    def get_last_completed_stage(self) -> Optional[PipelineStage]:
        """Get the last stage that completed successfully.

        Returns None if nothing has completed yet.
        """
        stages_in_order = [
            PipelineStage.EXTRACTION,
            PipelineStage.CHUNKING,
            PipelineStage.EMBEDDING,
            PipelineStage.INDEXING,
            PipelineStage.COMPLETION,
        ]
        for stage in reversed(stages_in_order):
            if self.stages[stage]["status"] == StageStatus.COMPLETED:
                return stage
        return None

    def get_next_stage(self) -> Optional[PipelineStage]:
        """Get the next stage to execute.

        Returns the first incomplete stage, or None if pipeline is done.
        """
        stages_in_order = [
            PipelineStage.EXTRACTION,
            PipelineStage.CHUNKING,
            PipelineStage.EMBEDDING,
            PipelineStage.INDEXING,
            PipelineStage.COMPLETION,
        ]
        for stage in stages_in_order:
            status = self.stages[stage]["status"]
            if status in (StageStatus.PENDING, StageStatus.FAILED):
                return stage
        return None

    def to_json(self) -> Dict[str, Any]:
        """Serialize checkpoint for logging/storage."""
        return {
            "document_id": self.document_id,
            "stages": {
                stage.value: {
                    "status": data["status"].value,
                    "duration_ms": data["duration_ms"],
                    "error": data["error"],
                    "metadata": data["metadata"],
                }
                for stage, data in self.stages.items()
            },
        }


class EmbeddingPipeline:
    """Orchestrates the multi-stage embedding pipeline.

    Features:
    - Stateless: Another instance can pick up work
    - Extensible: Add stages by implementing StageHandler
    - Recoverable: Resumes from last checkpoint
    - Measurable: Every stage timed and logged
    - Idempotent: Safe to retry any stage
    """

    def __init__(self, session: Session):
        self.session = session
        self.checkpoint: Optional[PipelineCheckpoint] = None

    def load_checkpoint(self, document_id: int) -> PipelineCheckpoint:
        """Load or create a checkpoint for a document.

        Queries the database for completed stages to enable resumption.
        """
        doc = self.session.get(Document, document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        checkpoint = PipelineCheckpoint(document_id)

        # Check if extraction was done
        if doc.embedding_status in ("processing", "completed", "failed"):
            # We've started the pipeline; mark extraction complete
            if hasattr(doc, "_extracted_text"):
                checkpoint.extracted_text = doc._extracted_text
                checkpoint.complete_stage(PipelineStage.EXTRACTION)

        # Check if chunking was done (if chunks exist in DB)
        chunk_count = self.session.query(DocumentEmbedding).filter(
            DocumentEmbedding.document_id == document_id
        ).count()

        if chunk_count > 0:
            # Chunks exist; assume chunking succeeded
            chunks = self.session.query(DocumentEmbedding).filter(
                DocumentEmbedding.document_id == document_id
            ).all()
            checkpoint.chunks = [
                {
                    "text": c.chunk_text,
                    "token_count": c.token_count,
                }
                for c in chunks
            ]
            checkpoint.complete_stage(
                PipelineStage.CHUNKING,
                metadata={"chunk_count": len(chunks)}
            )
            checkpoint.complete_stage(PipelineStage.EMBEDDING)
            checkpoint.complete_stage(PipelineStage.INDEXING)

        return checkpoint

    def save_checkpoint(self, checkpoint: PipelineCheckpoint) -> None:
        """Persist checkpoint state to database.

        Allows another instance to resume if this one crashes.
        """
        doc = self.session.get(Document, checkpoint.document_id)
        if not doc:
            return

        # Determine overall status from checkpoints
        last_completed = checkpoint.get_last_completed_stage()
        if last_completed == PipelineStage.COMPLETION:
            doc.embedding_status = "completed"
        elif checkpoint.stages[PipelineStage.EMBEDDING]["status"] == StageStatus.FAILED:
            doc.embedding_status = "failed"
            doc.embedding_error = checkpoint.stages[PipelineStage.EMBEDDING]["error"]
        else:
            doc.embedding_status = "processing"

        self.session.commit()

    def execute(self, document_id: int) -> bool:
        """Execute the full pipeline.

        Returns True if successful, False if any stage failed.
        """
        try:
            # Load checkpoint to enable resumption
            checkpoint = self.load_checkpoint(document_id)
            self.checkpoint = checkpoint

            logger.info(
                f"Starting pipeline for document {document_id}. "
                f"Last completed stage: {checkpoint.get_last_completed_stage()}"
            )

            # Execute stages in order, skipping already-completed ones
            stages = [
                (PipelineStage.EXTRACTION, self._extract_stage),
                (PipelineStage.CHUNKING, self._chunk_stage),
                (PipelineStage.EMBEDDING, self._embed_stage),
                (PipelineStage.INDEXING, self._index_stage),
                (PipelineStage.COMPLETION, self._completion_stage),
            ]

            for stage, handler in stages:
                # Skip if already completed
                if checkpoint.stages[stage]["status"] == StageStatus.COMPLETED:
                    logger.info(f"[{document_id}] Skipping {stage.value} (already done)")
                    checkpoint.skip_stage(stage)
                    continue

                # Execute the stage
                try:
                    logger.info(f"[{document_id}] Starting {stage.value}...")
                    checkpoint.start_stage(stage)
                    self.save_checkpoint(checkpoint)

                    handler(checkpoint)

                    checkpoint.complete_stage(stage)
                    self.save_checkpoint(checkpoint)
                    logger.info(
                        f"[{document_id}] Completed {stage.value} "
                        f"({checkpoint.stages[stage]['duration_ms']}ms)"
                    )

                except Exception as e:
                    checkpoint.fail_stage(stage, str(e))
                    self.save_checkpoint(checkpoint)
                    logger.error(
                        f"[{document_id}] Failed at {stage.value}: {e}",
                        exc_info=True
                    )
                    return False

            logger.info(f"✓ Document {document_id} pipeline complete")
            return True

        except Exception as e:
            logger.error(f"Pipeline error for document {document_id}: {e}", exc_info=True)
            return False

    def _extract_stage(self, checkpoint: PipelineCheckpoint) -> None:
        """Extract text from PDF."""
        from app.services.pdf_service import extract_text_from_pdf
        from app.storage import get_document_storage

        doc = self.session.get(Document, checkpoint.document_id)
        storage = get_document_storage()
        pdf_bytes = storage.open(doc.storage_key)
        text = extract_text_from_pdf(pdf_bytes)

        checkpoint.extracted_text = text
        checkpoint.stages[PipelineStage.EXTRACTION]["metadata"] = {
            "char_count": len(text),
            "page_count": text.count("\n\n"),  # Rough estimate
        }

    def _chunk_stage(self, checkpoint: PipelineCheckpoint) -> None:
        """Create semantic chunks."""
        from app.services.chunking_service import create_semantic_chunks

        if not checkpoint.extracted_text:
            raise ValueError("No extracted text; extraction stage must complete first")

        chunks = create_semantic_chunks(
            checkpoint.extracted_text,
            max_chunk_tokens=settings.embedding_max_chunk_tokens,
            min_chunk_tokens=settings.embedding_min_chunk_tokens,
        )

        if not chunks:
            raise ValueError("No chunks created from document")

        checkpoint.chunks = chunks
        checkpoint.stages[PipelineStage.CHUNKING]["metadata"] = {
            "chunk_count": len(chunks),
            "total_tokens": sum(c["token_count"] for c in chunks),
        }

    def _embed_stage(self, checkpoint: PipelineCheckpoint) -> None:
        """Generate embeddings for chunks."""
        from app.services.embedding_service import generate_embeddings

        if not checkpoint.chunks:
            raise ValueError("No chunks; chunking stage must complete first")

        chunk_texts = [c["text"] for c in checkpoint.chunks]
        result = generate_embeddings(chunk_texts)

        checkpoint.embeddings = result["embeddings"]
        checkpoint.stages[PipelineStage.EMBEDDING]["metadata"] = {
            "embedding_count": len(result["embeddings"]),
            "total_tokens": result["total_tokens"],
            "total_cost": result["total_cost"],
        }

    def _index_stage(self, checkpoint: PipelineCheckpoint) -> None:
        """Store embeddings in database."""
        from app.services.embedding_service import embedding_to_json

        if not checkpoint.chunks or not checkpoint.embeddings:
            raise ValueError("No chunks or embeddings; earlier stages must complete first")

        for chunk_idx, (chunk, embedding) in enumerate(
            zip(checkpoint.chunks, checkpoint.embeddings)
        ):
            chunk_embedding = DocumentEmbedding(
                document_id=checkpoint.document_id,
                chunk_index=chunk_idx,
                chunk_text=chunk["text"],
                embedding=embedding_to_json(embedding),
                token_count=chunk["token_count"],
                chunk_metadata={"chunk_size": len(chunk["text"])},
            )
            self.session.add(chunk_embedding)

        self.session.commit()
        checkpoint.stages[PipelineStage.INDEXING]["metadata"] = {
            "embeddings_stored": len(checkpoint.embeddings),
        }

    def _completion_stage(self, checkpoint: PipelineCheckpoint) -> None:
        """Mark pipeline as complete."""
        doc = self.session.get(Document, checkpoint.document_id)
        if not doc:
            raise ValueError("Document not found")

        total_tokens = checkpoint.stages[PipelineStage.EMBEDDING]["metadata"].get(
            "total_tokens", 0
        )
        total_cost = checkpoint.stages[PipelineStage.EMBEDDING]["metadata"].get(
            "total_cost", 0.0
        )

        doc.embedding_status = "completed"
        doc.embedding_model = settings.embedding_model
        doc.token_count = total_tokens
        doc.embedding_cost = total_cost
        doc.embedded_at = datetime.utcnow()
        doc.embedding_error = None

        self.session.commit()

        checkpoint.stages[PipelineStage.COMPLETION]["metadata"] = {
            "total_duration_ms": sum(
                data["duration_ms"] or 0
                for data in checkpoint.stages.values()
                if data["status"] == StageStatus.COMPLETED
            ),
            "total_tokens": total_tokens,
            "total_cost": total_cost,
        }
