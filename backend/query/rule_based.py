from backend.query.base import QueryRewriter
from backend.query.synonyms import SYNONYMS


class RuleBasedRewriter(QueryRewriter):
    """
    Expands abbreviations using a synonym dictionary.
    """

    def rewrite(
        self,
        query: str,
        recent_turns=None,
        summary: str = ""
    ) -> str:

        words = query.split()

        expanded = []

        for word in words:

            expanded.append(word)

            key = word.lower()

            if key in SYNONYMS:

                expanded.append(SYNONYMS[key])

        return " ".join(expanded)