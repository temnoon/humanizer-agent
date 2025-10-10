# CLAUDE.md - Humanizer Agent Bootstrap

**Last Updated**: Oct 10, 2025 | **Status**: Artifacts operational, Tier system ready

---

## 🔔 NEW SESSION START

```bash
# 1. Start services
./start.sh  # Backend:8000, Frontend:5173

# 2. Health check
curl http://localhost:8000/api/library/stats
curl http://localhost:8000/api/artifacts/health

# 3. Check artifacts (4 artifacts exist)
curl "http://localhost:8000/api/artifacts?limit=10"
```

---

## 🎯 Current State

**Mission**: Computational Madhyamaka - embeddings reveal meaning construction

**Recent Achievements** (Oct 10):
- ✅ **Tier system planned**: Complete architecture for FREE/MEMBER/PRO/PREMIUM/ENTERPRISE
- ✅ **MCP testing complete**: 11/12 tools operational, 1 bug fixed
- ✅ **UI consistency**: Sidebar artifacts list-only behavior
- ✅ **Artifact workflow tested**: Transformation → auto-save → GUI display verified
- ✅ **Personifier**: 396 pairs, 9.2/10 quality, auto-save enabled

**Database**:
- Chunks: 139,232 (90% embedded)
- Collections: 6,826 | Messages: 193,661
- **Artifacts: 4** (tested with real transformations)

---

## ⚠️ CRITICAL RULES

**SQLAlchemy**: NEVER use `metadata` field → use `custom_metadata`
**F-Strings**: Extract nested f-strings to variable first
**Venv**: Always `source venv/bin/activate` for backend commands
**Default User**: `c7a31f8e-91e3-47e6-bea5-e33d0f35072d`
**Routes**: Specific routes BEFORE parameterized routes (FastAPI order matters)

---

## 🚀 Quick Commands

**Start**: `./start.sh` (backend:8000, frontend:5173)
**Backend**: `cd backend && source venv/bin/activate && python [cmd]`
**DB**: `./dbswitch list|switch` | `./dbexplore stats`
**Embeddings**: `./embedgen plan|process|status`

**Artifacts**:
```bash
# List artifacts
curl "http://localhost:8000/api/artifacts?limit=10"

# Create artifact (via personify with auto-save)
curl -X POST http://localhost:8000/api/personify/rewrite \
  -H "Content-Type: application/json" \
  -d '{"text":"Your text","save_as_artifact":true,"artifact_topics":["test"]}'

# Search artifacts (semantic)
curl "http://localhost:8000/api/artifacts/search?query=consciousness&limit=10"
```

---

## 🎯 NEXT SESSION PRIORITY #1

### Tiered Subscription System (~4-5 hours)

**Goal**: Implement content length limits and smart chunking for production

**Read First**: `TIER_SYSTEM_PLAN.md` (complete architecture)

**Tiers**:
- FREE: 500 tokens, 10/month
- MEMBER: 2,000 tokens, 50/month
- PRO: 8,000 tokens, 200/month
- PREMIUM: UNLIMITED (smart chunking)
- ENTERPRISE: UNLIMITED + API access

**Implementation Checklist**:
1. ✅ Update `backend/models/user.py` - Add MEMBER, PRO tiers (5 min)
2. ✅ Create `backend/services/tier_service.py` - Validation logic (1 hour)
3. ✅ Create `backend/services/chunking_service.py` - Smart splitting (2 hours)
4. ✅ Update `backend/api/personifier_routes.py` - Add middleware (1 hour)
5. ✅ Create `backend/alembic/versions/006_add_tiers.py` - Migration (15 min)
6. ✅ Write unit tests - `backend/tests/test_tier_service.py` (30 min)
7. ✅ Manual testing - All tiers (30 min)

**Key Innovation**: PREMIUM tier splits long content (novels, papers) into semantic chunks, processes each, maintains context, and reassembles with smooth transitions.

---

## 📊 Artifacts System

**Endpoints** (all working):
- `POST /api/artifacts/save` - Create artifact
- `GET /api/artifacts` - List with filters
- `GET /api/artifacts/search` - Semantic search (FIXED: route order)
- `GET /api/artifacts/{id}` - Get details
- `PATCH /api/artifacts/{id}` - Update
- `DELETE /api/artifacts/{id}` - Delete
- `GET /api/artifacts/{id}/lineage` - Get ancestry

**GUI**:
- Sidebar: 🗂️ Artifacts tab → List with filters
- Main pane: Click artifact → Opens as tab with full metadata
- Dropdowns: Fixed contrast (dark bg, light text)

**Auto-Save**:
- `/api/personify/rewrite` with `save_as_artifact: true`
- Each transformation creates traceable artifact

**Key Files**:
- Backend: `backend/models/artifact_models.py`, `backend/services/artifact_service.py`, `backend/api/artifact_routes.py`
- Frontend: `frontend/src/hooks/useArtifacts.js`, `frontend/src/components/ArtifactBrowser.jsx`

---

## 📊 Personifier System

**Endpoints**:
- `/api/personify` - Pattern analysis (no rewrite)
- `/api/personify/rewrite` ⭐ - Production endpoint (Claude API)

**Parameters**:
- `text`, `strength`, `use_examples`, `n_examples`
- `save_as_artifact` (bool), `artifact_topics` (list)

**Training**:
- 396 pairs across 18 domains
- Quality: 9.2/10
- Categories: simplification (30%), direct_address (23%), hedging_removal (19%)

---

## 🎓 Key Patterns

**pgvector**: Cast explicitly `text(f"'{embedding_str}'::vector")`
**Semantic search**: Use `/api/library/chunks?search=query` (pgvector cosine)
**Artifacts**: All semantic outputs should be saveable
**Route order**: Specific routes (`/search`) BEFORE parameterized routes (`/{id}`)
**UI consistency**: Sidebars = lists only, main pane = details
**Refactor**: Keep files 200-300 lines

---

## 📚 Documentation

**Planning**:
- `TIER_SYSTEM_PLAN.md` - Complete tier architecture with chunking strategy
- `SESSION_SUMMARY_OCT10.md` - MCP testing, UI fixes, transformation testing

**Architecture**:
- `docs/DOCUMENTATION_INDEX.md` - 40+ architectural docs
- `docs/USER_SYSTEM_ARCHITECTURE.md` - Auth foundation

**Artifacts**:
- `ARTIFACTS_INTEGRATION_COMPLETE.md` - Phase 1
- `ARTIFACTS_PHASE2_COMPLETE.md` - Phase 2
- `MCP_TEST_REPORT_OCT10.md` - Comprehensive MCP testing

**Historical**:
- `SESSION_SUMMARY_OCT9_*.md` - Personifier development
- `~/humanizer_root/prime_motivation_report.md` - 3,200 words

---

## 🎯 Architecture Vision

**Semantic Composition Pipeline** (artifacts at every stage):
```
Query (anchor embedding)
  ↓
Semantic Search → save as artifact (search_results)
  ↓
Top N Chunks (interest list)
  ↓
Paragraph Extraction → save as artifact (extraction)
  ↓
Agent Commentary → save as artifact (commentary)
  ↓
Progressive Summarization → save as artifact (summary)
  ↓
Transformation → save as artifact (transformation)
  ↓
Final Output (fully traceable lineage)
```

**Goal**: Every semantic operation creates artifacts → full provenance → consciousness work

---

## 🚧 Future Priorities (After Tier System)

### Phase 2: Extended Functionality (~4-6 hours)
1. **Paragraph Extractor** (~1 hour)
   - Split chunks → embed paragraphs → rank by similarity
   - Auto-save extractions as artifacts

2. **Auto-save Integration** (~2-3 hours)
   - Add to `/api/embedding/cluster` → cluster summaries
   - Add to `/api/library/chunks` (search) → search results

3. **Progressive Summarization** (~4-6 hours)
   - Build hierarchy: chunks → summaries → root
   - Multi-resolution navigation

### Phase 3: Monetization (~3-4 hours)
1. **Stripe Integration**
   - Checkout flow
   - Webhook handlers
   - Subscription management

2. **Pricing Page UI**
   - Tier comparison table
   - Feature highlights
   - CTA buttons

---

## 🛠️ MCP Server

**Status**: Configured, 11/12 tools operational

**Location**: `~/humanizer_root/humanizer_mcp/`

**Config**: `~/.config/claude-code/mcp.json`

**Tools** (12 total):
- Library: list_books ✅, search_chunks ✅, get_library_stats ⚠️ (minor), search_images ⏳
- Artifacts: save_artifact ✅, search_artifacts ✅, list_artifacts ✅, get_artifact ✅
- Interest: track_interest ✅, get_interest_list ✅, get_connections ✅
- Quantum: read_quantum ⏳ (ready, needs backend)

**Test Report**: See `MCP_TEST_REPORT_OCT10.md`

---

## 🐛 Known Issues

### Minor Issues
1. **get_library_stats MCP wrapper**: Field name mismatch (API works)
2. **Artifact lineage endpoint**: Minor async issue (not blocking)

### Next to Fix
1. Update MCP wrapper field names
2. Test paragraph extraction

---

*Updated: Oct 10, 2025*
*Status: Artifacts operational, Tier system architecture complete*
*Next: Implement tiered subscription system with smart chunking*
*Read: TIER_SYSTEM_PLAN.md for implementation details*
