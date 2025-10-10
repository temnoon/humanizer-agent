"""
Personifier API Routes

POST /api/personify - Transform AI text to conversational
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from services.personifier_service import get_personifier_service
from services.llm_rewriter import LLMRewriter
from services.artifact_service import ArtifactService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["personifier"])


# Request/Response models
class PersonifyRequest(BaseModel):
    """Request to personify AI text."""

    text: str = Field(..., description="AI-written text to transform")
    strength: float = Field(1.0, ge=0.0, le=2.0, description="Transformation strength (0-2)")
    return_similar: bool = Field(True, description="Include similar conversational examples")
    n_similar: int = Field(5, ge=1, le=20, description="Number of similar examples")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "It's worth noting that this approach can be beneficial. You might want to consider the following factors: ...",
                "strength": 1.0,
                "return_similar": True,
                "n_similar": 5
            }
        }


class PatternDetection(BaseModel):
    """Detected AI writing patterns."""

    hedging: int
    formal_transitions: int
    passive_voice: int
    list_markers: int
    numbered_lists: int
    bullet_points: int


class AIPatterns(BaseModel):
    """AI pattern analysis."""

    patterns: PatternDetection
    total_score: float
    confidence: float
    is_ai_likely: bool


class Suggestion(BaseModel):
    """Transformation suggestion."""

    type: str
    message: str
    count: int


class SimilarChunk(BaseModel):
    """Similar conversational chunk."""

    chunk_id: str
    content: str
    token_count: int
    similarity: float
    metadata: dict


class TransformationInfo(BaseModel):
    """Transformation metadata."""

    vector: str
    strength: float
    original_magnitude: float
    transformed_magnitude: float


class PersonifyResponse(BaseModel):
    """Response from personify endpoint."""

    original_text: str
    ai_patterns: AIPatterns
    transformation: TransformationInfo
    similar_chunks: Optional[list[SimilarChunk]] = None
    suggestions: list[Suggestion]


class RewriteRequest(BaseModel):
    """Request to rewrite text using LLM."""

    text: str = Field(..., description="Text to rewrite")
    strength: float = Field(1.0, ge=0.0, le=2.0, description="Transformation strength (0-2)")
    use_examples: bool = Field(True, description="Use database examples as style guides")
    n_examples: int = Field(3, ge=1, le=5, description="Number of style example chunks")
    save_as_artifact: bool = Field(False, description="Save result as artifact")
    artifact_topics: Optional[List[str]] = Field(None, description="Topics for artifact (if saving)")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "It's worth noting that this approach can be beneficial...",
                "strength": 1.0,
                "use_examples": True,
                "n_examples": 3,
                "save_as_artifact": False
            }
        }


class RewriteResponse(BaseModel):
    """Response from rewrite endpoint."""

    original_text: str
    rewritten_text: str
    ai_patterns: AIPatterns
    similar_examples: Optional[list[SimilarChunk]] = None
    suggestions: list[Suggestion]
    transformation_info: dict
    artifact_id: Optional[str] = None  # Set if saved as artifact


@router.post("/personify", response_model=PersonifyResponse)
async def personify_text(
    request: PersonifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Transform AI-written text to conversational register.

    This endpoint:
    1. Analyzes input text for AI patterns
    2. Generates embedding for the text
    3. Applies "personify" transformation vector
    4. Finds similar conversational examples
    5. Returns transformation suggestions

    **Philosophy**: This transforms linguistic *register* (AI formal → human conversational),
    not ontological category (machine → human). It's honest transformation, not deceptive hiding.

    **Use case**: User pastes GPT/Claude output, receives conversational version + explanation.
    """
    try:
        logger.info(
            f"Personify request: "
            f"{len(request.text)} chars, strength={request.strength}"
        )

        # Validate text length
        if len(request.text) < 50:
            raise HTTPException(
                status_code=400,
                detail="Text too short. Minimum 50 characters required."
            )

        if len(request.text) > 5000:
            raise HTTPException(
                status_code=400,
                detail="Text too long. Maximum 5000 characters allowed."
            )

        # Get service
        service = get_personifier_service()

        # Perform transformation
        result = await service.personify(
            session=db,
            text=request.text,
            strength=request.strength,
            return_similar=request.return_similar,
            n_similar=request.n_similar
        )

        logger.info(
            f"Personification complete: "
            f"confidence={result['ai_patterns']['confidence']}%, "
            f"{len(result.get('similar_chunks', []))} similar chunks"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Personify failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Transformation failed: {str(e)}"
        )


@router.post("/personify/rewrite", response_model=RewriteResponse)
async def rewrite_text(
    request: RewriteRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Rewrite text using LLM-based transformation.

    This endpoint:
    1. Analyzes input text for AI patterns
    2. Uses Claude API to rewrite in conversational style
    3. Optionally uses database examples as style guides
    4. Returns actual rewritten text (not just similar examples)

    **Key difference from /personify**:
    - /personify: Finds similar conversational examples (retrieval)
    - /personify/rewrite: Actually rewrites the text (generation)

    **Use case**: When you need actual transformed text, not just examples.
    Industry-standard "humanization" that maintains meaning while changing style.
    """
    try:
        logger.info(
            f"Rewrite request: "
            f"{len(request.text)} chars, strength={request.strength}, "
            f"use_examples={request.use_examples}"
        )

        # Validate text length
        if len(request.text) < 50:
            raise HTTPException(
                status_code=400,
                detail="Text too short. Minimum 50 characters required."
            )

        if len(request.text) > 5000:
            raise HTTPException(
                status_code=400,
                detail="Text too long. Maximum 5000 characters allowed."
            )

        # Get services
        personifier_service = get_personifier_service()
        rewriter = LLMRewriter()

        # First, analyze patterns and get similar examples (if requested)
        analysis = await personifier_service.personify(
            session=db,
            text=request.text,
            strength=request.strength,
            return_similar=request.use_examples,
            n_similar=request.n_examples
        )

        # Extract pattern information for LLM
        detected_patterns = []
        ai_patterns = analysis['ai_patterns']['patterns']
        for pattern_name, count in ai_patterns.items():
            if count > 0:
                detected_patterns.append({
                    'name': pattern_name.replace('_', ' ').title(),
                    'count': count,
                    'type': pattern_name
                })

        # Rewrite using LLM
        if request.use_examples and analysis.get('similar_chunks'):
            # Use examples as style guides
            rewritten = rewriter.rewrite_with_examples(
                text=request.text,
                detected_patterns=detected_patterns,
                similar_examples=analysis['similar_chunks'],
                strength=request.strength
            )
        else:
            # Pure LLM rewriting based on patterns
            rewritten = rewriter.rewrite_casual(
                text=request.text,
                detected_patterns=detected_patterns,
                strength=request.strength
            )

        logger.info(
            f"Rewrite complete: "
            f"{len(request.text)} chars → {len(rewritten)} chars, "
            f"confidence={analysis['ai_patterns']['confidence']}%"
        )

        # Save as artifact if requested
        artifact_id = None
        if request.save_as_artifact:
            try:
                artifact_service = ArtifactService()

                # Get default user ID
                from config import DEFAULT_USER_ID

                # Prepare topics
                topics = request.artifact_topics or ['personify', 'transformation']

                # Collect detected patterns for metadata
                detected_patterns = [
                    pattern_name.replace('_', ' ').title()
                    for pattern_name, count in analysis['ai_patterns']['patterns'].items()
                    if count > 0
                ]

                artifact = await artifact_service.create_artifact(
                    session=db,
                    user_id=DEFAULT_USER_ID,
                    artifact_type='transformation',
                    operation='personify_rewrite',
                    content=rewritten,
                    content_format='plaintext',
                    source_operation_params={
                        'strength': request.strength,
                        'use_examples': request.use_examples,
                        'detected_patterns': detected_patterns,
                        'original_length': len(request.text),
                        'rewritten_length': len(rewritten)
                    },
                    generation_model='claude-sonnet-4.5',
                    topics=topics,
                    frameworks=['personify', 'conversational'],
                    custom_metadata={
                        'original_text': request.text,
                        'ai_confidence': analysis['ai_patterns']['confidence']
                    },
                    auto_embed=True
                )

                artifact_id = str(artifact.id)
                logger.info(f"Saved transformation as artifact: {artifact_id}")

            except Exception as e:
                logger.error(f"Failed to save artifact: {e}", exc_info=True)
                # Don't fail the request if artifact save fails

        return RewriteResponse(
            original_text=request.text,
            rewritten_text=rewritten,
            ai_patterns=analysis['ai_patterns'],
            similar_examples=analysis.get('similar_chunks'),
            suggestions=analysis['suggestions'],
            transformation_info={
                'method': 'llm_rewriting',
                'strength': request.strength,
                'used_examples': request.use_examples,
                'num_examples': len(analysis.get('similar_chunks', []))
            },
            artifact_id=artifact_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rewrite failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Rewrite failed: {str(e)}"
        )


class FeedbackRequest(BaseModel):
    """Request to submit transformation feedback."""

    transformation_id: str = Field(..., description="Unique ID for this transformation")
    original_text: str = Field(..., description="Original text")
    transformed_text: str = Field(..., description="Transformed text")
    metadata: dict = Field(default_factory=dict, description="Transformation metadata")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Quality rating 1-5")
    comments: list = Field(default_factory=list, description="User/agent comments")
    feedback_type: str = Field("evaluation", description="Type: evaluation, approval, rejection")
    use_for_training: bool = Field(False, description="Use this pair for future training")
    approved: Optional[bool] = Field(None, description="Whether transformation was approved")
    reason: Optional[str] = Field(None, description="Reason for rejection if applicable")


class FeedbackResponse(BaseModel):
    """Response from feedback submission."""

    feedback_id: str
    status: str
    message: str
    saved_for_training: bool


@router.post("/personify/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for a transformation.

    This endpoint:
    1. Stores the feedback for analysis
    2. Optionally adds the pair to training data if approved
    3. Returns confirmation

    **Use case**: After evaluating a transformation with the AUI, save feedback
    to improve future transformations and optionally add to training data.
    """
    try:
        import json
        from pathlib import Path
        from datetime import datetime

        logger.info(
            f"Feedback submission: "
            f"type={request.feedback_type}, rating={request.rating}, "
            f"use_for_training={request.use_for_training}"
        )

        # Generate feedback ID
        feedback_id = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.transformation_id}"

        # Save feedback to file
        feedback_dir = Path(__file__).parent.parent / "data" / "feedback"
        feedback_dir.mkdir(exist_ok=True)

        feedback_data = {
            "feedback_id": feedback_id,
            "transformation_id": request.transformation_id,
            "timestamp": datetime.now().isoformat(),
            "original_text": request.original_text,
            "transformed_text": request.transformed_text,
            "metadata": request.metadata,
            "rating": request.rating,
            "comments": request.comments,
            "feedback_type": request.feedback_type,
            "approved": request.approved,
            "reason": request.reason
        }

        feedback_file = feedback_dir / f"{feedback_id}.json"
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)

        # If approved and use_for_training, add to training data
        saved_for_training = False
        if request.use_for_training and request.approved and request.rating >= 4:
            training_file = Path(__file__).parent.parent / "data" / "curated_style_pairs.jsonl"

            # Create training pair
            training_pair = {
                "before": request.original_text,
                "after": request.transformed_text,
                "category": request.metadata.get("transformationType", "user_approved"),
                "source": "user_evaluation",
                "rating": request.rating,
                "timestamp": datetime.now().isoformat()
            }

            # Append to training file
            with open(training_file, 'a') as f:
                f.write(json.dumps(training_pair) + '\n')

            saved_for_training = True
            logger.info(f"Added to training data: {training_file}")

        logger.info(
            f"Feedback saved: {feedback_id}, "
            f"saved_for_training={saved_for_training}"
        )

        return FeedbackResponse(
            feedback_id=feedback_id,
            status="success",
            message="Feedback saved successfully",
            saved_for_training=saved_for_training
        )

    except Exception as e:
        logger.error(f"Feedback submission failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save feedback: {str(e)}"
        )


@router.get("/personify/health")
async def health_check():
    """
    Check if personifier service is ready.

    Returns:
        Status of Ollama and training data
    """
    try:
        import requests
        from pathlib import Path

        # Check Ollama
        ollama_ok = False
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            ollama_ok = response.status_code == 200
        except:
            pass

        # Check training data
        training_data_path = Path(__file__).parent.parent / "data" / "training_embeddings.json"
        training_data_ok = training_data_path.exists()

        # Check service initialization
        service_ok = False
        try:
            service = get_personifier_service()
            service._ensure_vector_loaded()
            service_ok = True
        except:
            pass

        return {
            "status": "ready" if (ollama_ok and training_data_ok and service_ok) else "degraded",
            "ollama": "ok" if ollama_ok else "unavailable",
            "training_data": "ok" if training_data_ok else "missing",
            "service": "ok" if service_ok else "not_initialized"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
