"""
Artifact Service - Business logic for artifact operations.

Handles:
- Artifact creation with auto-embedding
- Lineage tracking
- Semantic search over artifacts
- Composition and transformation helpers
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import numpy as np

from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.artifact_models import Artifact
from models.chunk_models import Chunk
from services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ArtifactService:
    """Service for artifact operations."""

    async def create_artifact(
        self,
        session: AsyncSession,
        user_id: str,
        artifact_type: str,
        operation: str,
        content: str,
        content_format: str = "markdown",
        source_chunk_ids: Optional[List[str]] = None,
        source_artifact_ids: Optional[List[str]] = None,
        source_operation_params: Optional[Dict[str, Any]] = None,
        parent_artifact_id: Optional[str] = None,
        generation_model: Optional[str] = None,
        generation_prompt: Optional[str] = None,
        topics: Optional[List[str]] = None,
        frameworks: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        auto_embed: bool = True
    ) -> Artifact:
        """
        Create a new artifact with optional auto-embedding.

        Args:
            session: Database session
            user_id: User creating the artifact
            artifact_type: Type of artifact (report, extraction, etc.)
            operation: Operation that created it
            content: The actual content
            content_format: Format of content (markdown, json, etc.)
            source_chunk_ids: Source chunks used
            source_artifact_ids: Source artifacts used
            source_operation_params: Parameters of the operation
            parent_artifact_id: Parent artifact if this is a refinement
            generation_model: Model used to generate
            generation_prompt: Prompt used for generation
            topics: Topics/tags
            frameworks: Frameworks applied
            custom_metadata: Additional metadata
            auto_embed: Whether to generate embedding automatically

        Returns:
            Created Artifact instance
        """
        # Calculate lineage depth
        lineage_depth = 0
        if parent_artifact_id:
            parent_query = select(Artifact).where(Artifact.id == UUID(parent_artifact_id))
            result = await session.execute(parent_query)
            parent = result.scalar_one_or_none()
            if parent:
                lineage_depth = parent.lineage_depth + 1
            else:
                logger.warning(f"Parent artifact {parent_artifact_id} not found")

        # Generate embedding if requested
        content_embedding = None
        if auto_embed and content:
            try:
                embedding_service = EmbeddingService()
                embedding_array = await embedding_service.generate_embedding(content)
                if embedding_array:
                    content_embedding = embedding_array
                    logger.info(f"Generated embedding for artifact (dim={len(embedding_array)})")
                else:
                    logger.warning("Embedding generation returned None")
            except Exception as e:
                logger.warning(f"Failed to generate embedding: {e}")

        # Calculate token count (rough estimate)
        token_count = len(content.split()) if content else 0

        # Create artifact
        artifact = Artifact(
            user_id=UUID(user_id),
            artifact_type=artifact_type,
            operation=operation,
            content=content,
            content_format=content_format,
            content_embedding=content_embedding,
            source_chunk_ids=[UUID(cid) for cid in source_chunk_ids] if source_chunk_ids else None,
            source_artifact_ids=[UUID(aid) for aid in source_artifact_ids] if source_artifact_ids else None,
            source_operation_params=source_operation_params or {},
            parent_artifact_id=UUID(parent_artifact_id) if parent_artifact_id else None,
            lineage_depth=lineage_depth,
            token_count=token_count,
            generation_model=generation_model,
            generation_prompt=generation_prompt,
            topics=topics,
            frameworks=frameworks,
            custom_metadata=custom_metadata or {}
        )

        session.add(artifact)
        await session.commit()
        await session.refresh(artifact)

        logger.info(
            f"Created artifact: type={artifact_type}, operation={operation}, "
            f"lineage_depth={lineage_depth}, tokens={token_count}"
        )

        return artifact

    async def get_artifact(
        self,
        session: AsyncSession,
        artifact_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Artifact]:
        """
        Get artifact by ID.

        Args:
            session: Database session
            artifact_id: Artifact UUID
            user_id: Optional user_id to filter by owner

        Returns:
            Artifact or None
        """
        query = select(Artifact).where(Artifact.id == UUID(artifact_id))

        if user_id:
            query = query.where(Artifact.user_id == UUID(user_id))

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def list_artifacts(
        self,
        session: AsyncSession,
        user_id: str,
        artifact_type: Optional[str] = None,
        operation: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_dir: str = "desc"
    ) -> tuple[List[Artifact], int]:
        """
        List artifacts with filters.

        Args:
            session: Database session
            user_id: User ID to filter
            artifact_type: Filter by type
            operation: Filter by operation
            limit: Max results
            offset: Pagination offset
            order_by: Field to sort by
            order_dir: Sort direction (asc/desc)

        Returns:
            Tuple of (artifacts list, total count)
        """
        # Build query
        query = select(Artifact).where(Artifact.user_id == UUID(user_id))

        if artifact_type:
            query = query.where(Artifact.artifact_type == artifact_type)

        if operation:
            query = query.where(Artifact.operation == operation)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await session.execute(count_query)
        total = count_result.scalar_one()

        # Apply ordering
        order_column = getattr(Artifact, order_by, Artifact.created_at)
        if order_dir == "desc":
            query = query.order_by(order_column.desc())
        else:
            query = query.order_by(order_column.asc())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        artifacts = result.scalars().all()

        return list(artifacts), total

    async def search_artifacts(
        self,
        session: AsyncSession,
        user_id: str,
        query_text: str,
        artifact_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over artifacts.

        Args:
            session: Database session
            user_id: User ID to filter
            query_text: Search query
            artifact_type: Optional type filter
            limit: Max results

        Returns:
            List of artifacts with similarity scores
        """
        # Generate query embedding
        try:
            embedding_service = EmbeddingService()
            query_embedding = await embedding_service.generate_embedding(query_text)
            if not query_embedding:
                logger.error("Query embedding generation returned None")
                return []
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []

        # Convert to string for pgvector
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

        # Build query with vector similarity
        filters = [
            Artifact.user_id == UUID(user_id),
            Artifact.content_embedding.isnot(None)
        ]

        if artifact_type:
            filters.append(Artifact.artifact_type == artifact_type)

        # Semantic search query
        search_query = text(f"""
            SELECT
                artifacts.*,
                1 - (artifacts.content_embedding <=> '{embedding_str}'::vector) as similarity
            FROM artifacts
            WHERE
                user_id = :user_id
                AND content_embedding IS NOT NULL
                {f"AND artifact_type = :artifact_type" if artifact_type else ""}
            ORDER BY artifacts.content_embedding <=> '{embedding_str}'::vector
            LIMIT :limit
        """)

        params = {"user_id": str(UUID(user_id)), "limit": limit}
        if artifact_type:
            params["artifact_type"] = artifact_type

        result = await session.execute(search_query, params)
        rows = result.fetchall()

        # Convert to dicts
        artifacts = []
        for row in rows:
            artifact = await self.get_artifact(session, str(row[0]))
            if artifact:
                artifact_dict = artifact.to_dict()
                artifact_dict["similarity"] = float(row[-1])  # Last column is similarity
                artifacts.append(artifact_dict)

        logger.info(f"Found {len(artifacts)} artifacts matching '{query_text}'")
        return artifacts

    async def get_lineage(
        self,
        session: AsyncSession,
        artifact_id: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get full lineage tree for an artifact.

        Args:
            session: Database session
            artifact_id: Starting artifact
            user_id: Optional user filter

        Returns:
            Lineage tree with ancestors and descendants
        """
        artifact = await self.get_artifact(session, artifact_id, user_id)
        if not artifact:
            return {}

        # Get ancestor chain
        ancestors = []
        current = artifact
        while current.parent_artifact_id:
            parent = await self.get_artifact(session, str(current.parent_artifact_id))
            if not parent:
                break
            ancestors.insert(0, parent.to_dict(include_content=False))
            current = parent

        # Get descendant tree
        descendants = artifact.get_descendant_tree(max_depth=5)

        return {
            "artifact": artifact.to_dict(),
            "ancestors": ancestors,
            "descendants": descendants,
            "lineage_depth": artifact.lineage_depth,
            "total_ancestors": len(ancestors),
            "total_descendants": len(artifact.children)
        }

    async def delete_artifact(
        self,
        session: AsyncSession,
        artifact_id: str,
        user_id: str
    ) -> bool:
        """
        Delete an artifact.

        Args:
            session: Database session
            artifact_id: Artifact to delete
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        artifact = await self.get_artifact(session, artifact_id, user_id)
        if not artifact:
            return False

        await session.delete(artifact)
        await session.commit()

        logger.info(f"Deleted artifact {artifact_id}")
        return True

    async def update_artifact(
        self,
        session: AsyncSession,
        artifact_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Artifact]:
        """
        Update artifact fields.

        Args:
            session: Database session
            artifact_id: Artifact to update
            user_id: User ID (for authorization)
            updates: Fields to update

        Returns:
            Updated artifact or None
        """
        artifact = await self.get_artifact(session, artifact_id, user_id)
        if not artifact:
            return None

        # Update allowed fields
        allowed_fields = [
            'is_approved', 'user_rating', 'user_notes',
            'topics', 'frameworks', 'custom_metadata'
        ]

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(artifact, field, value)

        await session.commit()
        await session.refresh(artifact)

        logger.info(f"Updated artifact {artifact_id}: {list(updates.keys())}")
        return artifact
