"""
Madhyamaka Detector - HYBRID Extreme View Detection

Detects eternalism, nihilism, and middle path proximity using:
- 70% Semantic Similarity (meaning-based, robust)
- 30% Regex Patterns (fast, explicit markers)

Heavily favors semantic understanding over literal pattern matching.
"""

from typing import List, Dict, Any, Optional
import re

from .semantic_scorer import get_semantic_scorer


class MadhyamakaDetector:
    """
    HYBRID detector: 70% semantic, 30% regex.

    Semantic scoring captures meaning, regex provides explicit marker detection.
    """

    # Regex patterns (used for 30% of score)
    ETERNALISM_MARKERS = {
        "absolute_language": [
            r'\b(always|never|must|essential|fundamental|absolute|inherent|true|truth)\b',
            r'\b(has to|need to|required|necessary|inevitable)\b'
        ],
        "universal_quantifiers": [
            r'\b(all|every|everyone|everything|nothing|no one|nobody)\b',
        ],
    }

    NIHILISM_MARKERS = {
        "absolute_negation": [
            r'\b(completely|totally|entirely|absolutely)\s+(meaningless|false|illusion|unreal)\b',
            r'\b(nothing|none)\s+(matters|exists|is real)\b'
        ],
    }

    MIDDLE_PATH_MARKERS = {
        "conditional_language": [
            r'\b(for some|sometimes|often|can be|might be|could be|depending on)\b',
        ],
        "metacognitive_awareness": [
            r'\b(I notice|I observe|it seems|constructed|construct)\b',
        ],
        "two_truths": [
            r'\b(conventionally|ultimately)\b',
        ],
    }

    def __init__(self, use_semantic: bool = True, semantic_weight: float = 0.7):
        """
        Initialize hybrid detector.

        Args:
            use_semantic: Enable semantic scoring (default: True)
            semantic_weight: Weight for semantic vs regex (default: 0.7)
        """
        self.use_semantic = use_semantic
        self.semantic_weight = semantic_weight
        self.regex_weight = 1.0 - semantic_weight

        # Initialize semantic scorer
        if use_semantic:
            self.semantic_scorer = get_semantic_scorer()
            if self.semantic_scorer is None:
                print("Warning: sentence-transformers not available, using regex only")
                self.use_semantic = False
        else:
            self.semantic_scorer = None

        # Compile regex patterns
        self.eternalism_patterns = self._compile_patterns(self.ETERNALISM_MARKERS)
        self.nihilism_patterns = self._compile_patterns(self.NIHILISM_MARKERS)
        self.middle_path_patterns = self._compile_patterns(self.MIDDLE_PATH_MARKERS)

    def _compile_patterns(self, markers: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
        """Compile regex patterns"""
        compiled = {}
        for category, patterns in markers.items():
            compiled[category] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled

    def _regex_score_eternalism(self, text: str) -> tuple[float, List[Dict], List[str]]:
        """Compute regex-based eternalism score"""
        indicators = []
        score = 0.0
        reified = set()

        # Absolute language
        for pattern in self.eternalism_patterns["absolute_language"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({"type": "absolute_language", "phrases": list(set(matches))})
                score += 0.35 * len(matches)  # Increased from 0.3

        # Universal quantifiers
        for pattern in self.eternalism_patterns["universal_quantifiers"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({"type": "universal_quantifiers", "phrases": list(set(matches))})
                score += 0.25 * len(matches)  # Increased from 0.2

        return (min(score / 1.5, 1.0), indicators, sorted(list(reified)))  # Reduced divisor from 2.0

    def _regex_score_nihilism(self, text: str) -> tuple[float, List[Dict]]:
        """Compute regex-based nihilism score"""
        indicators = []
        score = 0.0

        for pattern in self.nihilism_patterns["absolute_negation"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({"type": "absolute_negation", "phrases": list(set(matches))})
                score += 0.5 * len(matches)  # Increased from 0.4

        return (min(score / 1.2, 1.0), indicators)  # Reduced divisor from 1.5

    def _regex_score_middle_path(self, text: str) -> tuple[float, List[Dict]]:
        """Compute regex-based middle path score"""
        indicators = []
        score = 0.0

        for pattern in self.middle_path_patterns["conditional_language"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({"type": "conditional_language", "evidence": list(set(matches))})
                score += 0.3 * len(matches)

        for pattern in self.middle_path_patterns["metacognitive_awareness"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({"type": "metacognitive_awareness", "evidence": list(set(matches))})
                score += 0.25 * len(matches)

        for pattern in self.middle_path_patterns["two_truths"]:
            matches = pattern.findall(text)
            if matches:
                indicators.append({"type": "two_truths", "evidence": list(set(matches))})
                score += 0.4 * len(matches)

        return (min(score / 2.5, 1.0), indicators)

    def detect_eternalism(self, text: str) -> Dict[str, Any]:
        """
        Detect eternalism using semantic embeddings (primary) with regex as supplementary indicators.

        Semantic and regex scores are NOT combined - they're in different metric spaces.
        Semantic (embedding similarity) is the primary metric when available.
        Regex patterns provide qualitative indicators only.
        """
        # Get regex patterns as qualitative indicators
        regex_conf, indicators, reified = self._regex_score_eternalism(text)

        # Semantic score is PRIMARY metric (embedding latent space)
        if self.use_semantic and self.semantic_scorer:
            semantic_result = self.semantic_scorer.score_eternalism(text)
            semantic_conf = semantic_result["semantic_score"]

            # Use semantic score as confidence (100% metric-relative to embedding space)
            confidence = semantic_conf
            method = "semantic_primary"

            # Regex provides supplementary boolean indicators, not score
            has_regex_indicators = regex_conf > 0.3
        else:
            # Fallback to regex when semantic unavailable
            confidence = regex_conf
            semantic_conf = None
            method = "regex_fallback"
            has_regex_indicators = True

        # Severity based on primary confidence
        if confidence < 0.3:
            severity = "low"
        elif confidence < 0.5:
            severity = "medium"
        elif confidence < 0.7:
            severity = "high"
        else:
            severity = "critical"

        result = {
            "eternalism_detected": confidence > 0.4,
            "confidence": confidence,  # Pure semantic or pure regex, never mixed
            "severity": severity,
            "indicators": indicators,  # Qualitative patterns found
            "reified_concepts": reified,
            "scoring_method": method,
            "regex_indicators_present": has_regex_indicators if method == "semantic_primary" else None,
            "regex_score": regex_conf,  # Reported separately, not combined
        }

        if semantic_conf is not None:
            result["semantic_score"] = semantic_conf
            result["metric_space"] = "embedding_cosine_similarity"
        else:
            result["metric_space"] = "regex_pattern_count"

        return result

    def detect_nihilism(self, text: str) -> Dict[str, Any]:
        """
        Detect nihilism using semantic embeddings (primary) with regex as supplementary indicators.

        Semantic and regex scores are NOT combined - they're in different metric spaces.
        Semantic (embedding similarity) is the primary metric when available.
        Regex patterns provide qualitative indicators only.
        """
        # Get regex patterns as qualitative indicators
        regex_conf, indicators = self._regex_score_nihilism(text)

        # Semantic score is PRIMARY metric (embedding latent space)
        if self.use_semantic and self.semantic_scorer:
            semantic_result = self.semantic_scorer.score_nihilism(text)
            semantic_conf = semantic_result["semantic_score"]

            # Use semantic score as confidence (100% metric-relative to embedding space)
            confidence = semantic_conf
            method = "semantic_primary"

            # Regex provides supplementary boolean indicators, not score
            has_regex_indicators = regex_conf > 0.3
        else:
            # Fallback to regex when semantic unavailable
            confidence = regex_conf
            semantic_conf = None
            method = "regex_fallback"
            has_regex_indicators = True

        # Severity based on primary confidence
        if confidence < 0.3:
            severity = "low"
        elif confidence < 0.5:
            severity = "medium"
        elif confidence < 0.7:
            severity = "high"
        else:
            severity = "critical"

        result = {
            "nihilism_detected": confidence > 0.4,
            "confidence": confidence,  # Pure semantic or pure regex, never mixed
            "severity": severity,
            "indicators": indicators,  # Qualitative patterns found
            "scoring_method": method,
            "regex_indicators_present": has_regex_indicators if method == "semantic_primary" else None,
            "regex_score": regex_conf,  # Reported separately, not combined
        }

        if semantic_conf is not None:
            result["semantic_score"] = semantic_conf
            result["metric_space"] = "embedding_cosine_similarity"
        else:
            result["metric_space"] = "regex_pattern_count"

        return result

    def detect_middle_path_proximity(self, text: str) -> Dict[str, Any]:
        """
        Measure middle path proximity using semantic embeddings (primary) with regex as supplementary indicators.

        Semantic and regex scores are NOT combined - they're in different metric spaces.
        Semantic (embedding similarity) is the primary metric when available.
        Regex patterns provide qualitative indicators only.
        """
        # Get regex patterns as qualitative indicators
        regex_score, indicators = self._regex_score_middle_path(text)

        # Semantic score is PRIMARY metric (embedding latent space)
        if self.use_semantic and self.semantic_scorer:
            semantic_result = self.semantic_scorer.score_middle_path(text)
            semantic_score = semantic_result["semantic_score"]

            # Use semantic score as primary (100% metric-relative to embedding space)
            middle_path_score = semantic_score
            method = "semantic_primary"

            # Regex provides supplementary boolean indicators, not score
            has_regex_indicators = regex_score > 0.3
        else:
            # Fallback to regex when semantic unavailable
            middle_path_score = regex_score
            semantic_score = None
            method = "regex_fallback"
            has_regex_indicators = True

        # Proximity based on primary score
        if middle_path_score < 0.3:
            proximity = "far"
        elif middle_path_score < 0.5:
            proximity = "approaching"
        elif middle_path_score < 0.7:
            proximity = "close"
        else:
            proximity = "very_close"

        result = {
            "middle_path_score": middle_path_score,  # Pure semantic or pure regex, never mixed
            "proximity": proximity,
            "indicators": {"positive": indicators, "areas_for_refinement": []},
            "scoring_method": method,
            "regex_indicators_present": has_regex_indicators if method == "semantic_primary" else None,
            "regex_score": regex_score,  # Reported separately, not combined
        }

        if semantic_score is not None:
            result["semantic_score"] = semantic_score
            result["metric_space"] = "embedding_cosine_similarity"
        else:
            result["metric_space"] = "regex_pattern_count"

        return result

    def detect_clinging(self, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Detect clinging patterns in conversation history.
        """
        if not conversation_history:
            return {"clinging_detected": False, "confidence": 0.0}

        user_messages = [msg["content"] for msg in conversation_history if msg.get("role") == "user"]

        if len(user_messages) < 2:
            return {"clinging_detected": False, "confidence": 0.0, "note": "Insufficient history"}

        # Combine all user messages for semantic analysis
        combined_text = " ".join(user_messages)

        # Use semantic scoring for clinging
        if self.use_semantic and self.semantic_scorer:
            result = self.semantic_scorer.score_clinging(combined_text)
            confidence = result["semantic_score"]
            method = "semantic"
        else:
            # Fallback: simple pattern matching
            exclamations = sum(msg.count('!') for msg in user_messages)
            caps_words = sum(len(re.findall(r'\b[A-Z]{3,}\b', msg)) for msg in user_messages)
            confidence = min((exclamations + caps_words) / 10.0, 1.0)
            method = "regex_fallback"

        return {
            "clinging_detected": confidence > 0.4,
            "clinging_type": "attachment_to_views",
            "confidence": confidence,
            "scoring_method": method,
            "patterns": []
        }
