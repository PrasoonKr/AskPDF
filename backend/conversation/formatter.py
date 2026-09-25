class ConversationFormatter:
    """
    Formats conversation turns for LLM prompts.
    """

    def format(
        self,
        turns,
    ) -> str:

        if not turns:
            return "No previous conversation."

        formatted_turns = []

        for turn in turns:

            formatted_turns.append(
                (
                    f"User: {turn.user}\n\n"
                    f"Assistant: {turn.assistant}"
                )
            )

        return "\n\n".join(
            formatted_turns
        )