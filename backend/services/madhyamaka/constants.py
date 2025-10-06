"""
Madhyamaka Constants - Enums and Teachings

Core constants for the Madhyamaka Middle Path system:
- ExtremeType enum
- Nagarjuna's teachings database
"""

from enum import Enum


class ExtremeType(Enum):
    """Types of extreme views"""
    ETERNALISM = "eternalism"  # Reification, inherent existence
    NIHILISM = "nihilism"  # Denial of conventional function
    MIDDLE_PATH = "middle_path"  # Neither extreme
    CLINGING = "clinging"  # Attachment to views


# Nagarjuna's teachings database
NAGARJUNA_TEACHINGS = {
    "emptiness_not_nihilism": {
        "quote": "Those who do not discern the distinction between the two truths cannot discern the profound truth of the Buddha's teaching.",
        "source": "Mūlamadhyamakakārikā XXIV.9",
        "context": "nihilism_detected",
        "explanation": "Emptiness doesn't mean nothingness. Things function conventionally while being empty of inherent existence."
    },
    "clinging_to_emptiness": {
        "quote": "Victorious ones have said emptiness is the relinquishing of all views. Those who are possessed of the view of emptiness are said to be incorrigible.",
        "source": "Mūlamadhyamakakārikā XIII.8",
        "context": "clinging_to_views",
        "explanation": "Even the view of emptiness must not be clung to. It is medicine, not a new possession."
    },
    "dependent_origination": {
        "quote": "We state that whatever is dependent arising, that is emptiness. That is dependent upon convention. That itself is the middle path.",
        "source": "Mūlamadhyamakakārikā XXIV.18",
        "context": "general",
        "explanation": "Emptiness = Dependent origination = The middle path. They are three ways of pointing to the same truth."
    }
}
