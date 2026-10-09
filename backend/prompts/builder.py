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
    instruction = "Answer the user's question using ONLY the provided Context. If the context does not contain the answer, say 'I cannot answer this question based on the provided documents.'" if context.strip() else "There is no context provided. Refuse to answer any factual questions."

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