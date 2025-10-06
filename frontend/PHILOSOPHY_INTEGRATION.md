# Frontend Philosophy Integration

## Overview

The frontend has been redesigned to embody the "Language as a Sense" philosophical framework. This document explains the new components and how to use them.

## Three Realms Color System

All components use the Three Realms color palette defined in `tailwind.config.js`:

### Corporeal Realm (Green)
- **Color:** `#2D7D6E` (Forest Green)
- **Usage:** Input text areas, raw content, grounding elements
- **Meaning:** The physical substrate before consciousness constructs meaning

### Symbolic Realm (Purple)
- **Color:** `#6B46C1` (Royal Purple)
- **Usage:** Transformation parameters, framework selectors, outputs
- **Meaning:** Constructed belief frameworks (PERSONA/NAMESPACE/STYLE)

### Subjective Realm (Dark Blue/Indigo)
- **Color:** `#1E1B4B` (Deep Indigo)
- **Usage:** Background, contemplative exercises, witness prompts
- **Meaning:** Conscious awareness—the only truly "lived" realm

## Typography System

Three font families aligned with the Three Realms:

- **Contemplative (`font-contemplative`):** Serif fonts for subjective/conscious content
- **Structural (`font-structural`):** Sans-serif for symbolic/UI elements
- **Grounded (`font-grounded`):** Monospace for corporeal/input text

## New Components

### 1. MultiPerspectiveView

**Location:** `src/components/MultiPerspectiveView.jsx`

Displays multiple transformations simultaneously to reveal how meaning is constructed differently through different belief frameworks.

**Props:**
```jsx
<MultiPerspectiveView
  sourceText="Original text"
  perspectives={[
    {
      belief_framework: {
        persona: "Scholar",
        namespace: "academic",
        style: "formal",
        description: "...",
        philosophical_context: "..."
      },
      transformed_content: "...",
      emotional_profile: "...",
      emphasis: "..."
    }
  ]}
  philosophicalNote="Each perspective reveals..."
/>
```

**Features:**
- Expandable perspective cards
- Framework explanations
- Emotional profile analysis
- Awareness prompts

### 2. ContemplativeExercise

**Location:** `src/components/ContemplativeExercise.jsx`

Supports three types of contemplative practices:

#### Word Dissolution
- Animated character-by-character dissolution
- Emotional weight exploration
- Belief association prompts
- Guided practice instructions

#### Socratic Dialogue
- Questions that deconstruct assumptions
- Depth levels (1-5)
- Intent explanations
- Philosophical goals

#### Witness Prompt
- Stage-appropriate awareness pointers
- Minimal, spacious design
- Breathing prompts

**Props:**
```jsx
<ContemplativeExercise
  exercise={{
    exercise_type: "word_dissolution",
    word_dissolution: {
      word: "freedom",
      emotional_weight: "...",
      belief_associations: [...],
      dissolution_guidance: "..."
    },
    philosophical_context: "...",
    next_step: "..."
  }}
/>
```

### 3. PhilosophicalApp

**Location:** `src/PhilosophicalApp.jsx`

Main application component with three modes:

1. **Transform Mode:** Single perspective transformation
2. **Multi-Perspective Mode:** Generate 3 contrasting perspectives
3. **Contemplate Mode:** Contemplative exercises

**Features:**
- Three Realms visual design
- Mode tabs for different workflows
- Philosophical framing throughout
- Token validation with realm colors

## Installation

Install required dependencies:

```bash
cd frontend
npm install prop-types
```

## Running the Application

```bash
# Backend
cd backend
source venv/bin/activate
python main.py

# Frontend (in new terminal)
cd frontend
npm run dev
```

Visit: `http://localhost:5173`

## API Endpoints Used

### Single Transformation
```
POST /api/transform
```

### Multi-Perspective
```
POST /api/philosophical/perspectives
```

### Contemplative Exercises
```
POST /api/philosophical/contemplate
{
  "exercise_type": "word_dissolution" | "socratic_dialogue" | "witness",
  "content": "text",
  "user_stage": 1-5
}
```

### Archive Analysis (Future)
```
POST /api/philosophical/archive/analyze
```

## Design Principles Applied

All components follow the design principles from `docs/DESIGN_PRINCIPLES.md`:

1. ✅ **Make the Symbolic Realm Visible:** Framework parameters are explicit and explained
2. ✅ **Honor the Subjective Realm:** User has full agency, no forced flows
3. ✅ **Ground in the Corporeal Realm:** Input text uses green grounding colors
4. ✅ **Avoid False Objectivity:** No "better" labels, only "perspectives"
5. ✅ **Create Moments of Awareness:** Prompts throughout ("Notice how...")
6. ✅ **Support Emotional Belief Loop Revelation:** Emotional profiles shown
7. ✅ **Embrace Paradox:** Utility AND philosophy coexist

## User Journey Support

Components support all 5 stages of the user journey:

- **Stage 1 (Entry):** Transform mode with subtle philosophical hints
- **Stage 2 (Engagement):** Multi-perspective comparison
- **Stage 3 (Insight):** Framework explanations and emotional analysis
- **Stage 4 (Awakening):** Contemplative exercises
- **Stage 5 (Integration):** All modes available, user chooses

## Next Steps

Planned additions:

1. **Archive Visualization:** Belief network graph component
2. **Micro-Interactions:** Hover tooltips with philosophical insights
3. **Landing Page:** "Witness Language as a Sense" introduction
4. **Educational Content:** Interactive philosophy primers
5. **Custom Frameworks:** User-created PERSONA/NAMESPACE/STYLE combinations

## Switching Between Versions

The original utility-focused app is preserved in `App.jsx`. To switch:

```js
// main.jsx
import App from './App.jsx' // Utility version
// import PhilosophicalApp from './PhilosophicalApp.jsx' // Philosophy version
```

## Philosophy Notes

This interface is designed to:

- Reveal rather than conceal the constructed nature of meaning
- Support both utility (transformation) and awakening (realization)
- Make symbolic frameworks visible without overwhelming
- Honor user agency and conscious choice
- Create moments of awareness within workflows

The goal is not just text transformation—it's helping users witness their own meaning-making agency.

---

**Remember:** The Three Realms are not just a color scheme—they're an ontological framework for understanding how consciousness constructs meaning through language.
