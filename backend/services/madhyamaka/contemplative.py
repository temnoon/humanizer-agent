"""
Madhyamaka Contemplative Practice Generator

Generates contemplative practices for direct realization of middle path:
- Neti Neti (systematic negation)
- Two Truths contemplation
- Dependent Origination inquiry
"""

from typing import Dict, Any, Optional


class ContemplativePracticeGenerator:
    """
    Generates contemplative practices for direct realization of middle path.

    Practices include:
    - Neti Neti (systematic negation)
    - Two Truths contemplation
    - Dependent Origination inquiry
    """

    def generate_neti_neti(
        self,
        target_concept: str = "self",
        user_stage: int = 3,
        depth: str = "progressive"
    ) -> Dict[str, Any]:
        """
        Generate Neti Neti (not this, not that) practice for systematic negation.

        Args:
            target_concept: Concept to investigate (self, consciousness, thought, etc.)
            user_stage: User journey stage (determines depth)
            depth: "simple", "progressive", or "deep"

        Returns:
            Complete practice instructions with stages
        """
        practices = {
            "self": self._neti_neti_self(),
            "thought": self._neti_neti_thought(),
            "emotion": self._neti_neti_emotion(),
            "consciousness": self._neti_neti_consciousness()
        }

        practice_data = practices.get(target_concept, self._neti_neti_self())

        return {
            "practice_type": "neti_neti",
            "target": target_concept,
            "instructions": practice_data,
            "metadata": {
                "duration_minutes": 15 if depth == "simple" else 20 if depth == "progressive" else 30,
                "difficulty": "beginner" if user_stage <= 2 else "intermediate" if user_stage <= 4 else "advanced",
                "warning": "If this practice creates anxiety or dissociation, return to conventional reality. Ground in the body, name objects in the room. The goal is liberating insight, not destabilization."
            }
        }

    def _neti_neti_self(self) -> Dict[str, Any]:
        """Neti Neti practice for investigating the self"""
        return {
            "overview": "This practice systematically investigates what we call 'self' through progressive negation. Each negation is not mere denial but inquiry into emptiness.",

            "stages": [
                {
                    "stage": 1,
                    "investigation": "Is the self the body?",
                    "contemplation": "Notice the body: arms, legs, torso, head. Are you the body, or does the body appear in awareness? The body changes constantly - cells die and regenerate. Which body is the 'self'? The body of childhood? Of now? Of old age?",
                    "negation": "Not this (neti) - the self is not reducible to the body",
                    "not_nihilism": "This doesn't mean the body doesn't exist conventionally. It means 'self' is not inherently identical with body.",
                    "pause_instruction": "Rest here for 3 breaths. Notice what's observing the body."
                },
                {
                    "stage": 2,
                    "investigation": "Is the self thoughts?",
                    "contemplation": "Watch thoughts arise and pass. Thoughts come and go, but who is watching? Are you identical with thoughts, or do thoughts appear to you? Which thought is the self? The thought from 5 minutes ago? The current thought? The next thought?",
                    "negation": "Not this (neti) - the self is not reducible to thoughts",
                    "not_nihilism": "Thoughts function conventionally. Thinking happens. But 'self' is not inherently found in thoughts.",
                    "pause_instruction": "Rest here for 3 breaths. Notice the space between thoughts."
                },
                {
                    "stage": 3,
                    "investigation": "Is the self awareness itself?",
                    "contemplation": "Perhaps the self is the awareness witnessing body and thoughts? But notice: even this 'awareness' is a concept. Who is aware of awareness? Where does awareness begin and end? Is it a thing, or another constructed category?",
                    "negation": "Not this (neti) - even awareness as 'self' is a reification",
                    "not_nihilism": "Awareness occurs conventionally. Experience happens. But treating awareness as an independent, inherent self is still reification.",
                    "pause_instruction": "Rest here for 5 breaths. Let the question hang without answering."
                },
                {
                    "stage": 4,
                    "investigation": "Is there a self at all?",
                    "contemplation": "After negating body, thoughts, and awareness - is there anything left to call 'self'? Notice: you're still here, experiencing this moment. So what is this 'you'? Not the body, not thoughts, not even awareness as a thing. What remains?",
                    "negation": "Not this (neti), not that (neti)",
                    "middle_path_realization": "The self is neither inherently existing nor non-existing. It arises dependently, conventionally, without essence. You function as 'you' while being empty of inherent selfhood.",
                    "pause_instruction": "Rest in this recognition for 10 breaths."
                }
            ],

            "closing": {
                "integration": "As you return to daily life, notice how 'you' function perfectly well without an inherent self. Choices are made, actions happen, relationships form - all without a fixed, independent self at the center. This is the middle path: neither affirming nor denying the self.",
                "koan": "Who is it that realizes there is no self?"
            }
        }

    def _neti_neti_thought(self) -> Dict[str, Any]:
        """Neti Neti for investigating thoughts"""
        return {
            "overview": "Investigate the nature of thoughts through systematic inquiry.",
            "stages": [
                {
                    "stage": 1,
                    "investigation": "Where do thoughts come from?",
                    "contemplation": "Watch for the next thought to arise. Can you catch it at the moment of arising? Where was it before it appeared? Notice: thoughts seem to come from nowhere, appear briefly, and dissolve back into nowhere.",
                    "negation": "Thoughts have no findable origin",
                    "pause_instruction": "Rest here for 3 breaths."
                },
                {
                    "stage": 2,
                    "investigation": "What are thoughts made of?",
                    "contemplation": "Are thoughts physical? Mental? Energy? Words? Images? Try to locate the substance of a thought. Notice: thoughts are not solid things - they're fleeting events in awareness.",
                    "negation": "Thoughts have no intrinsic substance",
                    "pause_instruction": "Rest here for 3 breaths."
                },
                {
                    "stage": 3,
                    "investigation": "Who owns thoughts?",
                    "contemplation": "Do thoughts belong to you? Can you control which thoughts arise? Notice: thoughts appear unbidden. You can't choose to not think for the next 10 seconds. They arise from conditions, not from a controller.",
                    "negation": "Thoughts belong to no one",
                    "middle_path_realization": "Thoughts arise dependently, function conventionally, and are empty of inherent existence. They're neither 'yours' nor 'not yours' - they're just arising and passing.",
                    "pause_instruction": "Rest here for 5 breaths."
                }
            ],
            "closing": {
                "integration": "As thoughts arise throughout the day, notice their empty nature. You don't need to believe every thought or identify with it. They're just weather patterns in the mind.",
                "koan": "What is a thought before it's thought?"
            }
        }

    def _neti_neti_emotion(self) -> Dict[str, Any]:
        """Neti Neti for investigating emotions"""
        return {
            "overview": "Investigate the constructed nature of emotions.",
            "stages": [
                {
                    "stage": 1,
                    "investigation": "Where is the emotion located?",
                    "contemplation": "When you feel anger (or sadness, joy, fear), where is it? In the chest? The head? The whole body? Notice: you can't pinpoint an exact location. It's a constellation of sensations we label 'anger'.",
                    "negation": "Emotions have no fixed location",
                    "pause_instruction": "Rest here for 3 breaths."
                }
            ],
            "closing": {
                "integration": "Emotions arise, function, and pass - all without inherent existence. You can feel them fully without reifying them as solid things.",
                "koan": "What is anger when you stop calling it anger?"
            }
        }

    def _neti_neti_consciousness(self) -> Dict[str, Any]:
        """Neti Neti for investigating consciousness itself"""
        return {
            "overview": "The most subtle investigation - consciousness investigating itself.",
            "stages": [
                {
                    "stage": 1,
                    "investigation": "Can consciousness observe itself?",
                    "contemplation": "Try to be aware of awareness. Notice: there's always a split - the aware-er and the aware-ed. But who is the aware-er? If you try to observe that, it becomes the observed. Awareness always slips away from being grasped.",
                    "negation": "Consciousness cannot objectify itself",
                    "pause_instruction": "Rest here for 5 breaths."
                }
            ],
            "closing": {
                "integration": "Consciousness is not a thing to be found - it's the empty knowing in which all experience arises. Empty of essence, yet luminously present.",
                "koan": "What was your original face before you were conscious?"
            }
        }

    def generate_two_truths_contemplation(
        self,
        phenomenon: str = "this experience",
        user_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate Two Truths contemplation for holding conventional and ultimate truths together.

        Args:
            phenomenon: What to investigate (anger, thought, language, etc.)
            user_context: Current user context (optional)

        Returns:
            Complete two truths practice
        """
        return {
            "practice_type": "two_truths_contemplation",
            "phenomenon": phenomenon,

            "conventional_truth_practice": {
                "instruction": f"Notice the experience called '{phenomenon}'",
                "steps": [
                    f"Feel the experience directly - what is present when '{phenomenon}' is here?",
                    "Notice its effects - how does it influence thoughts, emotions, behavior?",
                    f"Recognize: This is what we conventionally call '{phenomenon}'. The word functions to communicate this experience.",
                    "Observe: At the conventional level, it's real, it has effects, it matters."
                ],
                "affirmation": f"At the conventional level, {phenomenon} is real. It has effects. It's unpleasant or pleasant. All of this is true conventionally."
            },

            "ultimate_truth_practice": {
                "instruction": f"Investigate the emptiness of '{phenomenon}'",
                "steps": [
                    f"Where is '{phenomenon}' located? In the body? In thoughts? In the situation?",
                    f"Notice: The various components are just what they are. Where is the inherent '{phenomenon}'?",
                    f"Recognize: '{phenomenon}' is a label applied to a constellation of conditions. It has no essence separate from these conditions.",
                    f"Notice: As soon as conditions change, what we called '{phenomenon}' transforms or dissolves."
                ],
                "affirmation": f"At the ultimate level, {phenomenon} is empty of inherent existence. It's a constructed category projected onto dependently arisen experiences."
            },

            "both_truths_together": {
                "instruction": "Now hold both truths simultaneously",
                "contemplation": f"{phenomenon.capitalize()} is happening (conventional) AND {phenomenon} is empty (ultimate). Neither truth cancels the other. The emptiness is not somewhere else - it's the very nature of the {phenomenon} that's occurring.",
                "paradox": f"Can you rest in the experience where {phenomenon} is both fully present and completely empty? Where it matters (you might need to address the situation) and doesn't matter (it's just conditions arising)?"
            },

            "insight_pointers": [
                f"If you're only seeing conventional truth: You're clinging to {phenomenon} as real. It will persist.",
                f"If you're only seeing ultimate truth: You might dismiss {phenomenon} as 'just illusion' and not address actual conditions. This is bypassing.",
                f"The middle path: Respond skillfully to {phenomenon} (conventional) while knowing it has no fixed nature (ultimate)."
            ],

            "closing_koan": f"When {phenomenon} arises, what arises? When {phenomenon} dissolves, what dissolves?"
        }

    def generate_dependent_origination_inquiry(
        self,
        starting_point: str = "this belief",
        trace_backward: bool = True,
        trace_forward: bool = True
    ) -> Dict[str, Any]:
        """
        Generate practice for investigating dependent origination.

        Traces conditions backward (what gave rise to this?) and
        forward (what does this give rise to?).
        """
        return {
            "practice_type": "dependent_origination_inquiry",
            "starting_concept": starting_point,

            "backward_trace": {
                "instruction": "Trace the conditions that gave rise to this belief/concept",
                "inquiry_steps": [
                    {
                        "question": f"Where did you first encounter the idea of '{starting_point}'?",
                        "contemplation": "Recall early experiences. Notice: The concept was taught, not discovered innately. It arose from cultural conditioning."
                    },
                    {
                        "question": f"What makes '{starting_point}' seem real?",
                        "contemplation": "Perhaps you've had experiences that seemed to confirm it. Notice: You interpreted those experiences through the lens of this concept."
                    },
                    {
                        "question": f"What would need to be different for '{starting_point}' to not make sense?",
                        "contemplation": "Imagine a different cultural/historical context. Notice: The concept depends on specific frameworks."
                    },
                    {
                        "question": f"What beliefs underlie belief in '{starting_point}'?",
                        "contemplation": "Trace the chain backward. Notice: Beliefs rest on other beliefs, all the way down."
                    }
                ],
                "realization": f"The belief in '{starting_point}' doesn't exist independently. It arose from countless conditions."
            } if trace_backward else None,

            "forward_trace": {
                "instruction": "Notice what arises dependent on this belief",
                "inquiry_steps": [
                    {
                        "question": f"How does believing in '{starting_point}' shape your experience?",
                        "contemplation": "Notice emotions, perceptions, interpretations that arise. They're all conditioned by this belief."
                    },
                    {
                        "question": f"What actions arise from belief in '{starting_point}'?",
                        "contemplation": "Notice behaviors. They're not inherent responses - they arise from the belief."
                    },
                    {
                        "question": f"What further beliefs does this enable?",
                        "contemplation": "Notice: Beliefs are generative. One belief gives rise to others."
                    }
                ],
                "realization": f"The belief in '{starting_point}' isn't isolated - it's a generative condition producing further conditions."
            } if trace_forward else None,

            "middle_path_insight": {
                "contemplation": f"The belief in '{starting_point}' arose from conditions (backward) and gives rise to conditions (forward). It's a link in an infinite chain of dependent origination. It has no independent existence, yet it functions powerfully.",
                "question": f"Can you hold the belief in '{starting_point}' lightly, using it when helpful while seeing through its empty nature?"
            },

            "practical_integration": {
                "daily_life": f"Next time you think about '{starting_point}':",
                "steps": [
                    "Notice the thought arise",
                    "Ask: What conditions gave rise to this thought right now?",
                    "Ask: What does this thought give rise to?",
                    "See the whole chain of dependent origination",
                    "Act skillfully without clinging to the belief as inherently true"
                ]
            }
        }
