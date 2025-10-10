# Architecture & Extension Summary
## Quick Reference Guide

**Version:** 1.0
**Date:** October 2025

---

## Document Map

This architecture specification is split across multiple files:

### 📊 **Part 1: Current Architecture & Proposed Tools**
**File:** [API_ARCHITECTURE_DIAGRAMS.md](API_ARCHITECTURE_DIAGRAMS.md)

**Contents:**
- Complete API overview (Mermaid diagrams)
- Data flow architecture
- AUI tool flow diagrams (6 current tools)
- Current API endpoint map (62 endpoints)
- Proposed AUI extensions (45 new tools!)
- Proposed API extensions (25 new endpoints)

**Key Insights:**
- Current: 6 tools, 62 endpoints, ~10% API coverage
- Proposed: 51 tools, 87 endpoints, ~80% API coverage
- 8.5x increase in AUI capabilities

### 📊 **Part 2: Integration & Implementation**
**File:** [API_ARCHITECTURE_DIAGRAMS_PART2.md](API_ARCHITECTURE_DIAGRAMS_PART2.md)

**Contents:**
- Integration architecture (complete system)
- Extended data flow diagrams
- Database schema extensions (5 new tables)
- Implementation roadmap (7 phases, 32 weeks)
- Tool priority matrix
- Testing strategy
- Performance optimization

**Key Insights:**
- 5 new database tables needed
- 15 new indexes for performance
- Phased rollout over 8 months
- Comprehensive testing at each phase

### 🎨 **Part 3: Visual Export & Examples**
**File:** [API_DIAGRAMS_VISUAL_EXPORT.md](API_DIAGRAMS_VISUAL_EXPORT.md)

**Contents:**
- PlantUML diagrams (for PowerPoint/Confluence)
- SVG export instructions
- Implementation examples (code)
- Tutorial animation component
- Tool implementation checklist
- Performance testing scripts
- Docker deployment configs

**Key Insights:**
- All diagrams exportable to PowerPoint/Keynote
- Working code examples for each component
- Ready-to-use Docker Compose configuration

---

## Quick Stats

### Current State (Oct 2025)

```
AUI Tools:              6
API Endpoints:         62
API Coverage:         ~10%
Database Tables:       15
Frontend Components:   25+
Lines of Code:      50,000+
```

### Proposed State (Q3 2026)

```
AUI Tools:             51  (+45, 8.5x)
API Endpoints:         87  (+25, 1.4x)
API Coverage:         ~80%  (+70pp)
Database Tables:       20  (+5)
Frontend Components:   40+  (+15)
New Features:       Major  (see below)
```

---

## The 45 New Tools

### Priority 1: API Coverage (30 tools - Q4 2025 to Q1 2026)

#### Book Management (8 tools)
1. list_books
2. get_book
3. update_book
4. delete_book
5. create_book_section
6. update_book_section
7. delete_book_section
8. export_book

#### Transformation (6 tools)
9. transform_chunk
10. list_transformations
11. get_transformation
12. reapply_transformation
13. get_transformation_lineage
14. batch_transform

#### Madhyamaka & Philosophy (7 tools)
15. detect_madhyamaka
16. analyze_philosophy
17. generate_perspectives
18. start_contemplation
19. list_contemplation_exercises
20. map_beliefs
21. socratic_dialogue

#### Vision & Media (4 tools)
22. analyze_image
23. ocr_image
24. search_images
25. import_apple_photos

#### Import & Archive (3 tools)
26. import_chatgpt
27. import_claude
28. check_import_status

#### Statistics (2 tools)
29. get_library_stats
30. get_embedding_stats

### Priority 2: High-Value New Features (15 tools - Q1 2026 to Q2 2026)

#### Conversation Intelligence (5 tools)
31. find_related_conversations
32. get_conversation_timeline
33. trace_conversation_thread
34. summarize_conversation
35. extract_insights

#### Framework Evolution (3 tools)
36. track_framework_evolution
37. compare_frameworks
38. detect_framework_shift

#### Advanced Embeddings (3 tools)
39. learn_transformation
40. apply_transformation_vector
41. compose_transformations

#### Workspace Management (4 tools)
42. save_workspace
43. load_workspace
44. list_workspaces
45. create_workspace_preset

---

## The 25 New API Endpoints

### Library Extensions (5 endpoints)
```
POST /api/library/collections/{id}/related
POST /api/library/collections/{id}/summarize
POST /api/library/collections/{id}/insights
POST /api/library/timeline
POST /api/library/threads
```

### Embedding Extensions (5 endpoints)
```
POST /api/embeddings/evolution
POST /api/embeddings/compare-frameworks
POST /api/embeddings/detect-shift
POST /api/embeddings/apply-transform
POST /api/embeddings/compose
```

### Transformation Extensions (1 endpoint)
```
POST /api/transformations/batch
```

### Workspace Management - NEW (6 endpoints)
```
POST   /api/workspace/save
GET    /api/workspace/load/{name}
GET    /api/workspace/list
POST   /api/workspace/presets
GET    /api/workspace/presets
DELETE /api/workspace/{name}
```

### Notifications - NEW (4 endpoints)
```
GET       /api/notifications
POST      /api/notifications/mark-read
GET       /api/notifications/subscribe
WebSocket /api/notifications/stream
```

### Workflows - NEW (4 endpoints)
```
POST /api/workflows
GET  /api/workflows
GET  /api/workflows/{id}
POST /api/workflows/{id}/execute
```

---

## The 5 New Database Tables

```sql
-- 1. Workspaces (save UI state)
CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR(200) NOT NULL,
  state JSONB NOT NULL,
  is_preset BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Notifications (background jobs)
CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  type VARCHAR(50) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Workflows (automation)
CREATE TABLE workflows (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR(200) NOT NULL,
  trigger JSONB NOT NULL,
  actions JSONB NOT NULL,
  enabled BOOLEAN DEFAULT true
);

-- 4. Framework Snapshots (evolution tracking)
CREATE TABLE framework_snapshots (
  id UUID PRIMARY KEY,
  framework_id VARCHAR(100) NOT NULL,
  snapshot_date DATE NOT NULL,
  cluster_data JSONB NOT NULL,
  UNIQUE(framework_id, snapshot_date)
);

-- 5. Related Content Cache (performance)
CREATE TABLE related_content_cache (
  id UUID PRIMARY KEY,
  source_id UUID NOT NULL,
  source_type VARCHAR(50) NOT NULL,
  related_items JSONB NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  UNIQUE(source_id, source_type)
);
```

---

## Implementation Timeline

### Phase 1: Foundation Extensions (4 weeks - Q4 2025)
**Tools:** 15 (Books, Transformations, Stats, Vision basics)
**APIs:** 2 new endpoints
**Focus:** Essential daily workflow tools

### Phase 2: Intelligence Layer (6 weeks - Q1 2026)
**Tools:** 10 (Conversation intelligence, Framework evolution, Import)
**APIs:** 8 new endpoints
**Database:** 2 new tables
**Focus:** Smart content discovery

### Phase 3: Philosophy Deepening (6 weeks - Q2 2026)
**Tools:** 7 (Madhyamaka, Contemplation, Belief mapping)
**APIs:** 7 new endpoints
**Components:** 6 new UI components
**Focus:** Full philosophical analysis

### Phase 4: Advanced Embeddings (3 weeks - Q2 2026)
**Tools:** 3 (Transformation arithmetic)
**APIs:** 3 new endpoints
**Focus:** Vector operations

### Phase 5: Workspace & Automation (5 weeks - Q3 2026)
**Tools:** 8 (Workspace, Workflows)
**APIs:** 9 new endpoints
**Database:** 2 new tables
**Focus:** Repeatable workflows

### Phase 6: Real-time & Notifications (4 weeks - Q3 2026)
**Tools:** 0 (infrastructure)
**APIs:** 4 new endpoints (+ WebSocket)
**Database:** 1 new table
**Infrastructure:** Redis, WebSocket server
**Focus:** Background job monitoring

### Phase 7: Voice Interface (4 weeks - Q4 2026)
**Tools:** 0 (enhancement)
**APIs:** 3 new endpoints (voice)
**Focus:** Accessibility & hands-free

**Total Timeline:** 32 weeks (~8 months)

---

## Priority Recommendations

### Top 10 Tools to Build First (Weeks 1-4)

Based on user value × implementation ease:

1. **list_books** (High value, trivial implementation)
   - Users constantly ask "what books do I have?"
   - 30 minutes to implement

2. **get_library_stats** (High value, easy)
   - Dashboard metrics
   - 1 hour to implement

3. **search_images** (High value, easy)
   - Already have media table
   - 1 hour to implement

4. **list_transformations** (High value, easy)
   - Browse transformation history
   - 30 minutes to implement

5. **export_book** (Very high value, medium effort)
   - Critical for publishing workflow
   - 2-3 days to implement (markdown/LaTeX/PDF)

6. **batch_transform** (High value, medium effort)
   - Transform multiple chunks at once
   - 1 day to implement

7. **find_related_conversations** (Very high value, hard)
   - Semantic discovery
   - 3-4 days to implement (embedding similarity)

8. **get_embedding_stats** (High value, easy)
   - Already have data, just format it
   - 1 hour to implement

9. **analyze_image** (High value, medium)
   - Claude Vision integration
   - 2 days to implement

10. **create_book_section** (High value, medium)
    - Essential for book workflow
    - 1 day to implement

**Total Effort:** ~2 weeks for top 10

---

## Architecture Patterns

### Pattern 1: Tool Definition → Automatic Execution

```python
# Just define the tool...
TOOLS.append({
    "name": "list_books",
    "endpoint": {
        "method": "GET",
        "path": "/api/books"
    },
    "parameters": {...},
    "gui_component": "BookLibrary"
})

# execute_tool() handles everything automatically!
```

**Benefits:**
- No custom code per tool
- Consistent behavior
- Easy to add new tools

### Pattern 2: GUI Action → Component Mapping

```javascript
// Frontend automatically maps actions to components
handleGuiAction({
  action: 'open_book_library',
  params: {filters: {...}}
})
→ Opens BookLibrary component with filters
```

**Benefits:**
- Declarative
- No conditional logic
- Extensible

### Pattern 3: Tutorial Animation System

```javascript
// Define animation steps
getAnimationSteps('search_embeddings', params)
→ Returns array of steps

// Animator executes them
TutorialAnimator.play(steps)
→ Highlights, clicks, types automatically
```

**Benefits:**
- Teaches users the GUI
- Reduces support burden
- Makes interface transparent

---

## Key Design Decisions

### Decision 1: Tool Registry Pattern

**Choice:** Central `TOOLS` array with declarative definitions

**Alternatives Considered:**
- Class-based tools (more OOP, more boilerplate)
- Decorator-based tools (more Pythonic, less discoverable)

**Rationale:**
- Easy to see all tools at once
- LLM-friendly format
- No code duplication
- Simple to test

### Decision 2: Background Jobs for Heavy Operations

**Choice:** Celery + Redis for async tasks

**Alternatives Considered:**
- FastAPI BackgroundTasks (simpler, less robust)
- Direct async/await (no retries, no monitoring)

**Rationale:**
- Clustering can take minutes
- Transformations use external API (rate limits)
- Users need progress updates
- Need retry logic

### Decision 3: Workspace State in Database (not localStorage)

**Choice:** PostgreSQL `workspaces` table

**Alternatives Considered:**
- localStorage (no sync across devices)
- Session storage (lost on close)
- Cookies (size limits)

**Rationale:**
- Sync across devices
- Share workspaces with team (future)
- Versioning/history possible
- No size limits

### Decision 4: Notification via WebSocket (not Polling)

**Choice:** WebSocket `/api/notifications/stream`

**Alternatives Considered:**
- Polling every N seconds (wasteful)
- Long polling (complex)
- Server-Sent Events (one-way only)

**Rationale:**
- Real-time updates
- Low latency
- Bi-directional (can send acks)
- Works with Redis pub/sub

---

## Testing Strategy

### Unit Tests (per tool)

```python
async def test_list_books(agent):
    result, gui_action = await agent.execute_tool(
        "list_books",
        {"book_type": "paper"}
    )
    assert isinstance(result, list)
    assert gui_action["component"] == "BookLibrary"
```

**Coverage:** 51 tools × 3 test cases each = 153 tests

### Integration Tests (workflows)

```python
async def test_research_workflow():
    # Search → Cluster → Create Book → Add Content
    response1 = await agent.process_message("Find Buddhism chunks")
    response2 = await agent.process_message("Cluster them")
    response3 = await agent.process_message("Create a book")
    response4 = await agent.process_message("Add top 10 chunks")
    # Verify end-to-end
```

**Coverage:** 10 common workflows

### E2E Tests (Playwright)

```javascript
test('user can search and create book via agent', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.press('Meta+`');  // Open agent
  await page.fill('[data-agent-input]', 'Find Buddhism chunks');
  await page.press('Enter');
  // Wait for ChunkBrowser to open
  await expect(page.locator('[data-tab-type="chunks"]')).toBeVisible();
  // Continue workflow...
});
```

**Coverage:** 5 critical user journeys

### Load Tests (Locust)

```python
class AgentUser(HttpUser):
    @task
    def search_chunks(self):
        self.client.post("/api/agent/chat", json={
            "message": "Find chunks about test",
            "model_name": "mistral:7b",
            "user_id": "test-user"
        })
```

**Target:** 100 concurrent users, 1000 req/min

---

## Performance Targets

### Response Times

| Operation | Target | Current | Gap |
|-----------|--------|---------|-----|
| Agent chat (no tool) | <500ms | ~2s | ⚠️ Needs optimization |
| Agent chat (with tool) | <2s | ~3-4s | ⚠️ Needs optimization |
| Clustering (1000 embeddings) | <10s | ~15s | ⚠️ Add caching |
| Book export (100 pages) | <5s | N/A | Build with performance in mind |

### Optimizations Needed

1. **Cache clustering results** (Redis, 7 days)
2. **Cache related content** (DB table, 1 day)
3. **Batch API calls** (group multiple tools)
4. **Optimize vector queries** (add covering indexes)
5. **Pre-compute framework snapshots** (daily cron)

---

## Deployment Architecture

### Development

```
localhost:5173 (Frontend - Vite)
localhost:8000 (Backend - FastAPI)
localhost:11434 (Ollama - LLM)
localhost:5432 (PostgreSQL)
```

### Production (Proposed)

```
Cloudflare Pages (Frontend)
    ↓ HTTPS
Cloudflare Workers (API Gateway)
    ↓
AWS ECS (Backend containers)
    ↓
AWS RDS (PostgreSQL + pgvector)
    ↓
AWS S3 (File storage)

Redis (ElastiCache)
Celery Workers (ECS tasks)
```

**Estimated Cost:** ~$200-300/month (moderate usage)

---

## Security Considerations

### API Authentication

```python
# All endpoints require authentication
@router.post("/api/agent/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user)  # JWT token
):
    # user.id automatically injected
    pass
```

### Tool Execution Safety

```python
# Validate all parameters
def validate_tool_params(tool: Dict, params: Dict):
    for param_name, param_def in tool["parameters"].items():
        if param_def.get("required") and param_name not in params:
            raise ValueError(f"Missing required parameter: {param_name}")

    # Type validation
    # SQL injection prevention (use parameterized queries)
    # Path traversal prevention (validate file paths)
```

### Rate Limiting

```python
# Prevent abuse
from slowapi import Limiter

limiter = Limiter(key_func=get_user_id)

@router.post("/api/agent/chat")
@limiter.limit("100/hour")  # 100 requests per hour per user
async def chat(...):
    pass
```

---

## Documentation Deliverables

### For Developers

- ✅ Architecture diagrams (this document)
- ✅ Implementation examples (Visual Export doc)
- ✅ API specifications (Part 1)
- ✅ Database schemas (Part 2)
- [ ] API client SDK (Python + JavaScript)
- [ ] Postman collection
- [ ] OpenAPI/Swagger docs (auto-generated)

### For Users

- [ ] User guide (how to use agent)
- [ ] Tool reference (what each tool does)
- [ ] Tutorial videos (screencasts)
- [ ] FAQ (common questions)

### For Operations

- [ ] Deployment guide (Docker, AWS, etc.)
- [ ] Monitoring setup (Grafana dashboards)
- [ ] Backup/restore procedures
- [ ] Incident response playbook

---

## Success Metrics

### Usage Metrics

```
Daily Active Users (DAU)
Tools Used Per Session (target: 5+)
Agent Conversations Per Day
Average Tools Per Conversation (target: 3+)
```

### Performance Metrics

```
P50 Response Time (target: <1s)
P95 Response Time (target: <3s)
Error Rate (target: <1%)
Tool Success Rate (target: >95%)
```

### Adoption Metrics

```
% Users Who Try Agent (target: 80%)
% Users Who Return to Agent (target: 60%)
% Users Who Master 5+ Tools (target: 40%)
Agent Usage vs Manual GUI Usage (target: 50/50)
```

---

## Questions for Stakeholders

### Product Questions

1. **Priority:** Which 10 tools should we build first?
2. **Scope:** Is voice interface in scope for 2026?
3. **Workflow:** What are the 5 most common user workflows we should optimize for?
4. **Philosophy:** How prominent should philosophical features be? (core vs optional)

### Technical Questions

1. **LLM:** Ollama (local) vs Claude API (cloud) as default?
2. **Deployment:** Self-hosted (Docker) vs Cloud (AWS/Cloudflare) first?
3. **Real-time:** WebSocket vs polling for notifications?
4. **Mobile:** Build mobile app or web-only?

### Resource Questions

1. **Team:** How many developers?
2. **Timeline:** Aggressive (4 months) vs Comfortable (8 months)?
3. **Budget:** What's the monthly cloud budget?
4. **Testing:** Manual QA or automated only?

---

## Next Steps

### Immediate (This Week)

1. **Review this architecture** - Team meeting
2. **Prioritize tools** - Create ranked list
3. **Setup tracking** - Jira/Linear board
4. **Assign Phase 1** - Who builds what?

### Short-term (Weeks 1-4)

1. **Implement top 10 tools**
2. **Build tutorial animation prototype**
3. **Create API client SDK**
4. **Write comprehensive tests**

### Medium-term (Months 2-4)

1. **Complete Priority 1 tools** (30 tools)
2. **Deploy to staging**
3. **Beta testing with users**
4. **Performance optimization**

### Long-term (Months 5-8)

1. **Complete Priority 2 tools** (15 tools)
2. **Build workflow automation**
3. **Launch voice interface**
4. **Production deployment**

---

## Summary

**What:** Comprehensive architecture for extending Humanizer Agent from 6 tools to 51 tools

**Why:** Give users full API access via natural language interface

**How:** Systematic rollout over 7 phases (32 weeks)

**Value:**
- 8.5x increase in AUI capabilities
- 80% API coverage (from 10%)
- Complete philosophical analysis tools
- Workspace automation
- Real-time notifications
- Voice interface

**Effort:**
- 45 new tools
- 25 new API endpoints
- 5 new database tables
- 15 new UI components
- ~32 weeks of development

**Risk Mitigation:**
- Phased rollout (incremental delivery)
- Comprehensive testing at each phase
- Performance monitoring throughout
- User feedback loops

**Success Criteria:**
- 80% of users try agent
- 60% return to agent regularly
- 40% master 5+ tools
- P95 response time <3s
- Tool success rate >95%

---

**All diagrams, code examples, and specifications are in:**

1. [API_ARCHITECTURE_DIAGRAMS.md](API_ARCHITECTURE_DIAGRAMS.md) - Part 1
2. [API_ARCHITECTURE_DIAGRAMS_PART2.md](API_ARCHITECTURE_DIAGRAMS_PART2.md) - Part 2
3. [API_DIAGRAMS_VISUAL_EXPORT.md](API_DIAGRAMS_VISUAL_EXPORT.md) - Part 3
4. **This file** - Summary & Quick Reference

---

*Last Updated: October 2025*
*Architecture Summary v1.0*
