import sys

sys.path.insert(0, 'src')
from speech_mcp.state import get_store

def run():
    print("Performing semantic search over RAG store...")
    query = 'expressive speech synthesis Hume Octave'
    results = get_store().search(query, limit=3)
    
    print(f"\nResults for: '{query}'")
    print("-" * 60)
    for r in results:
        filename = r['metadata'].get('filename', 'unknown')
        score = max(0, 1 - r.get("_distance", 0))
        content = r['content'][:120].replace('\n', ' ')
        print(f"[{filename}] score={score:.2f} | {content}...")

if __name__ == "__main__":
    run()
