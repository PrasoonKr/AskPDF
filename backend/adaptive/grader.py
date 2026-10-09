import json
import re
from typing import List, Any
from backend.adaptive.models import GradeResult


class RelevanceGrader:
    """
    Evaluates whether the retrieved context passages contain sufficient,
    relevant information to answer the user query.
    If irrelevant, extracts missing aspects/concepts to trigger targeted self-correction query rewriting.
    """

    STOPWORDS = {
        "what", "is", "the", "how", "do", "does", "in", "and", "or", "to", "of",
        "a", "an", "for", "with", "between", "versus", "vs", "explain", "describe",
        "tell", "me", "about", "can", "you", "which", "are", "by", "from", "on"
    }

    DISCLAIMER_PATTERNS = [
        r"\b(not (supported|used|applicable|discussed|covered|provided|available|relevant|included|implemented))\b",
        r"\b(does not support|do not support|will not (discuss|cover|be covered))\b",
        r"\b(outside the scope|intentionally skipped|omitted from|deprecated in|removed from|rejected|disabled|replaced by)\b",
        r"\b(strictly forbidden|completely absent|failed during|creation failed)\b",
        r"\b(only evaluates|ignored by|strictly (an? )?(introduction|overview))\b",
    ]

    def __init__(self, llm_service=None, score_threshold: float = 0.25):
        self.llm_service = llm_service
        self.score_threshold = score_threshold

    @staticmethod
    def _stem(word: str) -> str:
        w = word.lower().replace("z", "s")
        for suffix in ("ation", "ising", "izing", "ing", "ed", "es", "s"):
            if w.endswith(suffix) and len(w) > len(suffix) + 2:
                w = w[:-len(suffix)]
                break
        return w

    def grade(self, query: str, retrieved_docs: List[Any]) -> GradeResult:
        if not retrieved_docs:
            return GradeResult(
                is_relevant=False,
                confidence=1.0,
                reasoning="No candidate passages retrieved from the document store.",
                missing_aspects=[query],
                filtered_documents=[],
            )

        # 1. Fast Heuristic & Reranker Score Check
        top_score = getattr(retrieved_docs[0], "score", 0.0)
        query_keywords = [
            w.lower()
            for w in re.findall(r"\b[A-Za-z0-9_-]+\b", query)
            if w.lower() not in self.STOPWORDS and len(w) > 2
        ]
        stemmed_query_keywords = [self._stem(kw) for kw in query_keywords]

        # Combine text from top 3 chunks
        combined_text = " ".join([
            (getattr(d, "text", "") or getattr(getattr(d, "document", None), "text", ""))
            for d in retrieved_docs[:3]
        ]).lower().replace("z", "s")

        # Check for explicit disclaimer / negative context
        has_disclaimer = any(re.search(p, combined_text) for p in self.DISCLAIMER_PATTERNS)

        # Count how many query keywords appear in top retrieved passages (exact or stemmed)
        matched_keywords = [
            kw for kw, skw in zip(query_keywords, stemmed_query_keywords)
            if kw in combined_text or skw in combined_text
        ]
        keyword_overlap_ratio = len(matched_keywords) / max(len(query_keywords), 1)

        # 2. Fast Deterministic Heuristic Check
        # High confidence match A: Strong CrossEncoder reranker score (>= 0.20)
        if top_score >= 0.20 and not has_disclaimer:
            return GradeResult(
                is_relevant=True,
                confidence=0.95,
                reasoning=f"High semantic confidence match from Cross-Encoder (top_score={top_score:.3f}).",
                missing_aspects=[],
                filtered_documents=retrieved_docs,
            )

        # Fast rejection A: Explicit disclaimer / negation with low cross-encoder score (< 0.35)
        if has_disclaimer and top_score < 0.35:
            missing = [kw for kw in query_keywords if kw not in matched_keywords]
            return GradeResult(
                is_relevant=False,
                confidence=0.92,
                reasoning=f"Passage contains explicit disclaimer or out-of-scope negation (top_score={top_score:.3f}).",
                missing_aspects=missing if missing else [query],
                filtered_documents=[],
            )

        # Fast rejection B: Low score (< 0.10) or negligible keyword overlap (clear off-topic noise)
        if top_score < 0.10 or keyword_overlap_ratio < 0.20:
            missing = [kw for kw in query_keywords if kw not in matched_keywords]
            return GradeResult(
                is_relevant=False,
                confidence=0.95,
                reasoning=f"Irrelevant text (score={top_score:.3f} below threshold, keyword overlap={keyword_overlap_ratio*100:.0f}%).",
                missing_aspects=missing if missing else [query],
                filtered_documents=[],
            )

        # High confidence match B: Good keyword/stem overlap (>= 30%) with score above threshold and no disclaimer
        if keyword_overlap_ratio >= 0.30 and (top_score >= self.score_threshold or top_score == 0.0) and not has_disclaimer:
            return GradeResult(
                is_relevant=True,
                confidence=0.90,
                reasoning=f"High relevance match (top_score={top_score:.3f}, keyword overlap={keyword_overlap_ratio*100:.0f}%).",
                missing_aspects=[],
                filtered_documents=retrieved_docs,
            )

        # 3. Ambiguous zone: score between 0.10-0.20 with some keyword overlap
        # Use LLM to verify if available and fast enough (e.g. AWS Bedrock), otherwise fallback to heuristic
        if keyword_overlap_ratio >= 0.20 and top_score >= 0.10:
            if self.llm_service:
                import os
                if os.getenv("RAG_ENVIRONMENT", "local").lower() == "production":
                    prompt = (
                        f"You are a strict grading assistant.\n"
                        f"Evaluate if the following context contains ANY relevant information to answer the question.\n"
                        f"Question: {query}\n"
                        f"Context: {combined_text}\n"
                        f"Reply with exactly 'YES' if it is relevant, or 'NO' if it is completely irrelevant."
                    )
                    try:
                        llm_response = self.llm_service.generate(prompt).strip().upper()
                        if "YES" in llm_response:
                            return GradeResult(
                                is_relevant=True,
                                confidence=0.85,
                                reasoning="Borderline match verified as RELEVANT by LLM.",
                                missing_aspects=[],
                                filtered_documents=retrieved_docs,
                            )
                        elif "NO" in llm_response:
                            missing = [kw for kw in query_keywords if kw not in matched_keywords]
                            return GradeResult(
                                is_relevant=False,
                                confidence=0.85,
                                reasoning="Borderline match rejected as IRRELEVANT by LLM.",
                                missing_aspects=missing if missing else [query],
                                filtered_documents=[],
                            )
                    except Exception:
                        pass # Fallback to heuristic
            
            return GradeResult(
                is_relevant=True,
                confidence=0.75,
                reasoning=f"Borderline match accepted via heuristic (top_score={top_score:.3f}, keyword overlap={keyword_overlap_ratio*100:.0f}%).",
                missing_aspects=[],
                filtered_documents=retrieved_docs,
            )

        # Otherwise mark as irrelevant
        missing = [kw for kw in query_keywords if kw not in matched_keywords]
        return GradeResult(
            is_relevant=False,
            confidence=0.80,
            reasoning=f"Retrieved passages lack core query concepts. Missing: {missing}. Overlap: {keyword_overlap_ratio*100:.0f}%.",
            missing_aspects=missing,
            filtered_documents=[],
        )
