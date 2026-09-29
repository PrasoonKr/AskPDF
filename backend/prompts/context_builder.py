class ContextBuilder:
    """
    Builds formatted context from retrieved documents.
    """

    def build(
        self,
        search_results,
    ) -> str:

        if not search_results:
            return "No relevant context found."

        context = []

        for index, result in enumerate(search_results, start=1):
            context.append(
                (
                    f"[Document {index}]\n"
                    f"Source: {result.document.source.filename}\n"
                    f"Page: {result.document.page}\n\n"
                    f"{result.document.text}"
                )
            )

        return "\n\n".join(context)