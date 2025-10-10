# Personifier Frontend Implementation Plan

## Overview
Gateway feature to serve "humanizer.com" SEO traffic honestly. Transform AI writing → conversational using existing transformation arithmetic.

## Task 7: Landing Page (Personifier.jsx) - ~300 lines

**Location**: `frontend/src/components/Personifier.jsx`

**Key Features**:
- Large textarea for input (AI-written text)
- "Personify" button with strength slider (0-2)
- Loading state with spinner
- Error handling with user-friendly messages

**Layout**:
```
┌─────────────────────────────────────────┐
│  Personifier - Add Person-ness          │
├─────────────────────────────────────────┤
│  Paste AI text:                         │
│  ┌─────────────────────────────────┐   │
│  │ [Large textarea]                │   │
│  │                                 │   │
│  │                                 │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Strength: [━━━━━○━━━━] 1.0            │
│                                         │
│  [Personify] button                     │
└─────────────────────────────────────────┘
```

**API Integration**:
```javascript
const personify = async (text, strength) => {
  const response = await axios.post('http://localhost:8000/api/personify', {
    text,
    strength,
    return_similar: true,
    n_similar: 3
  });
  return response.data;
};
```

**State Management**:
- `inputText` - User's AI text
- `strength` - Transformation strength (default 1.0)
- `isLoading` - Loading state
- `result` - API response
- `error` - Error message

## Task 8: Diff View (DiffView.jsx) - ~200 lines

**Location**: `frontend/src/components/DiffView.jsx`

**Purpose**: Show before/after with syntax highlighting

**Layout**:
```
┌─────────────────┬─────────────────┐
│ Original (AI)   │ Similar Example │
├─────────────────┼─────────────────┤
│ It's worth      │ That sounds     │
│ noting that...  │ like a great... │
│                 │                 │
│ (Strike red)    │ (Highlight grn) │
└─────────────────┴─────────────────┘
```

**Features**:
- Side-by-side comparison
- Red highlights for AI patterns
- Green highlights for conversational alternatives
- Word-level diff (not char-level)
- Copy button for conversational version

**Library**: Use `react-diff-viewer-continued` or build custom with `diff` package

**Highlighting Logic**:
```javascript
const highlightPatterns = (text, patterns) => {
  // Red: hedging phrases, passive voice
  // Green: direct alternatives
  return annotatedText;
};
```

## Task 9: Explanation Panel - ~150 lines

**Location**: `frontend/src/components/ExplanationPanel.jsx`

**Purpose**: Educational - explain what was transformed

**Layout**:
```
┌─────────────────────────────────────┐
│ 📊 Patterns Detected                │
├─────────────────────────────────────┤
│ ✓ Hedging (3): "it's worth noting" │
│ ✓ Passive Voice (1): "can be"      │
│ ✓ List Markers (1): "following"    │
├─────────────────────────────────────┤
│ 💡 Suggestions                      │
├─────────────────────────────────────┤
│ • Remove hedging - be direct        │
│ • Use active voice instead          │
├─────────────────────────────────────┤
│ 🎯 Transformation                   │
├─────────────────────────────────────┤
│ Vector: personify                   │
│ Strength: 1.0                       │
│ Confidence: 100%                    │
└─────────────────────────────────────┘
```

**Props**:
- `patterns` - Detected AI patterns
- `suggestions` - Transformation suggestions
- `transformation` - Metadata
- `confidence` - AI detection confidence

**Visual Design**:
- Color-coded sections (info, success, warning)
- Expandable/collapsible sections
- Icons for each pattern type
- Progress bars for confidence

## Task 10: Navigation & Routing - ~50 lines

**Files to Update**:
- `frontend/src/App.jsx` - Add route
- `frontend/src/components/IconTabSidebar.jsx` - Add menu item

**Route**:
```javascript
<Route path="/personify" element={<Personifier />} />
```

**Sidebar Icon**:
```javascript
{
  id: 'personify',
  icon: '✨', // or custom SVG
  label: 'Personifier',
  path: '/personify'
}
```

**Deep Linking**: Support `?text=...` query param for pre-filled text

## Task 11: End-to-End Testing - Manual

**Test Cases**:
1. **Happy Path**:
   - Paste AI text → Click Personify → See diff + suggestions
2. **Edge Cases**:
   - Empty input → Show error
   - Text too short (<50 chars) → Show validation
   - Text too long (>5000 chars) → Show warning
3. **API Errors**:
   - Ollama down → Show friendly error
   - Network error → Retry option
4. **UX Flow**:
   - Adjust strength slider → See updated results
   - Copy conversational text → Success toast
   - Navigate away → Preserve input (localStorage)

**Browser Testing**: Chrome, Firefox, Safari

## Task 12: Marketing Copy - ~100 lines

**Location**: `frontend/src/components/Personifier.jsx` (header section)

**Honest Framing** (Critical):
```markdown
# Transform AI Writing → Conversational

**Not** "Make AI undetectable" (dishonest)
**IS** "Transform linguistic register" (honest, educational)

## What This Does
Adds "person-ness" - lexical patterns that make writing more conversational.
This is geometric transformation in semantic space, not deception.

## Why This Matters
- See language as constructed (not objective reality)
- Understand writing as learnable patterns
- Gateway to full transformation platform

## How It Works
1. Detect AI patterns (hedging, passive voice, formal transitions)
2. Apply transformation vector learned from human writing
3. Find similar conversational examples
4. Show you the difference

[Start Transforming →]
```

**SEO Keywords**: "ai writing transformer", "conversational writing", "linguistic register", "writing patterns"

**CTA Strategy**: Free tool → Educational → Platform upsell

---

## Implementation Order (Recommended)

1. **Start with Task 7** (Landing Page) - Core UX
2. **Then Task 9** (Explanation Panel) - Reusable component
3. **Then Task 8** (Diff View) - Most complex
4. **Then Task 10** (Navigation) - Integration
5. **Finally Task 11** (Testing) - Validation
6. **Last Task 12** (Marketing) - Polish

---

## File Structure

```
frontend/src/components/
├── Personifier.jsx           (Task 7 - Landing page)
├── DiffView.jsx              (Task 8 - Before/after comparison)
├── ExplanationPanel.jsx      (Task 9 - Pattern explanation)
└── PersonifierStyles.css     (Shared styles)

frontend/src/hooks/
└── usePersonifier.js         (API calls, state management)
```

---

## Dependencies to Install

```bash
cd frontend
npm install react-diff-viewer-continued  # For diff view
npm install react-syntax-highlighter      # For code highlighting (optional)
```

---

## Estimated Time

- Task 7: 1-2 hours (Landing page)
- Task 8: 2-3 hours (Diff view - most complex)
- Task 9: 1 hour (Explanation panel)
- Task 10: 30 minutes (Navigation)
- Task 11: 1 hour (Testing)
- Task 12: 30 minutes (Marketing copy)

**Total**: 6-8 hours for complete frontend

---

## Success Criteria

✅ User can paste AI text and see transformation
✅ Diff view clearly shows before/after
✅ Explanation panel educates about patterns
✅ Navigation integrated with existing UI
✅ All edge cases handled gracefully
✅ Marketing copy is honest and educational
✅ Performance: < 3 second response time
✅ Mobile responsive (bonus)
