"""
Reindex all docs in docs/ into LanceDB.
Run from repo root: python scripts/reindex_docs.py
"""
import logging
from pathlib import Path
import sys

# Make sure src is on path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from speech_mcp.rag.vector_store import DocumentStore

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def ingest_docs():
    db_path = repo_root / "data" / "lancedb"
    db_path.mkdir(parents=True, exist_ok=True)
    store = DocumentStore(db_path)

    docs_dir = repo_root / "docs"
    if not docs_dir.exists():
        logger.error(f"docs/ not found at {docs_dir}")
        return

    documents = []
    md_files = list(docs_dir.glob("*.md"))
    for file_path in md_files:
        content = file_path.read_text(encoding="utf-8")
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 40]
        for i, para in enumerate(paragraphs):
            documents.append({
                "id": f"{file_path.name}_{i}",
                "content": para,
                "metadata": {"filename": file_path.name, "chunk": i},
            })

    if documents:
        store.add_documents(documents, overwrite=True)
        print(f"Ingested {len(documents)} chunks from {len(md_files)} files.")
    else:
        print("No documents found.")


if __name__ == "__main__":
    ingest_docs()
