"""
Background job processor for transformation pipeline.

Handles:
- Transformation job processing
- Embedding generation for chunks
- Lineage tracking
- Progress updates
- Error handling and retries
"""

import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.pipeline_models import TransformationJob, ChunkTransformation, TransformationLineage
from models.chunk_models import Chunk, Message, Collection
from models.db_models import User, Session as DBSession
from services.pipeline_service import PipelineService
from agents.transformation_agent import TransformationAgent
from services.madhyamaka import MadhyamakaDetector, MadhyamakaTransformer
from database import get_db, embedding_service
import logging

logger = logging.getLogger(__name__)


class JobProcessor:
    """Background processor for transformation jobs."""

    def __init__(self):
        self.pipeline_service = PipelineService()
        self.transformation_agent = TransformationAgent()
        self.madhyamaka_detector = MadhyamakaDetector()
        self.madhyamaka_transformer = MadhyamakaTransformer()

    async def process_job(self, job_id: UUID, db: AsyncSession):
        """
        Process a transformation job.

        This is the main entry point for background processing.
        """
        try:
            # Get job
            job = await self.pipeline_service.get_job(db, job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Update status to processing
            job = await self.pipeline_service.update_job_status(db, job_id, "processing")
            logger.info(f"Started processing job {job_id}: {job.name}")

            # Get source chunks
            source_chunk_ids = [
                UUID(cid) for cid in job.configuration.get('source_chunk_ids', [])
            ]

            if not source_chunk_ids:
                raise ValueError("No source chunks specified in job configuration")

            # Process each chunk
            processed = 0
            failed = 0

            for i, chunk_id in enumerate(source_chunk_ids):
                try:
                    # Update current item
                    await self.pipeline_service.update_job_progress(
                        db, job_id,
                        processed_items=processed,
                        failed_items=failed,
                        current_item_id=chunk_id
                    )

                    # Process based on job type
                    if job.job_type == "persona_transform":
                        await self._process_persona_transform(db, job, chunk_id, i)
                    elif job.job_type == "madhyamaka_detect":
                        await self._process_madhyamaka_detect(db, job, chunk_id, i)
                    elif job.job_type == "madhyamaka_transform":
                        await self._process_madhyamaka_transform(db, job, chunk_id, i)
                    elif job.job_type == "perspectives":
                        await self._process_perspectives(db, job, chunk_id, i)
                    else:
                        logger.warning(f"Unknown job type: {job.job_type}")

                    processed += 1

                except Exception as e:
                    logger.error(f"Failed to process chunk {chunk_id}: {e}")
                    failed += 1

                # Update progress
                await self.pipeline_service.update_job_progress(
                    db, job_id,
                    processed_items=processed,
                    failed_items=failed
                )

            # Mark job as completed or failed
            if failed > 0 and processed == 0:
                await self.pipeline_service.update_job_status(
                    db, job_id, "failed",
                    error_message=f"All {failed} items failed to process"
                )
            else:
                await self.pipeline_service.update_job_status(db, job_id, "completed")

            logger.info(f"Completed job {job_id}: {processed} succeeded, {failed} failed")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}", exc_info=True)
            try:
                await self.pipeline_service.update_job_status(
                    db, job_id, "failed",
                    error_message=str(e)
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")

    async def _process_persona_transform(
        self,
        db: AsyncSession,
        job: TransformationJob,
        source_chunk_id: UUID,
        sequence: int
    ):
        """Process PERSONA/NAMESPACE/STYLE transformation."""
        # Get source chunk
        result = await db.execute(select(Chunk).where(Chunk.id == source_chunk_id))
        source_chunk = result.scalar_one_or_none()
        if not source_chunk:
            raise ValueError(f"Source chunk {source_chunk_id} not found")

        # Extract configuration
        config = job.configuration
        persona = config.get('persona', 'neutral')
        namespace = config.get('namespace', 'general')
        style = config.get('style', 'formal')
        depth = config.get('depth', 0.5)
        preserve_structure = config.get('preserve_structure', True)

        # Transform
        start_time = datetime.utcnow()
        result = await self.transformation_agent.transform(
            content=source_chunk.content,
            persona=persona,
            namespace=namespace,
            style=style,
            depth=depth,
            preserve_structure=preserve_structure
        )
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Extract transformed content from dict
        transformed_content = result.get('transformed_content')
        if not transformed_content:
            raise ValueError(f"Transformation failed: {result.get('error', 'Unknown error')}")

        # Create result chunk
        result_chunk = Chunk(
            message_id=source_chunk.message_id,
            collection_id=source_chunk.collection_id,
            user_id=source_chunk.user_id,
            content=transformed_content,
            chunk_level=source_chunk.chunk_level,
            chunk_sequence=source_chunk.chunk_sequence + 1000 + sequence,  # Avoid conflicts
            extra_metadata={
                'transformation_type': 'persona_transform',
                'source_chunk_id': str(source_chunk_id),
                'job_id': str(job.id),
                'persona': persona,
                'namespace': namespace,
                'style': style
            }
        )
        db.add(result_chunk)
        await db.flush()

        # Generate embedding for result chunk
        # TODO: Fix embedding dimension mismatch (1024 vs 1536)
        # Temporarily disabled until embedding service config is fixed
        # if embedding_service:
        #     try:
        #         embedding = await embedding_service.generate_embedding(transformed_content)
        #         result_chunk.embedding = embedding
        #         result_chunk.embedding_model = 'all-MiniLM-L6-v2'
        #         result_chunk.embedding_generated_at = datetime.utcnow()
        #     except Exception as e:
        #         logger.warning(f"Failed to generate embedding: {e}")

        # Calculate tokens used from metadata
        metadata = result.get('metadata', {})
        tokens_used = metadata.get('input_tokens', 0) + metadata.get('output_tokens', 0)

        # Create chunk transformation record
        await self.pipeline_service.create_chunk_transformation(
            db, job.id, source_chunk_id, result_chunk.id,
            transformation_type='persona_transform',
            parameters={'persona': persona, 'namespace': namespace, 'style': style},
            tokens_used=tokens_used,
            processing_time_ms=processing_time,
            sequence_number=sequence
        )

        # Create or update lineage
        await self._create_lineage(
            db, job, source_chunk_id, result_chunk.id,
            transformation_path=[f"persona→{persona}"],
            tokens_used=result.usage.get('total_tokens', 0) if hasattr(result, 'usage') else 0
        )

        await db.commit()

    async def _process_madhyamaka_detect(
        self,
        db: AsyncSession,
        job: TransformationJob,
        source_chunk_id: UUID,
        sequence: int
    ):
        """Process Madhyamaka extremes detection."""
        # Get source chunk
        result = await db.execute(select(Chunk).where(Chunk.id == source_chunk_id))
        source_chunk = result.scalar_one_or_none()
        if not source_chunk:
            raise ValueError(f"Source chunk {source_chunk_id} not found")

        # Detect extremes
        start_time = datetime.utcnow()
        try:
            eternalism = self.madhyamaka_detector.detect_eternalism(source_chunk.content)
            nihilism = self.madhyamaka_detector.detect_nihilism(source_chunk.content)
            middle_path = self.madhyamaka_detector.detect_middle_path_proximity(source_chunk.content)

            detection = {
                'eternalism': eternalism,
                'nihilism': nihilism,
                'middle_path': middle_path
            }
        except Exception as e:
            logger.warning(f"Madhyamaka detection failed: {e}, using simple analysis")
            detection = {'error': str(e)}

        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Create analysis result as chunk
        analysis_content = f"""Madhyamaka Analysis:

{str(detection)}

Source text analyzed: {source_chunk.content[:200]}...
"""

        result_chunk = Chunk(
            message_id=source_chunk.message_id,
            collection_id=source_chunk.collection_id,
            user_id=source_chunk.user_id,
            content=analysis_content,
            chunk_level='document',
            chunk_sequence=source_chunk.chunk_sequence + 1000 + sequence,
            extra_metadata={
                'transformation_type': 'madhyamaka_detect',
                'source_chunk_id': str(source_chunk_id),
                'job_id': str(job.id),
                'detection_result': detection
            }
        )
        db.add(result_chunk)
        await db.flush()

        # Create chunk transformation record
        await self.pipeline_service.create_chunk_transformation(
            db, job.id, source_chunk_id, result_chunk.id,
            transformation_type='madhyamaka_detect',
            parameters={'analysis_depth': job.configuration.get('analysis_depth', 'moderate')},
            tokens_used=0,
            processing_time_ms=processing_time,
            sequence_number=sequence
        )

        # Create lineage
        await self._create_lineage(
            db, job, source_chunk_id, result_chunk.id,
            transformation_path=['madhyamaka_detect'],
            tokens_used=0
        )

        await db.commit()

    async def _process_madhyamaka_transform(
        self,
        db: AsyncSession,
        job: TransformationJob,
        source_chunk_id: UUID,
        sequence: int
    ):
        """Process Madhyamaka transformation toward middle path."""
        # Get source chunk
        result = await db.execute(select(Chunk).where(Chunk.id == source_chunk_id))
        source_chunk = result.scalar_one_or_none()
        if not source_chunk:
            raise ValueError(f"Source chunk {source_chunk_id} not found")

        # Transform toward middle path
        start_time = datetime.utcnow()
        num_alternatives = job.configuration.get('num_alternatives', 5)
        user_stage = job.configuration.get('user_stage', 1)

        # Call the correct method - returns List[Dict[str, Any]]
        alternatives = self.madhyamaka_transformer.generate_middle_path_alternatives(
            source_chunk.content,
            num_alternatives=num_alternatives,
            user_stage=user_stage
        )
        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Create result chunk with alternatives
        result_content = f"# Middle Path Alternatives\n\n**Original Text:**\n{source_chunk.content}\n\n---\n\n"

        for i, alt in enumerate(alternatives, 1):
            result_content += f"## Alternative {i}\n\n"
            result_content += f"{alt['text']}\n\n"

            if alt.get('madhyamaka_improvements'):
                result_content += f"**Improvements:** {', '.join(alt['madhyamaka_improvements'])}\n\n"

            if alt.get('type'):
                result_content += f"**Type:** {alt['type']}\n\n"

            if alt.get('note'):
                result_content += f"*Note: {alt['note']}*\n\n"

            result_content += "---\n\n"

        result_chunk = Chunk(
            message_id=source_chunk.message_id,
            collection_id=source_chunk.collection_id,
            user_id=source_chunk.user_id,
            content=result_content,
            chunk_level='document',
            chunk_sequence=source_chunk.chunk_sequence + 1000 + sequence,
            extra_metadata={
                'transformation_type': 'madhyamaka_transform',
                'source_chunk_id': str(source_chunk_id),
                'job_id': str(job.id),
                'alternatives': [alt['text'] for alt in alternatives],
                'alternatives_full': alternatives,
                'num_alternatives': len(alternatives)
            }
        )
        db.add(result_chunk)
        await db.flush()

        # Create chunk transformation record
        await self.pipeline_service.create_chunk_transformation(
            db, job.id, source_chunk_id, result_chunk.id,
            transformation_type='madhyamaka_transform',
            parameters={'num_alternatives': num_alternatives, 'user_stage': user_stage},
            tokens_used=0,
            processing_time_ms=processing_time,
            sequence_number=sequence
        )

        # Create lineage
        await self._create_lineage(
            db, job, source_chunk_id, result_chunk.id,
            transformation_path=['madhyamaka_transform'],
            tokens_used=0
        )

        await db.commit()

    async def _process_perspectives(
        self,
        db: AsyncSession,
        job: TransformationJob,
        source_chunk_id: UUID,
        sequence: int
    ):
        """Process multi-perspective transformation."""
        # Get source chunk
        result = await db.execute(select(Chunk).where(Chunk.id == source_chunk_id))
        source_chunk = result.scalar_one_or_none()
        if not source_chunk:
            raise ValueError(f"Source chunk {source_chunk_id} not found")

        # Extract configuration
        config = job.configuration
        num_perspectives = config.get('num_perspectives', 3)

        # Generate multiple perspectives using Claude
        start_time = datetime.utcnow()

        # Create a multi-perspective prompt
        perspective_types = [
            "Academic/Scholarly: Analyze from a rigorous theoretical and research-based viewpoint",
            "Practical/Applied: Focus on real-world applications and concrete examples",
            "Critical/Skeptical: Question assumptions and identify potential weaknesses or counterarguments",
            "Historical/Contextual: Place in historical context and trace intellectual lineage",
            "Interdisciplinary: Connect to other fields and draw cross-domain insights"
        ]

        selected_perspectives = perspective_types[:num_perspectives]

        prompt = f"""Analyze the following text from {num_perspectives} different perspectives. For each perspective, provide a substantive analysis (2-3 paragraphs).

TEXT:
{source_chunk.content}

Please provide your analysis in the following format:

## Perspective 1: {selected_perspectives[0] if len(selected_perspectives) > 0 else 'General Analysis'}
[Your analysis here]

## Perspective 2: {selected_perspectives[1] if len(selected_perspectives) > 1 else 'Alternative View'}
[Your analysis here]

{f"## Perspective 3: {selected_perspectives[2]}" if len(selected_perspectives) > 2 else ""}
{f"[Your analysis here]" if len(selected_perspectives) > 2 else ""}

{f"## Perspective 4: {selected_perspectives[3]}" if len(selected_perspectives) > 3 else ""}
{f"[Your analysis here]" if len(selected_perspectives) > 3 else ""}

{f"## Perspective 5: {selected_perspectives[4]}" if len(selected_perspectives) > 4 else ""}
{f"[Your analysis here]" if len(selected_perspectives) > 4 else ""}
"""

        # Use transformation agent with neutral settings for analysis
        result = await self.transformation_agent.transform(
            content=prompt,
            persona='analytical scholar',
            namespace='multi-perspective analysis',
            style='academic',
            depth=0.7,
            preserve_structure=True
        )

        processing_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Extract transformed content
        transformed_content = result.get('transformed_content')
        if not transformed_content:
            raise ValueError(f"Perspective generation failed: {result.get('error', 'Unknown error')}")

        # Create result chunk
        result_chunk = Chunk(
            message_id=source_chunk.message_id,
            collection_id=source_chunk.collection_id,
            user_id=source_chunk.user_id,
            content=transformed_content,
            chunk_level='document',
            chunk_sequence=source_chunk.chunk_sequence + 1000 + sequence,
            extra_metadata={
                'transformation_type': 'perspectives',
                'source_chunk_id': str(source_chunk_id),
                'job_id': str(job.id),
                'num_perspectives': num_perspectives,
                'perspective_types': selected_perspectives
            }
        )
        db.add(result_chunk)
        await db.flush()

        # Calculate tokens used from metadata
        metadata = result.get('metadata', {})
        tokens_used = metadata.get('input_tokens', 0) + metadata.get('output_tokens', 0)

        await self.pipeline_service.create_chunk_transformation(
            db, job.id, source_chunk_id, result_chunk.id,
            transformation_type='perspectives',
            parameters={'num_perspectives': num_perspectives},
            tokens_used=tokens_used,
            processing_time_ms=processing_time,
            sequence_number=sequence
        )

        # Create lineage
        await self._create_lineage(
            db, job, source_chunk_id, result_chunk.id,
            transformation_path=[f"perspectives×{num_perspectives}"],
            tokens_used=tokens_used
        )

        await db.commit()

    async def _create_lineage(
        self,
        db: AsyncSession,
        job: TransformationJob,
        source_chunk_id: UUID,
        result_chunk_id: UUID,
        transformation_path: List[str],
        tokens_used: int
    ):
        """Create or update transformation lineage."""
        # Get source chunk's lineage to determine root and generation
        result = await db.execute(
            select(TransformationLineage)
            .where(TransformationLineage.chunk_id == source_chunk_id)
        )
        source_lineage = result.scalar_one_or_none()

        if source_lineage:
            # This is a transformation of an already-transformed chunk
            root_chunk_id = source_lineage.root_chunk_id
            generation = source_lineage.generation + 1
            parent_lineage_id = source_lineage.id
            full_path = source_lineage.transformation_path + transformation_path
        else:
            # This is the first transformation of an original chunk
            root_chunk_id = source_chunk_id
            generation = 1
            parent_lineage_id = None
            full_path = transformation_path

            # Create lineage for the source (generation 0)
            source_lineage = TransformationLineage(
                root_chunk_id=root_chunk_id,
                chunk_id=source_chunk_id,
                generation=0,
                transformation_path=[],
                session_ids=[job.session_id] if job.session_id else [],
                job_ids=[],
                depth=0
            )
            db.add(source_lineage)
            await db.flush()
            parent_lineage_id = source_lineage.id

        # Create lineage for result chunk
        await self.pipeline_service.create_or_update_lineage(
            db,
            root_chunk_id=root_chunk_id,
            chunk_id=result_chunk_id,
            parent_lineage_id=parent_lineage_id,
            generation=generation,
            transformation_path=full_path,
            session_id=job.session_id if job.session_id else None,
            job_id=job.id,
            tokens_used=tokens_used
        )


# Singleton processor instance
job_processor = JobProcessor()


async def process_transformation_job(job_id: UUID):
    """
    Background task to process a transformation job.

    This function is called by FastAPI BackgroundTasks.
    """
    async for db in get_db():
        try:
            await job_processor.process_job(job_id, db)
        except Exception as e:
            logger.error(f"Background processing failed for job {job_id}: {e}", exc_info=True)
        finally:
            await db.close()
