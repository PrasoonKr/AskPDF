import urllib.parse
import urllib.request
import json
import re
from typing import List, Dict, Any

class WebSearchService:
    """
    Handles queries routed to outside knowledge or real-time web search.
    Uses wttr.in for weather and Wikipedia for general knowledge (reliable on AWS EC2).
    """

    def search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        results = []
        
        # 1. Weather Fallback
        if "weather" in query.lower():
            location = "Delhi" # default
            # Extract location roughly
            match = re.search(r"in\s+([a-zA-Z\s]+)", query, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                
            try:
                req = urllib.request.Request(f"https://wttr.in/{urllib.parse.quote(location)}?format=j1", headers={"User-Agent": "curl/7.68.0"})
                with urllib.request.urlopen(req, timeout=4) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    current = data["current_condition"][0]
                    temp = current["temp_C"]
                    desc = current["weatherDesc"][0]["value"]
                    results.append({
                        "title": f"Current Weather in {location.title()}",
                        "text": f"The current weather in {location.title()} is {temp}°C and {desc}.",
                        "url": f"https://wttr.in/{urllib.parse.quote(location)}",
                        "source": "Weather API",
                    })
                    return results
            except Exception as e:
                pass
                
        # 2. Wikipedia API for general knowledge
        try:
            # Extract main noun phrase for wikipedia
            search_term = query.lower().replace("what is", "").replace("who is", "").replace("tell me about", "").strip(' ?.')
            encoded = urllib.parse.quote(search_term)
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}&utf8=&format=json"
            
            req = urllib.request.Request(url, headers={"User-Agent": "AskPDF-AdaptiveRAG/1.0"})
            with urllib.request.urlopen(req, timeout=4) as response:
                data = json.loads(response.read().decode("utf-8"))
                for item in data["query"]["search"][:max_results]:
                    # clean html tags from snippet
                    snippet = re.sub(r'<[^>]+>', '', item["snippet"])
                    results.append({
                        "title": item["title"],
                        "text": snippet,
                        "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(item['title'])}",
                        "source": "Wikipedia",
                    })
        except Exception as e:
            print(f"Wikipedia search error: {e}")

        # Fallback if both fail
        if not results:
            encoded = urllib.parse.quote_plus(query)
            results.append({
                "title": f"External Information: {query}",
                "text": f"Outside knowledge lookup for '{query}'. This query was identified as outside the scope of local uploaded documents.",
                "url": f"https://duckduckgo.com/?q={encoded}",
                "source": "External Knowledge",
            })

        return results[:max_results]
