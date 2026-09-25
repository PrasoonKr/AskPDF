from backend.query.base import QueryRewriter


class LLMRewriter(QueryRewriter):
    """
    Uses an LLM to rewrite a query for better retrieval.
    """

    def __init__(self, llm_service, conversation_formatter):
        self.llm_service = llm_service
        self.conversation_formatter = conversation_formatter

    def rewrite(
        self,
        query: str,
        recent_turns=None,
        summary: str = "",
    ) -> str:

        if not recent_turns and not summary:
            return query

        formatted_history = (
            self.conversation_formatter.format(
                recent_turns
            )
        )

        prompt = (
            "Rewrite the current question into a "
            "standalone search query for document "
            "retrieval.\n\n"

            "Use conversation memory only when needed "
            "to resolve references (like 'it', 'they') or missing context.\n\n"

            "Rules:\n"
            "- Preserve the user's exact original meaning.\n"
            "- Do NOT add extra adjectives, assumptions, or new concepts (e.g., do not change 'latency' to 'low latency').\n"
            "- If the query is already clear and standalone (e.g., a single keyword or concept), output it exactly as is.\n"
            "- Resolve pronouns and conversational references.\n"
            "- Do not answer the question.\n"
            "- Return only the standalone search query.\n\n"

            f"Conversation Summary:\n"
            f"{summary or 'No conversation summary.'}\n\n"

            f"Recent Conversation:\n"
            f"{formatted_history}\n\n"

            f"Current Question:\n"
            f"{query}"
        )

        result = self.llm_service.generate(prompt).strip()
        
        import re
        result = re.sub(r'[-_]', ' ', result)
        result = result.strip('"\' ')
        
        return result