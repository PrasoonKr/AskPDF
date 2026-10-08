import re
import json
from typing import List, Optional
from backend.adaptive.models import RouteType, RouteDecision


class AdaptiveRouter:
    """
    Query Analyzer and Adaptive Router.
    Routes queries to:
    - simple_rag: Direct, single-concept document questions
    - multi_query_rag: Complex, multi-hop, or comparative questions requiring multi-perspective retrieval
    - web_search: Real-time, outside knowledge, or queries unrelated to the ingested documents
    """

    WEB_SEARCH_INDICATORS = [
        r"\b(today|yesterday|tomorrow|current|latest|recent news|weather|stock price|election|who is the president)\b",
        r"\b(live score|cricket match|olympics|fifa|world cup|movie release|bitcoin price)\b",
        r"\b(outside knowledge|search the web|google it|internet)\b",
    ]

    GREETING_INDICATORS = [
        r"^(hi|hello|hey|how are you|good morning|good evening|good afternoon|what'?s up|sup|greetings)\b",
    ]

    COMPLEX_INDICATORS = [
        r"\b(compare|comparison|versus|vs\.?|difference between|pros and cons|trade-offs)\b",
        r"\b(and how does (it|that) (affect|impact|influence|relate))\b",
        r"\b(step by step|end to end|architecture overview|how do .* and .* work together)\b",
    ]

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    def route(self, query: str) -> RouteDecision:
        cleaned_query = query.strip()

        # 0. Fast Pattern Check for Greetings
        for pattern in self.GREETING_INDICATORS:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                return RouteDecision(
                    route=RouteType.GREETING,
                    confidence=0.99,
                    reasoning=f"Query matched simple greeting.",
                    sub_queries=[cleaned_query],
                )

        # 1. Fast Pattern Check for Outside Knowledge / Web Search
        for pattern in self.WEB_SEARCH_INDICATORS:
            if re.search(pattern, cleaned_query, re.IGNORECASE):
                return RouteDecision(
                    route=RouteType.WEB_SEARCH,
                    confidence=0.95,
                    reasoning=f"Query matched real-time / outside-world indicator: '{pattern}'",
                    sub_queries=[cleaned_query],
                )

        # 2. Check for Complex / Multi-faceted queries
        is_complex = False
        match_reason = ""
        for pattern in self.COMPLEX_INDICATORS:
            m = re.search(pattern, cleaned_query, re.IGNORECASE)
            if m:
                is_complex = True
                match_reason = f"Query contains comparative or multi-faceted construct: '{m.group(0)}'"
                break

        # Check for multiple conjunction clauses
        if not is_complex and (" and " in cleaned_query.lower() and len(cleaned_query.split()) > 10):
            is_complex = True
            match_reason = "Query contains multi-clause conjunctions spanning multiple topics"

        if is_complex:
            sub_queries = self._generate_sub_queries(cleaned_query)
            return RouteDecision(
                route=RouteType.MULTI_QUERY_RAG,
                confidence=0.88,
                reasoning=match_reason,
                sub_queries=sub_queries,
            )

        # 3. Default to Simple Focused RAG
        return RouteDecision(
            route=RouteType.SIMPLE_RAG,
            confidence=0.92,
            reasoning="Focused, single-concept query suitable for single-pass hybrid retrieval.",
            sub_queries=[cleaned_query],
        )

    def _generate_sub_queries(self, query: str) -> List[str]:
        """
        Decomposes complex queries into 2-3 focused sub-queries.
        Prioritizes fast rule-based decomposition (0.1ms) and only uses LLM
        for unstructured edge cases.
        """
        # 1. Fast deterministic decomposition
        diff_match = re.search(r"difference between (.*?) and (.*)", query, re.IGNORECASE)
        if diff_match:
            return [
                f"What is {diff_match.group(1).strip()}?",
                f"What is {diff_match.group(2).strip()}?",
                query.strip(),
            ]

        if " vs " in query.lower() or " versus " in query.lower():
            parts = re.split(r"\s+(?:vs\.?|versus)\s+", query, flags=re.IGNORECASE)
            if len(parts) >= 2:
                return [
                    f"What is {parts[0].strip()}?",
                    f"What is {parts[1].strip()}?",
                    query.strip(),
                ]

        if " and " in query.lower():
            # e.g. "what is a thread and process"
            match = re.match(r"(?:what\s+is\s+(?:a\s+|an\s+)?|explain\s+)?(.*?)\s+and\s+(.*)", query, re.IGNORECASE)
            if match:
                term1, term2 = match.group(1).strip(), match.group(2).strip()
                if term1 and term2:
                    return [
                        f"What is {term1}?",
                        f"What is {term2}?",
                        f"{term1} versus {term2} comparison",
                    ]

        # 2. LLM Fallback for unstructured complex queries
        if self.llm_service:
            try:
                prompt = (
                    "Decompose this complex query into 2 or 3 distinct, concise search sub-queries "
                    "for document retrieval. Return ONLY a JSON array of strings.\n\n"
                    f"Complex Query: {query}\n\n"
                    "Output JSON array:"
                )
                resp = self.llm_service.generate(prompt).strip()
                start = resp.find("[")
                end = resp.rfind("]")
                if start != -1 and end != -1:
                    subs = json.loads(resp[start : end + 1])
                    if isinstance(subs, list) and len(subs) >= 2:
                        return [str(s).strip() for s in subs[:3]]
            except Exception:
                pass

        return [query]
