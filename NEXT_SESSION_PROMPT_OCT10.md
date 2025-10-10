# Next Session Prompt - October 10, 2025

**Use this prompt to start your next session with Claude Code**

---

## Quick Start

```
I'm continuing work on the Humanizer Agent project. This is a new session.

IMMEDIATE PRIORITY: Implement the tiered subscription system.

CONTEXT:
- Last session (Oct 10): MCP testing complete, UI fixes done, tier system fully planned
- Current state: Artifacts system operational, personifier working, user auth exists
- Database: 139k chunks (90% embedded), 6,826 collections, 4 artifacts
- Services: Backend (port 8000) and Frontend (port 5173) need to be started

TASK:
Implement the complete tiered subscription system with 5 tiers (FREE/MEMBER/PRO/PREMIUM/ENTERPRISE) including:
1. Content length limits per tier
2. Smart semantic chunking for PREMIUM+ users (unlimited length)
3. Usage tracking and monthly reset logic
4. Enforcement middleware on personifier endpoint

RESOURCES TO READ FIRST:
- TIER_SYSTEM_PLAN.md - Complete architecture (1000+ lines)
- CLAUDE.md - Project bootstrap with quick commands
- SESSION_SUMMARY_OCT10.md - Previous session details

IMPLEMENTATION CHECKLIST (in order):
1. Update backend/models/user.py - Add MEMBER, PRO tiers (5 min)
2. Create backend/services/tier_service.py - Validation logic (1 hour)
3. Create backend/services/chunking_service.py - Smart splitting (2 hours)
4. Update backend/api/personifier_routes.py - Add middleware (1 hour)
5. Create backend/alembic/versions/006_add_tiers.py - Migration (15 min)
6. Write backend/tests/test_tier_service.py - Unit tests (30 min)
7. Manual testing all tiers (30 min)

ESTIMATED TIME: 4-5 hours

Let's start by:
1. Reading TIER_SYSTEM_PLAN.md to understand the complete architecture
2. Starting the services with ./start.sh
3. Updating the SubscriptionTier enum in backend/models/user.py
```

---

## Session Context Summary

### What Was Accomplished Last Session

**MCP Testing** ✅
- Tested all 12 Humanizer MCP tools
- 11/12 working (91% success)
- Fixed critical artifact search route order bug
- Configured MCP server in Claude Code

**UI Fixes** ✅
- Fixed dropdown contrast issue (white on white)
- Refactored ArtifactBrowser for consistency
- Removed redundant sidebar detail view
- Established pattern: sidebars = lists only

**Transformation Testing** ✅
- Tested full workflow: input → personifier → artifact → GUI
- 337-character quantum mechanics text
- Auto-saved to artifacts successfully
- Verified in database and GUI

**Tier System Planning** ✅
- Designed 5-tier subscription system
- Created complete implementation plan
- Key innovation: Smart chunking for PREMIUM tier
- Full architecture in TIER_SYSTEM_PLAN.md

### Current System State

**Database**:
- 139,232 chunks (90% embedded)
- 6,826 collections
- 193,661 messages
- 4 artifacts

**Services Status**:
- Backend: Port 8000 (needs restart)
- Frontend: Port 5173 (needs restart)
- PostgreSQL: Running with pgvector
- MCP Server: Configured at ~/.config/claude-code/mcp.json

**Key Files Modified Last Session**:
- backend/api/artifact_routes.py - Route order fix
- frontend/src/components/ArtifactBrowser.jsx - Dropdown fix, detail view removed
- frontend/src/components/Workstation.jsx - Artifact tab support
- frontend/src/components/IconTabSidebar.jsx - Artifact callback wiring

### Technical Patterns Established

**Route Order (Critical)**:
- Specific routes BEFORE parameterized routes
- Example: `/search` before `/{id}`
- FastAPI matches in definition order

**Sidebar UI Pattern**:
- Sidebars: Show lists only
- Main pane: Show details
- Click item in sidebar → opens in main pane as tab
- Sidebar stays on list view

**Theme Overrides**:
- Use inline styles for critical UI elements
- DaisyUI computed styles override CSS classes
- Example: `style={{ backgroundColor: '#1f2937', color: '#f9fafb' }}`

**Artifact Workflow**:
- All semantic operations should be saveable as artifacts
- Use `save_as_artifact: true` parameter
- Each artifact creates traceable lineage
- Enables provenance tracking

---

## Tier System Overview

### Tier Structure

| Tier | Monthly Cost | Max Tokens | Monthly Transforms | Key Feature |
|------|-------------|-----------|-------------------|-------------|
| FREE | $0 | 500 | 10 | Try service |
| MEMBER | $9 | 2,000 | 50 | Regular use |
| PRO | $29 | 8,000 | 200 | Professional |
| PREMIUM | $99 | UNLIMITED | UNLIMITED | Smart chunking |
| ENTERPRISE | Custom | UNLIMITED | UNLIMITED | API access |

### Key Innovation: Smart Chunking

**For PREMIUM/ENTERPRISE tiers with long content**:

1. **Input**: Novel, research paper, or long-form content (10k-100k+ tokens)
2. **Chunking**: Split at semantic boundaries (paragraphs, sentences)
3. **Context**: Include overlap from previous chunk (2-3 sentences)
4. **Processing**: Transform each chunk individually
5. **Artifacts**: Save each chunk as separate artifact
6. **Reassembly**: Combine chunks with smooth transitions
7. **Final Artifact**: Save complete output with lineage to chunk artifacts

**Example Flow**:
```
Input: 50,000 token novel
↓
Split into 8 chunks (~6,000 tokens each with overlap)
↓
Process chunk 1 → save as artifact_1
Process chunk 2 → save as artifact_2 (with context from chunk 1)
...
Process chunk 8 → save as artifact_8
↓
Reassemble all 8 chunks → remove duplicate context
↓
Save final artifact with parent_artifact_ids = [artifact_1...artifact_8]
↓
Output: Complete transformed novel with full provenance
```

---

## Implementation Details

### File 1: backend/models/user.py

**Change**:
```python
class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    MEMBER = "member"      # ADD
    PRO = "pro"            # ADD
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
```

### File 2: backend/services/tier_service.py (NEW)

**Purpose**: Validate tier limits and track usage

**Key Classes**:
- `TierLimits` - Tier configuration constants
- `TierService` - Business logic for tier management

**Key Methods**:
- `check_transform_allowed()` - Validate against limits
- `reset_monthly_usage_if_needed()` - Auto-reset on month change
- `increment_usage()` - Update counters after transform
- `recommend_tier_for_tokens()` - Suggest upgrade

### File 3: backend/services/chunking_service.py (NEW)

**Purpose**: Smart semantic content splitting

**Key Classes**:
- `ContentChunk` - Dataclass for chunk metadata
- `ChunkingService` - Chunking logic

**Key Methods**:
- `split_into_chunks()` - Main chunking algorithm
- `count_tokens()` - Token counting with tiktoken
- `reassemble_chunks()` - Combine transformed chunks
- `_split_into_sentences()` - Sentence-level splitting
- `_build_context()` - Create overlap context

### File 4: backend/api/personifier_routes.py (UPDATE)

**Changes**:
1. Add `current_user` dependency (require auth)
2. Count tokens in input
3. Call `TierService.check_transform_allowed()`
4. For long content with PREMIUM+: call `process_long_content()`
5. For regular content: call `process_single_transform()`
6. Increment usage counters

### File 5: backend/alembic/versions/006_add_tiers.py (NEW)

**Purpose**: Database migration

**Changes**:
```sql
ALTER TYPE subscriptiontier ADD VALUE IF NOT EXISTS 'member';
ALTER TYPE subscriptiontier ADD VALUE IF NOT EXISTS 'pro';
```

### File 6: backend/tests/test_tier_service.py (NEW)

**Tests**:
- Test each tier's token limits
- Test monthly transform limits
- Test monthly reset logic
- Test upgrade recommendations
- Test PREMIUM unlimited processing

---

## Quick Reference Commands

### Start Services
```bash
./start.sh  # Backend:8000, Frontend:5173
```

### Health Check
```bash
curl http://localhost:8000/api/library/stats
curl http://localhost:8000/api/artifacts/health
```

### Run Migration
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### Run Tests
```bash
cd backend
source venv/bin/activate
pytest backend/tests/test_tier_service.py -v
```

### Manual Testing
```bash
# Test FREE tier (should fail at 600 tokens)
curl -X POST http://localhost:8000/api/personify/rewrite \
  -H "Content-Type: application/json" \
  -d '{"text":"<600 tokens of text>","strength":1.0}'

# Test PREMIUM tier (should chunk long content)
curl -X POST http://localhost:8000/api/personify/rewrite \
  -H "Content-Type: application/json" \
  -d '{"text":"<10000 tokens of text>","strength":1.0}'
```

---

## Critical Rules

**SQLAlchemy**: NEVER use `metadata` field → use `custom_metadata`

**F-Strings**: Extract nested f-strings to variable first

**Venv**: Always `source venv/bin/activate` for backend commands

**Default User**: `c7a31f8e-91e3-47e6-bea5-e33d0f35072d`

**Routes**: Specific routes BEFORE parameterized routes

**Testing**: Test all tiers manually before committing

**Documentation**: Update CLAUDE.md after implementation

---

## Success Criteria

Implementation is complete when:

- [  ] All 5 tiers defined in enum
- [  ] TierService validates limits correctly
- [  ] ChunkingService splits long content
- [  ] Personifier endpoint enforces limits
- [  ] Database migration runs successfully
- [  ] All unit tests pass
- [  ] Manual testing shows:
  - [  ] FREE rejects 600 tokens
  - [  ] MEMBER rejects 2500 tokens
  - [  ] PRO rejects 9000 tokens
  - [  ] PREMIUM processes 20000 tokens with chunking
  - [  ] Monthly limits enforced
  - [  ] Monthly reset works on month change
  - [  ] Upgrade recommendations accurate

---

## Troubleshooting

### If services won't start
```bash
pkill -f uvicorn
pkill -f vite
./start.sh
```

### If database connection fails
```bash
./dbswitch list  # Check active profile
./dbswitch switch productionDB  # Switch if needed
```

### If migrations fail
```bash
cd backend
source venv/bin/activate
alembic current  # Check current version
alembic history  # View migration history
alembic upgrade head  # Apply migrations
```

### If tests fail
```bash
# Check test database exists
./dbswitch list

# Run specific test
pytest backend/tests/test_tier_service.py::test_free_tier_limit -v

# Run with output
pytest backend/tests/test_tier_service.py -v -s
```

---

## After Implementation

### Update CLAUDE.md
- Mark tier system as implemented
- Update "Current State" section
- Add new priority (Stripe integration or paragraph extractor)

### Create Session Summary
- Document what was implemented
- Note any issues encountered
- List files modified
- Record test results

### Store in ChromaDB
- Save comprehensive session summary
- Include implementation insights
- Tag appropriately

---

## Files to Read

**Must Read Before Starting**:
1. `TIER_SYSTEM_PLAN.md` - Complete architecture (read thoroughly)
2. `CLAUDE.md` - Quick commands and current state

**Reference During Implementation**:
3. `backend/models/user.py` - Current user model
4. `backend/api/personifier_routes.py` - Current endpoint
5. `SESSION_SUMMARY_OCT10.md` - Previous session details

**For Context**:
6. `docs/USER_SYSTEM_ARCHITECTURE.md` - Auth foundation
7. `MCP_TEST_REPORT_OCT10.md` - MCP status

---

## Estimated Timeline

**Total: 4-5 hours**

1. Setup & reading (20 min)
   - Read TIER_SYSTEM_PLAN.md
   - Start services
   - Verify current state

2. Enum update (5 min)
   - Update SubscriptionTier
   - Verify syntax

3. TierService (1 hour)
   - Create tier_service.py
   - Implement TierLimits class
   - Implement TierService class
   - Test manually

4. ChunkingService (2 hours)
   - Create chunking_service.py
   - Implement ContentChunk dataclass
   - Implement ChunkingService class
   - Test with various lengths
   - Debug edge cases

5. Personifier updates (1 hour)
   - Add auth dependency
   - Add tier checking
   - Implement process_long_content()
   - Wire up chunking

6. Migration (15 min)
   - Create migration file
   - Run migration
   - Verify in database

7. Testing (1 hour)
   - Write unit tests
   - Run all tests
   - Manual testing each tier
   - Document results

---

**Ready to implement!**

Start by reading TIER_SYSTEM_PLAN.md carefully, then follow the implementation checklist in order.
