"""
Madhyamaka Detector - Extreme View Detection

Detects eternalism, nihilism, and middle path proximity in text.
Uses HYBRID approach: 70% semantic similarity, 30% regex patterns.

Semantic scoring heavily weighted to capture meaning over literal patterns.
"""

from typing import List, Dict, Any, Optional
import re

from .semantic_scorer import get_semantic_scorer


class MadhyamakaDetector:
    """
    Detects eternalism, nihilism, and middle path proximity in text.

    Uses linguistic heuristics, semantic patterns, and embedding analysis.
    """

    # Linguistic markers for eternalism (reification)
    ETERNALISM_MARKERS = {
        "absolute_language": [
            r'\b(always|never|must|essential|fundamental|absolute|inherent|true|truth)\b',
            r'\b(has to|need to|required|necessary|inevitable)\b'
        ],
        "essentialist_claims": [
            r'\b(\w+)\s+is\s+(\w+)',  # "X is Y" without qualifiers
            r'\b(the|a)\s+(\w+)\s+of\s+(\w+)',  # "the X of Y"
        ],
        "universal_quantifiers": [
            r'\b(all|every|everyone|everything|nothing|no one|nobody)\b',
            r'\b(any|whatever|whenever|wherever)\b'
        ],
        "lack_of_conditionality": [
            # Absence of these indicates absolutism
            r'\b(if|when|depending|sometimes|often|might|could|may)\b'
        ]
    }

    # Linguistic markers for nihilism (negation of conventional)
    NIHILISM_MARKERS = {
        "absolute_negation": [
            r'\b(completely|totally|entirely|absolutely)\s+(meaningless|false|illusion|unreal)\b',
            r'\b(nothing|none)\s+(matters|exists|is real)\b'
        ],
        "denial_of_function": [
            r'\b(doesn\'t|does not|can\'t|cannot)\s+(work|function|mean anything)\b',
            r'\b(all|everything)\s+is\s+(false|illusion|meaningless|empty)\b'
        ],
        "extreme_relativism": [
            r'\b(all views|all beliefs|everything)\s+are\s+(equally|the same)\b',
            r'\b(no|there is no)\s+(truth|meaning|reality)\b'
        ]
    }

    # Markers for middle path understanding
    MIDDLE_PATH_MARKERS = {
        "metacognitive_awareness": [
            r'\b(I notice|I observe|it seems|it appears|I\'m aware)\b',
            r'\b(the label|the concept|the word|the idea)\b',
            r'\b(constructed|construct|apply|project)\b'
        ],
        "conditional_language": [
            r'\b(for some|in certain contexts|depending on|when|if)\b',
            r'\b(sometimes|often|can be|might be|could be)\b',
            r'\b(in my experience|from my perspective|it seems to me)\b'
        ],
        "two_truths_awareness": [
            r'\b(conventionally|ultimately|at one level|at another level)\b',
            r'\b(functions as|useful for|serves to)\b.*\b(but|while|yet)\b.*\b(empty|constructed|dependent)\b'
        ],
        "dependent_origination": [
            r'\b(arises? from|depends on|conditional|co-arises?|emerges? from)\b',
            r'\b(given|based on|in relation to|relative to)\b'
        ]
    }

    def __init__(self, use_semantic: bool = True, semantic_weight: float = 0.7):
        """
        Initialize detector with compiled regex patterns and semantic scorer.

        Args:
            use_semantic: Enable semantic similarity scoring (default: True)
            semantic_weight: Weight for semantic score vs regex (default: 0.7)
        """
        self.eternalism_patterns = self._compile_patterns(self.ETERNALISM_MARKERS)
        self.nihilism_patterns = self._compile_patterns(self.NIHILISM_MARKERS)
        self.middle_path_patterns = self._compile_patterns(self.MIDDLE_PATH_MARKERS)

        # Semantic scorer (None if not available)
        self.use_semantic = use_semantic
        self.semantic_weight = semantic_weight
        self.regex_weight = 1.0 - semantic_weight

        if use_semantic:
            self.semantic_scorer = get_semantic_scorer()
            if self.semantic_scorer is None:
                print("Warning: sentence-transformers not available, falling back to regex only")
                self.use_semantic = False
        else:
            self.semantic_scorer = None

    def _compile_patterns(self, markers: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns for efficient matching"""
        compiled = {}
        for category, patterns in markers.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def detect_eternalism(self, text: str) -> Dict[str, Any]:
        """
        Detect reification and absolutist language using HYBRID scoring.

        70% semantic similarity, 30% regex patterns.

        Returns:
            {
                "eternalism_detected": bool,
                "confidence": float (0-1),
                "indicators": List[Dict],
                "reified_concepts": List[str],
                "severity": str (low, medium, high, critical),
                "scoring_method": str,
                "semantic_score": float (if available),
                "regex_score": float
            }
        """
        indicators = []
        regex_score = 0.0
        reified_concepts = set()

        # Check absolute language
        for pattern in self.eternalism_patterns["absolute_language"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({
                    "type": "absolute_language",
                    "phrases": list(set(matches)),
                    "severity": "high"
                })
                total_score += 0.3 * len(matches)

        # Check essentialist claims ("X is Y" without qualification)
        for pattern in self.eternalism_patterns["essentialist_claims"]:
            matches = pattern.findall(text)
            if matches:
                # Check if any conditionality markers are nearby
                has_qualification = any(
                    cond_pattern.search(text)
                    for cond_pattern in self.eternalism_patterns["lack_of_conditionality"]
                )

                if not has_qualification:
                    indicators.append({
                        "type": "essentialist_claims",
                        "examples": [' '.join(m) if isinstance(m, tuple) else m for m in matches[:3]],
                        "severity": "medium"
                    })
                    total_score += 0.2 * len(matches)

                    # Extract reified concepts
                    for match in matches:
                        if isinstance(match, tuple):
                            reified_concepts.update([m for m in match if m and len(m) > 2])

        # Check universal quantifiers
        for pattern in self.eternalism_patterns["universal_quantifiers"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({
                    "type": "universal_quantifiers",
                    "phrases": list(set(matches)),
                    "severity": "medium"
                })
                total_score += 0.15 * len(matches)

        # Check for lack of conditionality (absence of "if", "when", etc.)
        conditional_count = sum(
            len(pattern.findall(text))
            for pattern in self.eternalism_patterns["lack_of_conditionality"]
        )

        # If text is long but has few conditional markers, increase eternalism score
        words = len(text.split())
        if words > 20 and conditional_count < 2:
            indicators.append({
                "type": "lack_of_conditionality",
                "explanation": "No acknowledgment of dependent arising or conditional nature",
                "severity": "medium"
            })
            total_score += 0.25

        # Calculate confidence (normalize to 0-1 range)
        confidence = min(total_score / 2.0, 1.0)

        # Determine severity
        if confidence < 0.3:
            severity = "low"
        elif confidence < 0.6:
            severity = "medium"
        elif confidence < 0.85:
            severity = "high"
        else:
            severity = "critical"

        return {
            "eternalism_detected": confidence > 0.5,
            "confidence": confidence,
            "indicators": indicators,
            "reified_concepts": sorted(list(reified_concepts)),
            "severity": severity,
            "score_breakdown": {
                "absolute_language": sum(1 for i in indicators if i["type"] == "absolute_language"),
                "essentialist_claims": sum(1 for i in indicators if i["type"] == "essentialist_claims"),
                "universal_quantifiers": sum(1 for i in indicators if i["type"] == "universal_quantifiers"),
                "lack_conditionality": sum(1 for i in indicators if i["type"] == "lack_of_conditionality")
            }
        }

    def detect_nihilism(self, text: str) -> Dict[str, Any]:
        """
        Detect denial of conventional truth or misunderstanding of emptiness.

        Returns similar structure to detect_eternalism
        """
        indicators = []
        total_score = 0.0

        # Check absolute negation
        for pattern in self.nihilism_patterns["absolute_negation"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({
                    "type": "absolute_negation",
                    "phrases": list(set(matches)),
                    "severity": "high"
                })
                total_score += 0.4 * len(matches)

        # Check denial of function
        for pattern in self.nihilism_patterns["denial_of_function"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({
                    "type": "denial_of_conventional_function",
                    "explanation": "Rejects that language accomplishes conventional purposes",
                    "severity": "high"
                })
                total_score += 0.35 * len(matches)

        # Check extreme relativism
        for pattern in self.nihilism_patterns["extreme_relativism"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({
                    "type": "extreme_relativism",
                    "phrases": list(set(matches)),
                    "severity": "medium"
                })
                total_score += 0.25 * len(matches)

        # Check for "emptiness as nothingness" confusion
        emptiness_words = re.findall(r'\b(empty|emptiness|void|nothingness|meaningless)\b', text, re.IGNORECASE)
        conventional_words = re.findall(r'\b(works|functions|useful|effective|pragmatic)\b', text, re.IGNORECASE)

        if len(emptiness_words) >= 2 and len(conventional_words) == 0:
            indicators.append({
                "type": "emptiness_as_nothingness",
                "explanation": "Misunderstands śūnyatā as mere negation without acknowledging conventional function",
                "severity": "critical"
            })
            total_score += 0.5

        # Calculate confidence
        confidence = min(total_score / 1.5, 1.0)

        # Determine severity
        if confidence < 0.3:
            severity = "low"
        elif confidence < 0.6:
            severity = "medium"
        elif confidence < 0.85:
            severity = "high"
        else:
            severity = "critical"

        return {
            "nihilism_detected": confidence > 0.5,
            "confidence": confidence,
            "indicators": indicators,
            "severity": severity,
            "warning": {
                "level": severity,
                "message": "User may be experiencing nihilistic insight. Offer grounding in conventional functionality." if confidence > 0.7 else None
            } if confidence > 0.7 else None
        }

    def detect_middle_path_proximity(self, text: str) -> Dict[str, Any]:
        """
        Measure how close text is to middle path understanding.

        Returns score (0-1) and analysis of positive indicators.
        """
        positive_indicators = []
        total_score = 0.0

        # Check metacognitive awareness
        metacog_matches = []
        for pattern in self.middle_path_patterns["metacognitive_awareness"]:
            matches = pattern.findall(text)
            if matches:
                metacog_matches.extend(matches)

        if metacog_matches:
            positive_indicators.append({
                "type": "metacognitive_awareness",
                "evidence": metacog_matches[:3],
                "score": min(0.25 * len(metacog_matches), 0.95)
            })
            total_score += min(0.25 * len(metacog_matches), 0.95)

        # Check conditional language
        conditional_matches = []
        for pattern in self.middle_path_patterns["conditional_language"]:
            matches = pattern.findall(text)
            if matches:
                conditional_matches.extend(matches)

        if conditional_matches:
            positive_indicators.append({
                "type": "conditional_language",
                "evidence": conditional_matches[:3],
                "score": min(0.2 * len(conditional_matches), 0.85)
            })
            total_score += min(0.2 * len(conditional_matches), 0.85)

        # Check two truths awareness
        for pattern in self.middle_path_patterns["two_truths_awareness"]:
            if pattern.search(text):
                positive_indicators.append({
                    "type": "two_truths_awareness",
                    "evidence": "Uses both conventional and ultimate perspectives",
                    "score": 0.92
                })
                total_score += 0.92
                break

        # Check dependent origination awareness
        dep_orig_matches = []
        for pattern in self.middle_path_patterns["dependent_origination"]:
            matches = pattern.findall(text)
            if matches:
                dep_orig_matches.extend(matches)

        if dep_orig_matches:
            positive_indicators.append({
                "type": "dependent_origination_awareness",
                "evidence": dep_orig_matches[:3],
                "score": min(0.3 * len(dep_orig_matches), 0.9)
            })
            total_score += min(0.3 * len(dep_orig_matches), 0.9)

        # Normalize score (accounting for possible overlap)
        middle_path_score = min(total_score / 2.5, 1.0)

        # Determine proximity level
        if middle_path_score < 0.3:
            proximity = "far"
        elif middle_path_score < 0.6:
            proximity = "approaching"
        elif middle_path_score < 0.85:
            proximity = "close"
        else:
            proximity = "very_close"

        return {
            "middle_path_score": middle_path_score,
            "proximity": proximity,
            "indicators": {
                "positive": positive_indicators,
                "areas_for_refinement": self._suggest_refinements(text, middle_path_score)
            }
        }

    def _suggest_refinements(self, text: str, current_score: float) -> List[Dict[str, Any]]:
        """Suggest areas for deepening middle path understanding"""
        suggestions = []

        # Check for subtle self-reification
        self_pronouns = len(re.findall(r'\b(I|me|my|mine|myself)\b', text, re.IGNORECASE))
        if self_pronouns > 5 and current_score < 0.9:
            suggestions.append({
                "type": "subtle_self_reification",
                "evidence": f"Frequent use of 'I' without questioning subject-object duality ({self_pronouns} instances)",
                "suggestion": "Explore: Who is the 'I' that notices? Is that also constructed?"
            })

        # Check for clinging to emptiness itself
        emptiness_refs = re.findall(r'\b(empty|emptiness|śūnyatā)\b', text, re.IGNORECASE)
        if len(emptiness_refs) >= 3:
            suggestions.append({
                "type": "potential_clinging_to_emptiness",
                "evidence": "Multiple references to emptiness",
                "suggestion": "Remember: Even emptiness is empty. Don't reify the teaching."
            })

        return suggestions

    def detect_clinging(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Detect attachment to views, even 'correct' ones.

        Analyzes conversation patterns for defensive assertion, repetition,
        spiritual superiority, etc.
        """
        if not conversation_history:
            return {"clinging_detected": False, "confidence": 0.0}

        patterns = []
        total_score = 0.0

        # Extract all user messages
        user_messages = [msg["content"] for msg in conversation_history if msg.get("role") == "user"]

        if len(user_messages) < 2:
            return {"clinging_detected": False, "confidence": 0.0, "note": "Insufficient history"}

        # Check for defensive assertion (exclamation marks, all caps, repeated emphasis)
        defensive_indicators = 0
        for msg in user_messages:
            exclamations = msg.count('!')
            all_caps_words = len(re.findall(r'\b[A-Z]{3,}\b', msg))

            if exclamations >= 2 or all_caps_words >= 1:
                defensive_indicators += 1

        if defensive_indicators >= 2:
            patterns.append({
                "type": "defensive_assertion",
                "evidence": "Repeated emphasis with exclamation marks or all caps",
                "psychological_indicator": "Protecting view from challenge"
            })
            total_score += 0.3

        # Check for repetition of same concepts
        # Count unique words vs total words as rough measure
        all_words = ' '.join(user_messages).lower().split()
        unique_words = set(all_words)
        repetition_ratio = len(all_words) / max(len(unique_words), 1)

        if repetition_ratio > 3.0:  # High repetition
            patterns.append({
                "type": "repetitive_assertion",
                "evidence": f"Repetition ratio: {repetition_ratio:.1f}",
                "psychological_indicator": "Clinging to particular concepts"
            })
            total_score += 0.25

        # Check for spiritual superiority language
        superiority_phrases = [
            r'\b(most people|others|they)\s+(don\'t|can\'t|cannot|won\'t)\s+(understand|grasp|see|get it)\b',
            r'\b(I|we)\s+(understand|know|see|realize)\s+what\s+(most|others|they)\s+(don\'t|can\'t)\b',
            r'\b(only|few|rare)\s+(people|ones)\s+(understand|know|see)\b'
        ]

        superiority_count = sum(
            len(re.findall(pattern, ' '.join(user_messages), re.IGNORECASE))
            for pattern in superiority_phrases
        )

        if superiority_count >= 1:
            patterns.append({
                "type": "spiritual_superiority",
                "evidence": "Language suggesting special understanding unavailable to others",
                "psychological_indicator": "Using emptiness to establish identity/status"
            })
            total_score += 0.35

        confidence = min(total_score, 1.0)

        return {
            "clinging_detected": confidence > 0.4,
            "clinging_type": "attachment_to_views",
            "confidence": confidence,
            "patterns": patterns
        }
