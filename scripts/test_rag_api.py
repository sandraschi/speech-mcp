import os
import requests

BASE_URL = os.getenv("SPEECH_MCP_BACKEND_URL", "http://localhost:10918") + "/api/v1"


def test_rag_api():
    print("--- Testing RAG Stats ---")
    try:
        res = requests.get(f"{BASE_URL}/stats")
        print(f"Stats: {res.json()}")
    except Exception as e:
        print(f"Stats failed: {e}")

    print("\n--- Testing RAG Search ---")
    try:
        res = requests.get(f"{BASE_URL}/search", params={"q": "WaveNet history"})
        results = res.json()
        print(f"Search results found: {len(results)}")
        if results:
            print(f"Top result: {results[0]['content'][:100]}...")
    except Exception as e:
        print(f"Search failed: {e}")


if __name__ == "__main__":
    test_rag_api()
