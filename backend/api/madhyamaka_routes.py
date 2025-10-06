"""
Madhyamaka API Routes - Middle Path Endpoints

RESTful API for Nagarjuna's Madhyamaka philosophy integration.

Endpoints:
- Detection: /api/madhyamaka/detect/*
- Transformation: /api/madhyamaka/transform/*
- Contemplation: /api/madhyamaka/contemplate/*
- Teaching: /api/madhyamaka/teach/*
- Measurement: /api/madhyamaka/measure/*
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.madhyamaka import (
    MadhyamakaDetector,
    MadhyamakaTransformer,
    ContemplativePracticeGenerator,
    NarrativeAnalyzer,
    NAGARJUNA_TEACHINGS
)

# Create router
router = APIRouter(prefix="/api/madhyamaka", tags=["madhyamaka"])

# Initialize services
detector = MadhyamakaDetector()
transformer = MadhyamakaTransformer()
contemplative = ContemplativePracticeGenerator()
narrative_analyzer = NarrativeAnalyzer()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class DetectionRequest(BaseModel):
    """Request for detecting extremes in text"""
    content: str = Field(..., description="Text to analyze")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")


class TransformRequest(BaseModel):
    """Request for transforming text toward middle path"""
    content: str = Field(..., description="Text to transform")
    num_alternatives: int = Field(default=5, ge=1, le=10, description="Number of alternatives")
    user_stage: int = Field(default=1, ge=1, le=5, description="User journey stage")


class ContemplationRequest(BaseModel):
    """Request for generating contemplative practice"""
    exercise_type: str = Field(..., description="Type: neti_neti, two_truths, dependent_origination")
    target_concept: Optional[str] = Field(default="self", description="Concept to investigate")
    phenomenon: Optional[str] = Field(default=None, description="Phenomenon for two truths")
    starting_point: Optional[str] = Field(default=None, description="Starting point for dependent origination")
    user_stage: int = Field(default=3, ge=1, le=5)
    depth: str = Field(default="progressive", description="simple, progressive, or deep")


class ClingingDetectionRequest(BaseModel):
    """Request for detecting clinging patterns"""
    conversation_history: List[Dict[str, str]] = Field(..., description="List of messages with role and content")
    analysis_depth: str = Field(default="moderate", description="moderate or deep")


class TeachingRequest(BaseModel):
    """Request for Nagarjuna teaching"""
    user_state: Dict[str, Any] = Field(..., description="Current user state and detected extremes")


class NarrativeAnalysisRequest(BaseModel):
    """Request for narrative analysis"""
    text: str = Field(..., description="Narrative text to analyze")
    primary_metric: str = Field(default="middle_path", description="Primary metric: middle_path, eternalism, or nihilism")


# ============================================================================
# DETECTION ENDPOINTS
# ============================================================================

@router.post("/detect/eternalism")
async def detect_eternalism(request: DetectionRequest) -> Dict[str, Any]:
    """
    Detect reification and absolutist language (eternalism).

    Identifies when user is treating language/beliefs as having inherent,
    fixed existence.

    Returns:
        Detection results with confidence, indicators, and middle path alternatives
    """
    try:
        result = detector.detect_eternalism(request.content)

        # Add middle path alternatives if eternalism detected
        if result["eternalism_detected"]:
            alternatives = transformer.generate_middle_path_alternatives(
                request.content,
                num_alternatives=3,
                user_stage=request.context.get("user_stage", 1) if request.context else 1
            )
            result["middle_path_alternatives"] = [
                {
                    "suggestion": alt["type"],
                    "reframed": alt["text"]
                }
                for alt in alternatives[:3]
            ]

            # Add teaching moment
            result["teaching_moment"] = {
                "principle": "dependent_origination",
                "guidance": "Notice how the meaning arises dependent on cultural conditioning, personal values, and temporal context. It has no inherent essence separate from these conditions."
            }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect/nihilism")
async def detect_nihilism(request: DetectionRequest) -> Dict[str, Any]:
    """
    Detect denial of conventional truth or misunderstanding of emptiness (nihilism).

    Identifies when user is rejecting all meaning/value or confusing
    emptiness with nothingness.

    Returns:
        Detection results with confidence, indicators, and corrective guidance
    """
    try:
        result = detector.detect_nihilism(request.content)

        # Add middle path alternatives if nihilism detected
        if result["nihilism_detected"]:
            result["middle_path_alternatives"] = [
                {
                    "suggestion": "two_truths_framework",
                    "reframed": "While language lacks inherent meaning (ultimate truth), it functions conventionally to coordinate action and share experience."
                },
                {
                    "suggestion": "emptiness_as_openness",
                    "reframed": "Language being empty of fixed meaning is what allows it to be flexible, contextual, and useful."
                }
            ]

            # Add teaching moment
            result["teaching_moment"] = {
                "principle": "two_truths",
                "guidance": "Nagarjuna teaches that emptiness doesn't mean non-existence. Language is empty of inherent meaning AND it works conventionally. Both truths are valid simultaneously."
            }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect/middle-path-proximity")
async def detect_middle_path_proximity(request: DetectionRequest) -> Dict[str, Any]:
    """
    Measure how close user's language is to middle path understanding.

    Returns score (0-1) and analysis of what's working and areas for growth.

    Returns:
        Middle path proximity analysis
    """
    try:
        result = detector.detect_middle_path_proximity(request.content)

        # Add next teachings suggestions if user is close
        if result["middle_path_score"] > 0.7:
            result["next_teachings"] = [
                {
                    "principle": "no_self_in_phenomena",
                    "description": "Extend emptiness understanding to the subject/observer",
                    "exercise": "witness_the_witness"
                }
            ]

            result["celebration"] = "This demonstrates sophisticated understanding of emptiness while maintaining conventional function. The middle path is neither rejecting phenomena as unreal nor clinging to them as inherently existing."

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.post("/detect/clinging")
async def detect_clinging(request: ClingingDetectionRequest) -> Dict[str, Any]:
    """
    Detect psychological attachment to views, even "correct" ones.

    Analyzes conversation patterns for defensive assertion, repetition,
    spiritual superiority, etc.

    Returns:
        Clinging detection with patterns and suggested interventions
    """
    try:
        result = detector.detect_clinging(request.conversation_history)

        # Add Nagarjuna correction if clinging detected
        if result.get("clinging_detected"):
            result["nagarjuna_correction"] = NAGARJUNA_TEACHINGS["clinging_to_emptiness"]

            result["suggested_intervention"] = {
                "type": "tetralemma_dissolution",
                "prompt": "Is emptiness something that exists? Does it not exist? Both? Neither? Or is even this question arising from the habit of reification?"
            }

            result["teaching_moment"] = {
                "guidance": "Notice the irony: holding tightly to the concept of 'no inherent existence.' What happens if you release even that? Can you use the teaching without possessing it?"
            }

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clinging detection failed: {str(e)}")


# ============================================================================
# TRANSFORMATION ENDPOINTS
# ============================================================================

@router.post("/transform/middle-path-alternatives")
async def generate_middle_path_alternatives(request: TransformRequest) -> Dict[str, Any]:
    """
    Generate alternative phrasings that avoid eternalism and nihilism.

    Offers reformulations appropriate to user's journey stage.

    Returns:
        List of middle path alternatives with scores and explanations
    """
    try:
        # Detect extremes first
        eternalism_result = detector.detect_eternalism(request.content)
        nihilism_result = detector.detect_nihilism(request.content)

        # Generate alternatives
        alternatives = transformer.generate_middle_path_alternatives(
            request.content,
            num_alternatives=request.num_alternatives,
            user_stage=request.user_stage
        )

        return {
            "original": request.content,
            "extreme_type": "eternalism" if eternalism_result["eternalism_detected"] else "nihilism" if nihilism_result["nihilism_detected"] else "balanced",
            "problematic_elements": {
                **eternalism_result.get("score_breakdown", {}),
                **{"nihilism_indicators": len(nihilism_result.get("indicators", []))}
            },
            "middle_path_alternatives": alternatives,
            "recommended": {
                f"for_stage_{i}_user": alternatives[0]["text"] if alternatives else request.content
                for i in [1, 3, 4]
            } if alternatives else {}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")


@router.post("/transform/dependent-origination")
async def reveal_dependent_origination(request: DetectionRequest) -> Dict[str, Any]:
    """
    Show how meaning arises from conditions, not essence.

    Traces the dependencies of concepts in the text.

    Returns:
        Dependent origination analysis with reframed text
    """
    try:
        # This would use NLP to extract key concepts and trace their conditions
        # For now, simplified implementation

        # Detect reified concepts
        eternalism_result = detector.detect_eternalism(request.content)
        reified_concepts = eternalism_result.get("reified_concepts", [])

        if not reified_concepts:
            return {
                "original_statement": request.content,
                "note": "No strongly reified concepts detected. Text already acknowledges conditionality."
            }

        # For first reified concept, show dependent origination
        concept = reified_concepts[0]

        return {
            "original_statement": request.content,
            "reified_elements": reified_concepts,
            "dependent_origination_analysis": {
                concept: {
                    "concept_depends_on": [
                        {
                            "condition": "Cultural framework",
                            "explanation": f"The concept '{concept}' is defined within specific cultural/linguistic contexts.",
                            "layer": 1
                        },
                        {
                            "condition": "Language creating categories",
                            "explanation": f"'{concept}' is a word that creates the appearance of a discrete thing, when experience is continuous flux.",
                            "layer": 2
                        }
                    ],
                    "without_these_conditions": f"The phenomenon we call '{concept}' would not be carved out as a distinct category."
                }
            },
            "middle_path_reframing": {
                "text": f"The concept '{concept}' arises dependent on cultural, linguistic, and contextual conditions. It functions conventionally while lacking inherent essence.",
                "what_changed": "Preserved conventional meaning while revealing dependent origination"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================================================
# CONTEMPLATION ENDPOINTS
# ============================================================================

@router.post("/contemplate/neti-neti")
async def generate_neti_neti_practice(request: ContemplationRequest) -> Dict[str, Any]:
    """
    Generate Neti Neti (not this, not that) practice for systematic negation.

    Provides step-by-step instructions for investigating the empty nature
    of concepts through progressive negation.

    Returns:
        Complete practice with stages, instructions, and koans
    """
    try:
        practice = contemplative.generate_neti_neti(
            target_concept=request.target_concept,
            user_stage=request.user_stage,
            depth=request.depth
        )

        practice["philosophical_context"] = "Neti Neti is a method for directly realizing emptiness through systematic investigation. It's not philosophical analysis but experiential inquiry."

        return practice

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Practice generation failed: {str(e)}")


@router.post("/contemplate/two-truths")
async def generate_two_truths_practice(request: ContemplationRequest) -> Dict[str, Any]:
    """
    Generate Two Truths contemplation for holding conventional and ultimate truths together.

    Helps user experientially understand how something can be both
    conventionally real and ultimately empty.

    Returns:
        Complete practice with conventional, ultimate, and integrated sections
    """
    try:
        phenomenon = request.phenomenon or "language"

        practice = contemplative.generate_two_truths_contemplation(
            phenomenon=phenomenon,
            user_context=request.dict().get("context")
        )

        practice["philosophical_context"] = "The Two Truths are not contradictory - they're complementary perspectives on the same reality. Mastering this is the heart of the middle path."

        practice["next_step"] = "Practice holding both truths in daily life. When conventional difficulties arise, remember ultimate emptiness. When tempted by nihilism, remember conventional function."

        return practice

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Practice generation failed: {str(e)}")


@router.post("/contemplate/dependent-origination")
async def generate_dependent_origination_practice(request: ContemplationRequest) -> Dict[str, Any]:
    """
    Generate practice for investigating dependent origination.

    Traces conditions backward (what gave rise to this?) and
    forward (what does this give rise to?).

    Returns:
        Complete inquiry practice with backward/forward traces
    """
    try:
        starting_point = request.starting_point or "self"

        practice = contemplative.generate_dependent_origination_inquiry(
            starting_point=starting_point,
            trace_backward=True,
            trace_forward=True
        )

        practice["philosophical_context"] = "Dependent origination (pratītyasamutpāda) is the Buddha's most profound teaching. Understanding it experientially is liberation."

        return practice

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Practice generation failed: {str(e)}")


# ============================================================================
# TEACHING ENDPOINTS
# ============================================================================

@router.post("/teach/situation")
async def get_teaching_for_situation(request: TeachingRequest) -> Dict[str, Any]:
    """
    Provide relevant Nagarjuna teaching for user's current state.

    Responds to detected extremes with appropriate middle path guidance.

    Returns:
        Teaching with quote, explanation, and next steps
    """
    try:
        user_state = request.user_state
        detected_extreme = user_state.get("detected_extreme")

        # Select appropriate teaching
        if detected_extreme == "nihilism":
            teaching_key = "emptiness_not_nihilism"
            diagnosis = "Mistaking emptiness for nihilism - common misunderstanding"
        elif user_state.get("clinging_detected"):
            teaching_key = "clinging_to_emptiness"
            diagnosis = "Attachment to views, even correct ones"
        else:
            teaching_key = "dependent_origination"
            diagnosis = "General middle path instruction"

        teaching_data = NAGARJUNA_TEACHINGS[teaching_key]

        return {
            "teaching": {
                "diagnosis": diagnosis,
                "core_principle": teaching_data["context"],
                "nagarjuna_quote": {
                    "text": teaching_data["quote"],
                    "source": teaching_data["source"]
                },
                "explanation": {
                    "short": teaching_data["explanation"],
                    "detailed": teaching_data["explanation"],  # Could expand this
                    "experiential": "Notice right now: Your experience is happening, even though it's empty of inherent existence. Sounds occur, sensations arise, thoughts appear. They're not nothing - they're just not inherently existing 'things.'"
                },
                "next_step": {
                    "practice": "two_truths_contemplation",
                    "focus": "Hold both truths together: Things work AND things are empty"
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Teaching retrieval failed: {str(e)}")


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/teachings")
async def list_teachings() -> Dict[str, Any]:
    """
    List all available Nagarjuna teachings.

    Returns:
        Dictionary of teachings with quotes and context
    """
    return {
        "teachings": NAGARJUNA_TEACHINGS,
        "total_count": len(NAGARJUNA_TEACHINGS)
    }


@router.post("/analyze-narrative")
async def analyze_narrative(request: NarrativeAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze narrative sentence-by-sentence for Madhyamaka metrics.

    Returns color-coded scores for each sentence for GUI visualization.

    Returns:
        {
            "sentences": [
                {
                    "text": str,
                    "index": int,
                    "scores": {"middle_path": float, "eternalism": float, "nihilism": float},
                    "colors": {"middle_path": str, "eternalism": str, "nihilism": str},
                    "dominant": str,
                    "primary_color": str
                },
                ...
            ],
            "overall_scores": {"middle_path": float, "eternalism": float, "nihilism": float},
            "summary": str,
            "sentence_count": int
        }
    """
    try:
        result = narrative_analyzer.analyze_narrative(
            text=request.text,
            primary_metric=request.primary_metric
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check for Madhyamaka service"""
    return {
        "status": "healthy",
        "service": "madhyamaka",
        "message": "The middle path neither exists nor does not exist. Yet this API responds."
    }
