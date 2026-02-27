# RAG Implementation Details: Speech-MCP Semantic Memory

## 🏗️ Architecture Overview
The Speech-MCP RAG system is designed for **low-latency, local-first intelligence** on the RTX 4090 substrate.

### 1. Vector Engine: LanceDB
- **Why**: LanceDB is a serverless, persistent vector database that allows for disk-based querying without a heavy background daemon. It integrates natively with Python and is optimized for the SOTA data-scale.
- **Persistence**: Data resides in `data/lancedb` in a columnar format.

### 2. Embedding Model: FastEmbed
- **Model**: `BAAI/bge-small-en-v1.5` (quantized).
- **Why**: FastEmbed provides high-utility embeddings with near-zero overhead on CPU, ensuring that searches don't bottleneck the GPU processes (RTX 4090).
- **Latency**: Sub-10ms for typical documentation queries.

### 3. Chunking Strategy
- **Logic**: Handled in `rag_core.py`.
- **Method**: Fixed-size chunking with overlap to preserve semantic context across boundaries.
- **Size**: Default ~512 tokens per chunk.

## 🔄 Lifecycle: How & When
The RAG process follows a two-stage lifecycle:

### A. Ingestion (Triggered manually/CI)
- **Script**: `scripts/reindex_docs.py`
- **When**: Run whenever documentation in `data/docs/` changes.
- **Process**:
    1. Scan markdown files.
    2. Extract metadata (filename, headers).
    3. Generate embeddings for each chunk.
    4. Upsert into the `documents` table in LanceDB.

### B. Retrieval (Triggered by user/agent)
- **When**: Whenever a `search_docs` or `ask_docs` tool is called, or via the Semantic Memory UI.
- **Process**:
    1. User query is embedded in real-time.
    2. Vector similarity search (Cosine distance) is performed against the local index.
    3. Results are returned with a 0-1 relevance score.
    4. `ask_docs` synthesizes these results into a natural language answer.

---

## 🛠️ Performance Metrics (Local RTX 4090)
- **Indexing**: ~100 docs per second.
- **Search Latency**: <5ms.
- **RAM Overhead**: ~150MB for the FastEmbed runtime.
