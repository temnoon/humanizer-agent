"""
Narrative Analyzer - Sentence-by-Sentence Madhyamaka Analysis

Analyzes narratives sentence-by-sentence for proximity to the four corners:
- Eternalism (reification)
- Nihilism (denial of convention)
- Middle Path (balanced understanding)
- Clinging (attachment to views)

Returns color-coded scores for GUI visualization.
"""

import re
from typing import List, Dict, Any, Tuple

from .detector import MadhyamakaDetector


class NarrativeAnalyzer:
    """
    Analyzes narratives sentence-by-sentence for Madhyamaka metrics.

    Provides color-coded scores for visual overlay rendering.
    """

    # Color scale for middle path proximity
    COLOR_SCALE = {
        "very_close": "#22c55e",   # green-500
        "close": "#4ade80",        # green-400
        "approaching": "#fbbf24",  # yellow-400
        "far": "#fb923c",          # orange-400
        "very_far": "#ef4444"      # red-500
    }

    def __init__(self):
        """Initialize with Madhyamaka detector"""
        self.detector = MadhyamakaDetector()

    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Handles common abbreviations and edge cases.
        """
        # Simple sentence splitting (can be improved with nltk)
        # Handles: periods, exclamation marks, question marks
        # Preserves: Mr., Dr., etc.

        # Replace common abbreviations temporarily
        text = text.replace("Mr.", "Mr<ABBREV>")
        text = text.replace("Mrs.", "Mrs<ABBREV>")
        text = text.replace("Dr.", "Dr<ABBREV>")
        text = text.replace("Ms.", "Ms<ABBREV>")
        text = text.replace("i.e.", "i<ABBREV>e<ABBREV>")
        text = text.replace("e.g.", "e<ABBREV>g<ABBREV>")

        # Split on sentence boundaries
        sentences = re.split(r'[.!?]+\s+', text)

        # Restore abbreviations and clean
        sentences = [
            s.replace("<ABBREV>", ".").strip()
            for s in sentences
            if s.strip()
        ]

        return sentences

    def _score_to_color(self, score: float, metric: str = "middle_path") -> str:
        """
        Convert score to color based on metric.

        For middle_path: higher score = greener (closer to middle path)
        For eternalism/nihilism: higher score = redder (more extreme)
        """
        if metric == "middle_path":
            # Higher is better
            if score >= 0.7:
                return self.COLOR_SCALE["very_close"]
            elif score >= 0.5:
                return self.COLOR_SCALE["close"]
            elif score >= 0.3:
                return self.COLOR_SCALE["approaching"]
            elif score >= 0.15:
                return self.COLOR_SCALE["far"]
            else:
                return self.COLOR_SCALE["very_far"]
        else:
            # For eternalism/nihilism/clinging: higher is worse (invert colors)
            if score >= 0.7:
                return self.COLOR_SCALE["very_far"]
            elif score >= 0.5:
                return self.COLOR_SCALE["far"]
            elif score >= 0.3:
                return self.COLOR_SCALE["approaching"]
            elif score >= 0.15:
                return self.COLOR_SCALE["close"]
            else:
                return self.COLOR_SCALE["very_close"]

    def _get_proximity_label(self, score: float) -> str:
        """Get human-readable proximity label"""
        if score >= 0.7:
            return "very_close"
        elif score >= 0.5:
            return "close"
        elif score >= 0.3:
            return "approaching"
        else:
            return "far"

    def analyze_sentence(self, sentence: str) -> Dict[str, Any]:
        """
        Analyze single sentence for all four metrics.

        Returns:
            {
                "text": str,
                "scores": {
                    "middle_path": float,
                    "eternalism": float,
                    "nihilism": float,
                    "clinging": float
                },
                "dominant": str,
                "colors": {
                    "middle_path": str,
                    "eternalism": str,
                    "nihilism": str,
                    "clinging": str
                }
            }
        """
        # Get all scores
        middle_path_result = self.detector.detect_middle_path_proximity(sentence)
        eternalism_result = self.detector.detect_eternalism(sentence)
        nihilism_result = self.detector.detect_nihilism(sentence)

        scores = {
            "middle_path": middle_path_result["middle_path_score"],
            "eternalism": eternalism_result["confidence"],
            "nihilism": nihilism_result["confidence"],
            "clinging": 0.0  # Clinging needs conversation history
        }

        # Determine dominant tendency
        dominant = max(scores, key=scores.get)

        # Get colors for each metric
        colors = {
            "middle_path": self._score_to_color(scores["middle_path"], "middle_path"),
            "eternalism": self._score_to_color(scores["eternalism"], "eternalism"),
            "nihilism": self._score_to_color(scores["nihilism"], "nihilism"),
            "clinging": self._score_to_color(scores["clinging"], "clinging"),
        }

        return {
            "text": sentence,
            "scores": scores,
            "dominant": dominant,
            "colors": colors,
            "proximity_labels": {
                "middle_path": self._get_proximity_label(scores["middle_path"]),
                "eternalism": "low" if scores["eternalism"] < 0.5 else "high",
                "nihilism": "low" if scores["nihilism"] < 0.5 else "high",
            }
        }

    def analyze_narrative(
        self,
        text: str,
        primary_metric: str = "middle_path"
    ) -> Dict[str, Any]:
        """
        Analyze entire narrative sentence-by-sentence.

        Args:
            text: Full narrative text
            primary_metric: Which metric to emphasize (middle_path, eternalism, nihilism)

        Returns:
            {
                "sentences": List[Dict],
                "overall_scores": Dict,
                "primary_metric": str,
                "summary": str
            }
        """
        sentences = self._split_sentences(text)

        analyzed_sentences = []

        for i, sentence in enumerate(sentences):
            analysis = self.analyze_sentence(sentence)
            analysis["index"] = i
            analysis["primary_color"] = analysis["colors"][primary_metric]
            analyzed_sentences.append(analysis)

        # Calculate overall scores
        if analyzed_sentences:
            overall_scores = {
                "middle_path": sum(s["scores"]["middle_path"] for s in analyzed_sentences) / len(analyzed_sentences),
                "eternalism": sum(s["scores"]["eternalism"] for s in analyzed_sentences) / len(analyzed_sentences),
                "nihilism": sum(s["scores"]["nihilism"] for s in analyzed_sentences) / len(analyzed_sentences),
            }
        else:
            overall_scores = {"middle_path": 0.0, "eternalism": 0.0, "nihilism": 0.0}

        # Generate summary
        summary = self._generate_summary(overall_scores, primary_metric, len(analyzed_sentences))

        return {
            "sentences": analyzed_sentences,
            "overall_scores": overall_scores,
            "primary_metric": primary_metric,
            "summary": summary,
            "sentence_count": len(analyzed_sentences)
        }

    def _generate_summary(self, overall_scores: Dict[str, float], metric: str, count: int) -> str:
        """Generate human-readable summary"""
        score = overall_scores.get(metric, 0.0)

        if metric == "middle_path":
            if score >= 0.7:
                return f"This narrative shows strong middle path understanding across {count} sentences (average score: {score:.2f})"
            elif score >= 0.5:
                return f"This narrative leans toward middle path understanding ({count} sentences, average: {score:.2f})"
            elif score >= 0.3:
                return f"This narrative is approaching middle path understanding ({count} sentences, average: {score:.2f})"
            else:
                return f"This narrative shows minimal middle path understanding ({count} sentences, average: {score:.2f})"
        elif metric == "eternalism":
            if score >= 0.5:
                return f"This narrative shows significant eternalism/reification ({count} sentences, average: {score:.2f})"
            else:
                return f"This narrative shows low eternalism ({count} sentences, average: {score:.2f})"
        elif metric == "nihilism":
            if score >= 0.5:
                return f"This narrative shows significant nihilism ({count} sentences, average: {score:.2f})"
            else:
                return f"This narrative shows low nihilism ({count} sentences, average: {score:.2f})"

        return f"Analyzed {count} sentences"
