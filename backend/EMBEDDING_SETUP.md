# AI Document Intelligence Setup Guide

This guide covers Phase 1 implementation of the AI processing architecture for semantic document search and RAG foundations.

## What's New

**Phase 1: Foundation** has been implemented with:

- ✅ Asynchronous document embedding pipeline (APScheduler-based)
- ✅ Semantic text chunking (sentence-aware, token-based)
- ✅ OpenAI embedding integration with retry logic
- ✅ pgvector storage for embeddings in PostgreSQL
- ✅ Semantic search API endpoint
- ✅ Embedding status monitoring
- ✅ Cost tracking and observability
- ✅ Comprehensive error handling

## Prerequisites

Before you can use the embedding features, you need:

1. **OpenAI API Account** — Sign up at https://platform.openai.com
2. **API Key** — Get your secret key from https://platform.openai.com/account/api-keys
3. **pgvector Extension** — Already available in Supabase PostgreSQL 15+

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

The new dependencies added:
- `openai>=1.3` — OpenAI API client
- `pypdf>=3.15` — PDF text extraction
- `nltk>=3.8` — Sentence tokenization
- `apscheduler>=3.10` — Background job scheduling
- `tenacity>=8.2` — Robust retry logic

### 2. Configure Environment Variables

Edit `backend/.env` and add:

```bash
# OpenAI API Key (required for embeddings)
OPENAI_API_KEY=sk-your-key-here

# Embedding configuration (optional, defaults shown)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_BATCH_SIZE=20
EMBEDDING_WORKER_ENABLED=true
EMBEDDING_MAX_RETRIES=3
EMBEDDING_RETRY_DELAY=1
EMBEDDING_MAX_CHUNK_TOKENS=800
EMBEDDING_MIN_CHUNK_TOKENS=100
```

### 3. Run AI Infrastructure Setup

This will:
- Enable pgvector extension in PostgreSQL
- Create embedding tables
- Download NLTK data
- Verify OpenAI API connection

```bash
python -m app.init_ai
```

Expected output:
```
Initializing StratOS AI - Document Intelligence
  Embedding model: text-embedding-3-small
  Max chunk tokens: 800
  Embedding worker: enabled

[1/3] Running database migrations...
✓ Database migrations complete

[2/3] Downloading NLTK data...
✓ NLTK punkt tokenizer downloaded

[3/3] Verifying OpenAI API...
✓ OpenAI API verified (50+ models available)

✓ AI infrastructure initialized successfully!
```

### 4. Start the Backend

```bash
# From backend directory
uvicorn app.main:app --reload
```

The embedding scheduler will start automatically and begin processing any pending documents.

## Usage

### Uploading Documents

Upload documents via the existing API or UI (no changes needed):

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@document.pdf" \
  -F "title=My Document" \
  -F "document_type=contract" \
  -F "project_id=1"
```

**What happens:**
1. File is validated and stored immediately ✓
2. Document is returned with `embedding_status: "queued"` ✓
3. Embedding scheduler picks it up ~30 seconds later
4. Text is extracted, chunked, embedded, and indexed
5. Embedding completes in 2-5 minutes (depending on document size)

### Checking Embedding Status

```bash
curl http://localhost:8000/documents/123/embedding-status
```

Response:
```json
{
  "document_id": 123,
  "embedding_status": "completed",
  "embedding_model": "text-embedding-3-small",
  "chunks_count": 42,
  "token_count": 15234,
  "embedding_cost_usd": 0.0152,
  "embedded_at": "2026-07-28T14:32:15",
  "error": null
}
```

**Status values:**
- `queued` — Waiting to be processed
- `processing` — Currently being embedded
- `completed` — Done; document is searchable
- `failed` — Error during embedding (see `error` field)

### Semantic Search

Once documents are embedded, search semantically:

```bash
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "project timeline risks",
    "limit": 10,
    "threshold": 0.7,
    "project_id": 1
  }'
```

Response:
```json
{
  "query": "project timeline risks",
  "results": [
    {
      "document_id": 1,
      "document_title": "Q3 Roadmap",
      "chunk_index": 3,
      "chunk_text": "Project timeline risks include...",
      "similarity_score": 0.92,
      "metadata": { "page": 2 }
    },
    ...
  ],
  "execution_time_ms": 45,
  "total_results": 5
}
```

**Parameters:**
- `query` (required) — What to search for
- `limit` (default: 10, max: 50) — Number of results
- `threshold` (default: 0.7) — Minimum similarity score (0.0-1.0)
- `project_id` (optional) — Filter by project
- `customer` (optional) — Filter by customer
- `document_type` (optional) — Filter by type

## Monitoring

### Check Embedding Queue Health

```bash
curl http://localhost:8000/search/health
```

### View Application Logs

The embedding pipeline logs:
- Document extraction
- Chunk creation statistics
- OpenAI API calls (tokens, cost)
- Any errors with full context

Example:
```
INFO: [123] Extracting text...
INFO: Created 42 semantic chunks from 278 sentences, total 15234 tokens
INFO: Embedding batch 1: 20 texts
INFO: Embedding batch 2: 20 texts
INFO: Embedding batch 3: 2 texts
INFO: Generated 42 embeddings, 15234 tokens, cost: $0.0152
INFO: ✓ Document 123 successfully embedded: 42 chunks, 15234 tokens, $0.0152, 8.3s
```

## Cost Tracking

Every document tracks embedding costs in `documents.embedding_cost`:

```python
# Get total cost across all documents
SELECT SUM(embedding_cost) FROM documents WHERE embedding_status = 'completed';
```

**Example costs:**
- 100 pages PDF → ~20k tokens → $0.0004
- 500 pages PDF → ~100k tokens → $0.002
- 1000 documents → ~2M tokens → $0.04/month

**Estimated monthly cost:** $0.50-$2.00 (for typical 100-1000 documents)

## Troubleshooting

### OpenAI API Key Not Set

**Error:** `OPENAI_API_KEY not configured; embedding worker will not process documents`

**Fix:** Add `OPENAI_API_KEY` to your `.env` file and restart the server.

### Rate Limiting

**Error:** `rate_limit_exceeded from OpenAI API`

**What it means:** You've hit OpenAI's rate limits (usually after 1000+ API calls)

**Fix:** Automatic retry with exponential backoff is built in. Wait a few minutes and retries will continue.

### Embedding Fails on Certain PDFs

**Common causes:**
1. **Scanned images** — PyPDF can't extract text from image-based PDFs. Fallback to keyword search.
2. **Encrypted/Password-protected** — PyPDF can't read these. Manual review needed.
3. **Unusual encoding** — Some PDFs use non-standard text encoding. Rare.

**Fix:** Failed documents stay in `embedding_status: "failed"` but remain searchable by keyword. Check the `embedding_error` field for details.

### Performance Issues

**Symptom:** Searches take >1 second

**Causes:**
- Large result set (1000+ chunks)
- Vector index not optimized yet
- Database connection issue

**Fixes:**
- Add filters (`project_id`, `customer`) to narrow results
- Increase `threshold` to 0.8+ to get fewer but higher-quality results
- Monitor pgvector index size; vacuum if needed

## Architecture Details

### Data Flow

```
Document Upload
  ↓
  Stored (immediately, status="queued")
  ↓
  APScheduler checks every 30s
  ↓
  Extract Text (PDF → string)
  ↓
  Semantic Chunking (string → chunks, ~800 tokens each)
  ↓
  OpenAI Embeddings (chunks → vectors via API)
  ↓
  Store in document_embeddings table
  ↓
  Update Document (status="completed")
  ↓
  Semantic Search available
```

### Database Tables

**documents** (existing, enhanced)
- `embedding_status` — Pipeline status
- `embedding_model` — Which model was used
- `token_count` — Total tokens in all chunks
- `embedding_cost` — USD cost to generate embeddings
- `embedded_at` — Completion timestamp

**document_embeddings** (new)
- `document_id` — Which document this chunk belongs to
- `chunk_index` — Chunk position (0, 1, 2, ...)
- `chunk_text` — Raw text of this chunk
- `embedding` — Vector (1536-dim for text-embedding-3-small)
- `token_count` — Tokens in this chunk
- `metadata` — Page number, section, etc.

**embedding_operations** (new, audit trail)
- Tracks every operation: extraction, chunking, embedding
- Logs errors, duration, and costs
- Used for debugging and monitoring

### Technology Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Embeddings | OpenAI text-embedding-3-small | Cost-effective, high-quality |
| Vector DB | pgvector | No new infrastructure |
| Job Queue | APScheduler | Simple, single-instance |
| Text Extraction | PyPDF | Pure Python, no deps |
| Chunking | Semantic (sentence-aware) | Preserves context |
| Retry Logic | tenacity | Robust, configurable |

## Next Steps (Phase 2)

Phase 2 (coming next) will add:
- ✅ Semantic search UI integration
- ✅ Embedding status indicators in documents page
- ✅ Hybrid search (vector + keyword fallback)
- ✅ Search result highlighting

Phase 3 (future) will add:
- ✅ RAG engine (LLM integration)
- ✅ AI agents for project analysis
- ✅ Risk assessment and recommendations
- ✅ Auto-generated summaries

## Support

If you run into issues:

1. Check the logs: `LOG_LEVEL=DEBUG uvicorn app.main:app` for verbose output
2. Run the setup again: `python -m app.init_ai`
3. Verify OpenAI API: Check your API key and quota at https://platform.openai.com/account/api-keys
4. Check database: Ensure pgvector tables were created: `\dt` in psql

---

**Phase 1 Status:** ✅ Complete and ready for testing

**Next:** Phase 2 (Semantic Search UI) — estimated 1 week

For questions or issues, refer to `docs/02_Architecture.md` for the full technical design.
