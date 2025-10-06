# Humanizer Agent

**Transform your conversational archives into publication-ready academic papers and technical documentation.**

## Overview

Humanizer Agent is an AI-powered transformation pipeline that turns raw conversational data (ChatGPT, Claude exports) into structured, publication-quality books and papers. Built on Claude's Sonnet 4.5 with FastAPI + React, it combines philosophical analysis with practical writing tools.

## Core Philosophy

Language isn't objective reality—it's a **sense** through which consciousness constructs meaning. This framework helps you:
- 🔄 **Transform narratives** across belief frameworks (PERSONA/NAMESPACE/STYLE)
- 🧘 **Detect philosophical positions** using Madhyamaka (Middle Path) analysis
- 👁️ **Generate multi-perspective analysis** from single viewpoints
- 📚 **Build structured documents** from conversation archives
- 🔗 **Preserve provenance** with full lineage tracking

## Key Features

### 🎭 Transformation Engine
- **Persona**: Shift narrative voice (academic, conversational, technical)
- **Namespace**: Reframe terminology (Buddhist → neuroscience, philosophy → engineering)
- **Style**: Adjust tone and structure (formal papers, blog posts, documentation)

### 📖 Book Builder
- **Hierarchical organization** (books → chapters → sections)
- **Markdown editor** with live preview (CodeMirror + ReactMarkdown)
- **Content linking** from transformation results or messages
- **TOML-assisted configuration** for LaTeX export (coming soon)

### 🔍 Philosophical Analysis
- **Madhyamaka detection**: Identify Middle Path reasoning patterns
- **Perspective generation**: Synthesize multiple viewpoints
- **Contemplative exercises**: Word dissolution, Socratic dialogue
- **Archive analysis**: Map belief structures across conversations

### 📊 Pipeline & Provenance
- **Background job processing** for batch transformations
- **Lineage tracking**: Every transformation links to its source
- **Graph visualization** of content evolution (coming soon)
- **Reapply transformations** to new content

### 💾 Archive Import
- **ChatGPT export** support (conversations.json)
- **Claude export** support (with attachments)
- **Image preservation**: DALL-E, uploads, Sediment screenshots
- **Full metadata**: timestamps, models, tool calls

## Tech Stack

**Backend**:
- Python 3.11 + FastAPI (async)
- PostgreSQL + pgvector (semantic search)
- SQLAlchemy (async ORM)
- Anthropic Claude SDK (Sonnet 4.5)
- sentence-transformers (embeddings)

**Frontend**:
- React 18 + Vite
- TailwindCSS + DaisyUI
- CodeMirror (markdown editing)
- axios (API client)

**Infrastructure**:
- Alembic (migrations)
- Poetry (Python dependencies)
- Background job processor

## Architecture Principles

1. **Local-first**: Your data stays on your machine
2. **Extend, don't rewrite**: Learn from DEC's Jupiter lesson—nurture working systems
3. **Provenance over everything**: Every byte traceable to its source
4. **Modular refactoring**: Target 200-300 lines per file, split at 500+ lines

## Current Status (Oct 2025)

### ✅ Completed
- Transformation engine (PERSONA/NAMESPACE/STYLE)
- PostgreSQL + pgvector embeddings
- ChatGPT/Claude archive import (8,640 media records)
- Madhyamaka service (refactored, tested, 89% pass rate)
- Transformation pipeline backend + frontend UI
- Transformations library (browse, filter, reapply)
- **Book Builder Phase 1 & 2** (foundation + markdown editor)

### 🚧 In Progress
- Manual UI testing of Book Builder
- Phase 3: Configuration & Export (TOML UI, LaTeX, PDF)

### 📋 Roadmap
- LaTeX typesetting engine
- PDF compositor
- Cover image generator
- Bibliography generator
- Cloudflare Workers deployment (future)

## Quick Start

```bash
# Clone repository
git clone <repo-url>
cd humanizer-agent

# Start both servers (backend + frontend)
./start.sh

# Access the app
open http://localhost:5173
```

**Servers**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Database Setup

```bash
# Install PostgreSQL
brew install postgresql

# Create database
createdb humanizer

# Run migrations
cd backend
alembic upgrade head
```

## Use Cases

1. **Academic Writing**: Transform ChatGPT research conversations into structured papers
2. **Technical Documentation**: Convert Q&A sessions into organized docs
3. **Multi-perspective Analysis**: Generate diverse viewpoints from single narratives
4. **Archive Mining**: Extract insights from thousands of historical conversations
5. **Belief Mapping**: Visualize philosophical patterns across your writing

## Philosophy in Practice

This isn't just a tool—it's a **contemplative practice**:

> "Language is not objective reality. It's a sense—like sight or sound—through which consciousness constructs meaning. The Humanizer Agent helps you shift from linguistic identification to self-awareness."

By transforming the *same content* through different frameworks, you directly experience the **constructed nature of meaning**. Buddhist → neuroscience → engineering. Same insights, different languages. All valid. All constructed.

## Documentation

- `CLAUDE.md` - Developer guide with activation checklist
- `BOOK_BUILDER_TESTING_GUIDE.md` - Phase 1 & 2 testing instructions
- `BOOK_BUILDER_BUGS_FIXED.md` - Bug documentation and fixes
- `docs/` - Architecture, design principles, roadmap
- `backend/tests/` - Comprehensive test suite

## Contributing

This is a personal research project exploring the intersection of AI, philosophy, and writing tools. Contributions welcome, but expect philosophical discussions about **why** we build, not just **what** we build.

## License

[Your chosen license]

## Credits

Built with Claude Sonnet 4.5, inspired by:
- **Nagarjuna's Madhyamaka** (Middle Path philosophy)
- **DEC's Jupiter** (extend working systems, don't rewrite)
- **Joplin's notebook structure** (hierarchical organization)
- **Sediment** (conversation archaeology)

---

**"The map is not the territory. The menu is not the meal. Language is not reality—it's just how we taste it."**
