"""
Embeddings Module (Lightweight Version)
Computes text similarity using TF-IDF + cosine similarity from scikit-learn.
No heavy ML frameworks required — runs fully on Vercel serverless.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using TF-IDF vectors.
    Returns a float between 0 and 1, where 1 means identical content.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
        )
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return float(max(0.0, min(1.0, similarity)))
    except Exception:
        return 0.0


def compute_batch_similarity(texts: list, reference_text: str) -> list:
    """
    Compute cosine similarity between a reference text and multiple texts.
    Returns a list of floats between 0 and 1.
    """
    if not reference_text.strip() or not texts:
        return [0.0] * len(texts)

    try:
        all_texts = [reference_text] + [t if t.strip() else " " for t in texts]
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
        )
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        ref_vec = tfidf_matrix[0:1]
        text_vecs = tfidf_matrix[1:]
        similarities = cosine_similarity(text_vecs, ref_vec).flatten()
        return [float(max(0.0, min(1.0, s))) for s in similarities]
    except Exception:
        return [0.0] * len(texts)
