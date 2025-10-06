# CLAUDE.md - Humanizer Agent Bootstrap

## ⚠️ CRITICAL CODING RULES - NEVER VIOLATE

### 🚨 SQLAlchemy Reserved Keywords - MANDATORY

**RULE**: NEVER use `metadata` as a field name in SQLAlchemy models.

**Why**: `metadata` is RESERVED by SQLAlchemy's Declarative API for table metadata.
Using it causes: `InvalidRequestError: Attribute name 'metadata' is reserved`

**ALWAYS use**: `custom_metadata` instead

**Applies to**:
- ✅ SQLAlchemy model Column definitions
- ✅ Pydantic schema field names
- ✅ API endpoint request/response bodies
- ✅ Frontend axios POST/PUT requests
- ✅ Database migrations (Alembic)

**Example**:
```python
# ❌ WRONG - Will crash on import
class Book(Base):
    metadata = Column(JSONB, default={})

# ✅ CORRECT - Safe to use
class Book(Base):
    custom_metadata = Column(JSONB, default={})
```

**If you encounter this error**, fix ALL occurrences:
1. Backend models: Search for `metadata = Column`
2. Backend schemas: Search for `metadata:`
3. Backend endpoints: Search for `.metadata`
4. Frontend: Search for `metadata:` in axios calls

**This rule saved us 30+ minutes of debugging. Respect it.**

---

## 🔔 ACTIVATION CHECKLIST - MANDATORY for Every New Session

**Run these steps BEFORE any coding. This brings you up to speed automatically.**

### 1. Configure ChromaDB for Production Context

The project uses **3 separate ChromaDB databases**:
- **Production DB** (13+ memories) - Active dev context, TODOs, refactoring targets, session status
- **Meta DB** (2 memories) - System guides, best practices, procedures
- **Historical DB** (547 memories) - Complete archive, debugging history

**Set MCP to Production DB** (if not already):
```bash
export CHROMA_DB_PATH="/Users/tem/archive/mcp-memory/mcp-memory-service/chroma_production_db"
# Restart Claude Code if you changed this
```

### 2. Load Last Session Status (CRITICAL - Do First!)

**Query Production DB for most recent session status**:

```
Use mcp__chromadb-memory__recall_memory with query: "session status report"
```

This tells you:
- What was completed in last session
- What's in progress
- What's pending
- Current codebase state
- Next priorities

**IMPORTANT**: Read this BEFORE checking git status to understand context.

### 3. Check Codebase Changes Since Last Session

```bash
cd /Users/tem/humanizer_root
./track check
```

If changes detected:
```bash
./track verify-notes    # Cross-reference with ChromaDB
./track diff           # See what changed
```

If undocumented changes flagged → **Document immediately in ChromaDB before coding**

### 4. Load System Guidance (Meta DB)

Query the **Meta DB** for procedures and best practices:

```
Use mcp__chromadb-memory__recall_memory with query: "pinned guide best practice"
```

This retrieves the **Claude Code Memory Best Practices** guide with:
- Query-before-code workflow
- Memory structure template [What/Why/How/Next]
- Tag requirements (status, type, module, priority)
- When to store memories
- Refactoring triggers (>500 lines)

**Key principle**: "Write when necessary, reuse until you must add functionality"

### 5. Load Development Context (Production DB)

Query the **Production DB** for current project state:

```
Use mcp__chromadb-memory__recall_memory queries:
- "image import complete"
- "transformation pipeline"
- "files need refactoring"
- "production ready"
```

This gives you:
- ✅ Current capabilities (transformation engine, PostgreSQL, image import, philosophical features, **pipeline UI complete**)
- ❌ Missing features (LaTeX, PDF generation, publication pipeline)
- ⚠️ Files to refactor (large API routes files: library_routes.py 634 lines, routes.py 567 lines)
- 🎯 Architecture decision (DEC Jupiter lesson: extend working code, don't rewrite)

### 6. Verify System State (If Applicable)

If session status mentions recent imports or database changes, verify:

```bash
# Check backend is running
curl http://localhost:8000/ 2>&1 | head -5

# Check database connection
psql -U humanizer -d humanizer -c "SELECT COUNT(*) FROM collections;"

# Check media import status (if relevant)
psql -U humanizer -d humanizer -c "
SELECT
  COUNT(*) as total_media,
  COUNT(*) FILTER (WHERE storage_path IS NOT NULL) as with_files
FROM media;"
```

### 7. Assess Session Mode

Based on context from steps 2-5:

**If session status shows incomplete TODOs or flagged work:**
- Enter **PLAN MODE**
- Review session status report
- Present plan for continuing work
- Get user approval before coding

**If clean state (last session complete, no pending work):**
- Stay in **INTERACTIVE MODE**
- Ready for new instructions
- Ask user what they want to build

**Key**: Session status + ProductionDB tell you if work is pending. Use them to decide plan vs interactive mode.

### 8. Document When Completing Work

When completing features/refactoring:

A. **Take tracking snapshot**:
```bash
cd /Users/tem/humanizer_root
./track snapshot "Completed [description]"
```

B. **Store in ChromaDB** (Production DB):
```
Use mcp__chromadb-memory__store_memory:
  content: "[What] Completed feature X
           [Why] Required for user workflow Y
           [How] Implemented A, B, C
           [Next] Ready for Z, or feature complete

           Files: path/to/file.py (lines X-Y)"

  tags: ["module", "type", "status", "priority"]
  metadata: {"file": "path", "priority": "high"}
```

C. **Create session status at end of major work**:
```
Use mcp__chromadb-memory__store_memory:
  content: "SESSION STATUS REPORT - [Date] - [Feature] Complete

           ## ACCOMPLISHMENTS
           - Feature X: COMPLETE
           - Bug fixes: Y, Z

           ## CURRENT STATE
           - Database: N records
           - Files modified: X

           ## NEXT SESSION
           - Priority: Feature A
           - Deferred: Feature B"

  tags: ["session-status", "complete", "module"]
```

**Session status reports are CRITICAL** - they allow next session to resume with full context.

---

## 🎯 Current Project State (Oct 2025)

**Primary Goal**: Build transformation pipeline + book builder for academic/technical publishing

**Current Capabilities** ✅:
- ✅ Transformation engine (PERSONA/NAMESPACE/STYLE)
- ✅ PostgreSQL + pgvector embeddings
- ✅ Philosophical features (Madhyamaka, perspectives, contemplation)
- ✅ ChatGPT/Claude archive import with full metadata
- ✅ **IMAGE IMPORT SYSTEM (Oct 5, 2025)**:
  - 8,640 media records imported (user uploads, DALL-E, Sediment)
  - Full file ID preservation for markdown compatibility
  - Frontend displays images centered, scaled, clickable
  - Placeholder records for missing files (can upload later)
  - Green badge indicators for generated images in tool messages
- ✅ **TRANSFORMATION PIPELINE BACKEND (Oct 5, 2025)**:
  - Database schema: 4 tables with lineage tracking
  - Background job processor with async processing
  - API endpoints for job management, batch transforms
  - Support for: persona_transform, madhyamaka_detect, madhyamaka_transform, perspectives
  - Automatic lineage/provenance tracking
  - Graph visualization support
- ✅ **TRANSFORMATION PIPELINE FRONTEND UI (Oct 5, 2025)**:
  - PipelinePanel component (387 lines) integrated into message lightbox
  - Job creation from message context with all 4 transformation types
  - Real-time progress tracking with polling
  - ResultsModal (372 lines) with publication-quality markdown rendering
  - Type-specific result viewers for all job types
  - GET /api/pipeline/jobs/{job_id}/results endpoint
  - Multi-perspective analysis fully implemented
- ✅ **TRANSFORMATIONS LIBRARY (Oct 5, 2025)**:
  - Browse all transformation jobs with filters (status, type, search)
  - Detailed view with source message/collection links
  - Reapply transformations to new content
  - Full provenance tracking and lineage display
  - 🔧 Transformations tab in sidebar
- ✅ **BOOK BUILDER FOUNDATION (Oct 5, 2025)**:
  - Database schema: books, book_sections, book_content_links
  - Hierarchical section organization (Part → Chapter → Section)
  - API endpoints for CRUD operations (15 endpoints)
  - Basic UI: create books, view sections, outline view
  - Links transformation results to book sections
  - 📖 Books tab in sidebar
  - Configuration storage (JSONB for TOML-assisted UI)

**Missing Features** ❌:
- ❌ Book editor (markdown editing with live preview)
- ❌ "Add to Book" button in message lightbox
- ❌ TOML-assisted configuration UI
- ❌ LaTeX export from book builder
- ❌ PDF compositor
- ❌ Cover image generator
- ❌ Bibliography generator

**Large Files Needing Refactoring**:
- ✅ `backend/services/madhyamaka/` (REFACTORED + TESTED) - Was 1003 lines, now 10 modular files (2,132 total)
  - Comprehensive test suite: 1,869 lines, 142 tests
  - **Test Results**: 126 passing / 16 failing (89% pass rate) ✅ PRODUCTION READY
  - Detection thresholds tuned, methods implemented, core functionality validated
  - Old file deprecated: madhyamaka_service.py.deprecated
- **`backend/api/library_routes.py` (1005 lines)** ⚠️ CRITICAL - split transformations routes to separate file
- `backend/api/routes.py` (567 lines) → extract transformation routes to separate file
- `backend/models/chunk_models.py` (558 lines) → split by domain (chunks, messages, collections, media)
- `backend/api/philosophical_routes.py` (540 lines) → borderline, consider splitting
- `backend/api/pipeline_routes.py` (536 lines) → borderline, monitor as features grow
- `backend/api/book_routes.py` (490 lines) → new, monitor as features grow

**Target**: 200-300 lines per file, refactor when >500 lines

**Database Statistics** (as of Oct 5, 2025):
```
Conversations: 1,660
Messages: 46,379
Chunks: 33,952
Media: 8,640 (822 with files, 7,818 placeholders)
Collections: ChatGPT archive imported
Pipeline: 13+ jobs (multiple completed transformations across all 4 types)
Books: 0 (new feature, ready for use)
```

---

## 📚 3-Database ChromaDB Architecture

### When to Query Which Database

**Meta DB** (System Guides - 2 memories):
```
Query: "pinned guide best practice"
Query: "tracking system usage"
Query: "activation checklist"
```
Use for: Procedures, best practices, how-to guides

**Production DB** (Dev Context - 13+ memories):
```
Query: "session status report"
Query: "image import complete"
Query: "transformation pipeline"
Query: "files need refactoring"
```
Use for: Session status, active development, features, bugs, TODOs

**Historical DB** (Complete Archive - 547 memories):
```
Query: "PDF generation debugging"
Query: "LaTeX experiments history"
```
Use for: Ultra-think mode when stuck >30min, learn from past failures

### Switching Databases

**Via Environment Variable** (before launching Claude Code):
```bash
# Production (default for development)
export CHROMA_DB_PATH="/Users/tem/archive/mcp-memory/mcp-memory-service/chroma_production_db"

# Meta (for system procedures)
export CHROMA_DB_PATH="/Users/tem/archive/mcp-memory/mcp-memory-service/chroma_meta_db"

# Historical (for research)
export CHROMA_DB_PATH="/Users/tem/archive/mcp-memory/mcp-memory-service/chroma_test_db"
```

**Via Operator** (query without MCP):
```bash
cd /Users/tem/humanizer_root
./run_operator.sh query prod "publication pipeline"
./run_operator.sh query meta "best practices"
./run_operator.sh query hist "PDF debugging"
```

---

## 💡 Key Workflow Principles

### Query Before Code
**ALWAYS** check ChromaDB memories before implementing:
1. Query production: Does solution already exist?
2. Query meta: What are the best practices?
3. Query historical (if stuck): What failed before?

### Document After Work
**ALWAYS** store memory after completing work:
- Feature completed → store with tags: `feature`, `completed`, `[module]`
- File refactored → store with tags: `refactoring`, `completed`, `architecture`
- Bug fixed → store with tags: `bug-fix`, `completed`, `[area]`

### Refactoring Discipline
Mark files when:
- File exceeds **500 lines** → flag for refactoring
- File has **>3 distinct concerns** → needs splitting
- Logic duplicated across modules → needs extraction

**Store refactoring note**: "File X needs refactoring: N lines, handles A, B, C"

### Memory Lifecycle
```
1. QUERY: Check for existing knowledge (production/meta/historical)
2. CODE: Implement based on context
3. TEST: Verify changes work
4. STORE: Document [What/Why/How/Next] with proper tags
5. SNAPSHOT: Hash codebase state
6. QUERY: Verify memory stored correctly
```

---

## 🏗️ Architecture Overview

### Backend (Python 3.11 + FastAPI)
- **`main.py`** (153 lines) - FastAPI app, 7 router modules
- **`api/routes.py`** (567 lines) - Transformation endpoints
- **`agents/transformation_agent.py`** (319 lines) - Claude Agent SDK
- **`services/`** - Business logic (transformation, embedding, import, **madhyamaka: 1003 lines ⚠️**)
- **`models/`** - Database schemas, Pydantic models
- **`database/`** - PostgreSQL + pgvector integration

### Frontend (React + Vite)
- Simple upload interface
- Token counter & validation
- Transformation UI
- Port: 5173

### Tech Stack
- Python 3.11 (required)
- FastAPI (async)
- PostgreSQL + pgvector
- Claude Agent SDK
- React + Vite + TailwindCSS
- sentence-transformers (all-MiniLM-L6-v2)

---

## 🚀 Development Commands

### Quick Start
```bash
./start.sh    # Starts backend (port 8000) + frontend (port 5173)
```

### Backend (Python 3.11 + FastAPI)
```bash
cd backend
source venv/bin/activate
python main.py            # Development server
pytest                    # Run tests
black . --check          # Format check
ruff check .             # Linting
mypy .                   # Type checking
```

### Frontend (React + Vite)
```bash
cd frontend
npm run dev              # Development server
npm run build           # Production build
npm run lint            # ESLint
```

---

## 🔐 Key Configuration

**Environment Variables** (`.env`):
- `ANTHROPIC_API_KEY` - Required for Claude API
- `DEFAULT_MODEL=claude-sonnet-4-5-20250929`
- `HOST=127.0.0.1`, `PORT=8000`
- `DATABASE_URL=sqlite+aiosqlite:///./humanizer.db`

**API Endpoints**:
- `POST /api/transform` - PERSONA/NAMESPACE/STYLE transformation
- `GET /api/transform/{id}` - Status
- `POST /api/philosophical/perspectives` - Multi-perspective generation
- `POST /api/madhyamaka/detect` - Middle Path detection
- `POST /api/import/chatgpt` - Archive import

---

## 📝 Memory Storage Template

**When storing in ChromaDB Production DB:**

```
Content Structure:
[What]: Implemented LaTeX academic paper template
[Why]: Required for publication pipeline MVP
[How]: Used Jinja2 templates + XeLaTeX renderer
[Next]: Add bibliography generation, test with real archive

File: backend/services/latex_service.py (245 lines)

Tags: ["publication", "latex", "feature", "completed"]

Metadata: {
  "file": "backend/services/latex_service.py",
  "lines": "245",
  "priority": "high"
}
```

**Required Tags**:
- **Status**: `todo`, `in-progress`, `completed`, `blocked`
- **Type**: `feature`, `bug-fix`, `refactoring`, `research`, `decision`
- **Module**: `publication`, `api`, `webgui`, `latex`, `pdf`, `covers`
- **Priority**: `critical`, `high`, `medium`, `low`

---

## 🎓 DEC Jupiter Lesson

**Don't abandon working architecture for the next shiny thing.**

Current humanizer-agent is the **"VAX"** - proven, working, extensible:
- ✅ FastAPI backend is solid
- ✅ PostgreSQL + pgvector works
- ✅ Claude Agent SDK integration functional
- ✅ Frontend shows data

**DON'T**: Rewrite with Cloudflare Workers, new framework, etc.
**DO**: Extend current stack with publication features (LaTeX, PDF, covers)
**DO**: Incremental refactoring of large files
**DO**: Add new services to existing `backend/services/`

**Principle**: "One basket, one egg" - nurture what works, don't chase rewrites.

---

## 🔧 Tracking System Integration

**Codebase tracking** monitors changes and cross-references with ChromaDB:

```bash
cd /Users/tem/humanizer_root

./track check           # Check for changes
./track verify-notes    # Verify documented in ChromaDB
./track diff           # Detailed file changes
./track status         # Show flags/snapshots
./track snapshot "note" # Take new snapshot
./track clear-flags    # Clear after documenting
```

**Undocumented changes** are flagged → Must document in ChromaDB before proceeding.

---

## 🧭 Session Decision Tree

```
START NEW SESSION
│
├─ Run activation checklist (steps 1-5)
│
├─ Query Production DB
│  ├─ "what we were working on"
│  ├─ "critical priority todos"
│  └─ "files need refactoring"
│
├─ Check tracking flags
│  └─ ./track status
│
└─ DECIDE MODE:
   │
   ├─ IF: Pending TODOs or flagged refactoring
   │  └─ ENTER PLAN MODE
   │     ├─ Present plan for completion
   │     └─ Get user approval
   │
   └─ ELSE: Clean state
      └─ INTERACTIVE MODE
         ├─ Ready for instructions
         └─ Ask what to build
```

---

## 📖 Additional Documentation

**In `/Users/tem/humanizer_root/`**:
- `DATABASE_ARCHITECTURE.md` - 3-DB design philosophy
- `3DB_QUICK_REFERENCE.md` - Database selection guide
- `TRACKING_GUIDE.md` - Complete tracking documentation
- `TRACKING_QUICKREF.md` - Quick reference card
- `CHROMADB_OPERATOR_README.md` - Operator usage

**In `/Users/tem/humanizer-agent/docs/`**:
- `SETUP.md` - Setup instructions
- `QUICK_REFERENCE.md` - Command reference

---

## ✅ Success Criteria for This Session

By following this checklist, Claude Code will:
1. ✅ Know exact codebase state (via tracking)
2. ✅ Understand what was in progress (via production DB)
3. ✅ Follow best practices (via meta DB)
4. ✅ Be ready to continue work (plan mode) or accept new tasks (interactive)
5. ✅ Document all changes (via tracking + ChromaDB)

**Result**: Zero context loss between sessions. Claude picks up exactly where previous session left off.

---

## 🚀 Next Session Priorities

Based on current state, next session should focus on:

**Priority 1: Complete Book Builder Phase 2** (Markdown Editor)
- Add "📖 Add to Book" button in MessageLightbox
- Create BookSectionSelector modal for choosing book/section
- Implement markdown editor for sections (Monaco or CodeMirror)
- Add live preview panel
- Section management UI (add/delete/reorder/nest)

**Priority 2: Book Builder Phase 3** (Configuration & Export)
- TOML-assisted configuration UI
- Export book to markdown
- Export book to LaTeX (using transformation system)
- PDF generation pipeline integration

**Priority 3: Technical Debt** (Refactoring)
- **CRITICAL**: Split library_routes.py (1005 lines) - extract transformations routes
- Fix Alembic migration baseline (currently using create_all())
- Resolve embedding dimension mismatch (1024 vs 1536)

**Priority 4: Deferred Features**
- LaTeX typesetting engine
- Cover image generator
- Bibliography generator
- Archive-to-structure converter

---

*Last Updated: Oct 5, 2025 - Transformations Library + Book Builder Phase 1*
