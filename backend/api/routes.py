"""API routes for transformation operations."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import uuid
from datetime import datetime

from models.schemas import (
    TransformationRequest,
    TransformationResponse,
    TransformationStatus,
    TransformationResult,
    CheckpointCreate,
    CheckpointResponse,
    RollbackRequest,
    TransformationStatusEnum,
    ErrorResponse
)
from agents.transformation_agent import TransformationAgent
from utils.storage import TransformationStorage
from utils.token_utils import (
    check_token_limit,
    should_chunk,
    TokenCounter,
    TextChunker
)

router = APIRouter(prefix="/api", tags=["transformations"])

# Initialize agent and storage
agent = TransformationAgent()
storage = TransformationStorage()


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify agent and storage work."""
    try:
        # Test storage
        test_id = "test-123"
        await storage.create_transformation(
            id=test_id,
            original_content="test",
            persona="test",
            namespace="test",
            style="casual",
            depth=0.5,
            preserve_structure=True
        )
        
        # Test agent
        agent_info = {
            "model": agent.model,
            "has_client": agent.client is not None,
        }
        
        # Clean up test
        await storage.delete_transformation(test_id)
        
        return {
            "storage": "ok",
            "agent": agent_info,
            "message": "All systems operational"
        }
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/check-tokens")
async def check_document_tokens(request: dict):
    """
    Check if document is within token limits for the user's tier.
    
    Returns token count, limits, and whether chunking is needed.
    """
    try:
        content = request.get("content", "")
        tier = request.get("user_tier", "free")
        
        # Check input token limit
        is_within, token_count, limit, message = check_token_limit(
            content, tier, "input"
        )
        
        # Check if chunking is needed (premium only)
        needs_chunking, _, num_chunks = should_chunk(content, tier)
        
        counter = TokenCounter()
        word_estimate = counter.estimate_words(token_count)
        
        return {
            "token_count": token_count,
            "word_estimate": word_estimate,
            "token_limit": limit,
            "is_within_limit": is_within,
            "message": message,
            "needs_chunking": needs_chunking,
            "num_chunks": num_chunks if needs_chunking else 1,
            "tier": tier
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Token check failed: {str(e)}"
        )


@router.post("/transform", response_model=TransformationResponse)
async def create_transformation(
    request: TransformationRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new narrative transformation.
    
    The transformation runs in the background and can be monitored
    via the status endpoint.
    """
    try:
        # Check token limits
        is_within, token_count, limit, message = check_token_limit(
            request.content, request.user_tier, "input"
        )
        
        if not is_within:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Document exceeds token limit",
                    "message": message,
                    "token_count": token_count,
                    "token_limit": limit,
                    "tier": request.user_tier
                }
            )
        
        # Generate transformation ID
        transformation_id = str(uuid.uuid4())
        
        # Check if chunking is needed
        needs_chunking, _, num_chunks = should_chunk(
            request.content, 
            request.user_tier
        )
        
        # Store initial transformation record
        await storage.create_transformation(
            id=transformation_id,
            original_content=request.content,
            persona=request.persona,
            namespace=request.namespace,
            style=request.style.value,
            depth=request.depth,
            preserve_structure=request.preserve_structure
        )
        
        # Start transformation in background
        if needs_chunking:
            background_tasks.add_task(
                process_transformation_chunked,
                transformation_id=transformation_id,
                request=request,
                num_chunks=num_chunks
            )
            message_text = f"Transformation started (processing in {num_chunks} chunks)"
        else:
            background_tasks.add_task(
                process_transformation,
                transformation_id=transformation_id,
                request=request
            )
            message_text = "Transformation started successfully"
        
        return TransformationResponse(
            id=transformation_id,
            status=TransformationStatusEnum.PENDING,
            created_at=datetime.utcnow(),
            message=message_text
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in create_transformation: {e}")
        print(error_details)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create transformation: {str(e)}"
        )


async def process_transformation(
    transformation_id: str,
    request: TransformationRequest
):
    """Background task to process transformation."""
    try:
        # Update status to processing
        await storage.update_status(
            transformation_id,
            TransformationStatusEnum.PROCESSING,
            progress=0.1
        )
        
        # Perform transformation
        result = await agent.transform(
            content=request.content,
            persona=request.persona,
            namespace=request.namespace,
            style=request.style.value,
            depth=request.depth,
            preserve_structure=request.preserve_structure,
            transformation_id=transformation_id
        )
        
        if result["success"]:
            # Store transformed content
            await storage.update_transformation(
                transformation_id,
                transformed_content=result["transformed_content"],
                status=TransformationStatusEnum.COMPLETED,
                progress=1.0,
                metadata=result["metadata"]
            )
        else:
            # Store error
            await storage.update_status(
                transformation_id,
                TransformationStatusEnum.FAILED,
                error=result["error"]
            )
            
    except Exception as e:
        # Handle unexpected errors
        await storage.update_status(
            transformation_id,
            TransformationStatusEnum.FAILED,
            error=str(e)
        )


async def process_transformation_chunked(
    transformation_id: str,
    request: TransformationRequest,
    num_chunks: int
):
    """
    Background task to process transformation with chunking.
    
    This splits long documents into chunks, transforms each,
    then reassembles them into a cohesive whole.
    """
    try:
        # Update status to processing
        await storage.update_status(
            transformation_id,
            TransformationStatusEnum.PROCESSING,
            progress=0.05
        )
        
        # Create chunker
        chunker = TextChunker()
        
        # Split text into chunks (preserving paragraphs when possible)
        if request.preserve_structure:
            chunks = chunker.split_by_paragraphs(
                request.content, 
                chunker.chunk_size
            )
        else:
            chunk_tuples = chunker.chunk_text(request.content)
            chunks = [chunk_text for chunk_text, _, _ in chunk_tuples]
        
        transformed_chunks = []
        total_chunks = len(chunks)
        
        # Transform each chunk
        for i, chunk in enumerate(chunks):
            # Update progress
            progress = 0.1 + (0.8 * (i / total_chunks))
            await storage.update_status(
                transformation_id,
                TransformationStatusEnum.PROCESSING,
                progress=progress
            )
            
            # Transform chunk
            result = await agent.transform(
                content=chunk,
                persona=request.persona,
                namespace=request.namespace,
                style=request.style.value,
                depth=request.depth,
                preserve_structure=request.preserve_structure,
                transformation_id=f"{transformation_id}_chunk_{i}"
            )
            
            if result["success"]:
                transformed_chunks.append(result["transformed_content"])
            else:
                # If any chunk fails, fail the whole transformation
                await storage.update_status(
                    transformation_id,
                    TransformationStatusEnum.FAILED,
                    error=f"Chunk {i+1}/{total_chunks} failed: {result.get('error', 'Unknown error')}"
                )
                return
        
        # Reassemble chunks
        if request.preserve_structure:
            # Use double newline to preserve paragraph structure
            final_content = "\n\n".join(transformed_chunks)
        else:
            # Use single space for smoother flow
            final_content = " ".join(transformed_chunks)
        
        # Store final result
        await storage.update_transformation(
            transformation_id,
            transformed_content=final_content,
            status=TransformationStatusEnum.COMPLETED,
            progress=1.0,
            metadata={
                "chunks_processed": total_chunks,
                "chunking_enabled": True
            }
        )
            
    except Exception as e:
        # Handle unexpected errors
        await storage.update_status(
            transformation_id,
            TransformationStatusEnum.FAILED,
            error=f"Chunked transformation failed: {str(e)}"
        )


@router.get("/transform/{transformation_id}", response_model=TransformationStatus)
async def get_transformation_status(transformation_id: str):
    """
    Get the status of a transformation job.
    
    Returns current progress, status, and any available results.
    """
    transformation = await storage.get_transformation(transformation_id)
    
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    return transformation


@router.get("/transform/{transformation_id}/result", response_model=TransformationResult)
async def get_transformation_result(transformation_id: str):
    """
    Get the final result of a completed transformation.
    
    Only available for completed transformations.
    """
    transformation = await storage.get_transformation(transformation_id)
    
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    if transformation.status != TransformationStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Transformation is not complete (status: {transformation.status})"
        )
    
    return TransformationResult(
        id=transformation.id,
        original_content=transformation.original_content,
        transformed_content=transformation.transformed_content,
        persona=transformation.persona,
        namespace=transformation.namespace,
        style=transformation.style,
        metadata={},
        completed_at=transformation.completed_at
    )


@router.get("/history", response_model=List[TransformationStatus])
async def get_transformation_history(
    limit: int = 50,
    offset: int = 0
):
    """
    Get transformation history.
    
    Returns a list of recent transformations with their status.
    """
    transformations = await storage.get_all_transformations(limit=limit, offset=offset)
    return transformations


@router.post("/transform/{transformation_id}/checkpoint", response_model=CheckpointResponse)
async def create_checkpoint(
    transformation_id: str,
    checkpoint: CheckpointCreate
):
    """
    Create a checkpoint for the current transformation state.
    
    Allows rolling back to this point later if needed.
    """
    transformation = await storage.get_transformation(transformation_id)
    
    if not transformation:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    # Use transformed content if available, otherwise original
    content = transformation.transformed_content or transformation.original_content
    
    result = await agent.create_checkpoint(
        transformation_id=transformation_id,
        current_content=content,
        checkpoint_name=checkpoint.name
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create checkpoint"))
    
    return CheckpointResponse(
        checkpoint_id=result["checkpoint_id"],
        name=result["name"],
        created_at=datetime.utcnow(),
        message="Checkpoint created successfully"
    )


@router.post("/transform/{transformation_id}/rollback")
async def rollback_transformation(
    transformation_id: str,
    rollback: RollbackRequest
):
    """
    Rollback to a previous checkpoint.
    
    Restores the transformation state to the specified checkpoint.
    """
    result = await agent.rollback_to_checkpoint(
        transformation_id=transformation_id,
        checkpoint_id=rollback.checkpoint_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Rollback failed"))
    
    # Update transformation with rolled back content
    await storage.update_transformation(
        transformation_id,
        transformed_content=result["content"],
        status=TransformationStatusEnum.CHECKPOINTED
    )
    
    return {
        "success": True,
        "message": f"Rolled back to checkpoint: {result['checkpoint_name']}",
        "checkpoint_name": result["checkpoint_name"]
    }


@router.delete("/transform/{transformation_id}")
async def delete_transformation(transformation_id: str):
    """
    Delete a transformation and all associated data.
    """
    success = await storage.delete_transformation(transformation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Transformation not found")
    
    return {"success": True, "message": "Transformation deleted"}


@router.post("/analyze")
async def analyze_content(content: str):
    """
    Analyze content to extract its inherent characteristics.
    
    Useful for understanding current persona/namespace/style before transformation.
    """
    analysis = await agent.analyze_content(content)
    
    if "error" in analysis:
        raise HTTPException(status_code=500, detail=analysis["error"])
    
    return analysis
