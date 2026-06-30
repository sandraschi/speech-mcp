import logging
from pathlib import Path

from .rag_core import BaseVectorStore

logger = logging.getLogger(__name__)


class DocumentStore(BaseVectorStore):
    """Specialized store for Speech-MCP documentation and semantic memory."""

    def __init__(self, db_path: Path):
        super().__init__(
            db_path=str(db_path),
            embedding_model_name="BAAI/bge-small-en-v1.5",
            table_name="speech_docs",
        )

    def list_sources(self) -> list[str]:
        """List distinct sources indexed."""
        if self.table_name not in self.db.list_tables():
            return []

        tbl = self.db.open_table(self.table_name)
        # Using a set comprehension on the arrow data for distinct sources
        return list({r["metadata"].get("filename", "unknown") for r in tbl.to_arrow().to_pylist() if "metadata" in r})
