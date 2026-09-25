class RetrievalMetrics:

    @staticmethod
    def hit_at_k(results, expected_source):
        """
        Returns True if expected source appears in retrieved results.
        """

        for result in results:

            if result.document.source.filename == expected_source:
                return True

        return False

    @staticmethod
    def average_similarity(results):

        if not results:
            return 0.0

        return sum(
            result.score
            for result in results
        ) / len(results)