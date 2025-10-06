# Humanizer Workstation - User Guide

**Version:** 2.0
**Date:** October 5, 2025

## Overview

The Humanizer Workstation is a sophisticated, Zed-like full-screen interface designed for text archaeology, document analysis, and philosophical exploration. It transforms the prototype interface into a professional tool for diving into your written archives and understanding yourself through your media artifacts.

## Key Features

### 🎯 Core Interface

- **Full-Screen Workstation Layout**: Clean, distraction-free environment inspired by modern code editors
- **Icon Tab Sidebar**: Hierarchical navigation with visual icons
- **Document Viewer**: Professional rendering for Markdown, code, LaTeX, and plain text
- **Split Pane Support**: Compare documents side-by-side
- **Mobile Responsive**: Fully functional on tablets and phones

### 📚 Navigation Hierarchy

The sidebar provides drillable navigation:

1. **📚 Library** - Browse your document library and options
2. **🗂️ Sessions** - View transformation sessions
3. **💬 Conversations** - Drill into conversations within a session
4. **📝 Messages** - Individual messages and documents

### 🎨 Customization

- **Style Configurator**: Visual theme editor accessible via settings button
- **Three Realms Color System**: Philosophical color palette (Corporeal/Symbolic/Subjective)
- **SCSS Variables**: Complete styling system with customizable variables
- **Theme Presets**: Ocean, Forest, Sunset, and custom themes
- **Import/Export**: Save and share your theme configurations

### 🔍 Phrase Flagging System

Intelligent phrase detection with configurable patterns:

- **LLM Slop Detection**: Identifies AI-generated filler phrases
- **Hedge Words**: Flags uncertain language
- **Passive Voice**: Detects passive constructions
- **Academic Jargon**: Highlights overly formal language
- **Filler Words**: Identifies unnecessary words
- **Custom Patterns**: Add your own detection rules

**Severity Levels:**
- 🔴 High (red) - Critical issues
- 🟡 Medium (yellow) - Moderate concerns
- 🟣 Low (purple) - Minor suggestions

### 📄 Document Rendering

**Supported Formats:**
- **Markdown**: Full GFM support (tables, task lists, strikethrough)
- **LaTeX/Math**: KaTeX rendering for mathematical expressions
- **Code**: Syntax highlighting for 100+ languages
- **Plain Text**: With phrase flagging and highlighting

**Export Options:**
- Markdown
- PDF (coming soon)
- HTML (coming soon)

### 📱 Mobile Support

- Responsive sidebar (slides in/out on mobile)
- Touch-friendly controls
- Optimized for tablet and phone screens
- Overlay mode on small screens

## Getting Started

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open http://localhost:5173

### First Steps

1. **Create a Session**: Click the 📚 Library or 🗂️ Sessions tab
2. **Add a Document**: Navigate to Messages and select/create content
3. **Configure Flagging**: Adjust phrase detection patterns in settings
4. **Customize Theme**: Click the settings button (⚙️) to open Style Configurator

## Architecture

### Component Structure

```
WorkstationApp.jsx          # Main application wrapper
├── Workstation.jsx          # Core layout and state management
│   ├── IconTabSidebar.jsx   # Hierarchical navigation
│   ├── DocumentViewer.jsx   # Document rendering and editing
│   └── StyleConfigurator.jsx # Theme customization
└── services/
    └── phraseFlagger.js     # Phrase detection system
```

### Styling System

**SCSS Architecture:**
- `workstation.scss` - Complete variable system
- CSS Custom Properties for runtime theming
- Three Realms color palette
- Responsive breakpoints and utilities

**Font Families (Three Realms):**
- **Contemplative**: Crimson Pro, Lora (Subjective realm)
- **Structural**: Inter, Source Sans 3 (Symbolic realm)
- **Grounded**: JetBrains Mono, Fira Code (Corporeal realm)

### State Management

The Workstation uses local React state for:
- Sidebar visibility and width
- Current view (sessions/conversations/messages)
- Selected items at each level
- Split view state
- Document content and metadata

### Data Persistence

- **Theme Settings**: localStorage (`workstation_theme`)
- **Phrase Patterns**: localStorage (`phrase_flagger_patterns`)
- **User ID**: localStorage (`humanizer_user_id`)
- **Sessions**: Backend API (PostgreSQL)

## Keyboard Shortcuts (Coming Soon)

- `Cmd/Ctrl + B` - Toggle sidebar
- `Cmd/Ctrl + P` - Quick open
- `Cmd/Ctrl + Shift + P` - Command palette
- `Cmd/Ctrl + K` - Split view
- `Cmd/Ctrl + ,` - Settings

## API Integration

### Session Management

```javascript
// Create session
POST /api/sessions
{ title: "My Session", user_id: "uuid" }

// Get sessions
GET /api/sessions?user_id=uuid&limit=50

// Clone session
POST /api/sessions/{id}/clone
```

### Transformation (Legacy API)

```javascript
// Transform text
POST /api/transform
{
  content: "...",
  persona: "Scholar",
  namespace: "philosophy",
  style: "academic"
}
```

## Customization Guide

### Creating Custom Themes

1. Open Style Configurator (⚙️ button)
2. Adjust colors, fonts, and spacing
3. Export theme as JSON
4. Share with others or import on different devices

### Adding Custom Phrase Patterns

```javascript
import { phraseFlagger } from './services/phraseFlagger'

phraseFlagger.addPattern({
  name: 'My Pattern',
  description: 'Custom detection pattern',
  pattern: /\b(word1|word2|word3)\b/gi,
  color: '#ef4444',
  bgColor: 'rgba(239, 68, 68, 0.2)',
  severity: 'high'
})
```

### Extending Document Types

Add support for new document types in `DocumentViewer.jsx`:

```javascript
if (type === 'custom') {
  return <CustomRenderer content={content} />
}
```

## Troubleshooting

### Sidebar not appearing
- Check if window width < 768px (mobile mode)
- Click hamburger menu to toggle sidebar

### Phrase flagging not working
- Check if patterns are enabled in localStorage
- Verify pattern regex syntax

### Theme not persisting
- Check browser localStorage permissions
- Clear cache and re-apply theme

### Backend import error
The madhyamaka_routes.py had an incorrect import. This has been fixed to use relative imports:
```python
# Fixed:
from services.madhyamaka_service import ...
```

## Philosophy Integration

The Workstation embodies the "Language as a Sense" framework:

- **Corporeal Realm** (Green): Physical substrate of text
- **Symbolic Realm** (Purple): Constructed frameworks and meaning
- **Subjective Realm** (Indigo): Conscious awareness and presence

Each UI element reflects its ontological realm through color, typography, and interaction design.

## Next Steps

Future enhancements planned:
- [ ] Full keyboard navigation
- [ ] Command palette
- [ ] Advanced search and filtering
- [ ] Collaborative features
- [ ] Plugin system for custom renderers
- [ ] Archive visualization (D3.js network graphs)
- [ ] Export to PDF/DOCX
- [ ] Integrated transformation workflow
- [ ] AI-assisted phrase detection
- [ ] Real-time collaboration

## Contributing

To add new features:

1. Follow the Three Realms design system
2. Maintain mobile responsiveness
3. Use SCSS variables for theming
4. Document all props with PropTypes
5. Add to this guide when complete

## Resources

- [DESIGN_PRINCIPLES.md](docs/DESIGN_PRINCIPLES.md) - UI/UX guidelines
- [PHILOSOPHY.md](docs/PHILOSOPHY.md) - Theoretical framework
- [USER_JOURNEY.md](docs/USER_JOURNEY.md) - User experience mapping

---

**Note**: The Workstation is the new default interface. Legacy interfaces (App.jsx, PhilosophicalApp.jsx) remain available by changing the import in main.jsx.
