"""
Pipeline service for transformation job management.

Handles:
- Job creation and configuration
- Batch transformation processing
- Lineage and provenance queries
- Graph generation for visualization
"""

from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.pipeline_models import (
    TransformationJob, ChunkTransformation, TransformationLineage,
    JobStatus, JobType
)
from models.chunk_models import Chunk, Collection, Message, ChunkRelationship
from models.db_models import User, Session as DBSession
from models.pipeline_schemas import (
    JobCreateRequest, TransformationConfig,
    GraphNode, GraphEdge, TransformationGraph
)


class PipelineService:
    """Service for transformation pipeline operations."""

    async def create_job(
        self,
        db: AsyncSession,
        user_id: UUID,
        request: JobCreateRequest
    ) -> TransformationJob:
        """
        Create a new transformation job.

        Resolves source chunks from chunk_ids, message_ids, or collection_id.
        """
        # Resolve source chunks
        source_chunk_ids = []

        if request.source_chunk_ids:
            source_chunk_ids.extend(request.source_chunk_ids)

        if request.source_message_ids:
            # Get all chunks from specified messages
            result = await db.execute(
                select(Chunk.id)
                .where(Chunk.message_id.in_(request.source_message_ids))
            )
            message_chunk_ids = [row[0] for row in result.fetchall()]
            source_chunk_ids.extend(message_chunk_ids)

        if request.source_collection_id:
            # Get all chunks from collection
            result = await db.execute(
                select(Chunk.id)
                .where(Chunk.collection_id == request.source_collection_id)
            )
            collection_chunk_ids = [row[0] for row in result.fetchall()]
            source_chunk_ids.extend(collection_chunk_ids)

        # Remove duplicates
        source_chunk_ids = list(set(source_chunk_ids))

        if not source_chunk_ids:
            raise ValueError("No chunks found for specified sources")

        # Create job configuration
        config = request.configuration.model_dump()
        config['source_chunk_ids'] = [str(cid) for cid in source_chunk_ids]
        if request.source_message_ids:
            config['source_message_ids'] = [str(mid) for mid in request.source_message_ids]
        if request.source_collection_id:
            config['source_collection_id'] = str(request.source_collection_id)

        # Create job
        job = TransformationJob(
            user_id=user_id,
            session_id=request.session_id,
            name=request.name,
            description=request.description,
            job_type=request.job_type,
            status=JobStatus.PENDING,
            total_items=len(source_chunk_ids),
            configuration=config,
            priority=request.priority
        )

        db.add(job)
        await db.commit()
        await db.refresh(job)

        return job

    async def get_job(
        self,
        db: AsyncSession,
        job_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[TransformationJob]:
        """Get job by ID with optional user filter."""
        query = select(TransformationJob).where(TransformationJob.id == job_id)

        if user_id:
            query = query.where(TransformationJob.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        db: AsyncSession,
        user_id: UUID,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[TransformationJob], int]:
        """List jobs with filters and pagination."""
        query = select(TransformationJob).where(TransformationJob.user_id == user_id)

        if status:
            query = query.where(TransformationJob.status == status)

        if job_type:
            query = query.where(TransformationJob.job_type == job_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # Get paginated results
        query = query.order_by(TransformationJob.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        jobs = result.scalars().all()

        return list(jobs), total

    async def update_job_status(
        self,
        db: AsyncSession,
        job_id: UUID,
        status: JobStatus,
        error_message: Optional[str] = None
    ) -> TransformationJob:
        """Update job status."""
        job = await self.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.status = status

        if status == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow()

        if status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.utcnow()

        if error_message:
            job.error_message = error_message
            job.error_count = (job.error_count or 0) + 1

        await db.commit()
        await db.refresh(job)

        return job

    async def update_job_progress(
        self,
        db: AsyncSession,
        job_id: UUID,
        processed_items: int,
        failed_items: int = 0,
        current_item_id: Optional[UUID] = None
    ) -> TransformationJob:
        """Update job progress."""
        job = await self.get_job(db, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        job.processed_items = processed_items
        job.failed_items = failed_items
        job.current_item_id = current_item_id

        if job.total_items > 0:
            job.progress_percentage = (processed_items / job.total_items) * 100

        await db.commit()
        await db.refresh(job)

        return job

    async def create_chunk_transformation(
        self,
        db: AsyncSession,
        job_id: UUID,
        source_chunk_id: UUID,
        result_chunk_id: UUID,
        transformation_type: str,
        parameters: Dict[str, Any],
        tokens_used: int = 0,
        processing_time_ms: int = 0,
        sequence_number: Optional[int] = None
    ) -> ChunkTransformation:
        """Create a chunk transformation record."""
        chunk_trans = ChunkTransformation(
            job_id=job_id,
            source_chunk_id=source_chunk_id,
            result_chunk_id=result_chunk_id,
            transformation_type=transformation_type,
            parameters=parameters,
            status="completed",
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
            sequence_number=sequence_number,
            completed_at=datetime.utcnow()
        )

        db.add(chunk_trans)

        # Also create a ChunkRelationship for graph queries
        relationship = ChunkRelationship(
            source_chunk_id=source_chunk_id,
            target_chunk_id=result_chunk_id,
            relationship_type="transforms_into",
            extra_metadata={
                "job_id": str(job_id),
                "transformation_type": transformation_type,
                "parameters": parameters
            }
        )

        db.add(relationship)
        await db.commit()
        await db.refresh(chunk_trans)

        return chunk_trans

    async def create_or_update_lineage(
        self,
        db: AsyncSession,
        root_chunk_id: UUID,
        chunk_id: UUID,
        parent_lineage_id: Optional[UUID],
        generation: int,
        transformation_path: List[str],
        session_id: UUID,
        job_id: UUID,
        tokens_used: int = 0
    ) -> TransformationLineage:
        """Create or update transformation lineage."""
        # Check if lineage already exists for this chunk
        result = await db.execute(
            select(TransformationLineage)
            .where(TransformationLineage.chunk_id == chunk_id)
        )
        lineage = result.scalar_one_or_none()

        if lineage:
            # Update existing
            if session_id not in lineage.session_ids:
                lineage.session_ids.append(session_id)
            if job_id not in lineage.job_ids:
                lineage.job_ids.append(job_id)
            lineage.total_transformations += 1
            lineage.total_tokens_used += tokens_used
        else:
            # Create new
            lineage = TransformationLineage(
                root_chunk_id=root_chunk_id,
                chunk_id=chunk_id,
                parent_lineage_id=parent_lineage_id,
                generation=generation,
                transformation_path=transformation_path,
                session_ids=[session_id] if session_id else [],
                job_ids=[job_id] if job_id else [],
                depth=generation,
                total_transformations=1,
                total_tokens_used=tokens_used
            )
            db.add(lineage)

        await db.commit()
        await db.refresh(lineage)

        return lineage

    async def get_lineage(
        self,
        db: AsyncSession,
        chunk_id: UUID
    ) -> Dict[str, Any]:
        """Get full transformation lineage for a chunk."""
        # Get the chunk's lineage record
        result = await db.execute(
            select(TransformationLineage)
            .where(TransformationLineage.chunk_id == chunk_id)
        )
        current_lineage = result.scalar_one_or_none()

        if not current_lineage:
            return {
                "chunk_id": chunk_id,
                "ancestors": [],
                "descendants": [],
                "root_chunk_id": chunk_id,
                "total_generations": 0
            }

        # Get all lineage nodes for this root
        result = await db.execute(
            select(TransformationLineage)
            .where(TransformationLineage.root_chunk_id == current_lineage.root_chunk_id)
            .order_by(TransformationLineage.generation)
        )
        all_lineage = result.scalars().all()

        # Separate ancestors and descendants
        ancestors = [l for l in all_lineage if l.generation < current_lineage.generation]
        descendants = [l for l in all_lineage if l.generation > current_lineage.generation]

        max_generation = max([l.generation for l in all_lineage]) if all_lineage else 0

        return {
            "chunk_id": chunk_id,
            "ancestors": [l.to_dict() for l in ancestors],
            "descendants": [l.to_dict() for l in descendants],
            "root_chunk_id": current_lineage.root_chunk_id,
            "total_generations": max_generation + 1
        }

    async def get_transformation_graph(
        self,
        db: AsyncSession,
        root_chunk_id: UUID,
        include_content: bool = False
    ) -> TransformationGraph:
        """Generate transformation graph for visualization."""
        # Get all lineage nodes for this root
        result = await db.execute(
            select(TransformationLineage)
            .options(selectinload(TransformationLineage.chunk))
            .where(TransformationLineage.root_chunk_id == root_chunk_id)
            .order_by(TransformationLineage.generation)
        )
        lineage_nodes = result.scalars().all()

        # Build nodes
        nodes = []
        for lineage in lineage_nodes:
            chunk = lineage.chunk
            content = chunk.content if include_content else ""
            content_preview = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content

            # Determine transformation type from path
            trans_type = lineage.transformation_path[-1] if lineage.transformation_path else "original"

            node = GraphNode(
                id=lineage.id,
                chunk_id=chunk.id,
                content=content,
                content_preview=content_preview,
                generation=lineage.generation,
                transformation_type=trans_type if trans_type != "original" else None,
                metadata=lineage.extra_metadata or {},
                node_type="transformation" if lineage.generation > 0 else "original"
            )
            nodes.append(node)

        # Build edges
        edges = []
        for lineage in lineage_nodes:
            if lineage.parent_lineage_id:
                edge_type = lineage.transformation_path[-1] if lineage.transformation_path else "transforms_into"

                edge = GraphEdge(
                    source=lineage.parent_lineage_id,
                    target=lineage.id,
                    relationship_type=edge_type,
                    label=edge_type.replace("_", " ").title()
                )
                edges.append(edge)

        max_generation = max([l.generation for l in lineage_nodes]) if lineage_nodes else 0

        return TransformationGraph(
            root_chunk_id=root_chunk_id,
            nodes=nodes,
            edges=edges,
            metadata={
                "root_chunk_id": str(root_chunk_id),
                "sessions": list(set([str(sid) for l in lineage_nodes for sid in (l.session_ids or [])])),
                "jobs": list(set([str(jid) for l in lineage_nodes for jid in (l.job_ids or [])]))
            },
            total_nodes=len(nodes),
            total_edges=len(edges),
            max_generation=max_generation,
            total_transformations=sum([l.total_transformations for l in lineage_nodes])
        )

    async def get_session_graph(
        self,
        db: AsyncSession,
        session_id: UUID,
        include_content: bool = False,
        max_generation: Optional[int] = None
    ) -> List[TransformationGraph]:
        """Get all transformation graphs for a session."""
        # Find all lineage nodes that include this session
        result = await db.execute(
            select(TransformationLineage.root_chunk_id)
            .where(TransformationLineage.session_ids.contains([session_id]))
            .distinct()
        )
        root_chunk_ids = [row[0] for row in result.fetchall()]

        graphs = []
        for root_id in root_chunk_ids:
            graph = await self.get_transformation_graph(db, root_id, include_content)

            # Filter by max_generation if specified
            if max_generation is not None:
                graph.nodes = [n for n in graph.nodes if n.generation <= max_generation]
                # Update edges to only include those with both nodes present
                node_ids = set([n.id for n in graph.nodes])
                graph.edges = [e for e in graph.edges if e.source in node_ids and e.target in node_ids]
                graph.total_nodes = len(graph.nodes)
                graph.total_edges = len(graph.edges)

            graphs.append(graph)

        return graphs

    async def get_collection_graph(
        self,
        db: AsyncSession,
        collection_id: UUID,
        include_content: bool = False,
        max_generation: Optional[int] = None,
        filter_by_job_type: Optional[JobType] = None
    ) -> List[TransformationGraph]:
        """Get all transformation graphs for a collection."""
        # Get all chunks in collection
        result = await db.execute(
            select(Chunk.id)
            .where(Chunk.collection_id == collection_id)
        )
        chunk_ids = [row[0] for row in result.fetchall()]

        # Find all lineage root chunks for these chunks
        result = await db.execute(
            select(TransformationLineage.root_chunk_id)
            .where(TransformationLineage.chunk_id.in_(chunk_ids))
            .distinct()
        )
        root_chunk_ids = [row[0] for row in result.fetchall()]

        graphs = []
        for root_id in root_chunk_ids:
            graph = await self.get_transformation_graph(db, root_id, include_content)

            # Filter by job type if specified
            if filter_by_job_type:
                # Get jobs of this type
                result = await db.execute(
                    select(TransformationJob.id)
                    .where(TransformationJob.job_type == filter_by_job_type)
                )
                job_ids = set([str(row[0]) for row in result.fetchall()])

                # Filter nodes that are part of these jobs
                # This is complex - for now, skip filtering by job type
                pass

            # Filter by max_generation if specified
            if max_generation is not None:
                graph.nodes = [n for n in graph.nodes if n.generation <= max_generation]
                node_ids = set([n.id for n in graph.nodes])
                graph.edges = [e for e in graph.edges if e.source in node_ids and e.target in node_ids]
                graph.total_nodes = len(graph.nodes)
                graph.total_edges = len(graph.edges)

            graphs.append(graph)

        return graphs
