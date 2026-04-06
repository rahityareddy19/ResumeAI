"""
Embeddings Module
Handles loading the sentence-transformers model and computing semantic similarity.
Uses the 'all-MiniLM-L6-v2' model — lightweight (~80MB), runs locally, no API key needed.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ── Global model instance (lazy-loaded) ──────────────────────────────────────
_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _load_model() -> SentenceTransformer:
    """Lazy-load the sentence transformer model on first use."""
    global _model
    if _model is None:
        print(f"[Embeddings] Loading model '{MODEL_NAME}'... (first time may download ~80MB)")
        _model = SentenceTransformer(MODEL_NAME)
        print(f"[Embeddings] Model loaded successfully.")
    return _model


def get_embedding(text: str) -> np.ndarray:
    """
    Generate an embedding vector for the given text.
    Returns a numpy array of shape (384,) for the MiniLM model.
    """
    model = _load_model()
    # Truncate very long texts to avoid memory issues
    max_chars = 10000
    if len(text) > max_chars:
        text = text[:max_chars]
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Compute cosine similarity between two texts using their embeddings.
    Returns a float between 0 and 1, where 1 means identical meaning.
    """
    if not text_a.strip() or not text_b.strip():
        return 0.0

    emb_a = get_embedding(text_a).reshape(1, -1)
    emb_b = get_embedding(text_b).reshape(1, -1)

    similarity = cosine_similarity(emb_a, emb_b)[0][0]

    # Clamp to [0, 1] range (cosine similarity can sometimes be slightly negative)
    return float(max(0.0, min(1.0, similarity)))


def compute_batch_similarity(texts: list, reference_text: str) -> list:
    """
    Compute cosine similarity between a reference text and multiple texts.
    More efficient than calling compute_similarity in a loop.
    Returns a list of floats.
    """
    if not reference_text.strip():
        return [0.0] * len(texts)

    model = _load_model()
    max_chars = 10000

    # Prepare texts
    ref_truncated = reference_text[:max_chars]
    texts_truncated = [t[:max_chars] if t.strip() else "" for t in texts]

    # Encode all at once
    ref_emb = model.encode(ref_truncated, convert_to_numpy=True).reshape(1, -1)
    text_embs = model.encode(texts_truncated, convert_to_numpy=True)

    # Compute similarities
    similarities = cosine_similarity(text_embs, ref_emb).flatten()

    return [float(max(0.0, min(1.0, s))) for s in similarities]
