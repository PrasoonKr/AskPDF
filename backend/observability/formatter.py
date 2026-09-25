class TraceFormatter:
    """
    Formats retrieval traces for debugging.
    """

    def format(
        self,
        trace,
    ) -> str:

        sections = []

        sections.append(
            "=" * 60
        )

        sections.append(
            "RAG RETRIEVAL TRACE"
        )

        sections.append(
            "=" * 60
        )

        sections.append(
            (
                "\nOriginal Query:\n"
                f"{trace.original_query}"
            )
        )

        sections.append(
            (
                "\nRewritten Query:\n"
                f"{trace.rewritten_query}"
            )
        )

        sections.append(
            self._format_results(
                "SEMANTIC RESULTS",
                trace.semantic_results,
            )
        )

        sections.append(
            self._format_results(
                "KEYWORD RESULTS",
                trace.keyword_results,
            )
        )

        sections.append(
            self._format_results(
                "FUSED RESULTS",
                trace.fused_results,
            )
        )

        if trace.reranked_results:

            sections.append(
                self._format_results(
                    "RERANKED RESULTS",
                    trace.reranked_results,
                )
            )

        sections.append(
            self._format_results(
                "FINAL RESULTS",
                trace.final_results,
            )
        )

        return "\n".join(sections)

    def _format_results(
        self,
        title,
        results,
    ):

        lines = [
            "",
            title,
            "-" * 60,
        ]

        if not results:

            lines.append(
                "No results."
            )

            return "\n".join(lines)

        for rank, result in enumerate(
            results,
            start=1,
        ):

            document = result.document

            lines.append(
                (
                    f"{rank}. "
                    f"Source: {document.source.filename} | "
                    f"Page: {document.page} | "
                    f"Score: {result.score:.4f}"
                )
            )

        return "\n".join(lines)