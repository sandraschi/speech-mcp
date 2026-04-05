import logging
from pathlib import Path

from speech_mcp.rag.vector_store import DocumentStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_docs():
    """Ingest curated documentation into LanceDB."""
    db_path = Path("data/lancedb")
    store = DocumentStore(db_path)

    docs_dir = Path("data/docs")
    if not docs_dir.exists():
        logger.error(f"Docs directory not found: {docs_dir}")
        return

    documents = []
    for file_path in docs_dir.glob("*.md"):
        content = file_path.read_text(encoding="utf-8")
        filename = file_path.name

        # Simple chunking by paragraph for now
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        for i, p in enumerate(paragraphs):
            documents.append(
                {
                    "id": f"{filename}_{i}",
                    "content": p,
                    "metadata": {"filename": filename, "chunk": i},
                }
            )

    if documents:
        store.add_documents(documents, overwrite=True)
        print(
            f"Successfully ingested {len(documents)} chunks from "
            f"{len(list(docs_dir.glob('*.md')))} files."
        )
    else:
        print("No documents found to ingest.")


if __name__ == "__main__":
    ingest_docs()
