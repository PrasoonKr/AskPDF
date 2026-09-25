from backend.query.base import QueryRewriter


class HybridRewriter(QueryRewriter):
    """
    Combines rule-based expansion with LLM-based rewriting.
    """

    def __init__(
        self,
        rule_rewriter,
        llm_rewriter,
    ):
        self.rule_rewriter = rule_rewriter
        self.llm_rewriter = llm_rewriter

    def rewrite(
        self,
        query: str,
        recent_turns=None,
        summary: str = "",
    ) -> str:

        standalone_query = (
            self.llm_rewriter.rewrite(
                query=query,
                recent_turns=recent_turns,
                summary=summary
            )
        )

        expanded_query = (
            self.rule_rewriter.rewrite(
                standalone_query
            )
        )

        return expanded_query