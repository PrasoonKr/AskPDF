def print_search_results(results):
    """
    Display retrieved search results.
    """

    print("\n" + "=" * 70)
    print("Retrieved Context")
    print("=" * 70)

    if not results:
        print("No relevant documents found.")
        return

    for rank, result in enumerate(results, start=1):

        print(f"\nRank {rank}")
        print(f"Score : {result.score:.4f}")
        print()

        print(result.document.text)

        print("-" * 70)