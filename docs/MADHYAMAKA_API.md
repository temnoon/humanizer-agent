# Madhyamaka API Documentation
## Nagarjuna's Middle Path - Functional Implementation

---

## Overview

The Madhyamaka API implements Nagarjuna's Middle Path philosophy to guide users away from eternalism (reification) and nihilism (denial of conventional truth) in their relationship with language and meaning.

**Base URL**: `http://localhost:8000/api/madhyamaka`

**Philosophy**: This API uses language to help users see beyond language. The paradox is intentional.

---

## Quick Start

### 1. Start the Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

Backend runs on `http://localhost:8000`

### 2. Test Detection Endpoint

```bash
curl -X POST http://localhost:8000/api/madhyamaka/detect/eternalism \
  -H "Content-Type: application/json" \
  -d '{"content": "Success is absolutely essential for happiness."}'
```

### 3. View Interactive Docs

Visit `http://localhost:8000/docs#/madhyamaka`

---

## API Endpoints

### Detection Endpoints

#### 1. Detect Eternalism (Reification)

**POST** `/api/madhyamaka/detect/eternalism`

Detects when user is treating language/beliefs as having inherent, fixed existence.

**Request:**
```json
{
  "content": "Success is absolutely essential for happiness. It's a fundamental truth.",
  "context": {
    "user_id": "user_123",
    "user_stage": 1
  }
}
```

**Response:**
```json
{
  "eternalism_detected": true,
  "confidence": 0.87,
  "severity": "high",
  "indicators": [
    {
      "type": "absolute_language",
      "phrases": ["absolutely essential", "fundamental truth"],
      "severity": "high"
    },
    {
      "type": "essentialist_claims",
      "examples": ["Success is...", "happiness is..."],
      "severity": "medium"
    }
  ],
  "reified_concepts": ["success", "happiness", "essential", "truth"],
  "middle_path_alternatives": [
    {
      "suggestion": "conditional_softening",
      "reframed": "For some people, pursuing what they define as success contributes to happiness"
    }
  ],
  "teaching_moment": {
    "principle": "dependent_origination",
    "guidance": "Notice how 'success' arises dependent on cultural conditioning..."
  }
}
```

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/madhyamaka/detect/eternalism \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Language is the foundation of reality. Truth is absolute and unchanging."
  }'
```

---

#### 2. Detect Nihilism

**POST** `/api/madhyamaka/detect/nihilism`

Detects when user is denying conventional truth or confusing emptiness with nothingness.

**Request:**
```json
{
  "content": "Language is completely meaningless. Nothing we say matters at all.",
  "context": {"user_stage": 3}
}
```

**Response:**
```json
{
  "nihilism_detected": true,
  "confidence": 0.92,
  "severity": "critical",
  "indicators": [
    {
      "type": "absolute_negation",
      "phrases": ["completely meaningless", "nothing matters"],
      "severity": "high"
    },
    {
      "type": "emptiness_as_nothingness",
      "explanation": "Misunderstands śūnyatā as mere negation",
      "severity": "critical"
    }
  ],
  "middle_path_alternatives": [
    {
      "suggestion": "two_truths_framework",
      "reframed": "While language lacks inherent meaning (ultimate), it functions conventionally"
    }
  ],
  "teaching_moment": {
    "principle": "two_truths",
    "guidance": "Emptiness doesn't mean non-existence..."
  },
  "warning": {
    "level": "critical",
    "message": "User may be experiencing nihilistic insight. Offer grounding."
  }
}
```

---

#### 3. Detect Middle Path Proximity

**POST** `/api/madhyamaka/detect/middle-path-proximity`

Measures how close user's language is to middle path understanding (0-1 score).

**Request:**
```json
{
  "content": "When I feel angry, I notice that 'anger' is a label I apply. The label is useful for communication, but the experience doesn't inherently mean anything - I construct that meaning."
}
```

**Response:**
```json
{
  "middle_path_score": 0.91,
  "proximity": "very_close",
  "indicators": {
    "positive": [
      {
        "type": "metacognitive_awareness",
        "evidence": "I notice that 'anger' is a label",
        "score": 0.95
      },
      {
        "type": "recognizes_conventional_utility",
        "evidence": "useful for communication",
        "score": 0.88
      },
      {
        "type": "sees_emptiness_without_nihilism",
        "evidence": "doesn't inherently mean anything - I construct",
        "score": 0.92
      }
    ],
    "areas_for_refinement": [
      {
        "type": "subtle_self_reification",
        "suggestion": "Explore: Who is the 'I' that notices?"
      }
    ]
  },
  "celebration": "This demonstrates sophisticated understanding..."
}
```

---

#### 4. Detect Clinging

**POST** `/api/madhyamaka/detect/clinging`

Detects psychological attachment to views, even "correct" ones.

**Request:**
```json
{
  "conversation_history": [
    {"role": "user", "content": "Everything is empty!"},
    {"role": "user", "content": "You don't understand - EVERYTHING is śūnyatā!"},
    {"role": "user", "content": "Emptiness is the ultimate truth that most people can't grasp."}
  ],
  "analysis_depth": "deep"
}
```

**Response:**
```json
{
  "clinging_detected": true,
  "clinging_type": "attachment_to_emptiness",
  "confidence": 0.89,
  "patterns": [
    {
      "type": "defensive_assertion",
      "evidence": "Repeated emphasis, all caps",
      "psychological_indicator": "Protecting view from challenge"
    },
    {
      "type": "spiritual_superiority",
      "evidence": "most people can't grasp",
      "psychological_indicator": "Using emptiness to establish identity"
    }
  ],
  "nagarjuna_correction": {
    "quote": "Those who are possessed of the view of emptiness are said to be incorrigible.",
    "source": "Mūlamadhyamakakārikā XIII.8"
  },
  "suggested_intervention": {
    "type": "tetralemma_dissolution",
    "prompt": "Is emptiness something that exists? Does it not exist? Both? Neither?"
  }
}
```

---

### Transformation Endpoints

#### 5. Generate Middle Path Alternatives

**POST** `/api/madhyamaka/transform/middle-path-alternatives`

Generates alternative phrasings that avoid extremes.

**Request:**
```json
{
  "content": "You must pursue success to be happy",
  "num_alternatives": 5,
  "user_stage": 2
}
```

**Response:**
```json
{
  "original": "You must pursue success to be happy",
  "extreme_type": "eternalism",
  "problematic_elements": {
    "absolute_language": 1,
    "essentialist_claims": 2,
    "universal_quantifiers": 0
  },
  "middle_path_alternatives": [
    {
      "text": "For some people, pursuing what they define as success contributes to happiness",
      "madhyamaka_improvements": [
        "Acknowledges conditionality",
        "Recognizes construction",
        "Avoids absolutism"
      ],
      "score": 0.88,
      "type": "conditional_softening"
    },
    {
      "text": "Happiness and success are constructed concepts whose relationship depends on conditioning",
      "madhyamaka_improvements": [
        "Foregrounds construction",
        "Removes reification"
      ],
      "score": 0.94,
      "type": "construction_framing"
    },
    {
      "text": "Notice: Does 'I need success to be happy' arise from experience or learned belief?",
      "madhyamaka_improvements": [
        "Shifts to inquiry",
        "Encourages direct investigation"
      ],
      "score": 0.96,
      "type": "contemplative_pointer"
    }
  ],
  "recommended": {
    "for_stage_1_user": "For some people, pursuing...",
    "for_stage_3_user": "Happiness and success are constructed...",
    "for_stage_4_user": "Notice: Does 'I need success...'?"
  }
}
```

---

#### 6. Reveal Dependent Origination

**POST** `/api/madhyamaka/transform/dependent-origination`

Shows how meaning arises from conditions, not essence.

**Request:**
```json
{
  "content": "Meditation is the path to enlightenment"
}
```

**Response:**
```json
{
  "original_statement": "Meditation is the path to enlightenment",
  "reified_elements": ["meditation", "path", "enlightenment"],
  "dependent_origination_analysis": {
    "meditation": {
      "concept_depends_on": [
        {
          "condition": "Cultural framework",
          "explanation": "The concept 'meditation' is defined within Buddhist traditions",
          "layer": 1
        },
        {
          "condition": "Language creating categories",
          "explanation": "'Meditation' creates the appearance of a discrete thing",
          "layer": 2
        }
      ],
      "without_these_conditions": "The phenomenon we call 'meditation' would not be carved out"
    }
  },
  "middle_path_reframing": {
    "text": "The concept 'meditation' arises dependent on cultural, linguistic, and contextual conditions. It functions conventionally while lacking inherent essence."
  }
}
```

---

### Contemplation Endpoints

#### 7. Generate Neti Neti Practice

**POST** `/api/madhyamaka/contemplate/neti-neti`

Generates systematic negation practice for investigating emptiness.

**Request:**
```json
{
  "exercise_type": "neti_neti",
  "target_concept": "self",
  "user_stage": 3,
  "depth": "progressive"
}
```

**Response:**
```json
{
  "practice_type": "neti_neti",
  "target": "self",
  "instructions": {
    "overview": "Systematic investigation through progressive negation...",
    "stages": [
      {
        "stage": 1,
        "investigation": "Is the self the body?",
        "contemplation": "Notice the body: arms, legs... Which body is the 'self'?",
        "negation": "Not this (neti) - self is not reducible to body",
        "not_nihilism": "This doesn't mean the body doesn't exist conventionally",
        "pause_instruction": "Rest here for 3 breaths"
      },
      {
        "stage": 2,
        "investigation": "Is the self thoughts?",
        "contemplation": "Watch thoughts arise and pass...",
        "negation": "Not this (neti) - self is not reducible to thoughts",
        "pause_instruction": "Rest here for 3 breaths"
      },
      {
        "stage": 3,
        "investigation": "Is the self awareness itself?",
        "contemplation": "Perhaps self is awareness? But who is aware of awareness?",
        "negation": "Not this (neti) - even awareness as self is reification",
        "pause_instruction": "Rest here for 5 breaths"
      },
      {
        "stage": 4,
        "investigation": "Is there a self at all?",
        "contemplation": "After negating all... what remains?",
        "negation": "Not this, not that",
        "middle_path_realization": "Self is neither inherently existing nor non-existing",
        "pause_instruction": "Rest here for 10 breaths"
      }
    ],
    "closing": {
      "integration": "Notice how 'you' function without inherent self...",
      "koan": "Who is it that realizes there is no self?"
    }
  },
  "metadata": {
    "duration_minutes": 20,
    "difficulty": "intermediate",
    "warning": "If this creates anxiety, return to conventional reality"
  }
}
```

**Other target_concept options**: "thought", "emotion", "consciousness"

---

#### 8. Generate Two Truths Contemplation

**POST** `/api/madhyamaka/contemplate/two-truths`

Generates practice for holding conventional and ultimate truths together.

**Request:**
```json
{
  "exercise_type": "two_truths",
  "phenomenon": "anger"
}
```

**Response:**
```json
{
  "practice_type": "two_truths_contemplation",
  "phenomenon": "anger",
  "conventional_truth_practice": {
    "instruction": "Notice the experience called 'anger'",
    "steps": [
      "Feel the experience directly - what is present?",
      "Notice its effects on thoughts, emotions, behavior",
      "Recognize: This is what we conventionally call 'anger'",
      "At the conventional level, it's real, it has effects"
    ],
    "affirmation": "At the conventional level, anger is real..."
  },
  "ultimate_truth_practice": {
    "instruction": "Investigate the emptiness of 'anger'",
    "steps": [
      "Where is 'anger' located?",
      "Notice: Components are just what they are. Where is inherent 'anger'?",
      "'Anger' is a label applied to conditions",
      "As conditions change, 'anger' transforms or dissolves"
    ],
    "affirmation": "At the ultimate level, anger is empty..."
  },
  "both_truths_together": {
    "instruction": "Hold both truths simultaneously",
    "contemplation": "Anger is happening AND anger is empty...",
    "paradox": "Can you rest where anger is both present and empty?"
  },
  "insight_pointers": [
    "Only conventional: clinging to anger as real",
    "Only ultimate: dismissing anger as illusion (bypassing)",
    "Middle path: Respond skillfully while knowing no fixed nature"
  ],
  "closing_koan": "When anger arises, what arises?"
}
```

---

#### 9. Generate Dependent Origination Inquiry

**POST** `/api/madhyamaka/contemplate/dependent-origination`

Generates practice for tracing conditions backward and forward.

**Request:**
```json
{
  "exercise_type": "dependent_origination",
  "starting_point": "belief in progress"
}
```

**Response:**
```json
{
  "practice_type": "dependent_origination_inquiry",
  "starting_concept": "belief in progress",
  "backward_trace": {
    "instruction": "Trace conditions that gave rise to this belief",
    "inquiry_steps": [
      {
        "question": "Where did you first encounter 'progress'?",
        "contemplation": "Recall early experiences. It was taught, not innate."
      },
      {
        "question": "What makes 'progress' seem real?",
        "contemplation": "You interpreted experiences through this lens."
      },
      {
        "question": "What would need to differ for 'progress' to not make sense?",
        "contemplation": "Imagine circular time conception..."
      }
    ],
    "realization": "Belief doesn't exist independently - arose from conditions"
  },
  "forward_trace": {
    "instruction": "Notice what arises from this belief",
    "inquiry_steps": [
      {
        "question": "How does believing shape experience?",
        "contemplation": "Notice emotions, perceptions conditioned by belief"
      },
      {
        "question": "What actions arise from this belief?",
        "contemplation": "Goal-setting, self-improvement..."
      }
    ],
    "realization": "Belief is generative - produces further conditions"
  },
  "middle_path_insight": {
    "contemplation": "Belief arose from conditions and gives rise to conditions...",
    "question": "Can you hold it lightly, using when helpful?"
  },
  "practical_integration": {
    "daily_life": "Next time you think about 'progress':",
    "steps": [
      "Notice thought arise",
      "Ask: What conditions gave rise?",
      "Ask: What does it give rise to?",
      "See the chain",
      "Act skillfully without clinging"
    ]
  }
}
```

---

### Teaching Endpoints

#### 10. Get Teaching for Situation

**POST** `/api/madhyamaka/teach/situation`

Provides relevant Nagarjuna teaching for user's current state.

**Request:**
```json
{
  "user_state": {
    "detected_extreme": "nihilism",
    "confidence": 0.87,
    "user_stage": 3
  }
}
```

**Response:**
```json
{
  "teaching": {
    "diagnosis": "Mistaking emptiness for nihilism",
    "core_principle": "two_truths",
    "nagarjuna_quote": {
      "text": "Those who do not discern the distinction between the two truths cannot discern the profound truth...",
      "source": "Mūlamadhyamakakārikā XXIV.9"
    },
    "explanation": {
      "short": "Emptiness doesn't mean nothingness...",
      "detailed": "When you realize language is empty of inherent meaning...",
      "experiential": "Notice right now: Your experience is happening, even though empty..."
    },
    "next_step": {
      "practice": "two_truths_contemplation",
      "focus": "Hold both truths together"
    }
  }
}
```

---

### Utility Endpoints

#### 11. List All Teachings

**GET** `/api/madhyamaka/teachings`

Returns all available Nagarjuna teachings.

**Response:**
```json
{
  "teachings": {
    "emptiness_not_nihilism": {
      "quote": "Those who do not discern...",
      "source": "Mūlamadhyamakakārikā XXIV.9",
      "context": "nihilism_detected"
    },
    "clinging_to_emptiness": {
      "quote": "Those who are possessed of the view...",
      "source": "Mūlamadhyamakakārikā XIII.8",
      "context": "clinging_to_views"
    }
  },
  "total_count": 3
}
```

---

#### 12. Health Check

**GET** `/api/madhyamaka/health`

Returns service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "madhyamaka",
  "message": "The middle path neither exists nor does not exist. Yet this API responds."
}
```

---

## Testing Examples

### Example 1: Detect & Transform Eternalism

```bash
# 1. Detect eternalism
curl -X POST http://localhost:8000/api/madhyamaka/detect/eternalism \
  -H "Content-Type: application/json" \
  -d '{"content": "Success is absolutely essential. Everyone must work hard to achieve their goals."}'

# 2. Get middle path alternatives
curl -X POST http://localhost:8000/api/madhyamaka/transform/middle-path-alternatives \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Success is absolutely essential",
    "num_alternatives": 3,
    "user_stage": 2
  }'
```

### Example 2: Nihilism Detection & Two Truths Practice

```bash
# 1. Detect nihilism
curl -X POST http://localhost:8000/api/madhyamaka/detect/nihilism \
  -H "Content-Type: application/json" \
  -d '{"content": "Nothing means anything. All language is completely meaningless."}'

# 2. Get two truths practice
curl -X POST http://localhost:8000/api/madhyamaka/contemplate/two-truths \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_type": "two_truths",
    "phenomenon": "meaning"
  }'
```

### Example 3: Check Middle Path Proximity

```bash
curl -X POST http://localhost:8000/api/madhyamaka/detect/middle-path-proximity \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I notice that when I say \"I am sad,\" the word \"sad\" is a label I apply to certain bodily sensations and thought patterns. The label is useful for communicating with others, but the experience itself has no inherent \"sadness\" - I construct that meaning based on past conditioning."
  }'
```

### Example 4: Neti Neti Practice

```bash
curl -X POST http://localhost:8000/api/madhyamaka/contemplate/neti-neti \
  -H "Content-Type: application/json" \
  -d '{
    "exercise_type": "neti_neti",
    "target_concept": "self",
    "user_stage": 3,
    "depth": "progressive"
  }'
```

---

## Integration Patterns

### Pattern 1: Real-time Detection in UI

```javascript
// Frontend: Detect extremes as user types
const checkLanguage = async (userText) => {
  const response = await fetch('http://localhost:8000/api/madhyamaka/detect/eternalism', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({content: userText})
  });

  const result = await response.json();

  if (result.eternalism_detected && result.confidence > 0.7) {
    showGentleNudge(result.middle_path_alternatives[0]);
  }
};
```

### Pattern 2: Progressive Journey Tracking

```javascript
// Track user's progress toward middle path over time
const checkJourneyProgress = async (userId, timeWindow = '30_days') => {
  // Get all user's recent chunks
  const chunks = await getUserChunks(userId, timeWindow);

  // Check middle path proximity for each
  const scores = await Promise.all(
    chunks.map(chunk =>
      fetch('/api/madhyamaka/detect/middle-path-proximity', {
        method: 'POST',
        body: JSON.stringify({content: chunk.content})
      }).then(r => r.json())
    )
  );

  // Calculate trend
  const averageScore = scores.reduce((sum, s) => sum + s.middle_path_score, 0) / scores.length;

  return {averageScore, trend: calculateTrend(scores)};
};
```

### Pattern 3: Contemplative Practice Sequencing

```javascript
// Offer practices based on detected issues
const offerPractice = async (userText, userStage) => {
  // Detect extreme
  const eternalism = await detectEternalism(userText);
  const nihilism = await detectNihilism(userText);

  if (eternalism.confidence > 0.7) {
    // Offer dependent origination inquiry
    return generateDependentOriginationPractice(eternalism.reified_concepts[0]);
  }

  if (nihilism.confidence > 0.7) {
    // Offer two truths practice
    return generateTwoTruthsPractice('language');
  }

  if (userStage >= 4) {
    // Advanced users get neti neti
    return generateNetiNetiPractice('self');
  }
};
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `422`: Validation error (missing/invalid parameters)
- `500`: Internal server error

Example error response:
```json
{
  "detail": "Validation error: content field is required"
}
```

---

## Philosophy Notes

### The Paradox of the API

This API uses language and computation (symbolic realm) to point toward the emptiness of language itself. It's a raft for crossing the river - once you've crossed, you don't need to carry it.

### Nagarjuna's Warning

Even the teachings of emptiness and the middle path must not be clung to:

> "Those who are possessed of the view of emptiness are said to be incorrigible."
> — Mūlamadhyamakakārikā XIII.8

This API is skillful means (upāya), not ultimate truth.

### The Goal

Not to make users "correct" in their language, but to help them see through the constructed nature of all conceptual frameworks - including this one.

---

## Next Steps

1. Test endpoints with your own text
2. Integrate detection into transformation pipeline
3. Build frontend Middle Path Navigator UI
4. Track user progress over time
5. Generate visualizations of extreme → middle path journey

---

**Remember**: The middle path is not a position to arrive at, but a process of releasing all positions. Use this API lightly, without reifying it as "the way."

✨ *Language as a sense. Empty of inherent meaning. Functioning conventionally.* ✨
