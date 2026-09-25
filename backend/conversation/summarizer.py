class ConversationSummarizer:
    """
    Summarizes older conversation turns
    into compact long-term memory.
    """

    def __init__(
        self,
        llm_service,
        conversation_formatter,
    ):
        self.llm_service = llm_service
        self.conversation_formatter = (
            conversation_formatter
        )

    def summarize(
        self,
        turns,
        previous_summary: str = "",
    ) -> str:

        if not turns:
            return previous_summary

        conversation = (
            self.conversation_formatter.format(
                turns
            )
        )

        prompt = (
            "Update the conversation summary using "
            "the previous summary and the new "
            "conversation turns.\n\n"

            "Preserve only information that may be "
            "useful for future conversation.\n\n"

            "Include:\n"
            "- Important topics discussed\n"
            "- Important user requests or constraints\n"
            "- Important conclusions\n"
            "- References required to understand "
            "future follow-up questions\n\n"

            "Rules:\n"
            "- Keep the summary concise.\n"
            "- Do not answer the user.\n"
            "- Do not include unnecessary details.\n"
            "- Return only the updated summary.\n\n"

            f"Previous Summary:\n"
            f"{previous_summary or 'No previous summary.'}\n\n"

            f"New Conversation Turns:\n"
            f"{conversation}"
        )

        return self.llm_service.generate(
            prompt
        ).strip()