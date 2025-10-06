"""
API routes for philosophical and contemplative features.

These endpoints support the "Language as a Sense" paradigm,
offering multi-perspective transformations, Socratic dialogue,
word dissolution exercises, and archive consciousness mapping.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import random
import uuid

from database import get_db, embedding_service
from models.db_models import Transformation as DBTransformation
from models.philosophical_schemas import (
    BeliefFramework,
    PerspectiveTransformation,
    MultiPerspectiveResponse,
    FrameworkExplanation,
    SocraticQuestion,
    SocraticDialogue,
    WordDissolutionExercise,
    WitnessPrompt,
    ArchiveAnalysisRequest,
    ArchiveAnalysisResponse,
    BeliefNetwork,
    BeliefPatternNode,
    EmotionalBeliefAnalysis,
    ContemplativeExerciseRequest,
    ContemplativeExerciseResponse,
    RealmType,
    create_framework_explanation,
    create_emotional_analysis
)
from models.schemas import TransformationRequest, TransformationStyle
from agents.transformation_agent import TransformationAgent

router = APIRouter(prefix="/api/philosophical", tags=["philosophical"])
agent = TransformationAgent()


# Multi-Perspective Transformations

@router.post("/perspectives", response_model=MultiPerspectiveResponse)
async def generate_multiple_perspectives(
    request: TransformationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate multiple perspective transformations simultaneously.

    Shows how the same content is experienced differently through
    different belief frameworks, revealing the constructed nature of meaning.
    """
    try:
        # Generate embeddings for source text if enabled
        source_embedding = None
        if request.session_id and request.user_id:
            source_embedding = await embedding_service.generate_embedding(request.content)
        # Define 3 contrasting frameworks to demonstrate plurality
        frameworks = [
            BeliefFramework(
                persona=request.persona,
                namespace=request.namespace,
                style=request.style.value,
                description=f"Primary framework: {request.persona} voice",
                philosophical_context=f"Emphasizes {request.persona.lower()} perspective in {request.namespace} domain"
            ),
            # Contrasting framework 1: Different persona
            BeliefFramework(
                persona="Poet" if request.persona != "Poet" else "Scholar",
                namespace=request.namespace,
                style="creative" if request.style.value != "creative" else "formal",
                description="Artistic/aesthetic perspective",
                philosophical_context="Emphasizes beauty, imagery, and feeling over logic"
            ),
            # Contrasting framework 2: Different namespace
            BeliefFramework(
                persona="Skeptic",
                namespace="philosophical" if request.namespace != "philosophical" else "scientific",
                style="questioning",
                description="Critical/questioning perspective",
                philosophical_context="Emphasizes paradox, assumptions, and deeper inquiry"
            )
        ]

        perspectives = []

        for framework in frameworks:
            # Transform with this framework
            result = await agent.transform(
                content=request.content,
                persona=framework.persona,
                namespace=framework.namespace,
                style=framework.style,
                depth=request.depth,
                preserve_structure=request.preserve_structure
            )

            if result["success"]:
                # Determine emotional profile (placeholder - could use AI)
                emotional_profiles = {
                    "formal": "Evokes professionalism, distance, authority",
                    "casual": "Evokes friendliness, ease, accessibility",
                    "lyrical": "Evokes beauty, feeling, aesthetic appreciation",
                    "questioning": "Evokes curiosity, doubt, deeper inquiry",
                    "technical": "Evokes precision, clarity, expertise"
                }

                transformed_content = result["transformed_content"]
                emotional_profile = emotional_profiles.get(
                    framework.style,
                    "Evokes framework-specific emotional response"
                )

                perspective = PerspectiveTransformation(
                    belief_framework=framework,
                    transformed_content=transformed_content,
                    emotional_profile=emotional_profile,
                    emphasis=f"Emphasizes {framework.persona.lower()}-centric values",
                    realm=RealmType.SYMBOLIC
                )

                perspectives.append(perspective)

                # Save to database if session provided
                if request.session_id and request.user_id:
                    transformed_embedding = await embedding_service.generate_embedding(transformed_content)

                    db_transformation = DBTransformation(
                        session_id=uuid.UUID(request.session_id),
                        user_id=uuid.UUID(request.user_id),
                        source_text=request.content,
                        source_embedding=source_embedding,
                        persona=framework.persona,
                        namespace=framework.namespace,
                        style=framework.style,
                        transformed_content=transformed_content,
                        transformed_embedding=transformed_embedding,
                        belief_framework=framework.dict(),
                        emotional_profile=emotional_profile,
                        philosophical_context=framework.philosophical_context,
                        status="completed",
                        extra_metadata={"transformation_type": "philosophical_perspective"}
                    )
                    db.add(db_transformation)

        if request.session_id and request.user_id:
            await db.commit()

        if not perspectives:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate any perspectives"
            )

        return MultiPerspectiveResponse(
            source_text=request.content,
            perspectives=perspectives,
            philosophical_note=(
                "Each perspective shows how meaning is constructed by the belief framework "
                "you bring to language. The 'objective truth' is an illusion—what's real is "
                "your subjective construction in this moment."
            ),
            metadata={
                "frameworks_generated": len(perspectives),
                "original_framework": f"{request.persona}/{request.namespace}/{request.style.value}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate perspectives: {str(e)}"
        )


@router.get("/frameworks/{persona}/{namespace}/{style}", response_model=FrameworkExplanation)
async def explain_framework(persona: str, namespace: str, style: str):
    """
    Get philosophical explanation of a specific belief framework.

    Helps users understand what a framework emphasizes and when to use it.
    """
    explanation = create_framework_explanation(persona, namespace, style)
    return explanation


# Contemplative Features

@router.post("/contemplate", response_model=ContemplativeExerciseResponse)
async def generate_contemplative_exercise(request: ContemplativeExerciseRequest):
    """
    Generate a contemplative exercise for consciousness practice.

    Exercises help shift users from intellectual understanding to
    direct experiential realization.
    """
    try:
        if request.exercise_type == "word_dissolution":
            return await _generate_word_dissolution(request.content)

        elif request.exercise_type == "socratic_dialogue":
            return await _generate_socratic_dialogue(request.content)

        elif request.exercise_type == "witness":
            return await _generate_witness_prompt(request.content, request.user_stage)

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown exercise type: {request.exercise_type}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate exercise: {str(e)}"
        )


async def _generate_word_dissolution(content: str) -> ContemplativeExerciseResponse:
    """Generate word dissolution exercise from content."""

    # Extract a meaningful word from content (simple heuristic)
    words = content.split()
    # Filter to substantive words (length > 4, not common articles)
    meaningful_words = [
        w.strip('.,!?;:').lower()
        for w in words
        if len(w) > 4 and w.lower() not in {'there', 'these', 'those', 'where', 'which', 'about'}
    ]

    if not meaningful_words:
        word = "awareness"
    else:
        # Pick a word from middle third (often more conceptually rich)
        mid_start = len(meaningful_words) // 3
        mid_end = 2 * len(meaningful_words) // 3
        word = meaningful_words[mid_start:mid_end][0] if meaningful_words[mid_start:mid_end] else meaningful_words[0]

    exercise = WordDissolutionExercise(
        word=word,
        emotional_weight=f"Notice any feelings, memories, or bodily sensations when you focus on '{word}'",
        belief_associations=[
            f"What do you believe about {word}?",
            f"How has {word} shaped your experience?",
            f"Where did your understanding of {word} come from?"
        ],
        dissolution_guidance=(
            f"1. Focus on the word: {word}\n"
            f"2. Feel its weight—notice any emotional response\n"
            f"3. Watch as it dissolves, letter by letter: {' '.join(word)}\n"
            f"4. {' '.join(word[:-1])}... {' '.join(word[:-2])}... {' '.join(word[:-3])}...\n"
            f"5. Rest in the silence that remains\n"
            f"6. What's here before language names it?"
        )
    )

    return ContemplativeExerciseResponse(
        exercise_type="word_dissolution",
        word_dissolution=exercise,
        philosophical_context=(
            "Words feel real because of emotional reinforcement (the Emotional Belief Loop). "
            "By dissolving a word back into silence, you witness the gap between symbolic "
            "construction and direct experience."
        ),
        next_step="After dissolution, return to reading the text. Notice if your relationship to that word has shifted."
    )


async def _generate_socratic_dialogue(content: str) -> ContemplativeExerciseResponse:
    """Generate Socratic dialogue to deconstruct assumptions in content."""

    # Extract potential assumptions (simplified - real implementation would use AI)
    # Look for declarative statements, "should" statements, etc.

    questions = [
        SocraticQuestion(
            question="What assumptions underlie this statement?",
            intent="Surface hidden beliefs",
            depth_level=2
        ),
        SocraticQuestion(
            question="How do you know this is true?",
            intent="Question epistemological foundation",
            depth_level=3
        ),
        SocraticQuestion(
            question="What would change if you held the opposite view?",
            intent="Explore contingency of belief",
            depth_level=3
        ),
        SocraticQuestion(
            question="Can you experience this directly, or only through language?",
            intent="Distinguish symbolic from lived",
            depth_level=4
        ),
        SocraticQuestion(
            question="What emotional weight does this belief carry?",
            intent="Reveal the Emotional Belief Loop",
            depth_level=3
        ),
        SocraticQuestion(
            question="Who would you be without this thought?",
            intent="Point to consciousness prior to belief",
            depth_level=5
        )
    ]

    dialogue = SocraticDialogue(
        initial_statement=content[:200] + "..." if len(content) > 200 else content,
        questions=questions,
        philosophical_goal=(
            "These questions aim to deconstruct the belief structures underlying "
            "the text, revealing how meaning is constructed rather than discovered."
        )
    )

    return ContemplativeExerciseResponse(
        exercise_type="socratic_dialogue",
        socratic_dialogue=dialogue,
        philosophical_context=(
            "Socratic questioning reveals that what we take as 'objective truth' "
            "is actually a web of beliefs, assumptions, and emotional reinforcements. "
            "By questioning assumptions, we loosen identification with symbolic constructs."
        ),
        next_step="After contemplating these questions, return to the text. Do you read it differently?"
    )


async def _generate_witness_prompt(content: Optional[str], user_stage: int) -> ContemplativeExerciseResponse:
    """Generate witness/awareness prompt appropriate to user stage."""

    prompts_by_stage = {
        1: WitnessPrompt(
            prompt="Before reading this text, take a breath. Notice you are about to construct meaning.",
            context="Entry stage: Gentle introduction to awareness",
            realm=RealmType.SUBJECTIVE
        ),
        2: WitnessPrompt(
            prompt="As you read these words, can you feel how meaning arises in your awareness?",
            context="Engagement stage: Noticing the construction process",
            realm=RealmType.SUBJECTIVE
        ),
        3: WitnessPrompt(
            prompt="What's here before you name it? Return to direct experience before language.",
            context="Insight stage: Distinguishing lived from symbolic",
            realm=RealmType.SUBJECTIVE
        ),
        4: WitnessPrompt(
            prompt="Witness awareness itself—that which is aware of all experience, including language.",
            context="Awakening stage: Pointing to consciousness",
            realm=RealmType.SUBJECTIVE
        ),
        5: WitnessPrompt(
            prompt="Rest as the awareness that constructs all meaning. Dance in language while free of it.",
            context="Integration stage: Conscious use while resting in awareness",
            realm=RealmType.SUBJECTIVE
        )
    }

    prompt = prompts_by_stage.get(user_stage, prompts_by_stage[1])

    return ContemplativeExerciseResponse(
        exercise_type="witness",
        witness_prompt=prompt,
        philosophical_context=(
            "The witness is consciousness itself—the subjective realm that is "
            "the only truly 'lived' dimension. All symbolic meaning arises in and to this awareness."
        ),
        next_step="Return to presence whenever you notice unconscious identification with thoughts or language."
    )


# Archive Analysis (Belief Pattern Detection)

@router.post("/archive/analyze", response_model=ArchiveAnalysisResponse)
async def analyze_archive_consciousness(request: ArchiveAnalysisRequest):
    """
    Analyze archive to detect belief patterns and construct consciousness map.

    Maps the user's belief structures, revealing how meaning has been
    constructed through recurring conceptual frameworks.
    """
    try:
        # This is a placeholder implementation
        # Real implementation would parse archive format and use AI for pattern detection

        # For now, generate example analysis
        belief_network = await _generate_belief_network_example(request.content)

        return ArchiveAnalysisResponse(
            belief_network=belief_network,
            time_being_analysis={
                "total_discrete_moments": 42,  # Placeholder
                "average_gap_between_moments": "3.2 seconds",
                "insight": "Your archive shows discrete moments, not continuous flow—aligned with Time-Being philosophy"
            },
            emotional_loops=[
                EmotionalBeliefAnalysis(
                    language="success, achievement, goals",
                    meaning="Progress toward socially-defined outcomes",
                    emotion="Anxiety, desire, urgency",
                    belief="Success is a real thing that must be achieved",
                    loop_strength=0.85
                ),
                EmotionalBeliefAnalysis(
                    language="productivity, efficiency, optimization",
                    meaning="Maximizing output per unit time",
                    emotion="Pressure, inadequacy, drive",
                    belief="Time must be used optimally or it's wasted",
                    loop_strength=0.78
                )
            ],
            awakening_insights=[
                "Your archive reveals heavy emphasis on achievement-oriented belief frameworks",
                "Notice how emotional weighting makes these concepts feel 'objectively real'",
                "These are constructed meaning structures—you can hold them lightly",
                "Try transforming your thoughts through different NAMESPACES (e.g., 'ecological' vs. 'business')"
            ]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Archive analysis failed: {str(e)}"
        )


async def _generate_belief_network_example(content: str) -> BeliefNetwork:
    """Generate example belief network (placeholder for real AI analysis)."""

    # Extract some words as concept nodes (simplified)
    words = content.split()
    # Get unique substantive words
    concepts = list(set([
        w.strip('.,!?;:').lower()
        for w in words
        if len(w) > 4
    ]))[:10]  # Limit to 10 for example

    nodes = [
        BeliefPatternNode(
            concept=concept,
            frequency=random.randint(5, 50),
            emotional_charge=random.random(),
            connected_concepts=random.sample(concepts, min(3, len(concepts)))
        )
        for concept in concepts
    ]

    return BeliefNetwork(
        nodes=nodes,
        clusters=[
            {
                "name": "Achievement Cluster",
                "concepts": ["success", "goals", "productivity"],
                "emotional_charge": 0.8
            },
            {
                "name": "Relational Cluster",
                "concepts": ["connection", "understanding", "communication"],
                "emotional_charge": 0.6
            }
        ],
        dominant_frameworks=[
            "Business/Achievement/Formal",
            "Academic/Analysis/Technical",
            "Personal/Reflection/Casual"
        ],
        philosophical_insight=(
            "Your belief network shows strong clustering around achievement and productivity. "
            "These nodes have high emotional charge, revealing the Emotional Belief Loop at work. "
            "Remember: these are constructed frameworks, not objective reality."
        )
    )


# Framework Suggestions Based on Context

@router.post("/suggest-frameworks")
async def suggest_frameworks(content: str, context: str = "general"):
    """
    Suggest appropriate belief frameworks based on content and context.

    Helps users choose frameworks intentionally rather than unconsciously.
    """
    try:
        # Placeholder suggestions based on context
        suggestions = {
            "academic": [
                {"persona": "Scholar", "namespace": "academic", "style": "formal"},
                {"persona": "Researcher", "namespace": "scientific", "style": "technical"},
                {"persona": "Critic", "namespace": "theoretical", "style": "analytical"}
            ],
            "creative": [
                {"persona": "Poet", "namespace": "aesthetic", "style": "lyrical"},
                {"persona": "Artist", "namespace": "expressive", "style": "vivid"},
                {"persona": "Storyteller", "namespace": "narrative", "style": "engaging"}
            ],
            "business": [
                {"persona": "Executive", "namespace": "business", "style": "formal"},
                {"persona": "Consultant", "namespace": "strategic", "style": "professional"},
                {"persona": "Entrepreneur", "namespace": "innovation", "style": "dynamic"}
            ],
            "personal": [
                {"persona": "Friend", "namespace": "personal", "style": "casual"},
                {"persona": "Sage", "namespace": "wisdom", "style": "reflective"},
                {"persona": "Coach", "namespace": "growth", "style": "encouraging"}
            ],
            "philosophical": [
                {"persona": "Philosopher", "namespace": "philosophical", "style": "contemplative"},
                {"persona": "Skeptic", "namespace": "critical", "style": "questioning"},
                {"persona": "Mystic", "namespace": "spiritual", "style": "poetic"}
            ]
        }

        context_suggestions = suggestions.get(context, suggestions["general"])

        return {
            "context": context,
            "suggestions": context_suggestions,
            "philosophical_note": (
                "These are suggestions, not prescriptions. Each framework is a lens through which "
                "to construct meaning. Experiment and notice how different frameworks evoke different experiences."
            )
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest frameworks: {str(e)}"
        )
