"""
Madhyamaka Transformer - Middle Path Language Transformation

Transforms language toward the middle path by:
- Adding conditionality to absolutist claims
- Framing concepts as constructions
- Transforming assertions to inquiry
- Applying two truths framework
"""

from typing import List, Dict, Any, Optional
import re

from .detector import MadhyamakaDetector


class MadhyamakaTransformer:
    """
    Transforms language toward the middle path.

    Applies tetralemma, reveals dependent origination, generates alternatives.
    """

    def __init__(self):
        self.detector = MadhyamakaDetector()

    def generate_middle_path_alternatives(
        self,
        text: str,
        num_alternatives: int = 5,
        user_stage: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generate alternative phrasings that avoid extremes.

        Args:
            text: Original text
            num_alternatives: Number of alternatives to generate
            user_stage: User journey stage (1-5) for appropriate depth

        Returns:
            List of alternative phrasings with scores and explanations
        """
        alternatives = []

        # Detect what kind of extreme we're dealing with
        eternalism_result = self.detector.detect_eternalism(text)
        nihilism_result = self.detector.detect_nihilism(text)

        # Generate alternatives based on detected issues
        if eternalism_result["eternalism_detected"]:
            alternatives.extend(
                self._generate_anti_eternalism_alternatives(
                    text,
                    eternalism_result["reified_concepts"],
                    user_stage
                )
            )

        if nihilism_result["nihilism_detected"]:
            alternatives.extend(
                self._generate_anti_nihilism_alternatives(text, user_stage)
            )

        # Always add some general middle path alternatives
        alternatives.extend(
            self._generate_general_middle_path_alternatives(text, user_stage)
        )

        # Sort by score and return top N
        alternatives.sort(key=lambda x: x.get("score", 0), reverse=True)
        return alternatives[:num_alternatives]

    def _generate_anti_eternalism_alternatives(
        self,
        text: str,
        reified_concepts: List[str],
        user_stage: int
    ) -> List[Dict[str, Any]]:
        """Generate alternatives that soften absolutist claims"""
        alternatives = []

        # Strategy 1: Add conditionality
        conditional_text = self._add_conditionality(text)
        if conditional_text != text:
            alternatives.append({
                "text": conditional_text,
                "madhyamaka_improvements": [
                    "Acknowledges conditionality",
                    "Avoids absolutism",
                    "Recognizes variability"
                ],
                "score": 0.88,
                "preserves_conventional_meaning": True,
                "type": "conditional_softening"
            })

        # Strategy 2: Frame as construction
        if user_stage >= 2:
            construction_text = self._frame_as_construction(text, reified_concepts)
            if construction_text:
                alternatives.append({
                    "text": construction_text,
                    "madhyamaka_improvements": [
                        "Foregrounds construction",
                        "Removes reification",
                        "Meta-cognitive awareness"
                    ],
                    "score": 0.94,
                    "preserves_conventional_meaning": True,
                    "type": "construction_framing"
                })

        # Strategy 3: Transform to inquiry (for advanced users)
        if user_stage >= 4:
            inquiry_text = self._transform_to_inquiry(text)
            if inquiry_text:
                alternatives.append({
                    "text": inquiry_text,
                    "madhyamaka_improvements": [
                        "Shifts to metacognitive inquiry",
                        "Avoids making counter-claim",
                        "Encourages direct investigation"
                    ],
                    "score": 0.96,
                    "type": "contemplative_pointer",
                    "preserves_conventional_meaning": False,
                    "note": "Transforms assertion into inquiry"
                })

        return alternatives

    def _add_conditionality(self, text: str) -> str:
        """Add conditional qualifiers to absolutist statements"""
        # Replace "is" with "can be" or "is often"
        text = re.sub(r'\b(is)\b', r'can be', text, count=1)

        # Add "for some people" if making universal claim
        if re.search(r'\b(everyone|all|people|we)\b', text, re.IGNORECASE):
            text = "For some people, " + text[0].lower() + text[1:]

        # Replace "must" with "might benefit from"
        text = re.sub(r'\bmust\b', 'might benefit from', text, flags=re.IGNORECASE)

        # Replace "never" with "rarely" or "seldom"
        text = re.sub(r'\bnever\b', 'rarely', text, flags=re.IGNORECASE)

        # Replace "always" with "often"
        text = re.sub(r'\balways\b', 'often', text, flags=re.IGNORECASE)

        return text

    def _frame_as_construction(self, text: str, reified_concepts: List[str]) -> Optional[str]:
        """Reframe statement to foreground construction process"""
        if not reified_concepts:
            return None

        # Take first reified concept and reframe around it
        concept = reified_concepts[0] if reified_concepts else "this concept"

        return f"The concept '{concept}' in this context suggests that {text.lower()} - though this framing depends on how we've learned to construct meaning."

    def _transform_to_inquiry(self, text: str) -> Optional[str]:
        """Transform assertion into contemplative inquiry"""
        # Convert statement to question
        if "is" in text.lower():
            return f"Notice: Does the thought '{text}' arise from direct experience or learned belief? What happens if you question it?"
        else:
            return f"What if you investigate: '{text}' - is this arising from conditioned patterns or present-moment awareness?"

    def _generate_anti_nihilism_alternatives(
        self,
        text: str,
        user_stage: int
    ) -> List[Dict[str, Any]]:
        """Generate alternatives that restore conventional functionality"""
        alternatives = []

        # Strategy: Add two truths framework
        two_truths_text = f"Conventionally, language functions to communicate. Ultimately, {text.lower()} This doesn't mean words are useless - it means they're empty of fixed meaning while serving their purpose."

        alternatives.append({
            "text": two_truths_text,
            "madhyamaka_improvements": [
                "Explicitly invokes two truths",
                "Validates conventional",
                "Points to ultimate without nihilism"
            ],
            "score": 0.92,
            "type": "two_truths_framework",
            "teaching_depth": "intermediate"
        })

        return alternatives

    def _generate_general_middle_path_alternatives(
        self,
        text: str,
        user_stage: int
    ) -> List[Dict[str, Any]]:
        """Generate general middle path versions regardless of extreme detected"""
        alternatives = []

        # For all users: Simple conditional version
        simple = self._add_conditionality(text)
        if simple != text:
            alternatives.append({
                "text": simple,
                "madhyamaka_improvements": ["Adds nuance", "Avoids extremes"],
                "score": 0.75,
                "preserves_conventional_meaning": True,
                "type": "simple_softening"
            })

        return alternatives
