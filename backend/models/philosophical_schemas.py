"""
Philosophical extensions to the transformation API.

These schemas add philosophical framing to transformation responses,
supporting the "Language as a Sense" paradigm.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class RealmType(str, Enum):
    """The three ontological realms."""
    CORPOREAL = "corporeal"  # Physical, sensory substrate
    SYMBOLIC = "symbolic"    # Objective/linguistic constructions
    SUBJECTIVE = "subjective"  # Conscious experience


class BeliefFramework(BaseModel):
    """Represents a belief framework (PERSONA + NAMESPACE + STYLE)."""
    persona: str = Field(description="Voice/conscious position from which meaning is witnessed")
    namespace: str = Field(description="Conceptual domain or belief world")
    style: str = Field(description="Tone and presentation approach")

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this belief framework"
    )

    philosophical_context: Optional[str] = Field(
        default=None,
        description="What this framework emphasizes philosophically"
    )


class PerspectiveTransformation(BaseModel):
    """A single perspective transformation with philosophical context."""

    belief_framework: BeliefFramework
    transformed_content: str

    emotional_profile: Optional[str] = Field(
        default=None,
        description="What emotions/feelings this perspective evokes"
    )

    emphasis: Optional[str] = Field(
        default=None,
        description="What aspects of meaning this framework emphasizes"
    )

    realm: RealmType = Field(
        default=RealmType.SYMBOLIC,
        description="Which ontological realm this operates in"
    )


class MultiPerspectiveResponse(BaseModel):
    """Response containing multiple perspective transformations."""

    source_text: str = Field(description="Original text (Corporeal realm)")

    perspectives: List[PerspectiveTransformation] = Field(
        description="Different belief framework transformations"
    )

    philosophical_note: Optional[str] = Field(
        default="Each perspective reveals how meaning is constructed by the belief framework, not inherent in the words.",
        description="Philosophical insight about the transformations"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)


class EmotionalBeliefAnalysis(BaseModel):
    """Analysis of the Emotional Belief Loop for a text."""

    language: str = Field(description="Key words/phrases triggering emotional response")
    meaning: str = Field(description="Constructed semantic content")
    emotion: str = Field(description="Emotional reactions evoked")
    belief: str = Field(description="Reinforced belief about reality")

    loop_strength: float = Field(
        ge=0.0,
        le=1.0,
        description="How strongly this loop reinforces the illusion of objectivity"
    )


class FrameworkExplanation(BaseModel):
    """Explanation of a belief framework's philosophical basis."""

    framework_name: str
    what_it_does: str = Field(description="Functional description")
    why_it_matters: str = Field(description="Philosophical significance")
    when_to_use: Optional[str] = Field(
        default=None,
        description="Practical application contexts"
    )

    examples: List[str] = Field(
        default_factory=list,
        description="Example transformations"
    )


class SocraticQuestion(BaseModel):
    """A question designed to deconstruct assumptions."""

    question: str
    intent: str = Field(description="What assumption this question targets")
    depth_level: int = Field(
        ge=1,
        le=5,
        description="How deep this question goes (1=surface, 5=fundamental)"
    )


class SocraticDialogue(BaseModel):
    """A Socratic dialogue session."""

    initial_statement: str
    questions: List[SocraticQuestion]

    philosophical_goal: str = Field(
        default="Reveal the constructed nature of the concept being examined",
        description="What this dialogue aims to illuminate"
    )


class WordDissolutionExercise(BaseModel):
    """Contemplative exercise for dissolving linguistic constructs."""

    word: str
    emotional_weight: Optional[str] = Field(
        default=None,
        description="What emotional response this word evokes"
    )

    belief_associations: List[str] = Field(
        default_factory=list,
        description="Beliefs connected to this word"
    )

    dissolution_guidance: str = Field(
        default="Focus on the word. Feel its weight. Now let it dissolve, character by character, returning to silence.",
        description="Instructions for the dissolution practice"
    )


class WitnessPrompt(BaseModel):
    """Prompt for returning to direct experience."""

    prompt: str = Field(description="The witness/awareness prompt")

    context: Optional[str] = Field(
        default=None,
        description="When/why to use this prompt"
    )

    realm: RealmType = Field(
        default=RealmType.SUBJECTIVE,
        description="This points to the Subjective realm"
    )


class BeliefPatternNode(BaseModel):
    """A node in the belief network graph."""

    concept: str
    frequency: int = Field(description="How often this concept appears")
    emotional_charge: float = Field(
        ge=0.0,
        le=1.0,
        description="Strength of emotional association"
    )

    connected_concepts: List[str] = Field(
        default_factory=list,
        description="Other concepts this connects to"
    )


class BeliefNetwork(BaseModel):
    """
    Consciousness map showing how concepts are interconnected.

    This visualizes the user's belief structures as a network,
    revealing the constructed nature of their meaning frameworks.
    """

    nodes: List[BeliefPatternNode]

    clusters: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Identified clusters of related beliefs"
    )

    dominant_frameworks: List[str] = Field(
        default_factory=list,
        description="Most frequently invoked belief frameworks"
    )

    philosophical_insight: Optional[str] = Field(
        default=None,
        description="What this network reveals about constructed meaning"
    )


class ArchiveAnalysisRequest(BaseModel):
    """Request for archive belief-pattern analysis."""

    archive_format: str = Field(description="Format: chatgpt, claude, facebook, twitter, etc.")
    content: str = Field(description="Archive content to analyze")

    analysis_depth: str = Field(
        default="moderate",
        description="How deep to analyze: surface, moderate, deep"
    )


class ArchiveAnalysisResponse(BaseModel):
    """Response from archive analysis."""

    belief_network: BeliefNetwork

    time_being_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Analysis of discrete moments vs. continuous narrative"
    )

    emotional_loops: List[EmotionalBeliefAnalysis] = Field(
        default_factory=list,
        description="Identified emotional belief loops"
    )

    awakening_insights: List[str] = Field(
        default_factory=list,
        description="Suggested insights from the analysis"
    )


# Contemplative Features

class ContemplativeExerciseRequest(BaseModel):
    """Request for a contemplative exercise."""

    exercise_type: str = Field(description="Type: word_dissolution, socratic_dialogue, witness")
    content: Optional[str] = Field(default=None, description="Content to work with")

    user_stage: Optional[int] = Field(
        default=1,
        ge=1,
        le=5,
        description="User journey stage (1=Entry, 5=Integration)"
    )


class ContemplativeExerciseResponse(BaseModel):
    """Response with contemplative exercise."""

    exercise_type: str

    # One of these will be populated based on exercise_type
    word_dissolution: Optional[WordDissolutionExercise] = None
    socratic_dialogue: Optional[SocraticDialogue] = None
    witness_prompt: Optional[WitnessPrompt] = None

    philosophical_context: Optional[str] = Field(
        default=None,
        description="Why this exercise matters"
    )

    next_step: Optional[str] = Field(
        default=None,
        description="What to do after completing this exercise"
    )


# Perspective Framing Helpers

def create_framework_explanation(persona: str, namespace: str, style: str) -> FrameworkExplanation:
    """
    Generate philosophical explanation for a belief framework.

    This helps users understand what each framework emphasizes.
    """
    framework_name = f"{persona} / {namespace} / {style}"

    # Basic template - can be expanded with specific knowledge per framework
    what_it_does = f"Transforms text through the lens of a {persona} voice, operating in the {namespace} conceptual domain, with a {style} presentation."

    why_it_matters = f"This framework shapes meaning by emphasizing {persona.lower()}-specific values and using {namespace} belief structures."

    when_to_use = f"Use when you want to witness the text from a {persona.lower()}'s perspective in {namespace} contexts."

    return FrameworkExplanation(
        framework_name=framework_name,
        what_it_does=what_it_does,
        why_it_matters=why_it_matters,
        when_to_use=when_to_use
    )


def create_emotional_analysis(original: str, transformed: str, framework: BeliefFramework) -> EmotionalBeliefAnalysis:
    """
    Analyze how the emotional belief loop differs between original and transformation.

    This is a placeholder - real implementation would use AI analysis.
    """
    return EmotionalBeliefAnalysis(
        language=f"Key terms shift from original to {framework.style} tone",
        meaning="Semantic content remains similar but contextual framing changes",
        emotion=f"Evokes {framework.style}-appropriate emotional response",
        belief=f"Reinforces {framework.persona} belief structures",
        loop_strength=0.7
    )
