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
- **Production DB** (15+ memories) - Active dev context, TODOs, refactoring targets, session status
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

This retrieves the **Claude Code Memory Best Practices** guide.

### 5. Document When Completing Work

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
           - Priority: Feature A"

  tags: ["session-status", "complete", "module"]
```

**Session status reports are CRITICAL** - they allow next session to resume with full context.

---

## 🎯 Current Project State (Oct 2025)

**Primary Goal**: Build transformation pipeline + book builder for academic/technical publishing

**Alignment with Mission**: All features support "Language as a Sense" framework - helping users witness their own subjective agency through narrative transformation.

### Backend Capabilities ✅

- ✅ **Transformation Engine**: PERSONA/NAMESPACE/STYLE transformations
- ✅ **PostgreSQL + pgvector**: Embeddings, semantic search
- ✅ **Philosophical Features**: Madhyamaka detection, multi-perspective analysis, contemplation exercises
- ✅ **Archive Import**: ChatGPT/Claude conversation import with full metadata
- ✅ **Image System**: 8,640 media records, DALL-E/SD/MJ metadata extraction, Apple Photos integration
- ✅ **Transformation Pipeline**: Background job processing, lineage tracking, 4 transformation types
- ✅ **Vision System**: Claude vision API integration, OCR, image analysis
- ✅ **Book Builder Backend**: CRUD operations, hierarchical sections, content linking (15 API endpoints)

### Frontend Capabilities ✅

- ✅ **Unified Architecture** (Oct 6, 2025 - Phase 2 Complete):
  - **WorkspaceContext** (195 lines): Single source of truth - tabs, inspector pane, interest list, preferences
  - **LayoutManager** (140 lines): Unified pane system (sidebar | main | preview | inspector)
  - **MessageViewer** (352 lines): Non-modal message viewer in inspector pane - NO MORE MODALS
  - **InterestList** (120 lines): Browse path tracking (surfaces user's subjective journey)
  - **Workstation** (385 lines): Main component using context + LayoutManager + inspector
  - **Philosophy**: "Witness your own subjective agency" - makes exploration path visible
- ✅ **Book Builder UI**: Full-screen editor, section navigator, markdown + LaTeX rendering, content cards
- ✅ **Image Browser**: Infinite scroll (8,640+ images), metadata panel, conversation links
- ✅ **Transformation Library**: Browse/filter jobs, reapply transformations, provenance tracking
- ✅ **Pipeline Panel**: Job creation, progress tracking, results modal
- ✅ **Configurable Limits**: Items-per-page dropdown (50-2000), no hardcoded limits

### Bug Fixes ✅

- ✅ Unicode filename encoding (screenshots work)
- ✅ Book persistence (user_id migration)
- ✅ Layout bugs fixed
- ✅ Image display in conversations
- ✅ Media duplicate records (backend deduplication + .limit(1) fix)
- ✅ React duplicate key warnings (ImageGallery fixed)
- ✅ Search functionality (Oct 7, 2025 - LibraryBrowser + TransformationsLibrary handleSearch fixed)

### Known Issues ⚠️

- ⚠️ Database has duplicate media records (handled gracefully, cleanup recommended)

### Missing Features ❌

- ❌ Book Builder Phase 2 (CRUD on content cards)
- ❌ Vision OCR background processing
- ❌ LaTeX/PDF export
- ❌ TOML-assisted config UI

### Database Statistics (Oct 6, 2025)

```
Conversations: 1,660
Messages: 46,379
Chunks: 33,952
Media: 8,640 (1,841 with files)
Books: 4 active
Book Sections: 7
Book Content Links: 16
Transformation Jobs: 13+
```

---

## 🏗️ Architecture Overview

### Backend (Python 3.11 + FastAPI)
- FastAPI app with 7 router modules
- PostgreSQL + pgvector
- Claude Agent SDK for transformations
- Background job processor
- Vision API integration

### Frontend (React + Vite)
- **New** (Oct 6): WorkspaceContext + LayoutManager architecture
- React 18 + TailwindCSS
- react-resizable-panels for all panes
- CodeMirror for markdown editing
- Port: 5173

### Tech Stack
- Python 3.11 (required)
- FastAPI (async)
- PostgreSQL + pgvector
- Claude Agent SDK
- React + Vite + TailwindCSS
- sentence-transformers

---

## 🚀 Development Commands

### Quick Start
```bash
./start.sh    # Starts backend (port 8000) + frontend (port 5173)
```

### Database Switching (NEW - Oct 7)
```bash
cd backend

# List available database profiles
./dbswitch list

# Switch between databases
./dbswitch switch test        # Switch to test database
./dbswitch switch production  # Switch back to production
./dbswitch current           # Show active profile

# Database management
./dbinit create humanizer_test2       # Create new database
./dbinit schema humanizer_test2       # Initialize schema
./dbinit stats humanizer              # Show database statistics
./dbinit backup humanizer             # Backup to SQL file

# After switching, RESTART the backend for changes to take effect
./start.sh
```

See: `backend/DATABASE_SWITCHING.md` for full guide

### Backend
```bash
cd backend
source venv/bin/activate
python main.py            # Development server
pytest                    # Run tests
```

### Frontend
```bash
cd frontend
npm run dev              # Development server
npm test                 # Run unit/integration tests (132 tests)
npm run test:ui          # Visual test runner
npm run test:coverage    # Coverage report
npm run test:e2e         # End-to-end tests (Playwright)
npm run build            # Production build
```

---

## 🧪 Testing Strategy (Next Priority)

**Why Testing Matters**: The Humanizer mission requires users to trust the interface enough to explore deeply. The "corporeal substrate" (UI) must be reliable, predictable, persistent.

### Testing Approach

**Unit Tests** (Jest + React Testing Library):
- WorkspaceContext: Tab management, localStorage persistence
- LayoutManager: Pane sizing, prop rendering
- InterestList: Item management, navigation
- Book components: Section loading, content linking

**Integration Tests**:
- Workstation + WorkspaceContext: Tab lifecycle
- Book builder flow: Create → Edit → Save → Verify
- Interest list + navigation: Add items → Navigate to them

**E2E Tests** (Playwright):
- User journey: Browse images → View conversation → Add to interest list
- Book workflow: Open book → Edit section → Add content → Verify persistence
- Pane persistence: Resize → Refresh → Verify restored

**Test Setup**:
```bash
cd frontend
npm install --save-dev @testing-library/react @testing-library/jest-dom @playwright/test
```

**Files to Create**:
```
frontend/src/__tests__/
  contexts/WorkspaceContext.test.jsx
  layout/LayoutManager.test.jsx
  integration/book-builder.test.jsx

frontend/e2e/
  user-journeys.spec.js
```

---

## 📚 3-Database ChromaDB Architecture

**Meta DB** (System Guides - 2 memories):
```
Query: "pinned guide best practice"
```

**Production DB** (Dev Context - 15+ memories):
```
Query: "session status report"
Query: "testing suite next session"
Query: "frontend refactoring"
```

**Historical DB** (Complete Archive - 547 memories):
```
Query: "PDF generation debugging"
```

Use for: Ultra-think mode when stuck >30min

---

## 💡 Key Workflow Principles

### Query Before Code
**ALWAYS** check ChromaDB memories before implementing:
1. Query production: Does solution already exist?
2. Query meta: What are the best practices?
3. Query historical (if stuck): What failed before?

### Document After Work
**ALWAYS** store memory after completing work with proper tags:
- Status: `todo`, `in-progress`, `completed`
- Type: `feature`, `bug-fix`, `refactoring`
- Module: `publication`, `api`, `webgui`, `frontend`
- Priority: `critical`, `high`, `medium`, `low`

### Refactoring Discipline
- File exceeds **500 lines** → flag for refactoring
- File has **>3 distinct concerns** → needs splitting
- **Target**: 200-300 lines per file

---

## 🎓 DEC Jupiter Lesson

**Don't abandon working architecture for the next shiny thing.**

Current humanizer-agent is the **"VAX"** - proven, working, extensible.

**DON'T**: Rewrite with new frameworks
**DO**: Extend current stack incrementally
**DO**: Refactor large files systematically

**Principle**: "One basket, one egg" - nurture what works.

---

## 🚀 Next Session Priorities

**Updated: Oct 7, 2025 (Late Evening) - Database Switching System + Documentation Complete**

### Priority 0: Git Operations (DO THIS FIRST!)

**Objective**: Commit and push all new work to GitHub

**Files to commit**:
```bash
# New files
backend/dbswitch
backend/dbinit
backend/db_profiles/production.env
backend/db_profiles/test.env
backend/db_profiles/archive.env
backend/DATABASE_SWITCHING.md
backend/QUICK_START_DB_SWITCHING.md
PITCH_DECK_AND_FUNCTIONAL_SPEC.md

# Modified
CLAUDE.md
```

**Commit message**:
```bash
git add backend/dbswitch backend/dbinit backend/db_profiles/ backend/DATABASE_SWITCHING.md backend/QUICK_START_DB_SWITCHING.md PITCH_DECK_AND_FUNCTIONAL_SPEC.md CLAUDE.md

git commit -m "feat: Database switching system + comprehensive pitch deck/functional spec

- Database switching: dbswitch CLI for profile management
- Database management: dbinit CLI for create/backup/restore
- 3 profiles: production, test, archive (expandable)
- Full documentation: DATABASE_SWITCHING.md + quick start guide
- Pitch deck: 175-page comprehensive functional specification
- Sufficient for complete platform recreation by another team

Tested: All 132 frontend tests passing, database switching working"

git push origin master
```

**Estimated time**: 5 minutes

### Priority 1: Continue Chrome DevTools MCP Testing

**Status**: Completed initial round (all systems working, no errors)

**Remaining tasks**:
1. Test edge cases (error handling, long content, special characters)
2. Document any bugs found
3. Performance testing (large datasets, slow connections)

---

### Priority 2: Apply useListNavigation to Remaining Lists

**Objective**: Consistent navigation across all list components

**Tasks**:
1. Apply to LibraryBrowser (collections)
2. Apply to ImageBrowser (main pane)
3. Test keyboard shortcuts across all components

**Estimated time**: 1-2 hours

---

### Priority 3: Consolidate Image Browsers

**Objective**: Merge ImageGallery (sidebar) and ImageBrowser (main pane) into one unified component

**Tasks**:
1. Decide on single component approach (enhance ImageBrowser)
2. Remove ImageGallery sidebar component
3. Use navigation in sidebar → opens ImageBrowser in main pane
4. Ensure all features work (pagination, search, filters, metadata panel)

**Estimated time**: 2-3 hours

---

### Priority 4: Book Builder Phase 2

**Objective**: CRUD operations on content cards

**Tasks**:
1. Add/edit/delete content cards in book sections
2. Drag-to-reorder functionality for content cards
3. Backend PATCH endpoint for content links
4. Test book builder Phase 2 features

**Estimated time**: 4-6 hours

---

### Priority 5: Technical Debt - Continue API Refactoring

**Files needing refactoring** (>500 lines):
- `backend/api/vision_routes.py` (643 lines) ← **NEXT TARGET**
- `backend/api/pipeline_routes.py` (608 lines)
- `backend/api/routes.py` (567 lines)

**✅ COMPLETED**: `library_routes.py` (1,152 → 1,219 lines across 5 modular files)

---

## ✅ Completed This Session

### Oct 7, 2025 (Late Evening) - Database Switching System + Comprehensive Documentation

**Objective**: Enable isolated database testing and create complete platform specification

**Implementation**: Database Switching System
- **dbswitch** CLI tool (287 lines) - Profile switcher with safety features
- **dbinit** CLI tool (356 lines) - Database create/backup/restore/stats
- **3 database profiles**: production.env, test.env, archive.env
- **Full isolation**: Test archive imports without affecting production
- **Safety**: Automatic backups, confirmation prompts, API key preservation

**Results**:
- ✅ Switch between databases with single command
- ✅ Create/initialize/backup databases via CLI
- ✅ Tested: production (1.8GB) ↔ test (10MB empty)
- ✅ macOS-compatible (fixed grep -P → sed patterns)
- ✅ Documentation: DATABASE_SWITCHING.md + QUICK_START guide

**Implementation**: Comprehensive Documentation
- **PITCH_DECK_AND_FUNCTIONAL_SPEC.md** (175 pages, 40K+ lines)
- Complete pitch deck for investors
- Full functional specifications for developers
- Database schemas (15+ tables, all indexes)
- API specs (50+ endpoints with examples)
- UI/UX specs (component patterns, visual system)
- 8-week implementation guide
- Philosophy → Implementation mapping
- Sufficient for complete platform recreation

**Results**:
- ✅ Investor-ready pitch deck
- ✅ Developer handoff documentation
- ✅ Platform migration specification
- ✅ AI assistant can recreate entire tool from this spec

**Chrome DevTools MCP Testing**:
- ✅ Image browser (pagination, search, 8,640 images working)
- ✅ Conversation viewer (navigation, messages displaying)
- ✅ Message navigation (prev/next, keyboard shortcuts)
- ✅ Book builder (sections, preview with LaTeX + images)
- ✅ Transformations library (list, detail, filters)
- ✅ Console health (no errors, 132 tests passing)

**Files Created**:
- backend/dbswitch (executable)
- backend/dbinit (executable)
- backend/db_profiles/*.env (3 files)
- backend/DATABASE_SWITCHING.md
- backend/QUICK_START_DB_SWITCHING.md
- PITCH_DECK_AND_FUNCTIONAL_SPEC.md

---

### Oct 7, 2025 (Earlier) - Library Routes Refactoring

**Objective**: Break down monolithic `library_routes.py` (1,152 lines) into modular, maintainable files

**Implementation**:
```
backend/api/
├── library_routes.py          35 lines  (orchestrator - includes sub-routers)
├── library_schemas.py        103 lines  (Pydantic response models)
├── library_collections.py    323 lines  (collection + message endpoints)
├── library_media.py          393 lines  (media + search + stats endpoints)
└── library_transformations.py 365 lines  (transformation library endpoints)
```

**Results**:
- ✅ Zero logic changes (pure extraction refactor)
- ✅ All 12 backend tests passing (test_library_collections.py)
- ✅ All 132 frontend tests passing
- ✅ All 11 API routes working correctly
- ✅ Server running without errors
- ✅ Fixed deprecation warning (`regex` → `pattern`)

**Architecture Benefits**:
- **Modularity**: Each file has single responsibility
- **Maintainability**: All files under 400 lines (target: 200-300)
- **Scalability**: Easy to add new endpoints to appropriate module
- **Testability**: Can test modules independently

**API Coverage** (11 routes):
- Collections: GET /collections, GET /collections/{id}, GET /messages/{id}/chunks
- Media: GET /media, GET /media/{id}/metadata, GET /media/{id}/file
- Search: GET /search
- Stats: GET /stats
- Transformations: GET /transformations, GET /transformations/{id}, POST /transformations/{id}/reapply

---

### Oct 7, 2025 (Part 2) - Full-Page Message Viewer with LaTeX

**Objective**: Replace cramped inspector pane with full-page markdown editor for professional reading experience

**Implementation**:

**New Component**: `MarkdownEditorTab.jsx` (169 lines)
- **Flip view**: 📝 Edit mode ↔ 👁️ Rendered preview
- **LaTeX preprocessing**: Automatic delimiter conversion (`\[...\]` → `$$...$$`, `\(...\)` → `$...$`)
- **Professional typography**: Physics-paper styling with proper spacing, larger fonts, academic aesthetics
- **Reusable**: Works for messages, books, any markdown content

**Integration**:
- Updated `Workstation.jsx`: Added `markdownEditor` tab type
- Updated `ConversationViewer.jsx`: Messages open as full-page tabs (not inspector)
- Messages fetch all chunks and combine into single document

**Results**:
- ✅ Messages display in full-page tabs (no more cramped bottom pane)
- ✅ Beautiful LaTeX rendering with KaTeX (Lagrangian equations, tensors, etc.)
- ✅ Flip toggle for edit/preview modes
- ✅ Professional academic paper aesthetics
- ⚠️ Known issue: Images show JSON metadata (needs custom renderer)

**Bug Fixes**:
- ✅ Fixed sidebar occlusion (removed `fixed` positioning)
- ✅ Added `data-testid="sidebar"` for E2E tests
- ✅ Configured Playwright to use system Chromium

---

### Oct 7, 2025 (Part 3) - Image System & Navigation Refactor

**Objective**: Fix image browsing issues and add unified navigation system

**Problems Addressed**:
1. ❌ ImageGallery limited to 500 images (database has 8,640)
2. ❌ "Add to Book" button missing from message cards
3. ❌ No message navigation (prev/next arrows + keyboard)
4. ❌ No unified navigation system across components

**Implementation**:

**1. Fixed ImageGallery Pagination** (`ImageGallery.jsx`)
- Added server-side pagination (100 items/page, 87 pages total)
- Added search and filter support (generator, mime type)
- Added pagination UI (‹ Page X/Y ›)
- **Before**: Hardcoded 500 limit
- **After**: Full access to all 8,640+ images

**2. Restored "Add to Book" Button** (`ConversationViewer.jsx` lines 731-749)
- Added purple "Add to Book" button next to "View" button
- Fetches message chunks on click
- Opens BookSectionSelector modal
- Users can now add messages to books again

**3. Created useListNavigation Hook** (`hooks/useListNavigation.js` - NEW, 107 lines)
- **Purpose**: Unified keyboard and UI navigation for ALL lists
- **Features**:
  - Keyboard navigation (ArrowUp/Down, Enter, Escape)
  - Current index tracking with prev/next functions
  - Selection handling with callbacks
  - Loop support (optional)
  - Enable/disable toggle
- **Reusable**: Works for messages, images, conversations, collections

**4. Integrated Message Navigation** (`ConversationViewer.jsx`)
- Added Prev/Next buttons with position indicator ("X of Y")
- Keyboard shortcuts (↑/↓ arrows) work
- Auto-scroll to message on navigation
- Current message highlighted (realm-symbolic border)
- Visual feedback for navigation state

**Results**:
- ✅ ImageGallery: Can access all 8,640+ images (was 500)
- ✅ Message Actions: "Add to Book" button restored
- ✅ Navigation: Prev/Next buttons + keyboard shortcuts work
- ✅ Visual Feedback: Current message highlighted
- ✅ Position Indicator: Shows "X of Y" messages
- ✅ Reusable Hook: Future lists can use same pattern

**Architecture Improvements**:
- Created foundation for unified navigation across ALL lists
- Established pattern: Import hook → Pass items → Use handlers
- All future list components should use `useListNavigation`

**Files Modified**:
- `frontend/src/components/ImageGallery.jsx` - Pagination added
- `frontend/src/components/ConversationViewer.jsx` - Navigation + button
- `frontend/src/hooks/useListNavigation.js` - NEW hook created

**Remaining Work** (Next Session):
1. Apply `useListNavigation` to other lists (LibraryBrowser, ImageBrowser)
2. Consolidate ImageGallery and ImageBrowser into one component
3. Unified action buttons pattern across all lists

---

### Oct 6, 2025 - Testing Suite & Frontend Phase 2

### Testing Suite - COMPLETE
- 132 tests passing (Vitest + Playwright)
- Unit: WorkspaceContext, LayoutManager, InterestList, SearchBar, SettingsModal, useKeyboardShortcuts
- Integration: Book builder, Navigation flows
- E2E: User journeys, pane persistence

### Frontend Phase 2 - COMPLETE
- **MessageViewer** (352 lines): Non-modal message viewer
- **WorkspaceContext**: Enhanced with inspector pane state
- **ConversationViewer**: Refactored to use inspector instead of modal
- **Architecture**: 100% pane-based, zero modal overlays
- **SearchBar, SettingsModal, Keyboard shortcuts**: All integrated

### Bug Fixes - COMPLETE
- Backend media duplicate crash (library_routes.py:715)
- Frontend duplicate keys (ImageGallery + API deduplication)

---

## 📊 Current Test Coverage

**Total Tests**: 132 passing ✅
- **Unit tests**: 93 (WorkspaceContext, LayoutManager, InterestList, SearchBar, SettingsModal, useKeyboardShortcuts)
- **Integration tests**: 21 (Book builder, Navigation flows)
- **E2E tests**: Comprehensive (User journeys, Pane persistence)

**Test Commands**:
```bash
npm test                 # Run all unit/integration tests
npm run test:ui          # Visual test runner
npm run test:coverage    # Coverage report
npm run test:e2e         # End-to-end tests
```

---

### Oct 7, 2025 (Part 4) - Critical Bug Fixes & Chrome DevTools MCP Setup

**Objective**: Fix remaining bugs and prepare for comprehensive testing

**Bug Fixes**:

1. **React Hooks Order Violation** (ConversationViewer.jsx:192-229)
   - **Problem**: `useListNavigation` hook called after early returns, causing "rendered more hooks" error
   - **Fix**: Moved all hooks (useMemo, useCallback, useListNavigation) BEFORE any return statements
   - **Result**: Gizmo editing now works, no more hook order crashes

2. **Image Rendering in Books** (MarkdownEditor.jsx:20-50)
   - **Problem**: Book preview showed raw JSON instead of images
   - **Fix**: Added image preprocessing (same as MarkdownEditorTab)
   - **Supports**: Both `sediment://` and `file-service://` protocols
   - **Result**: Images now render in book preview pane

3. **Book Selector Shows Only One Book** (BookSectionSelector.jsx:48-49)
   - **Problem**: Only last book showed in selector modal
   - **Fix**: Removed `user_id` filter to match BookBuilder behavior
   - **Result**: All books now appear in "Add to Book" modal

4. **Image ID Format Normalization** (3 files)
   - **Problem**: Uncertain handling of sediment:// vs file-service:// formats
   - **Analysis**: Database uses `file-XXXXX` (dashes only, zero underscores)
   - **Fix**: Precise prefix replacement `file_` → `file-` (not all underscores)
   - **Files**: MarkdownEditorTab.jsx, MarkdownEditor.jsx, ConversationViewer.jsx
   - **Result**: Safe edge case handling, won't corrupt IDs with legitimate underscores

5. **Text Overflow in Transformations Sidebar** (TransformationsLibrary.jsx)
   - **Problem**: Text breaking awkwardly, cramped configuration JSON
   - **Fix**: Added `break-words`, `flex-wrap`, `shrink-0` classes throughout
   - **Changes**: Date/time layout (vertical), Configuration JSON wrapping, all text elements
   - **Result**: Proper text wrapping, respects container margins

6. **DOM Nesting Warning** (MarkdownEditorTab.jsx:143-156)
   - **Problem**: `<pre>` nested in `<p>` causing validation warning
   - **Fix**: Custom `p` component detects block children, renders as `<div>` when needed
   - **Result**: No more DOM nesting warnings

**Infrastructure**:

7. **Chrome DevTools MCP Configuration** (~/.claude/mcp_servers.json)
   - Added `chrome-devtools` MCP server using npx chrome-devtools-mcp@latest
   - Configured with NVM Node.js path
   - Ready for comprehensive testing after Claude Code restart

**Files Modified**:
- `ConversationViewer.jsx`: Hook order, memoization
- `MarkdownEditor.jsx`: Image + LaTeX preprocessing
- `MarkdownEditorTab.jsx`: Image preprocessing, DOM nesting fix
- `BookSectionSelector.jsx`: Remove user_id filter
- `TransformationsLibrary.jsx`: Text overflow fixes (8 locations)
- `~/.claude/mcp_servers.json`: Chrome DevTools MCP added

**Testing Status**:
- ✅ All 132 frontend tests still passing
- ✅ Server running without errors
- ✅ Ready for comprehensive end-to-end testing with Chrome DevTools MCP

---

*Last Updated: Oct 7, 2025 (Late Evening) - Bug Fixes Complete, Ready for Testing*
