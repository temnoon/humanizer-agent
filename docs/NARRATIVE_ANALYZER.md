# Narrative Analyzer - Color-Coded Madhyamaka Analysis

## Overview

The Narrative Analyzer provides real-time, sentence-by-sentence analysis of narratives using Madhyamaka Buddhist philosophy. Each sentence is evaluated across four dimensions and color-coded for visual understanding.

## Features

### 1. Sentence-by-Sentence Analysis
- Automatic sentence splitting
- Individual scoring for each sentence
- Four-corner evaluation:
  - **Middle Path** proximity (0-1 score)
  - **Eternalism** detection (reification/absolutism)
  - **Nihilism** detection (denial of convention)
  - **Clinging** detection (attachment to views)

### 2. Color-Coded Visualization
**Color Scale** (for Middle Path proximity):
- 🟢 **Very Close** (0.7-1.0): Deep Green (#22c55e)
- 🟢 **Close** (0.5-0.7): Light Green (#4ade80)
- 🟡 **Approaching** (0.3-0.5): Yellow (#fbbf24)
- 🟠 **Far** (0.15-0.3): Orange (#fb923c)
- 🔴 **Very Far** (0-0.15): Red (#ef4444)

For Eternalism/Nihilism, colors are inverted (higher scores = more red).

### 3. Interactive Features
- **Togglable Overlay**: Show/hide color highlighting
- **Markdown Rendering**: Toggle between plain text and markdown
- **Hover Tooltips**: Detailed scores appear on hover
- **Metric Selector**: Choose primary analysis metric
- **Sample Text**: Load example for quick testing

### 4. Detailed Scoring
Hover over any sentence to see:
- Middle Path score + proximity level
- Eternalism score + intensity level
- Nihilism score + intensity level
- Dominant tendency

## Usage

### API Endpoint
```
POST /api/madhyamaka/analyze-narrative
Content-Type: application/json

{
  "text": "Your narrative text here...",
  "primary_metric": "middle_path"  // or "eternalism", "nihilism"
}
```

### Response Format
```json
{
  "sentences": [
    {
      "text": "For every tool we gain, we lose a skill.",
      "index": 0,
      "scores": {
        "middle_path": 0.733,
        "eternalism": 0.072,
        "nihilism": 0.045
      },
      "colors": {
        "middle_path": "#22c55e",
        "eternalism": "#4ade80",
        "nihilism": "#22c55e"
      },
      "dominant": "middle_path",
      "primary_color": "#22c55e"
    }
  ],
  "overall_scores": {
    "middle_path": 0.513,
    "eternalism": 0.287,
    "nihilism": 0.112
  },
  "summary": "This narrative leans toward middle path understanding...",
  "sentence_count": 6
}
```

### Frontend Component
```jsx
import NarrativeAnalyzer from './components/NarrativeAnalyzer';

// Use in app
<NarrativeAnalyzer />
```

## Example Analysis

**Input Text:**
```
For every tool we gain, we lose a skill. This is the fundamental 
truth of human progress. Technology shapes us completely. But we 
must adapt and find balance in all things. Sometimes the old ways 
have merit, sometimes innovation serves us better.
```

**Analysis Results:**
1. "For every tool we gain, we lose a skill." 
   - Middle Path: 0.733 (Very Close) 🟢
   - Balanced trade-off acknowledged

2. "This is the fundamental truth of human progress."
   - Eternalism: 0.654 (High) 🔴
   - Absolutist language ("fundamental truth")

3. "Technology shapes us completely."
   - Eternalism: 0.521 (Medium) 🟠
   - Universal claim without qualification

4. "But we must adapt and find balance in all things."
   - Middle Path: 0.612 (Close) 🟢
   - Conditional, balanced perspective

5. "Sometimes the old ways have merit"
   - Middle Path: 0.743 (Very Close) 🟢
   - Conditional language ("sometimes")

6. "sometimes innovation serves us better."
   - Middle Path: 0.698 (Close) 🟢
   - Contextual, nuanced

**Overall Score:** Middle Path 0.513 (Close)

## Technical Architecture

### Backend
- **NarrativeAnalyzer** class (`services/madhyamaka/narrative_analyzer.py`)
- Sentence splitting with abbreviation handling
- Hybrid scoring (70% semantic, 30% regex)
- Color mapping based on score ranges

### Frontend
- **NarrativeAnalyzer** component (`components/NarrativeAnalyzer.jsx`)
- React hooks for state management
- Inline tooltips with CSS positioning
- TailwindCSS for styling
- Optional markdown/LaTeX rendering (react-markdown + rehype-katex)

### Scoring Method
Each sentence evaluated using:
1. **Semantic similarity** to curated examples (70% weight)
2. **Regex pattern matching** for explicit markers (30% weight)
3. Hybrid score: `(0.7 * semantic) + (0.3 * regex)`

## Use Cases

### 1. Writing Analysis
Analyze your own writing for unconscious extremes:
```
- Spot absolutist language
- Identify missing qualifications
- Find opportunities for nuance
```

### 2. Reading Comprehension
Understand author's philosophical stance:
```
- Map eternalism vs nihilism tendencies
- Track middle path proximity
- See sentence-level patterns
```

### 3. Meditation Practice
Use as contemplative tool:
```
- Write stream-of-consciousness
- Analyze for clinging patterns
- Track progress over time
```

### 4. Editorial Review
Review content before publication:
```
- Ensure balanced presentation
- Avoid dogmatic framing
- Add appropriate qualifications
```

## Tips

### Getting Accurate Results
1. **Use complete sentences** - Fragments may score poorly
2. **Provide context** - Longer texts give better overall scores
3. **Check all metrics** - Dominant tendency may not be primary metric
4. **Hover for details** - Surface scores don't show full picture

### Interpreting Colors
- **Green doesn't mean "correct"** - It means balanced/conditional
- **Red doesn't mean "wrong"** - It means absolutist/extreme
- **Context matters** - Some statements should be absolute (math, safety)

### Best Practices
- Start with sample text to understand scoring
- Toggle overlay on/off to see contrast
- Check individual sentence scores via hover
- Compare overall vs sentence-level scores

## Limitations

1. **Sentence splitting** - May split incorrectly on complex punctuation
2. **Context awareness** - Sentences analyzed independently
3. **Language** - Optimized for philosophical/narrative English
4. **Markdown rendering** - Complex LaTeX may not render perfectly in tooltip view

## Future Enhancements

Planned features:
- [ ] PDF export with color overlay
- [ ] Paragraph-level aggregation
- [ ] Historical tracking/comparison
- [ ] Custom color schemes
- [ ] Conversation mode (multi-turn analysis)
- [ ] Export to Anki flashcards
- [ ] Integration with contemplative practice generator

