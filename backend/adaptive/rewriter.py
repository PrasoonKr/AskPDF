from typing import List, Optional


class SelfCorrectingRewriter:
    """
    Reformulates queries when relevance grading fails.
    Uses missing concepts and critique to construct a more targeted search query.
    """

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

    def rewrite_failed_query(
        self,
        original_query: str,
        critique: str,
        missing_aspects: List[str],
        attempt_number: int = 1,
    ) -> str:
        """
        Produce a revised, highly specific search query for the next retrieval attempt.
        """
        # LLM rewriting disabled — costs ~6s per call on CPU, rule-based is sufficient
        # for retry query reformulation and runs in <1ms


        # Robust rule-based reformulation
        missing_str = " ".join(missing_aspects) if missing_aspects else ""
        if attempt_number == 1 and missing_str:
            # Emphasize the missing core terms along with the original subject
            return f"{original_query} {missing_str}".strip()
        else:
            # Simplify to core nouns and technical terms
            words = [w for w in original_query.split() if len(w) > 3 and not w.lower().startswith("what")]
            return f"{' '.join(words)} {missing_str}".strip()
