"""
Transformation Arithmetic Service

Implements embedding arithmetic for PERSONA/NAMESPACE/STYLE transformations.

Core idea: If "King - Man + Woman = Queen", then:
           "Chunk + Skeptical - Neutral = Skeptical Version"

This reveals transformations as geometric operations in semantic space.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from collections import defaultdict

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk_models import Chunk

logger = logging.getLogger(__name__)


class TransformationArithmeticService:
    """
    Service for learning and applying transformation vectors.

    Transformations are vector operations in embedding space:
    - Learn transformation vectors from paired examples
    - Apply transformations to predict semantic shifts
    - Measure transformation distances
    - Find transformation trajectories
    """

    def __init__(self):
        """Initialize service."""
        self.transformation_vectors: Dict[str, np.ndarray] = {}
        self.framework_embeddings: Dict[str, np.ndarray] = {}

    async def learn_framework_vector(
        self,
        session: AsyncSession,
        framework_name: str,
        example_chunk_ids: List[str],
        baseline_name: str = "neutral",
        baseline_chunk_ids: Optional[List[str]] = None
    ) -> np.ndarray:
        """
        Learn a transformation vector from examples.

        Args:
            session: Database session
            framework_name: Name of framework (e.g., "skeptical", "academic")
            example_chunk_ids: IDs of chunks exemplifying this framework
            baseline_name: Name of baseline framework
            baseline_chunk_ids: IDs of baseline chunks (or use random sample)

        Returns:
            Transformation vector (framework - baseline)
        """
        # Fetch framework examples
        framework_query = select(Chunk).where(
            and_(
                Chunk.id.in_(example_chunk_ids),
                Chunk.embedding.is_not(None)
            )
        )
        result = await session.execute(framework_query)
        framework_chunks = result.scalars().all()

        if not framework_chunks:
            logger.warning(f"No framework chunks found for {framework_name}")
            return np.zeros(1024)  # Return zero vector

        # Compute mean embedding for framework
        framework_embeddings = np.array([c.embedding for c in framework_chunks])
        framework_mean = np.mean(framework_embeddings, axis=0)

        # Fetch baseline examples
        if baseline_chunk_ids:
            baseline_query = select(Chunk).where(
                and_(
                    Chunk.id.in_(baseline_chunk_ids),
                    Chunk.embedding.is_not(None)
                )
            )
        else:
            # Use random sample as baseline
            baseline_query = select(Chunk).where(
                Chunk.embedding.is_not(None)
            ).order_by(func.random()).limit(len(framework_chunks))

        result = await session.execute(baseline_query)
        baseline_chunks = result.scalars().all()

        if not baseline_chunks:
            logger.warning("No baseline chunks found")
            return framework_mean  # Just use framework mean

        # Compute mean embedding for baseline
        baseline_embeddings = np.array([c.embedding for c in baseline_chunks])
        baseline_mean = np.mean(baseline_embeddings, axis=0)

        # Transformation vector is the difference
        transformation_vector = framework_mean - baseline_mean

        # Normalize
        transformation_vector = transformation_vector / (np.linalg.norm(transformation_vector) + 1e-8)

        # Store
        self.transformation_vectors[framework_name] = transformation_vector
        self.framework_embeddings[framework_name] = framework_mean
        self.framework_embeddings[baseline_name] = baseline_mean

        logger.info(
            f"Learned transformation vector '{framework_name}' from {len(framework_chunks)} examples "
            f"(magnitude: {np.linalg.norm(framework_mean - baseline_mean):.3f})"
        )

        return transformation_vector

    def apply_transformation(
        self,
        embedding: np.ndarray,
        transformation_name: str,
        strength: float = 1.0
    ) -> np.ndarray:
        """
        Apply transformation to an embedding.

        Args:
            embedding: Original embedding
            transformation_name: Name of transformation to apply
            strength: Transformation strength (0.0 to 1.0+)

        Returns:
            Transformed embedding
        """
        if transformation_name not in self.transformation_vectors:
            logger.warning(f"Transformation '{transformation_name}' not found")
            return embedding

        vector = self.transformation_vectors[transformation_name]
        transformed = embedding + (strength * vector)

        # Normalize to unit vector (for cosine similarity)
        transformed = transformed / (np.linalg.norm(transformed) + 1e-8)

        return transformed

    def compose_transformations(
        self,
        embedding: np.ndarray,
        transformations: List[Tuple[str, float]]
    ) -> np.ndarray:
        """
        Apply multiple transformations in sequence.

        Note: Order matters! Skeptical → Academic ≠ Academic → Skeptical

        Args:
            embedding: Starting embedding
            transformations: List of (name, strength) tuples

        Returns:
            Composed transformation result
        """
        current = embedding.copy()

        for name, strength in transformations:
            current = self.apply_transformation(current, name, strength)

        return current

    async def find_similar_transformations(
        self,
        session: AsyncSession,
        source_embedding: np.ndarray,
        target_embedding: np.ndarray,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find chunks that represent similar transformations.

        Given: original embedding → transformed embedding
        Find: chunks in database that are "along the transformation path"

        Args:
            session: Database session
            source_embedding: Starting point
            target_embedding: End point
            n_results: Number of results to return

        Returns:
            List of similar transformation examples from database
        """
        # Compute transformation direction
        direction = target_embedding - source_embedding
        direction = direction / (np.linalg.norm(direction) + 1e-8)

        # Find chunks whose embeddings align with this direction
        # (Use SQL for efficiency - dot product with direction vector)
        query = select(Chunk).where(
            Chunk.embedding.is_not(None)
        ).limit(1000)  # Sample for speed

        result = await session.execute(query)
        chunks = result.scalars().all()

        # Compute alignment scores
        scored_chunks = []
        for chunk in chunks:
            chunk_direction = chunk.embedding - source_embedding
            chunk_direction = chunk_direction / (np.linalg.norm(chunk_direction) + 1e-8)

            # Cosine similarity between directions
            alignment = np.dot(direction, chunk_direction)

            scored_chunks.append({
                "chunk": chunk,
                "alignment": float(alignment),
                "distance_from_source": float(np.linalg.norm(chunk.embedding - source_embedding)),
                "distance_from_target": float(np.linalg.norm(chunk.embedding - target_embedding))
            })

        # Sort by alignment
        scored_chunks.sort(key=lambda x: x["alignment"], reverse=True)

        # Return top results
        results = []
        for sc in scored_chunks[:n_results]:
            chunk = sc["chunk"]
            results.append({
                "id": str(chunk.id),
                "content": chunk.content[:200],
                "alignment": sc["alignment"],
                "distance_from_source": sc["distance_from_source"],
                "distance_from_target": sc["distance_from_target"],
                "token_count": chunk.token_count
            })

        return results

    def measure_transformation_distance(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        metric: str = "cosine"
    ) -> float:
        """
        Measure semantic distance between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding
            metric: Distance metric ('cosine', 'euclidean', 'manhattan')

        Returns:
            Distance value
        """
        if metric == "cosine":
            # Cosine distance (1 - cosine similarity)
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2) + 1e-8
            )
            return float(1.0 - similarity)

        elif metric == "euclidean":
            return float(np.linalg.norm(embedding1 - embedding2))

        elif metric == "manhattan":
            return float(np.sum(np.abs(embedding1 - embedding2)))

        else:
            raise ValueError(f"Unknown metric: {metric}")

    def predict_transformation_target(
        self,
        source_embedding: np.ndarray,
        transformations: List[str],
        strengths: Optional[List[float]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Predict where an embedding will land after transformations.

        Args:
            source_embedding: Starting point
            transformations: List of transformation names
            strengths: Optional list of strengths (default: all 1.0)

        Returns:
            (predicted_embedding, metadata)
        """
        if strengths is None:
            strengths = [1.0] * len(transformations)

        if len(strengths) != len(transformations):
            raise ValueError("Strengths must match transformations length")

        # Apply transformations
        current = source_embedding.copy()
        trajectory = [current.copy()]

        for name, strength in zip(transformations, strengths):
            current = self.apply_transformation(current, name, strength)
            trajectory.append(current.copy())

        # Compute cumulative distance
        cumulative_distance = 0.0
        for i in range(len(trajectory) - 1):
            cumulative_distance += self.measure_transformation_distance(
                trajectory[i], trajectory[i+1], metric="cosine"
            )

        metadata = {
            "transformations_applied": list(zip(transformations, strengths)),
            "cumulative_distance": cumulative_distance,
            "trajectory_length": len(trajectory),
            "final_distance_from_source": self.measure_transformation_distance(
                source_embedding, current, metric="cosine"
            )
        }

        return current, metadata

    async def find_transformation_examples(
        self,
        session: AsyncSession,
        framework_name: str,
        n_examples: int = 10,
        min_token_count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find chunks that exemplify a learned transformation framework.

        Args:
            session: Database session
            framework_name: Framework to find examples of
            n_examples: Number of examples to return
            min_token_count: Minimum chunk size

        Returns:
            List of example chunks
        """
        if framework_name not in self.framework_embeddings:
            logger.warning(f"Framework '{framework_name}' not learned yet")
            return []

        framework_embedding = self.framework_embeddings[framework_name]

        # Find chunks closest to framework centroid
        query = select(Chunk).where(
            and_(
                Chunk.embedding.is_not(None),
                Chunk.token_count >= min_token_count
            )
        ).limit(1000)

        result = await session.execute(query)
        chunks = result.scalars().all()

        # Score by similarity to framework
        scored = []
        for chunk in chunks:
            similarity = np.dot(chunk.embedding, framework_embedding) / (
                np.linalg.norm(chunk.embedding) * np.linalg.norm(framework_embedding) + 1e-8
            )
            scored.append((chunk, float(similarity)))

        # Sort and return top
        scored.sort(key=lambda x: x[1], reverse=True)

        examples = []
        for chunk, similarity in scored[:n_examples]:
            examples.append({
                "id": str(chunk.id),
                "content": chunk.content,
                "similarity": similarity,
                "token_count": chunk.token_count,
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None
            })

        return examples


# Convenience function
async def learn_transformations_from_clusters(
    session: AsyncSession,
    clusters: Dict[int, Dict[str, Any]]
) -> TransformationArithmeticService:
    """
    Learn transformation vectors from discovered clusters.

    Args:
        session: Database session
        clusters: Output from EmbeddingClusteringService.analyze_clusters()

    Returns:
        Service with learned transformations
    """
    service = TransformationArithmeticService()

    # Use largest cluster as baseline
    baseline_cluster = max(clusters.items(), key=lambda x: x[1]["size"])
    baseline_id = baseline_cluster[0]

    logger.info(f"Using cluster #{baseline_id} as baseline (size: {baseline_cluster[1]['size']})")

    # Learn transformation for each other cluster
    for cluster_id, analysis in clusters.items():
        if cluster_id == baseline_id:
            continue

        # Extract chunk IDs from cluster (would need to modify cluster_analysis to include IDs)
        # For now, skip - this is a placeholder

        logger.info(f"Cluster #{cluster_id}: {analysis['top_words'][:3]}")

    return service
