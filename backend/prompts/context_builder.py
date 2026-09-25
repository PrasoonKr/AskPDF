from backend.config import RetrievalConfig


class ContextBuilder:
    """
    Builds formatted context from retrieved documents.
    """

    def build(
        self,
        search_results,
    ) -> str:

        relevant_results = [
            result
            for result in search_results
            if result.score >= RetrievalConfig.SIMILARITY_THRESHOLD
        ]

        if not relevant_results:
            return "No relevant context found."

        context = []

        for index, result in enumerate(relevant_results, start=1):
            context.append(
                (
                    f"[Document {index}]\n"
                    f"Source: {result.document.source.filename}\n"
                    f"Page: {result.document.page}\n\n"
                    f"{result.document.text}"
                )
            )

        return "\n\n".join(context)