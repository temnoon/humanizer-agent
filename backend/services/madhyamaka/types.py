"""
Madhyamaka Types - Core enums and constants

Defines the fundamental types used throughout the madhyamaka module.
"""

from enum import Enum


class ExtremeType(Enum):
    """Types of extreme views in Madhyamaka philosophy."""
    ETERNALISM = "eternalism"  # Reification, inherent existence
    NIHILISM = "nihilism"  # Denial of conventional function
    MIDDLE_PATH = "middle_path"  # Neither extreme
    CLINGING = "clinging"  # Attachment to views


# User journey stages for progressive depth
USER_STAGES = {
    1: "initial_awareness",      # Just beginning to notice language patterns
    2: "pattern_recognition",     # Seeing patterns in own speech
    3: "active_investigation",    # Actively questioning views
    4: "direct_experience",       # Contemplative practice
    5: "natural_expression"       # Spontaneous middle path speech
}


# Severity levels for extreme detection
SEVERITY_THRESHOLDS = {
    "low": (0.0, 0.3),
    "medium": (0.3, 0.6),
    "high": (0.6, 0.85),
    "critical": (0.85, 1.0)
}


def get_severity(score: float) -> str:
    """Determine severity level from confidence score."""
    for severity, (min_val, max_val) in SEVERITY_THRESHOLDS.items():
        if min_val <= score < max_val:
            return severity
    return "critical"  # >= 0.85
