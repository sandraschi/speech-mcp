import asyncio
from pathlib import Path

from speech_mcp.rag.vector_store import DocumentStore

# Global State Container
# Following SOTA materialist pattern: Data constitutes the only objective reality.
_store: DocumentStore | None = None
_timers: dict[str, asyncio.Task] = {}
_alarms: list[dict] = []


def get_store() -> DocumentStore:
    """Lazy-initialization for DocumentStore."""
    global _store
    if _store is None:
        db_path = Path("data/lancedb")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _store = DocumentStore(db_path)
    return _store


async def run_timer(timer_id: str, seconds: int, label: str):
    """Internal helper to manage timer lifecycle."""
    try:
        await asyncio.sleep(seconds)
        # Log expiration to stdout for capture
        print(f"TIMER EXPIRED: {label}")
        if timer_id in _timers:
            del _timers[timer_id]
    except asyncio.CancelledError:
        pass
