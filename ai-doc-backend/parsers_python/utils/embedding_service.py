"""
AI Embedding Service for document comparison.

Provides two embedding strategies:
1. Primary: sentence-transformers (true semantic embeddings via neural network)
2. Fallback: TF-IDF vectorization (lexical similarity, lightweight)

The service auto-detects available libraries and selects the best strategy.
"""

import logging
import numpy as np
from typing import List, Optional

logger = logging.getLogger(__name__)

# Try to import sentence-transformers (requires PyTorch)
_sentence_model = None
_embedding_method = None

try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
    logger.info("sentence-transformers available - semantic embeddings enabled")
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.info("sentence-transformers not available - will use TF-IDF fallback")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available - basic fallback will be used")


def get_embedding_method() -> str:
    """Return the current embedding method being used."""
    global _embedding_method
    if _embedding_method:
        return _embedding_method
    if _SENTENCE_TRANSFORMERS_AVAILABLE:
        return "sentence-transformers"
    if _SKLEARN_AVAILABLE:
        return "tfidf"
    return "basic"


def _get_sentence_model():
    """Lazy-load the sentence-transformers model."""
    global _sentence_model, _embedding_method
    if _sentence_model is None:
        logger.info("Loading sentence-transformers model: all-MiniLM-L6-v2 ...")
        _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        _embedding_method = "sentence-transformers"
        logger.info("Model loaded successfully")
    return _sentence_model


def embed_texts_semantic(texts: List[str]) -> np.ndarray:
    """
    Generate semantic embeddings using sentence-transformers.

    Args:
        texts: List of text strings to embed

    Returns:
        numpy array of shape (n_texts, embedding_dim)
    """
    model = _get_sentence_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings


def embed_texts_tfidf(texts_a: List[str], texts_b: List[str]):
    """
    Generate TF-IDF vectors for two sets of texts.

    Args:
        texts_a: First document's chunks
        texts_b: Second document's chunks

    Returns:
        (vectors_a, vectors_b) as sparse matrices
    """
    global _embedding_method
    _embedding_method = "tfidf"

    vectorizer = TfidfVectorizer(
        max_features=10000,
        stop_words='english',
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    # Fit on combined corpus, transform separately
    all_texts = texts_a + texts_b
    vectorizer.fit(all_texts)

    vectors_a = vectorizer.transform(texts_a)
    vectors_b = vectorizer.transform(texts_b)

    return vectors_a, vectors_b


def cosine_similarity_matrix(embeddings_a: np.ndarray, embeddings_b: np.ndarray) -> np.ndarray:
    """
    Compute pairwise cosine similarity between two sets of embeddings.

    Args:
        embeddings_a: shape (m, d)
        embeddings_b: shape (n, d)

    Returns:
        Similarity matrix of shape (m, n) where values are in [-1, 1]
    """
    if _SKLEARN_AVAILABLE:
        return sklearn_cosine(embeddings_a, embeddings_b)

    # Manual cosine similarity as fallback
    a_norm = embeddings_a / (np.linalg.norm(embeddings_a, axis=1, keepdims=True) + 1e-10)
    b_norm = embeddings_b / (np.linalg.norm(embeddings_b, axis=1, keepdims=True) + 1e-10)
    return np.dot(a_norm, b_norm.T)


def compute_similarity(texts_a: List[str], texts_b: List[str]) -> np.ndarray:
    """
    Compute similarity matrix between two lists of texts using the best available method.

    Args:
        texts_a: Chunks from document A
        texts_b: Chunks from document B

    Returns:
        Similarity matrix of shape (len(texts_a), len(texts_b))
    """
    if not texts_a or not texts_b:
        return np.array([])

    if _SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            logger.info(f"Computing semantic embeddings for {len(texts_a)} + {len(texts_b)} chunks")
            emb_a = embed_texts_semantic(texts_a)
            emb_b = embed_texts_semantic(texts_b)
            return cosine_similarity_matrix(emb_a, emb_b)
        except Exception as e:
            logger.warning(f"Sentence-transformers failed, falling back to TF-IDF: {e}")

    if _SKLEARN_AVAILABLE:
        logger.info(f"Computing TF-IDF similarity for {len(texts_a)} + {len(texts_b)} chunks")
        vec_a, vec_b = embed_texts_tfidf(texts_a, texts_b)
        return cosine_similarity_matrix(vec_a.toarray(), vec_b.toarray())

    # Last resort: basic word overlap (Jaccard-like)
    logger.warning("Using basic word overlap similarity (no ML libraries available)")
    return _basic_similarity(texts_a, texts_b)


def _basic_similarity(texts_a: List[str], texts_b: List[str]) -> np.ndarray:
    """Basic word overlap similarity as ultimate fallback."""
    global _embedding_method
    _embedding_method = "basic"

    matrix = np.zeros((len(texts_a), len(texts_b)))

    sets_a = [set(t.lower().split()) for t in texts_a]
    sets_b = [set(t.lower().split()) for t in texts_b]

    for i, sa in enumerate(sets_a):
        for j, sb in enumerate(sets_b):
            if not sa and not sb:
                matrix[i, j] = 1.0
            elif not sa or not sb:
                matrix[i, j] = 0.0
            else:
                intersection = len(sa & sb)
                union = len(sa | sb)
                matrix[i, j] = intersection / union if union > 0 else 0.0

    return matrix
