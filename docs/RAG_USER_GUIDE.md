# Speech-MCP RAG: User Guide

The semantic search (RAG) system in speech-mcp lets you query a local knowledge base using natural language. It runs entirely on your machine — no cloud calls, no latency beyond the local RTX 4090.

## What it is

Speech-MCP ships with a curated knowledge base of speech AI documentation: TTS provider guides, expressive synthesis research, turn-taking theory, voice cloning techniques, and more. The RAG layer makes this searchable via two MCP tools and a web UI.

**Two tools, two use cases:**

- **`search_docs`** — fast retrieval, returns ranked document chunks. Good for "find me the relevant bits."
- **`ask_docs`** — retrieval + synthesis. Finds the relevant chunks, then uses Claude's reasoning to compose a grounded answer. Good for "explain this to me."

## Using it from Claude Desktop

```
search_docs("how does Hume EVI handle turn-taking?")
```

Returns up to 5 ranked document chunks with relevance scores (0–1). Useful when you want raw source material to read yourself.

```
ask_docs("What's the difference between Hume Octave and EVI, and when should I use each?")
```

Returns a synthesized answer citing the actual documents used. The answer is grounded — if the knowledge base doesn't cover it, the tool says so rather than hallucinating.

## Using it from the Webapp

Open `http://localhost:10908` and navigate to **Semantic Memory**. The search bar queries the same LanceDB index in real time. Results show filename, relevance score, and a content preview.

The REST endpoint is also directly accessible:

```
GET http://localhost:10909/api/v1/search?q=expressive+synthesis
```

## What's in the knowledge base

The index is built from markdown files in `docs/`. Current coverage includes:

- Hume AI EVI v2/v3 and Octave TTS documentation
- ElevenLabs voice cloning and multilingual synthesis
- Academic overviews: turn-taking, prosody, voice activity projection
- Speech-MCP architecture and tool reference docs
- Chinese AI speech research (2025–2026 landscape)

## Adding your own documents

Drop any markdown file into `docs/` and run the reindexing script:

```powershell
cd D:\Dev\repos\speech-mcp
uv run scripts/reindex_docs.py
```

The script scans the folder, chunks documents into ~512-token segments with overlap, generates embeddings using the local `BAAI/bge-small-en-v1.5` model (runs on CPU, ~150MB RAM), and upserts into LanceDB. Existing entries for unchanged files are not duplicated.

Good candidates to add: your own voice project notes, custom TTS workflow docs, persona sheets for bots or avatars.

## Technical details (brief)

| Component | Detail |
|---|---|
| Vector store | LanceDB (embedded, no server process) |
| Embedding model | BAAI/bge-small-en-v1.5 via FastEmbed (384 dimensions) |
| Similarity metric | Cosine distance |
| Index persistence | `data/lancedb/speech_docs.lance` |
| Search latency | <5ms on local hardware |
| `ask_docs` synthesis | FastMCP `ctx.sample()` → Claude |

The index survives server restarts. No re-indexing needed unless `docs/` content changes.

## Limitations

- English-primary: the embedding model is optimized for English. Non-English documents will index and return results but quality degrades.
- `ask_docs` requires a connected MCP client (Claude Desktop) since it uses `ctx.sample()` for synthesis. `search_docs` works standalone.
- The index is local — not shared across machines. If you run speech-mcp on another host, re-index there.
