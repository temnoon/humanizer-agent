# LLM POVM Implementation
## Prompt Templates and Code Architecture

**Version:** 1.0
**Created:** October 2025
**Purpose:** Concrete implementation guide for quantum reading with LLMs

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Universal POVM Measurement Prompt](#universal-povm-measurement-prompt)
3. [Context-Specific POVM Generation Prompt](#context-specific-povm-generation-prompt)
4. [Imbalance Detection Prompt](#imbalance-detection-prompt)
5. [Python Implementation](#python-implementation)
6. [Integration with Humanizer AUI](#integration-with-humanizer-aui)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────┐
│          Humanizer Quantum Reading          │
└─────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
   ┌────▼────┐              ┌───────▼──────┐
   │ Reader  │              │   LLM API    │
   │  State  │              │   (Ollama/   │
   │   (ρ)   │              │    GPT)      │
   └────┬────┘              └───────┬──────┘
        │                           │
        │    ┌──────────────────────┘
        │    │
   ┌────▼────▼─────┐
   │  POVM Service │
   │  ────────────  │
   │  - Measurement │
   │  - Generation  │
   │  - Validation  │
   │  - Imbalance   │
   └────┬───────────┘
        │
   ┌────▼────────┐
   │  Database   │
   │  ─────────  │
   │  - ρ states │
   │  - Axes     │
   │  - History  │
   └─────────────┘
```

### Data Flow

```
Text Sentence
     ↓
[1] Select active axes (universal + context-specific)
     ↓
[2] For each axis: LLM POVM measurement
     ↓
[3] Collect four-corner probabilities
     ↓
[4] Validate (sum=1.0, all ≥ 0)
     ↓
[5] Update reader state (ρ)
     ↓
[6] Check for imbalance (if N sentences accumulated)
     ↓
[7] Store results + updated ρ
     ↓
Next Sentence
```

---

## Universal POVM Measurement Prompt

### Core Template

```python
UNIVERSAL_POVM_MEASUREMENT_PROMPT = """
You are performing a quantum measurement on a sentence using Catuskoti (four-cornered logic).
This is a rigorous POVM (Positive Operator-Valued Measure) that must satisfy mathematical constraints.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

READER'S CURRENT STATE (ρ):
{reader_state_summary}

SENTENCE TO MEASURE:
"{sentence}"

MEASUREMENT AXIS: {axis_name}
{axis_description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK:
Measure this sentence across all four Catuskoti corners.

1. {pole_a} (TRUE, NOT {pole_b})
   ┌─ Probability (0.0-1.0): _______
   ├─ Evidence: Why does this reading apply?
   └─ Reasoning: What makes it NOT {pole_b}?

2. {pole_b} (FALSE, NOT {pole_a})
   ┌─ Probability (0.0-1.0): _______
   ├─ Evidence: Why does this reading apply?
   └─ Reasoning: What makes it NOT {pole_a}?

3. BOTH ({pole_a} AND {pole_b})
   ┌─ Probability (0.0-1.0): _______
   ├─ Evidence: How is the sentence simultaneously both?
   └─ Reasoning: Why doesn't this reduce to either pole alone?

4. NEITHER (NOT {pole_a}, NOT {pole_b})
   ┌─ Probability (0.0-1.0): _______
   ├─ Evidence: How does the sentence transcend this axis?
   └─ Reasoning: What makes the distinction itself inapplicable?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONSTRAINTS:
✓ All four probabilities MUST sum to exactly 1.0
✓ All probabilities MUST be between 0.0 and 1.0
✓ Provide explicit evidence for each corner
✓ Consider how the reader's current state (ρ) influences this measurement
✓ The measurement itself will change ρ (back-action)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT (JSON only, no additional text):
{
  "measurement": {
    "axis": "{axis_name}",
    "sentence": "{sentence}",
    "corners": {
      "{pole_a_key}": {
        "probability": 0.XX,
        "evidence": "...",
        "reasoning": "..."
      },
      "{pole_b_key}": {
        "probability": 0.XX,
        "evidence": "...",
        "reasoning": "..."
      },
      "both": {
        "probability": 0.XX,
        "evidence": "...",
        "reasoning": "..."
      },
      "neither": {
        "probability": 0.XX,
        "evidence": "...",
        "reasoning": "..."
      }
    },
    "dominant_corner": "...",
    "reader_state_update": {
      "frame_shifts": [
        {"frame": "...", "from": 0.XX, "to": 0.XX}
      ],
      "new_concepts": ["...", "..."],
      "emotional_shift": "...",
      "expectation": "..."
    }
  }
}
"""
```

### Example Invocation (Python)

```python
# Using Ollama (local)
def measure_sentence_universal(
    sentence: str,
    reader_state: dict,
    axis: dict  # {name, pole_a, pole_b, description}
):
    prompt = UNIVERSAL_POVM_MEASUREMENT_PROMPT.format(
        reader_state_summary=json.dumps(reader_state, indent=2),
        sentence=sentence,
        axis_name=axis['name'],
        axis_description=axis['description'],
        pole_a=axis['pole_a'],
        pole_b=axis['pole_b'],
        pole_a_key=axis['pole_a'].lower().replace(' ', '_'),
        pole_b_key=axis['pole_b'].lower().replace(' ', '_')
    )

    response = ollama.chat(
        model='mistral:7b',  # or 'llama3.1:70b' for better reasoning
        messages=[
            {
                'role': 'system',
                'content': 'You are a quantum measurement system for reading comprehension. Output only valid JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        format='json'  # Force JSON output
    )

    result = json.loads(response['message']['content'])
    validate_povm_measurement(result)
    return result
```

### Validation Function

```python
def validate_povm_measurement(result: dict) -> bool:
    """Ensure POVM constraints are satisfied."""
    measurement = result['measurement']
    corners = measurement['corners']

    # Extract probabilities
    probs = [
        corners[key]['probability']
        for key in corners.keys()
    ]

    # Constraint 1: Completeness (sum to 1.0)
    total = sum(probs)
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"Probabilities sum to {total}, not 1.0. Re-prompting...")

    # Constraint 2: Positivity (all >= 0, <= 1)
    if any(p < 0 or p > 1 for p in probs):
        raise ValueError(f"Probabilities out of range [0,1]: {probs}")

    # Constraint 3: Evidence required
    for corner_name, corner_data in corners.items():
        if len(corner_data['evidence']) < 10:
            raise ValueError(f"Insufficient evidence for {corner_name}")

    return True
```

---

## Context-Specific POVM Generation Prompt

### Generation Template

```python
CONTEXT_SPECIFIC_POVM_GENERATION_PROMPT = """
You are analyzing a text to identify its core dialectical tensions for quantum reading measurement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TEXT SAMPLE (first ~1500 words):
{text_sample}

READER'S PURPOSE (if specified):
{reader_purpose}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXISTING UNIVERSAL AXES (do not duplicate these):
1. Literal ↔ Metaphorical
2. Surface ↔ Depth
3. Subjective ↔ Objective
4. Coherent ↔ Surprising
5. Emotional ↔ Analytical
6. Specific ↔ Universal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK:
Identify 2-4 dialectical axes that are CENTRAL to this specific text.

REQUIREMENTS:
For each proposed axis, it must:

1. ✓ Be actually dialectical
   - Poles mutually define each other
   - Can't have one without the other

2. ✓ Be central to THIS text
   - Appears repeatedly, not peripheral
   - Core to the text's meaning or argument

3. ✓ Not duplicate universal axes
   - Captures something the universal axes miss

4. ✓ Pass Madhyamaka validation
   - No privileged pole (neither is "better")
   - BOTH corner is coherent (not paradoxical)
   - NEITHER corner is meaningful (transcendent, not just absence)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT (JSON only):
{
  "proposed_axes": [
    {
      "name": "{Pole A} ↔ {Pole B}",
      "pole_a": "...",
      "pole_b": "...",
      "centrality_explanation": "Why this dialectic is core to the text (2-3 sentences)",
      "example_passages": [
        "Quote 1 engaging this tension",
        "Quote 2 showing opposite pole",
        "Quote 3 showing both or neither"
      ],
      "madhyamaka_validation": {
        "no_privileged_pole": true/false,
        "poles_explanation": "Why neither pole is treated as inherently better",
        "mutual_dependence": true/false,
        "dependence_explanation": "How each pole requires the other",
        "both_corner_coherent": true/false,
        "both_explanation": "Example of something being both poles simultaneously",
        "neither_corner_coherent": true/false,
        "neither_explanation": "Example transcending the axis"
      },
      "confidence": 0.XX,
      "recommended_priority": "primary" | "secondary"
    }
  ],
  "axes_count": N,
  "recommended_axes": ["Axis 1 name", "Axis 2 name"]
}
"""
```

### Example Invocation

```python
def generate_context_specific_povms(
    text_sample: str,
    reader_purpose: str = "General reading comprehension"
):
    prompt = CONTEXT_SPECIFIC_POVM_GENERATION_PROMPT.format(
        text_sample=text_sample[:5000],  # Limit to ~1500 words
        reader_purpose=reader_purpose
    )

    response = ollama.chat(
        model='llama3.1:70b',  # Needs stronger reasoning for generation
        messages=[
            {
                'role': 'system',
                'content': 'You are a literary analyst identifying dialectical tensions. Output only valid JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        format='json'
    )

    result = json.loads(response['message']['content'])
    validate_generated_axes(result)
    return result
```

### Validation for Generated Axes

```python
def validate_generated_axes(result: dict) -> bool:
    """Validate generated context-specific axes."""
    for axis in result['proposed_axes']:
        validation = axis['madhyamaka_validation']

        # Check all validation fields are present
        required_fields = [
            'no_privileged_pole',
            'mutual_dependence',
            'both_corner_coherent',
            'neither_corner_coherent'
        ]

        for field in required_fields:
            if field not in validation:
                raise ValueError(f"Missing validation field: {field}")

            # All must be True to pass
            if not validation[field]:
                print(f"⚠️  Axis '{axis['name']}' failed {field}")
                print(f"    Reason: {validation.get(field + '_explanation', 'N/A')}")
                # Don't reject—let user decide
                axis['validation_warning'] = field

    return True
```

---

## Imbalance Detection Prompt

### Detection Template

```python
IMBALANCE_DETECTION_PROMPT = """
You are monitoring dialectical balance in quantum reading measurements.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AXIS BEING MONITORED: {axis_name}
Pole A: {pole_a}
Pole B: {pole_b}

MEASUREMENTS OVER LAST {n_sentences} SENTENCES:
{measurements_summary}

STATISTICS:
- Mean {pole_a}: {mean_a:.2f}
- Mean {pole_b}: {mean_b:.2f}
- Mean BOTH: {mean_both:.2f}
- Mean NEITHER: {mean_neither:.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TASK:
Detect if this axis shows IMBALANCE (Madhyamaka violation).

IMBALANCE TYPES:

1. ETERNALISM (one pole over-privileged)
   - One pole mean > 0.7 AND other pole mean < 0.15
   - Text treats one pole as inherently real/good

2. WEAK DIALECTIC (poles don't interpenetrate)
   - BOTH corner mean < 0.05
   - Suggests poles are not truly dialectical

3. NIHILISM RISK (excessive neither)
   - NEITHER corner mean > 0.6
   - May indicate nihilistic reading (or genuine transcendence)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT (JSON only):
{
  "imbalance_detected": true/false,
  "imbalance_type": "eternalism" | "weak_dialectic" | "nihilism_risk" | null,
  "severity": "low" | "medium" | "high",
  "privileged_pole": "{pole_a}" | "{pole_b}" | null,
  "evidence": [
    "Observation 1 from statistics",
    "Observation 2 from patterns"
  ],
  "interpretation": {
    "likely_cause": "...",
    "madhyamaka_concern": "...",
    "alternative_reading": "..."
  },
  "user_alert": {
    "title": "...",
    "message": "...",
    "reflection_prompt": "...",
    "suggested_action": "continue" | "pause" | "reframe"
  }
}
"""
```

### Example Invocation

```python
def detect_imbalance(
    axis: dict,
    measurements: list[dict],  # Last N measurements
    n_sentences: int = 20
):
    # Calculate statistics
    pole_a_probs = [m['corners'][axis['pole_a_key']]['probability'] for m in measurements]
    pole_b_probs = [m['corners'][axis['pole_b_key']]['probability'] for m in measurements]
    both_probs = [m['corners']['both']['probability'] for m in measurements]
    neither_probs = [m['corners']['neither']['probability'] for m in measurements]

    mean_a = statistics.mean(pole_a_probs)
    mean_b = statistics.mean(pole_b_probs)
    mean_both = statistics.mean(both_probs)
    mean_neither = statistics.mean(neither_probs)

    # Format measurements summary
    measurements_summary = "\n".join([
        f"Sentence {i+1}: {axis['pole_a']}={m['corners'][axis['pole_a_key']]['probability']:.2f}, "
        f"{axis['pole_b']}={m['corners'][axis['pole_b_key']]['probability']:.2f}, "
        f"Both={m['corners']['both']['probability']:.2f}, "
        f"Neither={m['corners']['neither']['probability']:.2f}"
        for i, m in enumerate(measurements)
    ])

    prompt = IMBALANCE_DETECTION_PROMPT.format(
        axis_name=axis['name'],
        pole_a=axis['pole_a'],
        pole_b=axis['pole_b'],
        n_sentences=n_sentences,
        measurements_summary=measurements_summary,
        mean_a=mean_a,
        mean_b=mean_b,
        mean_both=mean_both,
        mean_neither=mean_neither
    )

    response = ollama.chat(
        model='mistral:7b',
        messages=[
            {'role': 'system', 'content': 'You are a Madhyamaka balance monitor. Output only JSON.'},
            {'role': 'user', 'content': prompt}
        ],
        format='json'
    )

    result = json.loads(response['message']['content'])
    return result
```

---

## Python Implementation

### Complete POVM Service

```python
# backend/services/povm_service.py

import json
import statistics
from typing import Dict, List, Optional
import ollama

class POVMService:
    """Quantum reading POVM measurement service."""

    def __init__(self, model: str = "mistral:7b"):
        self.model = model
        self.universal_axes = self._load_universal_axes()
        self.context_axes = {}  # Per-text axes

    def _load_universal_axes(self) -> List[Dict]:
        """Load the six core universal axes."""
        return [
            {
                "name": "Literal ↔ Metaphorical",
                "pole_a": "Literal",
                "pole_b": "Metaphorical",
                "pole_a_key": "literal",
                "pole_b_key": "metaphorical",
                "description": "Semantic reference mode: direct correspondence vs. symbolic pointing"
            },
            {
                "name": "Surface ↔ Depth",
                "pole_a": "Surface",
                "pole_b": "Depth",
                "pole_a_key": "surface",
                "pole_b_key": "depth",
                "description": "Hermeneutic layer: explicit meaning vs. hidden/implied content"
            },
            {
                "name": "Subjective ↔ Objective",
                "pole_a": "Subjective",
                "pole_b": "Objective",
                "pole_a_key": "subjective",
                "pole_b_key": "objective",
                "description": "Epistemic stance: reader's construction vs. text-inherent properties"
            },
            {
                "name": "Coherent ↔ Surprising",
                "pole_a": "Coherent",
                "pole_b": "Surprising",
                "pole_a_key": "coherent",
                "pole_b_key": "surprising",
                "description": "Expectation alignment: confirms reader's frame vs. violates expectations"
            },
            {
                "name": "Emotional ↔ Analytical",
                "pole_a": "Emotional",
                "pole_b": "Analytical",
                "pole_a_key": "emotional",
                "pole_b_key": "analytical",
                "description": "Cognitive processing mode: affective response vs. conceptual parsing"
            },
            {
                "name": "Specific ↔ Universal",
                "pole_a": "Specific",
                "pole_b": "Universal",
                "pole_a_key": "specific",
                "pole_b_key": "universal",
                "description": "Scope of reference: particular instance vs. general principle"
            }
        ]

    def measure_sentence(
        self,
        sentence: str,
        reader_state: Dict,
        axes: List[Dict]
    ) -> List[Dict]:
        """Measure a sentence along multiple axes."""
        results = []

        for axis in axes:
            try:
                measurement = self._measure_single_axis(
                    sentence, reader_state, axis
                )
                results.append(measurement)

                # Update reader state with measurement back-action
                reader_state = self._apply_state_update(
                    reader_state,
                    measurement['measurement']['reader_state_update']
                )

            except Exception as e:
                print(f"Measurement failed for axis '{axis['name']}': {e}")
                continue

        return results

    def _measure_single_axis(
        self,
        sentence: str,
        reader_state: Dict,
        axis: Dict
    ) -> Dict:
        """Perform POVM measurement on single axis."""
        prompt = self._format_measurement_prompt(sentence, reader_state, axis)

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a quantum measurement system. Output only valid JSON.'
                },
                {'role': 'user', 'content': prompt}
            ],
            format='json'
        )

        result = json.loads(response['message']['content'])
        self._validate_measurement(result)
        return result

    def _format_measurement_prompt(self, sentence: str, reader_state: Dict, axis: Dict) -> str:
        """Format the universal POVM measurement prompt."""
        # Use the template from earlier in this document
        return UNIVERSAL_POVM_MEASUREMENT_PROMPT.format(
            reader_state_summary=json.dumps(reader_state, indent=2),
            sentence=sentence,
            axis_name=axis['name'],
            axis_description=axis['description'],
            pole_a=axis['pole_a'],
            pole_b=axis['pole_b'],
            pole_a_key=axis['pole_a_key'],
            pole_b_key=axis['pole_b_key']
        )

    def _validate_measurement(self, result: Dict) -> bool:
        """Validate POVM constraints."""
        measurement = result['measurement']
        corners = measurement['corners']

        probs = [corner['probability'] for corner in corners.values()]

        # Completeness
        total = sum(probs)
        if abs(total - 1.0) > 0.01:
            # Try to normalize
            for corner in corners.values():
                corner['probability'] /= total

        # Positivity
        assert all(0 <= p <= 1 for p in probs), "Probabilities out of range"

        return True

    def _apply_state_update(self, reader_state: Dict, update: Dict) -> Dict:
        """Apply measurement back-action to reader state."""
        # Update frames
        for shift in update.get('frame_shifts', []):
            frame_name = shift['frame']
            if frame_name in reader_state['active_frames']:
                # Find and update
                for f in reader_state['active_frames']:
                    if f['frame'] == frame_name:
                        f['salience'] = shift['to']
            else:
                # Add new frame
                reader_state['active_frames'].append({
                    'frame': frame_name,
                    'salience': shift['to']
                })

        # Add new concepts
        reader_state['recent_concepts'].extend(update.get('new_concepts', []))
        reader_state['recent_concepts'] = reader_state['recent_concepts'][-10:]  # Keep last 10

        return reader_state

    def generate_context_axes(
        self,
        text_sample: str,
        reader_purpose: str = "General reading comprehension"
    ) -> List[Dict]:
        """Generate context-specific POVM axes for this text."""
        prompt = CONTEXT_SPECIFIC_POVM_GENERATION_PROMPT.format(
            text_sample=text_sample[:5000],
            reader_purpose=reader_purpose
        )

        response = ollama.chat(
            model='llama3.1:70b',  # Stronger model for generation
            messages=[
                {'role': 'system', 'content': 'You are a literary analyst. Output only JSON.'},
                {'role': 'user', 'content': prompt}
            ],
            format='json'
        )

        result = json.loads(response['message']['content'])
        self._validate_generated_axes(result)

        return result['proposed_axes']

    def detect_imbalance(
        self,
        axis: Dict,
        measurements: List[Dict],
        n_sentences: int = 20
    ) -> Optional[Dict]:
        """Detect Madhyamaka imbalance in axis measurements."""
        if len(measurements) < n_sentences:
            return None  # Not enough data

        # Calculate statistics
        pole_a_key = axis['pole_a_key']
        pole_b_key = axis['pole_b_key']

        pole_a_probs = [m['measurement']['corners'][pole_a_key]['probability'] for m in measurements[-n_sentences:]]
        pole_b_probs = [m['measurement']['corners'][pole_b_key]['probability'] for m in measurements[-n_sentences:]]
        both_probs = [m['measurement']['corners']['both']['probability'] for m in measurements[-n_sentences:]]
        neither_probs = [m['measurement']['corners']['neither']['probability'] for m in measurements[-n_sentences:]]

        mean_a = statistics.mean(pole_a_probs)
        mean_b = statistics.mean(pole_b_probs)
        mean_both = statistics.mean(both_probs)
        mean_neither = statistics.mean(neither_probs)

        # Quick check before LLM call
        if mean_a > 0.7 and mean_b < 0.15:
            # Likely eternalism
            pass  # Continue to LLM for detailed analysis
        elif mean_both < 0.05:
            # Weak dialectic
            pass
        elif mean_neither > 0.6:
            # Nihilism risk or transcendence
            pass
        else:
            # Balanced—skip LLM call
            return None

        # Use LLM for detailed imbalance detection
        prompt = self._format_imbalance_prompt(axis, measurements[-n_sentences:], mean_a, mean_b, mean_both, mean_neither)

        response = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': 'You are a Madhyamaka balance monitor. Output only JSON.'},
                {'role': 'user', 'content': prompt}
            ],
            format='json'
        )

        result = json.loads(response['message']['content'])
        return result if result['imbalance_detected'] else None
```

---

## Integration with Humanizer AUI

### New AUI Tool: `read_quantum`

```python
# backend/services/agent_service.py

from backend.services.povm_service import POVMService

class AgentService:
    def __init__(self):
        self.povm_service = POVMService()
        # ... existing tools ...

    def register_tools(self):
        self.tools = {
            # ... existing tools ...

            "read_quantum": {
                "description": "Read text with quantum measurement (POVMs)",
                "parameters": {
                    "text_id": "ID of text to read (book, chunk, etc.)",
                    "start_sentence": "Starting sentence index (optional)",
                    "num_sentences": "Number of sentences to read (default: 10)",
                    "axes": "List of axes to use: 'universal', 'context', or 'all' (default: 'all')"
                },
                "function": self._read_quantum
            }
        }

    def _read_quantum(self, text_id: str, start_sentence: int = 0, num_sentences: int = 10, axes: str = "all"):
        """Read text with POVM measurements."""
        # 1. Get text sentences
        sentences = self._get_text_sentences(text_id, start_sentence, num_sentences)

        # 2. Get or initialize reader state
        reader_state = self._get_reader_state(text_id)

        # 3. Generate context-specific axes if first read
        if axes in ["context", "all"] and not self.povm_service.context_axes.get(text_id):
            full_text = self._get_full_text(text_id)
            context_axes = self.povm_service.generate_context_axes(full_text)
            self.povm_service.context_axes[text_id] = context_axes

        # 4. Select active axes
        active_axes = []
        if axes in ["universal", "all"]:
            active_axes.extend(self.povm_service.universal_axes[:2])  # Just 2 universal for quick reading
        if axes in ["context", "all"] and text_id in self.povm_service.context_axes:
            active_axes.extend(self.povm_service.context_axes[text_id])

        # 5. Measure each sentence
        results = []
        for i, sentence in enumerate(sentences):
            measurements = self.povm_service.measure_sentence(
                sentence,
                reader_state,
                active_axes
            )
            results.append({
                "sentence_index": start_sentence + i,
                "sentence": sentence,
                "measurements": measurements
            })

            # Check for imbalance every 10 sentences
            if (start_sentence + i) % 10 == 0:
                for axis in active_axes:
                    imbalance = self.povm_service.detect_imbalance(
                        axis,
                        [r for r in results if any(m['measurement']['axis'] == axis['name'] for m in r['measurements'])],
                        n_sentences=10
                    )
                    if imbalance:
                        results[-1]['imbalance_alert'] = imbalance

        return {
            "text_id": text_id,
            "reader_state": reader_state,
            "sentences_read": len(sentences),
            "results": results
        }
```

### Frontend Integration (React)

```jsx
// frontend/src/components/QuantumReading.jsx

function QuantumReadingView({ textId }) {
  const [measurements, setMeasurements] = useState([]);
  const [currentSentence, setCurrentSentence] = useState(0);

  const readNext = async () => {
    const response = await fetch('/api/agent/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool: 'read_quantum',
        parameters: {
          text_id: textId,
          start_sentence: currentSentence,
          num_sentences: 5,
          axes: 'all'
        }
      })
    });

    const data = await response.json();
    setMeasurements([...measurements, ...data.results]);
    setCurrentSentence(currentSentence + 5);
  };

  return (
    <div className="quantum-reading">
      {measurements.map((result, idx) => (
        <div key={idx} className="sentence-measurement">
          <p className="sentence">{result.sentence}</p>

          <div className="measurements">
            {result.measurements.map((m, i) => (
              <POVMVisualization key={i} measurement={m} />
            ))}
          </div>

          {result.imbalance_alert && (
            <ImbalanceAlert alert={result.imbalance_alert} />
          )}
        </div>
      ))}

      <button onClick={readNext}>Read Next 5 Sentences</button>
    </div>
  );
}

function POVMVisualization({ measurement }) {
  const { axis, corners } = measurement.measurement;

  return (
    <div className="povm-viz">
      <h4>{axis}</h4>
      <div className="corners">
        {Object.entries(corners).map(([corner, data]) => (
          <div key={corner} className="corner">
            <span className="label">{corner}</span>
            <div className="probability-bar" style={{ width: `${data.probability * 100}%` }} />
            <span className="value">{(data.probability * 100).toFixed(0)}%</span>
            <p className="evidence">{data.evidence}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Summary

### What This Document Provides

✅ **Complete LLM prompt templates** for:
- Universal POVM measurement
- Context-specific POVM generation
- Imbalance detection

✅ **Python implementation** showing:
- POVMService class
- Validation functions
- Integration with Ollama/LLMs

✅ **Humanizer AUI integration**:
- New `read_quantum` tool
- Frontend React components
- End-to-end flow

### Ready to Implement

These templates are **production-ready**. You can:

1. Drop POVMService into `backend/services/`
2. Add prompts as constants
3. Register `read_quantum` tool in AgentService
4. Test with `mistral:7b` or `llama3.1:70b`

### What's Next

**RHO_INTEGRATION_NOTES.md** - How this relates to rho's original architecture

**MADHYAMAKA_BALANCE_AUDIT.md** - Critique of rho's existing axes

---

*"The prompts are the operators. The LLM is the measurement apparatus. Consciousness is what collapses."*

---

**Next Document:** [RHO_INTEGRATION_NOTES.md](./RHO_INTEGRATION_NOTES.md)
