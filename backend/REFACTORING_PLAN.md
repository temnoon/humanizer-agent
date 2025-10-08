# Backend API Refactoring Plan

**Goal**: Refactor large API route files (>500 lines) into modular, maintainable components while ensuring zero regression through comprehensive testing.

**Target**: 200-300 lines per file (per CLAUDE.md guidelines)

---

## 📊 Current State

### Files to Refactor

| File | Lines | Target |
|------|-------|--------|
| `api/library_routes.py` | 1,152 | Split into 4 files (~300 each) |
| `api/vision_routes.py` | 643 | Split into 2-3 files (~250 each) |
| `api/pipeline_routes.py` | 608 | Split into 2-3 files (~250 each) |
| `api/routes.py` | 567 | Split into 2 files (~300 each) |

### Existing Tests

**Current coverage**: Only `tests/services/madhyamaka/` exists
- ❌ **NO API route tests exist**
- ❌ **NO integration tests for endpoints**
- ⚠️ **CRITICAL RISK**: Refactoring without tests could introduce regressions

---

## 🎯 Refactoring Strategy

### Phase 1: library_routes.py (1,152 lines → 4 files)

**Current structure:**
```
library_routes.py (1,152 lines)
├── Response Models (lines 33-120): 7 Pydantic schemas
├── Collection Routes (132-508): 4 endpoints, 377 lines
├── Stats Route (509-559): 1 endpoint, 51 lines
├── Media Routes (560-816): 3 endpoints, 257 lines
└── Transformation Routes (817-1152): 3 endpoints, 336 lines
```

**Proposed structure:**
```
api/library/
├── __init__.py (exports all routers)
├── schemas.py (~120 lines)
│   ├── CollectionSummary
│   ├── MessageSummary
│   ├── ChunkDetail
│   ├── MediaDetail
│   ├── TransformationSummary
│   ├── TransformationDetail
│   └── CollectionHierarchy
├── collection_routes.py (~400 lines)
│   ├── GET /collections
│   ├── GET /collections/{collection_id}
│   ├── GET /messages/{message_id}/chunks
│   ├── GET /search
│   └── GET /stats
├── media_routes.py (~300 lines)
│   ├── GET /media
│   ├── GET /media/{media_id}/metadata
│   └── GET /media/{media_id}/file
└── transformation_routes.py (~350 lines)
    ├── GET /transformations
    ├── GET /transformations/{job_id}
    └── POST /transformations/{job_id}/reapply
```

**Main API integration:**
```python
# In main.py or routes aggregator:
from api.library import collection_router, media_router, transformation_router

app.include_router(collection_router)
app.include_router(media_router)
app.include_router(transformation_router)
```

### Phase 2: vision_routes.py (643 lines → 2-3 files)

**Analysis needed** - will examine structure after Phase 1

### Phase 3: routes.py (567 lines → 2 files)

**Analysis needed** - will examine structure after Phase 1

---

## ✅ Testing Strategy (CRITICAL)

### Step 1: Baseline API Tests (BEFORE refactoring)

**Create comprehensive test coverage:**
```
backend/tests/api/
├── conftest.py (test fixtures, DB setup)
├── test_library_collections.py
├── test_library_media.py
├── test_library_transformations.py
├── test_vision_routes.py
└── test_general_routes.py
```

**Test coverage requirements:**
- ✅ All GET endpoints (200 OK responses)
- ✅ All POST endpoints (create operations)
- ✅ Error cases (404, 400, 500)
- ✅ Query parameters (search, filters, pagination)
- ✅ Database interactions (using test DB)
- ✅ File operations (media files, uploads)

**Example test structure:**
```python
# test_library_collections.py
class TestCollectionRoutes:
    async def test_list_collections_empty(self, client, db):
        response = await client.get("/api/library/collections")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_collections_with_data(self, client, db, sample_collection):
        response = await client.get("/api/library/collections")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == str(sample_collection.id)

    async def test_get_collection_hierarchy(self, client, db, sample_collection):
        response = await client.get(f"/api/library/collections/{sample_collection.id}")
        assert response.status_code == 200
        assert "messages" in response.json()
```

### Step 2: Run Baseline Tests

```bash
cd backend
pytest tests/api/ -v --tb=short
```

**Success criteria**: All tests PASS with current implementation

### Step 3: Refactor with Continuous Testing

**For each module refactored:**
1. Create new file structure
2. Move code (copy-paste initially, don't delete original)
3. Run tests → MUST PASS
4. If tests pass → Delete old code
5. If tests fail → Debug and fix
6. Repeat for next module

### Step 4: Final Verification

```bash
# Run ALL tests
pytest tests/ -v --cov=api --cov-report=html

# Check coverage report
open htmlcov/index.html
```

**Success criteria:**
- ✅ All tests pass
- ✅ Coverage >80% for API routes
- ✅ No regression in functionality

---

## 🚨 Risk Mitigation

### Risks

1. **Breaking existing frontend integration** - Frontend calls these endpoints
2. **Database query changes** - SQLAlchemy queries might behave differently when moved
3. **Import dependency issues** - Circular imports, missing dependencies
4. **File path handling** - Media file routes use filesystem paths

### Mitigation

1. **Keep URL routes identical** - Only file structure changes, not API contract
2. **Test-driven refactoring** - Tests fail? Don't commit
3. **Incremental changes** - One file at a time, verify before next
4. **Git safety** - Create feature branch, commit after each successful phase
5. **Frontend smoke test** - Run frontend after refactoring, verify all features work

---

## 📋 Execution Checklist

### Pre-Refactoring
- [ ] Review this plan with user
- [ ] Create feature branch `refactor/backend-api-routes`
- [ ] Set up test infrastructure (`conftest.py`, fixtures)
- [ ] Write baseline tests for library_routes.py endpoints
- [ ] Run baseline tests - all PASS

### Phase 1: library_routes.py
- [ ] Create `api/library/` directory structure
- [ ] Create `schemas.py` (move Pydantic models)
- [ ] Create `collection_routes.py` (move collection endpoints)
- [ ] Create `media_routes.py` (move media endpoints)
- [ ] Create `transformation_routes.py` (move transformation endpoints)
- [ ] Update main API to import new routers
- [ ] Run tests - all PASS
- [ ] Frontend smoke test - all features work
- [ ] Commit: "refactor: Split library_routes.py into modular structure"

### Phase 2: vision_routes.py
- [ ] Analyze structure
- [ ] Plan refactoring
- [ ] Write baseline tests
- [ ] Refactor with testing
- [ ] Verify & commit

### Phase 3: routes.py
- [ ] Analyze structure
- [ ] Plan refactoring
- [ ] Write baseline tests
- [ ] Refactor with testing
- [ ] Verify & commit

### Post-Refactoring
- [ ] Run full test suite
- [ ] Update CLAUDE.md (remove from "Technical Debt")
- [ ] Document new structure in README
- [ ] Store session status in ChromaDB
- [ ] Merge feature branch

---

## 🎓 Success Criteria

**Refactoring successful if:**
1. ✅ All files <500 lines (target: 200-300)
2. ✅ All tests pass (100% passing)
3. ✅ Frontend functionality unchanged
4. ✅ API contract unchanged (same URLs, responses)
5. ✅ Code is MORE readable (better separation of concerns)
6. ✅ Test coverage >80%

**Estimated time:**
- Test infrastructure setup: 2-3 hours
- library_routes.py refactoring: 3-4 hours
- vision_routes.py refactoring: 2 hours
- routes.py refactoring: 2 hours
- **Total: ~10-12 hours**

---

## 📝 Questions for Review

1. **Approve refactoring plan?** (structure, file splits, naming)
2. **Approve testing strategy?** (test first, then refactor)
3. **Time commitment acceptable?** (~10-12 hours total)
4. **Any concerns about breaking changes?**
5. **Proceed with Phase 1 (library_routes.py)?**

---

**Next step**: Review this plan, then proceed to create baseline tests for library_routes.py endpoints.
