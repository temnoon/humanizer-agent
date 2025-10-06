"""
Semantic Scoring for Madhyamaka Detection

Uses sentence embeddings to compute semantic similarity between input text
and curated examples of eternalism, nihilism, and middle path understanding.

Heavily weights semantic meaning over regex pattern matching.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from .semantic_examples import EXAMPLE_DATABASE


class SemanticScorer:
    """
    Computes semantic similarity scores for Madhyamaka detection.

    Uses sentence embeddings to compare input text against curated examples
    of different philosophical positions.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize semantic scorer with embedding model.

        Args:
            model_name: HuggingFace model for sentence embeddings
        """
        if not EMBEDDINGS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self.model = SentenceTransformer(model_name)
        self._cache = {}

        # Pre-compute embeddings for all examples
        self._precompute_example_embeddings()

    def _precompute_example_embeddings(self):
        """Pre-compute embeddings for all curated examples"""
        for category, examples in EXAMPLE_DATABASE.items():
            self._cache[f"{category}_embeddings"] = self.model.encode(
                examples,
                convert_to_numpy=True,
                show_progress_bar=False
            )

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

    def _max_similarity(self, text_embedding: np.ndarray, example_embeddings: np.ndarray) -> float:
        """
        Compute maximum similarity between text and a set of examples.

        Returns the highest similarity score (best match).
        """
        similarities = [
            self._cosine_similarity(text_embedding, example_emb)
            for example_emb in example_embeddings
        ]
        return max(similarities) if similarities else 0.0

    def _avg_top_k_similarity(
        self,
        text_embedding: np.ndarray,
        example_embeddings: np.ndarray,
        k: int = 3
    ) -> float:
        """
        Compute average of top-k similarities.

        More robust than max - considers multiple close matches.
        """
        similarities = [
            self._cosine_similarity(text_embedding, example_emb)
            for example_emb in example_embeddings
        ]

        if not similarities:
            return 0.0

        # Sort descending and take top k
        top_k = sorted(similarities, reverse=True)[:min(k, len(similarities))]
        return float(np.mean(top_k))

    def score_eternalism(self, text: str) -> Dict[str, Any]:
        """
        Score text for eternalism (reification, absolutism) using semantic similarity.

        Returns:
            {
                "semantic_score": float (0-1),
                "max_similarity": float,
                "avg_top3_similarity": float,
                "confidence": str (low/medium/high/very_high)
            }
        """
        # Encode input text
        text_embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)

        # Get eternalism example embeddings
        eternalism_embeddings = self._cache["eternalism_embeddings"]

        # Compute similarities
        max_sim = self._max_similarity(text_embedding, eternalism_embeddings)
        avg_top3 = self._avg_top_k_similarity(text_embedding, eternalism_embeddings, k=3)

        # Weighted score: 60% avg_top3, 40% max (balance robustness & sensitivity)
        semantic_score = (0.6 * avg_top3) + (0.4 * max_sim)

        # Determine confidence
        if semantic_score < 0.3:
            confidence = "low"
        elif semantic_score < 0.5:
            confidence = "medium"
        elif semantic_score < 0.7:
            confidence = "high"
        else:
            confidence = "very_high"

        return {
            "semantic_score": semantic_score,
            "max_similarity": max_sim,
            "avg_top3_similarity": avg_top3,
            "confidence": confidence
        }

    def score_nihilism(self, text: str) -> Dict[str, Any]:
        """
        Score text for nihilism (denial of conventional truth) using semantic similarity.
        """
        text_embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        nihilism_embeddings = self._cache["nihilism_embeddings"]

        max_sim = self._max_similarity(text_embedding, nihilism_embeddings)
        avg_top3 = self._avg_top_k_similarity(text_embedding, nihilism_embeddings, k=3)

        semantic_score = (0.6 * avg_top3) + (0.4 * max_sim)

        if semantic_score < 0.3:
            confidence = "low"
        elif semantic_score < 0.5:
            confidence = "medium"
        elif semantic_score < 0.7:
            confidence = "high"
        else:
            confidence = "very_high"

        return {
            "semantic_score": semantic_score,
            "max_similarity": max_sim,
            "avg_top3_similarity": avg_top3,
            "confidence": confidence
        }

    def score_middle_path(self, text: str) -> Dict[str, Any]:
        """
        Score text for middle path understanding using semantic similarity.
        """
        text_embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        middle_path_embeddings = self._cache["middle_path_embeddings"]

        max_sim = self._max_similarity(text_embedding, middle_path_embeddings)
        avg_top3 = self._avg_top_k_similarity(text_embedding, middle_path_embeddings, k=3)

        # For middle path, we want higher confidence when close matches exist
        semantic_score = (0.6 * avg_top3) + (0.4 * max_sim)

        # Determine proximity
        if semantic_score < 0.3:
            proximity = "far"
        elif semantic_score < 0.5:
            proximity = "approaching"
        elif semantic_score < 0.7:
            proximity = "close"
        else:
            proximity = "very_close"

        return {
            "semantic_score": semantic_score,
            "max_similarity": max_sim,
            "avg_top3_similarity": avg_top3,
            "proximity": proximity
        }

    def score_clinging(self, text: str) -> Dict[str, Any]:
        """
        Score text for clinging/attachment to views using semantic similarity.
        """
        text_embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        clinging_embeddings = self._cache["clinging_embeddings"]

        max_sim = self._max_similarity(text_embedding, clinging_embeddings)
        avg_top3 = self._avg_top_k_similarity(text_embedding, clinging_embeddings, k=3)

        semantic_score = (0.6 * avg_top3) + (0.4 * max_sim)

        if semantic_score < 0.3:
            confidence = "low"
        elif semantic_score < 0.5:
            confidence = "medium"
        elif semantic_score < 0.7:
            confidence = "high"
        else:
            confidence = "very_high"

        return {
            "semantic_score": semantic_score,
            "max_similarity": max_sim,
            "avg_top3_similarity": avg_top3,
            "confidence": confidence
        }

    def comparative_analysis(self, text: str) -> Dict[str, Any]:
        """
        Compare text against all categories to determine dominant tendency.

        Returns:
            {
                "eternalism": score,
                "nihilism": score,
                "middle_path": score,
                "clinging": score,
                "dominant": category with highest score,
                "balanced": bool (no category dominates strongly)
            }
        """
        scores = {
            "eternalism": self.score_eternalism(text)["semantic_score"],
            "nihilism": self.score_nihilism(text)["semantic_score"],
            "middle_path": self.score_middle_path(text)["semantic_score"],
            "clinging": self.score_clinging(text)["semantic_score"],
        }

        dominant = max(scores, key=scores.get)
        max_score = scores[dominant]

        # Check if scores are relatively balanced (no strong dominance)
        score_values = list(scores.values())
        balanced = (max(score_values) - min(score_values)) < 0.2

        return {
            **scores,
            "dominant": dominant,
            "dominant_score": max_score,
            "balanced": balanced
        }


# Global scorer instance (lazy initialization)
_scorer_instance = None


def get_semantic_scorer() -> Optional[SemanticScorer]:
    """
    Get global semantic scorer instance (singleton pattern).

    Returns None if sentence-transformers not available.
    """
    global _scorer_instance

    if not EMBEDDINGS_AVAILABLE:
        return None

    if _scorer_instance is None:
        _scorer_instance = SemanticScorer()

    return _scorer_instance
