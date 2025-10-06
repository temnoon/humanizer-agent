"""
Madhyamaka Middle Path Service

Buddhist philosophy-based language analysis and transformation.

This package provides:
- Detection of eternalism and nihilism in language
- Transformation toward middle path understanding
- Contemplative practice generation

Based on Nagarjuna's Madhyamaka philosophy.
"""

from .constants import ExtremeType, NAGARJUNA_TEACHINGS
from .detector import MadhyamakaDetector
from .transformer import MadhyamakaTransformer
from .contemplative import ContemplativePracticeGenerator
from .narrative_analyzer import NarrativeAnalyzer

__all__ = [
    "ExtremeType",
    "NAGARJUNA_TEACHINGS",
    "MadhyamakaDetector",
    "MadhyamakaTransformer",
    "ContemplativePracticeGenerator",
    "NarrativeAnalyzer",
]

__version__ = "1.0.0"
