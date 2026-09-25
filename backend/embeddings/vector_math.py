import numpy as np

def dot_product(vec1, vec2):
    total = 0.0

    for x, y in zip(vec1, vec2):
        total += x * y

    return total


def cosine_similarity(vec1, vec2):
    dot = dot_product(vec1, vec2)

    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)

    if magnitude1 == 0 or magnitude2 == 0:
        raise ValueError("Cosine similarity is undefined for zero vectors.")

    return dot / (magnitude1 * magnitude2)