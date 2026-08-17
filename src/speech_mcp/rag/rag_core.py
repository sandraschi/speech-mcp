import logging
from pathlib import Path
from typing import Any

import lancedb

from speech_mcp.rag.fastembed_gpu import create_text_embedding, repo_root_from_here

logger = logging.getLogger(__name__)


class BaseVectorStore:
    """Manages document embeddings and retrieval using LanceDB and FastEmbed."""

    def __init__(
        self,
        db_path: str,
        embedding_model_name: str = "BAAI/bge-small-en-v1.5",
        table_name: str = "documents",
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(self.db_path))
        cache_dir = str(self.db_path / "cache")
        self.embedding_model, self.embed_device, self.embed_batch_size = create_text_embedding(
            embedding_model_name,
            cache_dir,
            repo_root=repo_root_from_here(),
        )
        self.table_name = table_name

    def add_documents(self, documents: list[dict[str, Any]], overwrite: bool = True):
        """
        Embed and index documents.
        documents: List of dicts with 'content' and 'metadata'.
        """
        if not documents:
            return

        logger.info("Embedding %s items into '%s'...", len(documents), self.table_name)

        contents = [doc["content"] for doc in documents]
        all_embeddings: list[Any] = []
        batch = self.embed_batch_size
        for start in range(0, len(contents), batch):
            chunk = contents[start : start + batch]
            all_embeddings.extend(list(self.embedding_model.embed(chunk)))

        data = []
        for doc, emb in zip(documents, all_embeddings, strict=True):
            entry = {
                "id": doc.get("id"),
                "vector": emb.tolist(),
                "content": doc.get("content"),
                "metadata": doc.get("metadata", {}),
            }
            if "source" in doc:
                entry["source"] = doc["source"]
            data.append(entry)

        if overwrite or self.table_name not in list(self.db.list_tables()):
            self.db.create_table(self.table_name, data=data, mode="overwrite")
        else:
            tbl = self.db.open_table(self.table_name)
            tbl.add(data)

        logger.info("Indexed %s items into LanceDB table '%s'.", len(data), self.table_name)

    def search(self, query: str, limit: int = 5, where: str | None = None) -> list[dict[str, Any]]:
        """Semantic search with optional pre-filter."""
        tables = list(self.db.list_tables())
        if self.table_name not in tables:
            logger.warning("Table '%s' not found.", self.table_name)
            return []

        tbl = self.db.open_table(self.table_name)
        query_embedding = next(iter(self.embedding_model.embed([query])))

        search_req = tbl.search(query_embedding).limit(limit)
        if where:
            search_req = search_req.where(where)

        return search_req.to_arrow().to_pylist()

    def count_rows(self) -> int:
        tables = list(self.db.list_tables())
        if self.table_name not in tables:
            return 0
        tbl = self.db.open_table(self.table_name)
        return tbl.count_rows()
