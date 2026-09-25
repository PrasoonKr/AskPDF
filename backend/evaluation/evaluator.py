from backend.embeddings.service import EmbeddingService
from backend.evaluation.dataset import EvaluationDataset
from backend.evaluation.metrics import RetrievalMetrics


class RetrievalEvaluator:

    def __init__(
        self,
        embedding_service: EmbeddingService,
        document_store,
        dataset_path: str,
    ):
        self.embedding_service = embedding_service
        self.document_store = document_store

        self.dataset = EvaluationDataset(
            dataset_path
        )

    def evaluate(self):

        questions = self.dataset.load()

        total_questions = len(questions)

        hits = 0

        similarity_scores = []

        print("=" * 60)
        print("Retrieval Evaluation")
        print("=" * 60)

        for sample in questions:

            query = sample["question"]

            expected_source = sample[
                "expected_source"
            ]

            query_embedding = (
                self.embedding_service.embed_query(
                    query
                )
            )

            results = self.document_store.semantic_search(
                query_embedding
            )

            hit = RetrievalMetrics.hit_at_k(
                results,
                expected_source,
            )

            if hit:
                hits += 1

            similarity_scores.append(
                RetrievalMetrics.average_similarity(
                    results
                )
            )

            print(f"\nQuestion : {query}")
            print(
                f"Expected : {expected_source}"
            )
            print(
                f"Result   : {'PASS' if hit else 'FAIL'}"
            )

        accuracy = (
            hits / total_questions
        ) * 100

        average_similarity = (
            sum(similarity_scores)
            / len(similarity_scores)
        )

        print("\n" + "=" * 60)
        print("Summary")
        print("=" * 60)

        print(
            f"Questions Tested : {total_questions}"
        )

        print(
            f"Hit@K            : {accuracy:.2f}%"
        )

        print(
            f"Average Similarity : "
            f"{average_similarity:.4f}"
        )