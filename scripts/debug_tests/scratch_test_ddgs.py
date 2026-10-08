import sys
from duckduckgo_search import DDGS
import json

def test():
    query = "what's the weather today in delhi?"
    print(f"Querying: {query}")
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3, backend="lite"))
            print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
