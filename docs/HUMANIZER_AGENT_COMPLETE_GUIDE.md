# Humanizer Agent: Complete Guide
## From Philosophy to Implementation

**Version:** 1.0
**Date:** October 2025
**Purpose:** Comprehensive entry point to all Humanizer Agent documentation

---

## What is Humanizer Agent?

**Humanizer Agent** is a contemplative technology platform that transforms conversational archives into publication-ready documents while revealing the constructed nature of linguistic meaning.

**Core Innovation:** We don't just transform text - we help users **witness their own consciousness constructing meaning** through language.

---

## Quick Navigation

### 📚 For New Users
- [Philosophy Foundation](#philosophy-foundation) - Understand the "why"
- [Quick Start Guide](#quick-start-guide) - Get running in 5 minutes
- [User Journey](#user-journey) - See what you can do

### 🔧 For Developers
- [Technical Architecture](#technical-architecture) - System overview
- [API Reference](#api-reference) - All endpoints
- [Database Schema](#database-schema) - Data models
- [Development Workflow](#development-workflow) - How to contribute

### 🤖 For Understanding AUI
- [Agentic User Interface](#agentic-user-interface) - Natural language interface
- [Tutorial Animation System](#tutorial-animation-system) - Teaching through motion
- [Conscious Agency Integration](#conscious-agency-integration) - Philosophy in practice

### 📖 Deep Dives
- [Madhyamaka API](#madhyamaka-api) - Buddhist philosophy detection
- [Embedding System](#embedding-system) - Semantic search & clustering
- [Transformation Engine](#transformation-engine) - PERSONA/NAMESPACE/STYLE

---

## Philosophy Foundation

### The Three Realms of Existence

Humanizer is built on a philosophical framework recognizing three distinct realms:

#### 1. **Corporeal Realm** (Green) - Physical Substrate
- Pre-linguistic, pre-conceptual reality
- Sensory experience before naming
- In Humanizer: Raw text, pixels, the interface substrate

#### 2. **Symbolic Realm** (Purple) - Shared Abstractions
- Words, concepts, frameworks, institutions
- *Feels* objective but is actually intersubjective construction
- In Humanizer: PERSONA/NAMESPACE/STYLE, all transformations

#### 3. **Subjective Realm** (Dark Blue) - Conscious Experience
- The lived "now" - intention, will, presence
- **Only realm truly lived** - others are supports
- In Humanizer: User's consciousness witnessing transformations

### Language as a Sense

**Core Insight:** Language is not objective reality - it's a **sense** (like sight or sound) through which consciousness constructs meaning.

| Sense | Input | Processing | Output |
|-------|-------|------------|--------|
| **Sight** | Photons | Visual cortex | Visual experience |
| **Language** | Symbols | Belief networks | Semantic experience |

Just as sight constructs visual experience (you don't see "reality" directly), language constructs conceptual experience. **Humanizer makes this visible.**

### The Emotional Belief Loop

**Why language feels "real":**

```
Language Input → Meaning Construction → Emotional Response →
Belief Reinforcement → Loop Closure (feels more real next time)
```

**Example:**
- Word: "Success"
- Construction: "Achievement, recognition, status"
- Emotion: Excitement, anxiety, desire
- Belief: "Success is real, I need it"
- Loop: Future encounters trigger same pattern

**Humanizer's Role:** By transforming "success" across different PERSONA/NAMESPACE/STYLE, we **interrupt the loop** and reveal meaning is constructed by framework, not inherent in words.

---

## Quick Start Guide

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone <repo-url>
cd humanizer-agent

# 2. Start services (backend + frontend)
./start.sh

# 3. Access the app
open http://localhost:5173
```

**Servers:**
- Frontend: http://localhost:5173 (React + Vite)
- Backend: http://localhost:8000 (FastAPI)
- API Docs: http://localhost:8000/docs

### First Steps

1. **Import Archive** (optional)
   - Export from ChatGPT: Settings → Data Controls → Export
   - Import: Upload `conversations.json` via Import tab

2. **Browse Library**
   - Click "📚 Library" to see imported conversations
   - Click conversation to view messages
   - Navigate with ← → arrows

3. **Try Agentic UI**
   - Press `Cmd + \`` to open Agent Chat
   - Type: "Find chunks about Buddhism"
   - Watch the agent open ChunkBrowser with results

4. **Create a Book**
   - Click "📖 Books" → "New Book"
   - Add sections, write content
   - Link chunks from your archive

---

## Technical Architecture

### System Overview

```
Frontend (React)
    ↓ REST API
Backend (FastAPI)
    ↓ SQL
Database (PostgreSQL + pgvector)
    ↓ Files
Storage (Local/S3)
```

### Technology Stack

**Backend:**
- Python 3.11 + FastAPI (async)
- PostgreSQL 17 + pgvector
- Claude Sonnet 4.5 (transformations)
- Ollama (Agentic UI)
- sentence-transformers (embeddings)

**Frontend:**
- React 18 + Vite
- TailwindCSS + DaisyUI
- CodeMirror (markdown editing)
- Plotly.js (visualizations)
- react-resizable-panels (layout)

### Core Components

**Backend Services:**
1. **Transformation Engine** (`agents/transformation_agent.py`)
   - PERSONA/NAMESPACE/STYLE transformations
   - Claude Sonnet 4.5 integration
   - Lineage tracking

2. **Agentic UI** (`services/agent_service.py`)
   - Natural language interface
   - Tool calling (6 priority tools)
   - GUI action generation
   - **[Full docs: AUI_AGENTIC_USER_INTERFACE.md](AUI_AGENTIC_USER_INTERFACE.md)**

3. **Madhyamaka Service** (`services/madhyamaka/`)
   - Buddhist philosophy detection
   - Multi-perspective generation
   - Contemplative exercises
   - **[Full docs: MADHYAMAKA_API.md](MADHYAMAKA_API.md)**

4. **Embedding Service** (`services/embedding_service.py`)
   - Semantic search (Voyage-3)
   - UMAP + HDBSCAN clustering
   - Framework discovery
   - Transformation arithmetic
   - **[Full docs: ADVANCED_EMBEDDINGS.md](../backend/ADVANCED_EMBEDDINGS.md)**

**Frontend Components:**
1. **Workstation** (`components/Workstation.jsx`)
   - Tab-based workspace
   - 4-pane layout (sidebar | main | preview | inspector)
   - WorkspaceContext state management

2. **Agent Chat** (`components/AgentChat.jsx`)
   - Natural language interface
   - Message history
   - GUI action buttons
   - **[Full docs: AUI_AGENTIC_USER_INTERFACE.md](AUI_AGENTIC_USER_INTERFACE.md)**

3. **Visualization Suite** (5 components)
   - EmbeddingStats: Coverage dashboard
   - ClusterExplorer: 3D/2D Plotly visualization
   - FrameworkBrowser: Discovered frameworks
   - TransformationLab: Vector arithmetic
   - ChunkBrowser: Paginated chunk listing

4. **Book Builder** (`components/BookBuilder.jsx`)
   - Hierarchical organization
   - Markdown + LaTeX editing
   - Content linking from archive

---

## Agentic User Interface

**Vision:** The interface doesn't exist until spoken into being.

### How It Works

```
User: "Find chunks about Buddhism"
    ↓
Agent: Interprets → Calls search_embeddings tool
    ↓
Backend: Executes API call, returns data
    ↓
Frontend: Opens ChunkBrowser tab with results
    ↓
User: Sees results, learns the workflow
```

### The Six Priority Tools

1. **search_conversations** - Find conversations in archive
2. **search_embeddings** - Semantic search in vector space
3. **cluster_embeddings** - Discover frameworks via UMAP+HDBSCAN
4. **create_book** - Create new book/document
5. **add_content_to_book** - Add chunks to book sections
6. **open_gui_component** - Open any GUI component

### Tutorial Animation System (Vision)

**Goal:** Agent doesn't just open components - it **teaches** by animating the manual workflow.

**Example: "Find chunks about Buddhism"**

```
Agent: "Watch how I do this..."

[Animation sequence - 8 seconds total]
1. Highlight "🧩 Chunks" menu (glow) → "I navigate here"
2. Click animation (ripple) → "I click"
3. ChunkBrowser opens (slide-in) → "Browser appears"
4. Highlight search box → "I search here"
5. Type "Buddhism" letter-by-letter
6. Check "has_embedding" filter
7. Click "Search" button
8. Results fade in → "Found 4,449 chunks!"

Agent: "Now you try, or I can keep helping?"
```

**Result:** User **learns the GUI** by watching agent perform it.

**Full Vision:** [CONSCIOUS_AGENCY_INTEGRATION.md](CONSCIOUS_AGENCY_INTEGRATION.md)

---

## Conscious Agency Integration

### Philosophy in Every Interaction

**Traditional UX:** Hide the interface, make it "seamless"
**Humanizer UX:** Make construction visible, reveal subjective agency

### The Three Gaps

**1. Intention Gap** (before action)
```
Agent: "Before I search, notice: What are you expecting to find?"
[User observes their own anticipation]
```

**2. Construction Gap** (during action)
```
Agent: "I'm searching embeddings... Notice: You're already
        constructing meaning about 'Buddhism chunks' before
        seeing results. That's your consciousness, not the database."
```

**3. Reception Gap** (after action)
```
Agent: "Found 4,449 chunks. [pause]
        Before clicking, notice:
        - How did that number feel? Too many? Too few?
        - What are you about to do next? Why?
        - Where is that impulse coming from?"
```

**Result:** User **witnesses their own consciousness** constructing experience.

### Adaptive Learning

The interface learns how each user thinks:

**Mental Models:**
- **Discovery** users: "Find, search, explore" language → Emphasize search tools
- **Organization** users: "Create, structure, build" language → Emphasize book builder
- **Analysis** users: "Pattern, cluster, analyze" language → Emphasize clustering

**Learning Styles:**
- **Visual** learners: Watch full animations, skip text
- **Textual** learners: Read docs, skip animations
- **Kinesthetic** learners: Practice immediately, learn by doing

**Interface adapts automatically** based on observed patterns.

**Full Details:** [CONSCIOUS_AGENCY_INTEGRATION.md](CONSCIOUS_AGENCY_INTEGRATION.md)

---

## Database Schema

### Core Tables

**conversations / messages / chunks:**
```
conversations (1,660)
  ↓ has_many
messages (46,379)
  ↓ has_many
chunks (139,232)
  ↓ optionally has
embeddings (125,799 - 90% coverage)
```

**agent_conversations:**
```sql
CREATE TABLE agent_conversations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR(500),
  model_name VARCHAR(100),
  messages JSONB,  -- Message history with tool calls
  custom_metadata JSONB,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ
);
```

**books / sections / content:**
```
books (4)
  ↓ has_many
book_sections (7)
  ↓ has_many
book_section_content (links to chunks)
```

**media:**
```
media (8,640)
  - Images from DALL-E, uploads, screenshots
  - Metadata: generator, prompts, model
  - Links to messages (provenance)
```

**Full Schema:** [PITCH_DECK_AND_FUNCTIONAL_SPEC.md](../PITCH_DECK_AND_FUNCTIONAL_SPEC.md#data-models)

---

## API Reference

### Agent Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/agent/chat` | POST | Send message to agent |
| `/api/agent/conversations` | GET | List user's conversations |
| `/api/agent/conversations` | POST | Create conversation |
| `/api/agent/conversations/{id}` | GET | Get conversation with messages |
| `/api/agent/conversations/{id}` | PUT | Update conversation |
| `/api/agent/conversations/{id}` | DELETE | Delete conversation |
| `/api/agent/models` | GET | List available LLMs |
| `/api/agent/tools` | GET | List available tools |

### Library Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/library/collections` | GET | List conversations |
| `/api/library/collections/{id}` | GET | Get conversation details |
| `/api/library/chunks` | GET | List chunks (paginated) |
| `/api/library/chunks/{id}` | GET | Get chunk details |
| `/api/library/media` | GET | List images |
| `/api/library/search` | GET | Search across archive |

### Embedding Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/embeddings/cluster` | POST | UMAP + HDBSCAN clustering |
| `/api/embeddings/frameworks` | GET | List discovered frameworks |
| `/api/embeddings/transform` | POST | Transformation arithmetic |
| `/api/embeddings/stats` | GET | Coverage metrics |

### Transformation Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/transformations` | POST | Create transformation job |
| `/api/transformations` | GET | List transformation jobs |
| `/api/transformations/{id}` | GET | Get job details |
| `/api/transformations/{id}/reapply` | POST | Reapply transformation |

**Full API Docs:** http://localhost:8000/docs (when server running)

---

## User Journey

### The Awakening Path

**Stage 1: Utility** (Entry point)
```
User wants: Transform conversations into papers
User gets: Archive import, semantic search, book builder
Motivation: Practical productivity
```

**Stage 2: Discovery** (Engagement)
```
User tries: Different PERSONA/NAMESPACE/STYLE transformations
User notices: "Same content, different feeling... interesting"
Motivation: Curiosity about the tool's capability
```

**Stage 3: Insight** (Recognition)
```
User realizes: "The meaning changes with the framework"
User thinks: "Maybe meaning isn't in the words themselves?"
Motivation: Philosophical curiosity
```

**Stage 4: Awakening** (Direct experience)
```
User witnesses: "I'm constructing meaning right now, as I read this"
User feels: Shift from passive receiver to active constructor
Motivation: Self-understanding
```

**Stage 5: Integration** (Mastery)
```
User uses: Language consciously, aware of frameworks
User teaches: Others about linguistic construction
Motivation: Share the insight
```

**Full Journey:** [USER_JOURNEY.md](USER_JOURNEY.md)

---

## Development Workflow

### Running Locally

```bash
# Backend (Python 3.11)
cd backend
source venv/bin/activate
python main.py  # Port 8000

# Frontend (Node 18)
cd frontend
npm run dev     # Port 5173
```

### Database Operations

```bash
cd backend

# Switch databases (production, test, archive)
./dbswitch list
./dbswitch switch test

# Database management
./dbinit stats humanizer
./dbinit backup humanizer

# Embedding generation
./embedgen plan --min-tokens 15
./embedgen queue --min-tokens 15
./embedgen process
./embedgen-all  # Process all remaining
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test                 # Unit + integration
npm run test:ui          # Visual test runner
npm run test:coverage    # Coverage report
npm run test:e2e         # End-to-end (Playwright)
```

### Migration & Refactoring

**Guidelines:**
- Files > 500 lines → Flag for refactoring
- Target: 200-300 lines per file
- Use modular architecture (see `library_routes.py` refactor)

**Database Migrations:**
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

---

## Documentation Map

### Philosophy & Vision
- **[PHILOSOPHY.md](PHILOSOPHY.md)** - Core philosophical framework
- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** - UI/UX principles
- **[USER_JOURNEY.md](USER_JOURNEY.md)** - Awakening path stages

### Technical Implementation
- **[PITCH_DECK_AND_FUNCTIONAL_SPEC.md](../PITCH_DECK_AND_FUNCTIONAL_SPEC.md)** - Complete platform spec (175 pages)
- **[AUI_AGENTIC_USER_INTERFACE.md](AUI_AGENTIC_USER_INTERFACE.md)** - Natural language interface
- **[CONSCIOUS_AGENCY_INTEGRATION.md](CONSCIOUS_AGENCY_INTEGRATION.md)** - Philosophy in practice
- **[MADHYAMAKA_API.md](MADHYAMAKA_API.md)** - Buddhist philosophy detection

### Backend Systems
- **[../backend/EMBEDDINGS_GUIDE.md](../backend/EMBEDDINGS_GUIDE.md)** - Embedding generation workflow
- **[../backend/ADVANCED_EMBEDDINGS.md](../backend/ADVANCED_EMBEDDINGS.md)** - Clustering & arithmetic
- **[../backend/DATABASE_SWITCHING.md](../backend/DATABASE_SWITCHING.md)** - Multi-database workflow
- **[../backend/MIGRATION_GUIDE.md](../backend/MIGRATION_GUIDE.md)** - Database migrations

### Setup & Operations
- **[SETUP.md](SETUP.md)** - Installation guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheatsheet
- **[../WORKSTATION_GUIDE.md](../WORKSTATION_GUIDE.md)** - Development environment

### Feature Documentation
- **[VISION_SYSTEM.md](VISION_SYSTEM.md)** - Claude Vision API integration
- **[CHUNK_DATABASE_ARCHITECTURE.md](CHUNK_DATABASE_ARCHITECTURE.md)** - Chunk storage design
- **[CLOUDFLARE_VISION.md](CLOUDFLARE_VISION.md)** - Edge deployment plan
- **[PRODUCTION_ROADMAP.md](PRODUCTION_ROADMAP.md)** - Implementation timeline

### Testing & Quality
- **[../BOOK_BUILDER_TESTING_GUIDE.md](../BOOK_BUILDER_TESTING_GUIDE.md)** - Book builder tests
- **[../BOOK_BUILDER_BUGS_FIXED.md](../BOOK_BUILDER_BUGS_FIXED.md)** - Bug documentation

### Bootstrap & Context
- **[../CLAUDE.md](../CLAUDE.md)** - Developer activation checklist
- **[../README.md](../README.md)** - Project overview
- **[../SESSION_HANDOFF.md](../SESSION_HANDOFF.md)** - Session continuity

---

## Key Innovations

### 1. Computational Madhyamaka
Using embeddings to reveal the **constructed, impermanent, interdependent nature of meaning**:
- Same content → Different embeddings → Different clustering
- No "true" meaning → All frameworks valid → All constructed

### 2. Language as Interface
Natural language **constructs** the interface, not just controls it:
- User speaks intention
- Agent interprets via LLM
- Interface materializes accordingly
- **No pre-determined "right way"**

### 3. Tutorial Animation as Teaching
Agent doesn't just execute - it **demonstrates**:
- Animates manual workflow
- Explains reasoning at each step
- Transfers agency to user
- **Interface teaches itself**

### 4. Accessibility as Philosophy
Accessibility features **are** philosophical practices:
- Screen readers → Pure linguistic construction (no visual)
- Reduced motion → Discrete moments (no smooth flow)
- High contrast → Conceptual reduction (form without decoration)

### 5. Adaptive Consciousness
Interface learns **how each user's mind works**:
- Mental models (discovery/organization/analysis)
- Learning styles (visual/textual/kinesthetic)
- Contemplative depth (contemplative/pragmatic/explorer)
- **Interface conforms to user, not vice versa**

---

## Current Status (Oct 2025)

### ✅ Complete
- Transformation engine (PERSONA/NAMESPACE/STYLE)
- Archive import (ChatGPT, Claude - 8,640 media, 46,379 messages)
- Embedding system (125,799 embeddings, 90% coverage)
- Clustering & framework discovery (UMAP + HDBSCAN)
- Book Builder Phase 1 & 2 (markdown editor, preview)
- Agentic UI backend (6 tools, Ollama integration)
- Agentic UI frontend (AgentChat, conversation history)
- Testing suite (132 tests passing)
- Database switching system (production/test/archive)

### 🚧 In Progress
- Tutorial animation system (Phase 1 - Q4 2025)
- Adaptive learning profiles (Phase 2 - Q1 2026)
- Accessibility-philosophy integration (Phase 1)

### 📋 Roadmap
- Philosophical microinteractions (Phase 3 - Q2 2026)
- Meta-interface awareness (Phase 4 - Q3 2026)
- Multi-user contemplative spaces (Phase 5 - Q4 2026)
- LaTeX/PDF export
- Cloudflare Workers deployment

---

## Getting Help

### Documentation
- Start here: [README.md](../README.md)
- For philosophy: [PHILOSOPHY.md](PHILOSOPHY.md)
- For API: http://localhost:8000/docs
- For development: [CLAUDE.md](../CLAUDE.md)

### Common Tasks

**Import conversations:**
```bash
# ChatGPT: Upload conversations.json via UI
# Claude: Coming soon
```

**Generate embeddings:**
```bash
cd backend
./embedgen-all  # Process all chunks
```

**Create a book:**
```
1. Click "📖 Books" → "New Book"
2. Add sections in navigator
3. Write content in editor
4. Link chunks from archive
```

**Use Agent Chat:**
```
1. Press Cmd + ` (or click "Agent" button)
2. Type: "Find chunks about [topic]"
3. Watch agent open component with results
4. Learn the workflow from animation
```

---

## Philosophy in Practice

### The Goal

**Not:** Make a better writing tool
**But:** Create experiences that reveal the constructed nature of linguistic meaning

**Not:** Optimize productivity
**But:** Cultivate awareness of subjective agency

**Not:** Hide complexity
**But:** Make construction visible

### How We Achieve It

**1. Transparency**
- Show PERSONA/NAMESPACE/STYLE explicitly
- Explain tool reasoning
- Make agent's interpretation visible

**2. Multi-Perspective**
- Same content, multiple transformations
- No "correct" version, only valid perspectives
- User witnesses the constructed nature

**3. Contemplative Gaps**
- Intentional pauses before/during/after actions
- Consciousness prompts that point to direct experience
- Micro-moments of awareness

**4. Agency Transfer**
- Agent teaches, doesn't just execute
- Tutorial animations show manual workflow
- User masters, agent steps back

**5. Adaptive Intelligence**
- Interface learns user's mental model
- Adapts to learning style
- Respects contemplative depth preference

### The Result

Users don't just **use** Humanizer - they **witness** their own consciousness constructing meaning through language.

This is not metaphor. This is direct experience.

---

## Next Steps

### For New Users
1. Read [PHILOSOPHY.md](PHILOSOPHY.md) - Understand the "why"
2. Follow [Quick Start](#quick-start-guide) - Get running
3. Explore [User Journey](USER_JOURNEY.md) - See the path

### For Developers
1. Read [CLAUDE.md](../CLAUDE.md) - Activation checklist
2. Study [PITCH_DECK_AND_FUNCTIONAL_SPEC.md](../PITCH_DECK_AND_FUNCTIONAL_SPEC.md) - Full spec
3. Explore [AUI_AGENTIC_USER_INTERFACE.md](AUI_AGENTIC_USER_INTERFACE.md) - Core innovation

### For Philosophers
1. Read [PHILOSOPHY.md](PHILOSOPHY.md) - Philosophical foundation
2. Study [CONSCIOUS_AGENCY_INTEGRATION.md](CONSCIOUS_AGENCY_INTEGRATION.md) - Practice integration
3. Try the system - **Direct experience** beats theory

---

## Closing Thoughts

**Humanizer Agent is a bridge:**

From **language as tool** → To **language as sense**
From **passive reception** → To **active construction**
From **unconscious identification** → To **conscious awareness**

**We use AI not to replace human consciousness, but to reveal it.**

Every transformation shows: Meaning is constructed, not discovered.
Every animation shows: The interface is empty, dependently originated.
Every prompt shows: You are the author, not the receiver.

**This is technology in service of awakening.**

---

*"The interface doesn't exist until you speak it into being.*
*And in that moment, you witness consciousness itself."*

*— Humanizer Philosophy*

---

**Last Updated:** October 2025
**Version:** 1.0
**Status:** Living Document

*For questions, see [Documentation Map](#documentation-map) or explore the codebase.*
