import asyncio
import logging
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from speech_mcp.rag.vector_store import DocumentStore

from prometheus_client import Counter, Histogram

# DocumentStore is imported lazily inside get_store() to avoid slow
# lancedb/fastembed/onnxruntime imports at module load time (Claude Desktop timeout).

# Global State Container
# Following advanced materialist pattern: Data constitutes the only objective reality.
_store: Any | None = None
_timers: dict[str, asyncio.Task] = {}
_alarms: list[dict] = []
_history: deque[dict] = deque(maxlen=200)  # Forensic interaction history

# System Log Buffer (Circular, 1000 items)
_log_buffer: deque[dict] = deque(maxlen=1000)
_log_listeners: list[asyncio.Queue] = []

# Prometheus Metrics
M_REQUESTS = Counter("substrate_requests_total", "Total substrate requests", ["method", "endpoint"])
M_LATENCY = Histogram("substrate_request_latency_seconds", "Request latency in seconds", ["endpoint"])
M_ERRORS = Counter("substrate_errors_total", "Total substrate errors", ["type", "context"])
M_TOKENS = Counter("substrate_tokens_processed_total", "Total tokens processed", ["provider"])


def get_store():
    """Lazy-initialization for DocumentStore. Auto-ingests docs/ if empty."""
    global _store
    if _store is None:
        from speech_mcp.rag.vector_store import DocumentStore  # lazy: avoids startup timeout

        # Always use absolute path relative to package root
        repo_root = Path(__file__).parent.parent.parent  # src/speech_mcp -> repo root
        db_path = repo_root / "data" / "lancedb"
        db_path.mkdir(parents=True, exist_ok=True)
        _store = DocumentStore(db_path)
        # Auto-ingest docs/ if table is empty
        if _store.count_rows() == 0:
            docs_dir = repo_root / "docs"
            if docs_dir.exists():
                import threading

                threading.Thread(target=_ingest_docs, args=(_store, docs_dir), daemon=True).start()
    return _store


def _ingest_docs(store: "DocumentStore", docs_dir: Path):
    """Background ingest of all .md files in docs/."""
    import logging as _logging

    log = _logging.getLogger(__name__)
    log.info(f"Auto-ingesting docs from {docs_dir}...")
    documents = []
    for file_path in docs_dir.glob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
            for i, para in enumerate(paragraphs):
                documents.append(
                    {
                        "id": f"{file_path.name}_{i}",
                        "content": para,
                        "metadata": {"filename": file_path.name, "chunk": i},
                    }
                )
        except Exception as e:
            log.warning(f"Failed to read {file_path.name}: {e}")
    if documents:
        store.add_documents(documents, overwrite=True)
        log.info(f"Auto-ingested {len(documents)} chunks from {len(list(docs_dir.glob('*.md')))} docs")
    else:
        log.warning("No documents found to ingest")


async def run_timer(timer_id: str, seconds: int, label: str):
    """Internal helper to manage timer lifecycle."""
    try:
        await asyncio.sleep(seconds)
        # Log expiration to substrate logs
        add_log("INFO", "TIMER", f"Timer expired: {label}")
        from speech_mcp.voice_bus import speak_reply

        speak_reply(f"Timer done. {label}" if label and label != "Default" else "Timer done.")
        _timers.pop(timer_id, None)
    except asyncio.CancelledError:
        pass


def add_log(level: str, context: str, msg: str):
    """Add a log entry to the circular buffer and notify listeners."""
    context = context.upper()
    entry = {
        "id": datetime.now().timestamp(),
        "time": datetime.now().strftime("%H:%M:%S"),
        "level": level.upper(),
        "context": context,
        "msg": msg,
    }
    _log_buffer.append(entry)
    for q in _log_listeners:
        q.put_nowait(entry)


def add_history(type: str, content: str, provider: str, status: str = "success"):
    """Record an interaction in the forensic trace."""
    entry = {
        "id": str(datetime.now().timestamp()),
        "type": type,
        "content": content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": status,
        "provider": provider,
    }
    _history.appendleft(entry)
    add_log("SUCCESS", "HISTORY", f"Archived {type} event: {content[:30]}...")


class SubstrateLogHandler(logging.Handler):
    """Bridge for standard logging to our system log buffer."""

    def emit(self, record: logging.LogRecord):
        # Extract context from logger name
        ctx = record.name.split(".")[-1]
        add_log(record.levelname, ctx, record.getMessage())


def get_log_handler() -> logging.Handler:
    """Get the singleton log handler for the substrate."""
    handler = SubstrateLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler
