"""
Embedding Clustering Service

Advanced clustering and analysis of chunk embeddings using:
- UMAP for dimensionality reduction (preserves topology better than t-SNE)
- HDBSCAN for density-based clustering (no need to specify cluster count)
- Framework discovery and temporal trajectory analysis

Aligned with Humanizer mission: Revealing constructed nature of beliefs through
geometric patterns in semantic space.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime
from collections import Counter, defaultdict

import umap
import hdbscan
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.chunk_models import Chunk, Collection

logger = logging.getLogger(__name__)


class EmbeddingClusteringService:
    """
    Service for clustering chunk embeddings to discover:
    - Belief frameworks (PERSONA/NAMESPACE/STYLE patterns)
    - Conversation topics
    - Temporal evolution of perspectives
    """

    def __init__(
        self,
        n_neighbors: int = 15,
        min_dist: float = 0.1,
        min_cluster_size: int = 15,
        min_samples: int = 5,
        metric: str = "cosine"
    ):
        """
        Initialize clustering service.

        Args:
            n_neighbors: UMAP parameter - larger values = more global structure
            min_dist: UMAP parameter - smaller values = tighter clusters
            min_cluster_size: HDBSCAN parameter - minimum cluster size
            min_samples: HDBSCAN parameter - conservative clustering parameter
            metric: Distance metric ('cosine', 'euclidean', etc.)
        """
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.metric = metric

    async def fetch_embeddings(
        self,
        session: AsyncSession,
        user_id: Optional[str] = None,
        collection_id: Optional[str] = None,
        limit: Optional[int] = None,
        min_token_count: int = 15
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Fetch embeddings from database.

        Args:
            session: Database session
            user_id: Filter by user (optional)
            collection_id: Filter by collection (optional)
            limit: Maximum number of embeddings
            min_token_count: Minimum token count for chunks

        Returns:
            (embeddings_array, chunk_metadata)
        """
        # Build query
        query = select(Chunk).where(
            and_(
                Chunk.embedding.is_not(None),
                Chunk.token_count >= min_token_count
            )
        )

        if user_id:
            query = query.where(Chunk.user_id == user_id)

        if collection_id:
            query = query.where(Chunk.collection_id == collection_id)

        if limit:
            query = query.limit(limit)

        # Execute
        result = await session.execute(query)
        chunks = result.scalars().all()

        if not chunks:
            logger.warning("No chunks with embeddings found")
            return np.array([]), []

        # Extract embeddings and metadata
        embeddings = []
        metadata = []

        for chunk in chunks:
            embeddings.append(chunk.embedding)
            metadata.append({
                "id": str(chunk.id),
                "content": chunk.content[:200],  # Preview
                "token_count": chunk.token_count,
                "collection_id": str(chunk.collection_id),
                "user_id": str(chunk.user_id),
                "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
                "chunk_level": chunk.chunk_level,
                "content_type": chunk.content_type
            })

        embeddings_array = np.array(embeddings, dtype=np.float32)

        logger.info(f"Fetched {len(embeddings)} embeddings (shape: {embeddings_array.shape})")

        return embeddings_array, metadata

    def reduce_dimensionality(
        self,
        embeddings: np.ndarray,
        n_components: int = 2,
        random_state: int = 42
    ) -> np.ndarray:
        """
        Reduce dimensionality using UMAP.

        Args:
            embeddings: High-dimensional embeddings (e.g., 1024-d)
            n_components: Target dimensions (2 or 3 for visualization)
            random_state: Random seed for reproducibility

        Returns:
            Reduced embeddings
        """
        logger.info(f"Reducing {embeddings.shape} to {n_components} dimensions...")

        reducer = umap.UMAP(
            n_neighbors=self.n_neighbors,
            min_dist=self.min_dist,
            n_components=n_components,
            metric=self.metric,
            random_state=random_state
        )

        reduced = reducer.fit_transform(embeddings)

        logger.info(f"Reduced to shape: {reduced.shape}")

        return reduced

    def cluster_embeddings(
        self,
        embeddings: np.ndarray,
        use_reduced: bool = False
    ) -> Tuple[np.ndarray, hdbscan.HDBSCAN]:
        """
        Cluster embeddings using HDBSCAN.

        Args:
            embeddings: Embeddings to cluster (full or reduced dimensionality)
            use_reduced: If True, cluster on reduced dims (faster, less accurate)

        Returns:
            (cluster_labels, clusterer_object)
        """
        logger.info(f"Clustering {len(embeddings)} embeddings...")

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric=self.metric,
            cluster_selection_method='eom',  # Excess of Mass
            prediction_data=True  # Enable soft clustering
        )

        cluster_labels = clusterer.fit_predict(embeddings)

        # Count clusters (-1 is noise)
        unique_labels = set(cluster_labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(cluster_labels).count(-1)

        logger.info(f"Found {n_clusters} clusters ({n_noise} noise points)")

        return cluster_labels, clusterer

    def analyze_clusters(
        self,
        cluster_labels: np.ndarray,
        metadata: List[Dict[str, Any]],
        top_n_words: int = 10
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze discovered clusters.

        Args:
            cluster_labels: Cluster assignment for each chunk
            metadata: Chunk metadata
            top_n_words: Number of top words to extract per cluster

        Returns:
            Dictionary mapping cluster_id → cluster_analysis
        """
        clusters = {}

        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # Skip noise
                continue

            # Get chunks in this cluster
            cluster_mask = cluster_labels == cluster_id
            cluster_metadata = [m for i, m in enumerate(metadata) if cluster_mask[i]]

            # Extract cluster characteristics
            all_content = " ".join([m["content"] for m in cluster_metadata])
            words = all_content.lower().split()
            word_counts = Counter(words)

            # Remove stop words (basic)
            stop_words = set([
                "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
                "for", "of", "with", "is", "are", "was", "were", "been", "be"
            ])
            filtered_words = {w: c for w, c in word_counts.items() if w not in stop_words and len(w) > 3}
            top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:top_n_words]

            # Time distribution
            timestamps = [m["created_at"] for m in cluster_metadata if m["created_at"]]
            if timestamps:
                earliest = min(timestamps)
                latest = max(timestamps)
            else:
                earliest = latest = None

            # Representative chunk (longest one)
            representative = max(cluster_metadata, key=lambda m: m["token_count"])

            clusters[int(cluster_id)] = {
                "cluster_id": int(cluster_id),
                "size": int(cluster_mask.sum()),
                "top_words": [{"word": w, "count": c} for w, c in top_words],
                "representative_chunk": representative,
                "time_range": {
                    "earliest": earliest,
                    "latest": latest
                },
                "avg_token_count": np.mean([m["token_count"] for m in cluster_metadata]),
                "content_types": dict(Counter([m["content_type"] for m in cluster_metadata]))
            }

        return clusters

    async def discover_belief_frameworks(
        self,
        session: AsyncSession,
        user_id: Optional[str] = None,
        n_clusters_estimate: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Auto-discover belief frameworks from embeddings.

        This is the main high-level function that:
        1. Fetches embeddings
        2. Reduces dimensionality
        3. Clusters
        4. Analyzes clusters

        Args:
            session: Database session
            user_id: User to analyze
            n_clusters_estimate: Rough estimate of expected clusters (adjusts params)

        Returns:
            Complete clustering results with analysis
        """
        logger.info(f"Discovering belief frameworks for user: {user_id or 'all'}")

        # Adjust parameters based on estimated clusters
        if n_clusters_estimate:
            self.min_cluster_size = max(10, 1000 // n_clusters_estimate)

        # 1. Fetch embeddings
        embeddings, metadata = await self.fetch_embeddings(
            session,
            user_id=user_id,
            min_token_count=15  # Skip very short chunks
        )

        if len(embeddings) == 0:
            return {
                "error": "No embeddings found",
                "n_chunks": 0,
                "n_clusters": 0
            }

        # 2. Reduce dimensionality (for visualization)
        reduced_2d = self.reduce_dimensionality(embeddings, n_components=2)
        reduced_3d = self.reduce_dimensionality(embeddings, n_components=3)

        # 3. Cluster on full-dimensional embeddings (more accurate)
        cluster_labels, clusterer = self.cluster_embeddings(embeddings)

        # 4. Analyze clusters
        cluster_analysis = self.analyze_clusters(cluster_labels, metadata)

        # 5. Attach 2D/3D coordinates to metadata
        for i, meta in enumerate(metadata):
            meta["coords_2d"] = reduced_2d[i].tolist()
            meta["coords_3d"] = reduced_3d[i].tolist()
            meta["cluster_id"] = int(cluster_labels[i])

        # 6. Compile results
        results = {
            "n_chunks": len(embeddings),
            "n_clusters": len(cluster_analysis),
            "n_noise": int((cluster_labels == -1).sum()),
            "clusters": cluster_analysis,
            "chunk_metadata": metadata,  # Includes coords and cluster assignments
            "parameters": {
                "n_neighbors": self.n_neighbors,
                "min_dist": self.min_dist,
                "min_cluster_size": self.min_cluster_size,
                "min_samples": self.min_samples,
                "metric": self.metric
            }
        }

        logger.info(f"Discovered {results['n_clusters']} belief frameworks from {results['n_chunks']} chunks")

        return results

    def compute_cluster_centroids(
        self,
        embeddings: np.ndarray,
        cluster_labels: np.ndarray
    ) -> Dict[int, np.ndarray]:
        """
        Compute centroid embedding for each cluster.

        These centroids can be stored in database for future similarity comparisons.

        Args:
            embeddings: Original high-dimensional embeddings
            cluster_labels: Cluster assignments

        Returns:
            Dictionary mapping cluster_id → centroid_embedding
        """
        centroids = {}

        for cluster_id in set(cluster_labels):
            if cluster_id == -1:
                continue

            cluster_mask = cluster_labels == cluster_id
            cluster_embeddings = embeddings[cluster_mask]

            # Mean of all embeddings in cluster
            centroid = np.mean(cluster_embeddings, axis=0)

            # Normalize (for cosine similarity)
            centroid = centroid / np.linalg.norm(centroid)

            centroids[int(cluster_id)] = centroid

        return centroids


# Convenience function for CLI usage
async def cluster_user_embeddings(
    session: AsyncSession,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quick function to cluster embeddings for a user.

    Args:
        session: Database session
        user_id: User to analyze (None = all users)

    Returns:
        Clustering results
    """
    service = EmbeddingClusteringService()
    return await service.discover_belief_frameworks(session, user_id=user_id)
