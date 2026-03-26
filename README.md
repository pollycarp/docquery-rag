# Document Q&A Assistant with RAG & Citation

A production-ready Retrieval-Augmented Generation (RAG) system that lets you upload documents (PDF, DOCX, TXT) and ask natural language questions. Every answer includes verifiable citations pointing back to the source document and page.

---

## What it does

- **Ingest** documents — PDF, DOCX, and TXT files are chunked, embedded, and stored in a vector database
- **Answer questions** — semantic search finds the most relevant chunks, a local LLM generates a cited answer
- **Cite sources** — every answer references the exact document and section it came from
- **Track usage** — latency, query logs, and embedding versions are recorded automatically
- **Evaluate quality** — built-in evaluation pipeline measures Hit Rate, MRR, and Exact Match

---

## Architecture

```
User (UI / API)
      │
      ▼
 FastAPI Backend
      │
      ├── POST /api/ingest     → Load → Chunk → Embed → Store
      ├── POST /api/query      → Embed query → Vector search → LLM → Answer
      ├── GET  /api/documents  → List ingested documents
      ├── GET  /api/stats      → Usage statistics
      └── GET  /metrics        → Prometheus metrics
      │
      ├── sentence-transformers (local embeddings, no API key needed)
      ├── Ollama / llama3.2    (local LLM, runs on your machine)
      └── PostgreSQL + pgvector (vector database, runs in Docker)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| LLM | Ollama (`llama3.2`) — runs locally |
| Vector DB | PostgreSQL 16 + pgvector |
| ORM | SQLAlchemy 2 |
| Evaluation | Custom metrics + MLflow |
| Monitoring | Prometheus (via prometheus-fastapi-instrumentator) |
| Testing | pytest |
| Container | Docker + Docker Compose |

---

## Prerequisites

Before running this project, install the following:

| Tool | Version | Download |
|---|---|---|
| Python | 3.11 | https://python.org/downloads |
| Docker Desktop | Latest | https://docs.docker.com/desktop/install/windows-install |
| Ollama | Latest | https://ollama.com/download |

---

## Setup

### 1. Clone or download the project

```bash
cd C:\Users\user\Documents\rag
```

### 2. Create and activate a Python 3.11 virtual environment

```bash
py -3.11 -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file

```bash
copy .env.example .env
```

Open `.env` and set your API key:

```env
POSTGRES_PORT=5433
API_KEY=dev-secret-key
```

### 5. Start the database

```bash
docker-compose up -d
```

### 6. Download the LLM model (one-time, ~2GB)

```bash
# If ollama is in your PATH:
ollama pull llama3.2

# If not in PATH (Windows):
& "C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe" pull llama3.2
```

### 7. Start the API server

```bash
uvicorn app.main:app --reload
```

API is now running at: `http://127.0.0.1:8000`

### 8. Start the UI (new terminal)

```bash
venv\Scripts\activate
streamlit run ui/app.py
```

UI is now running at: `http://localhost:8501`

---

## Using the Application

### Via the UI

1. Open `http://localhost:8501` in your browser
2. Go to the **Documents** tab → upload a PDF, DOCX, or TXT file
3. Go to the **Ask** tab → type your question
4. View the answer with citations and source chunks
5. Check the **Stats** tab for usage metrics

### Via the API

All endpoints (except `/health` and `/metrics`) require the header:
```
X-API-Key: dev-secret-key
```

**Ingest a document:**
```bash
curl -X POST http://127.0.0.1:8000/api/ingest \
  -H "X-API-Key: dev-secret-key" \
  -F "file=@sample_docs/sample_policy.txt"
```

**Ask a question:**
```bash
curl -X POST http://127.0.0.1:8000/api/query \
  -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of sick leave am I entitled to?", "top_k": 5}'
```

**List documents:**
```bash
curl -H "X-API-Key: dev-secret-key" http://127.0.0.1:8000/api/documents
```

**Delete a document:**
```bash
curl -X DELETE http://127.0.0.1:8000/api/documents/1 \
  -H "X-API-Key: dev-secret-key"
```

**View stats:**
```bash
curl -H "X-API-Key: dev-secret-key" http://127.0.0.1:8000/api/stats
```

**Interactive API docs:** `http://127.0.0.1:8000/docs`

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Expected output: **37 tests passing**

---

## Evaluation

Run the evaluation pipeline against the golden dataset:

```bash
# With MLflow tracking
python evaluation/run_evaluation.py

# Without MLflow (console output only)
python evaluation/run_evaluation.py --no-mlflow

# Custom top-k
python evaluation/run_evaluation.py --top-k 3
```

View results in MLflow:
```bash
mlflow ui
# Open http://127.0.0.1:5000
```

### Baseline scores (llama3.2 + all-MiniLM-L6-v2)

| Metric | Score |
|---|---|
| Hit Rate @5 | 88% |
| MRR | 0.79 |
| Exact Match | 88% |
| Citation Rate | 100% |

---

## Re-ingestion (after embedding model upgrade)

If you change the embedding model, re-embed all existing documents:

```bash
python scripts/reingest_all.py --docs-folder sample_docs/
```

Dry run (preview only):
```bash
python scripts/reingest_all.py --docs-folder sample_docs/ --dry-run
```

---

## Project Structure

```
rag/
├── app/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # All settings (reads from .env)
│   ├── database.py              # DB connection + table setup
│   ├── logging_config.py        # Structured JSON logging
│   ├── middleware.py            # Request timing + logging
│   ├── models/
│   │   ├── document.py          # Document + Chunk DB models
│   │   └── query_log.py         # QueryLog DB model
│   ├── services/
│   │   ├── loader.py            # PDF / DOCX / TXT file reader
│   │   ├── chunker.py           # Recursive text splitter
│   │   ├── embedder.py          # sentence-transformers embeddings
│   │   ├── retriever.py         # Vector similarity search
│   │   ├── llm.py               # Ollama LLM integration
│   │   └── qa.py                # Full RAG pipeline
│   └── api/
│       ├── dependencies.py      # API key auth
│       └── routes/
│           ├── ingest.py        # Ingestion endpoints
│           ├── query.py         # Q&A endpoint
│           └── stats.py         # Stats endpoint
├── ui/
│   ├── app.py                   # Streamlit UI
│   └── api_client.py            # HTTP client for the API
├── evaluation/
│   ├── golden_dataset.json      # Ground truth Q&A pairs
│   ├── metrics.py               # Hit Rate, MRR, Exact Match
│   ├── evaluator.py             # Evaluation runner
│   └── run_evaluation.py        # CLI entry point + MLflow logging
├── scripts/
│   ├── ingest_documents.py      # CLI document ingestion tool
│   └── reingest_all.py          # Re-embed after model upgrade
├── tests/
│   ├── test_api.py              # Auth + endpoint tests
│   ├── test_ingestion.py        # Loader + chunker tests
│   ├── test_metrics.py          # Evaluation metric tests
│   ├── test_observability.py    # Middleware + stats tests
│   └── test_retriever.py        # Retriever tests
├── sample_docs/
│   └── sample_policy.txt        # Sample document for testing
├── docker-compose.yml           # PostgreSQL + pgvector
├── requirements.txt
├── .env.example                 # Environment variable template
└── .gitignore
```

---

## Monitoring

- **Prometheus metrics:** `http://127.0.0.1:8000/metrics`
- **API docs (Swagger):** `http://127.0.0.1:8000/docs`
- **MLflow UI:** run `mlflow ui` → open `http://127.0.0.1:5000`

---

## Configuration

All settings are in `.env`. Key options:

| Variable | Default | Description |
|---|---|---|
| `API_KEY` | `dev-secret-key` | Change this in production |
| `POSTGRES_PORT` | `5433` | DB port (5433 avoids conflicts) |
| `OLLAMA_MODEL` | `llama3.2` | LLM model name |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `CHUNK_SIZE` | `512` | Max characters per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `5` | Chunks retrieved per query |
