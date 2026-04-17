import logging
from pathlib import Path
from typing import Any

import lancedb
from fastembed import TextEmbedding

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
        self.embedding_model = TextEmbedding(model_name=embedding_model_name)
        self.table_name = table_name

    def add_documents(self, documents: list[dict[str, Any]], overwrite: bool = True):
        """
        Embed and index documents.
        documents: List of dicts with 'content' and 'metadata'.
        """
        if not documents:
            return

        logger.info(f"Embedding {len(documents)} items into '{self.table_name}'...")

        contents = [doc["content"] for doc in documents]
        embeddings = list(self.embedding_model.embed(contents))

        data = []
        for doc, emb in zip(documents, embeddings, strict=True):
            entry = {
                "id": doc.get("id"),
                "vector": emb.tolist(),
                "content": doc.get("content"),
                "metadata": doc.get("metadata", {}),
            }
            if "source" in doc:
                entry["source"] = doc["source"]
            data.append(entry)

        if overwrite or self.table_name not in self.db.list_tables():
            self.db.create_table(self.table_name, data=data, mode="overwrite")
        else:
            tbl = self.db.open_table(self.table_name)
            tbl.add(data)

        logger.info(f"Indexed {len(data)} items into LanceDB table '{self.table_name}'.")

    def search(self, query: str, limit: int = 5, where: str | None = None) -> list[dict[str, Any]]:
        """Semantic search with optional pre-filter."""
        if self.table_name not in self.db.list_tables():
            logger.warning(f"Table '{self.table_name}' not found.")
            return []

        tbl = self.db.open_table(self.table_name)
        query_embedding = next(iter(self.embedding_model.embed([query])))

        search_req = tbl.search(query_embedding).limit(limit)
        if where:
            search_req = search_req.where(where)

        return search_req.to_arrow().to_pylist()

    def count_rows(self) -> int:
        if self.table_name not in self.db.list_tables():
            return 0
        tbl = self.db.open_table(self.table_name)
        return tbl.count_rows()
