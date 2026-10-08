# System prompt is now passed natively via generator.py


def build_prompt(
    query: str,
    context: str,
    conversation: str | None = None,
    conversation_summary: str | None = None,
):
    """
    Build the final RAG prompt.
    """
    instruction = "Answer the question based ONLY on the provided Context." if context.strip() else "Respond to the user naturally."

    return (
        f"Context:\n"
        f"{context}\n\n"
        f"Conversation Summary:\n"
        f"{conversation_summary or 'No conversation summary.'}\n\n"
        f"Recent Conversation:\n"
        f"{conversation or 'No previous conversation.'}\n\n"
        f"Question:\n"
        f"{query}\n\n"
        f"{instruction}"
    )