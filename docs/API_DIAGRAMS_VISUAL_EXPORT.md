# API Diagrams: Visual Export
## PlantUML, SVG Instructions, and Implementation Examples

**Version:** 1.0
**Date:** October 2025
**Purpose:** Renderable diagrams for presentations and documentation

---

## Using These Diagrams

### PlantUML Diagrams

All PlantUML diagrams below can be:
1. **Copied to PlantUML.com** - Online editor
2. **Rendered in VS Code** - PlantUML extension
3. **Exported to PNG/SVG** - For presentations
4. **Embedded in Confluence/Notion** - Direct rendering

### Mermaid Diagrams

Mermaid diagrams (in Part 1 & 2) can be:
1. **Rendered in GitHub** - Native support
2. **Rendered in Notion** - `/code` → mermaid
3. **Converted to images** - mermaid.live
4. **Embedded in docs** - Most modern doc tools support

---

## PlantUML: System Architecture

```plantuml
@startuml Humanizer-Agent-Architecture
!define RECTANGLE class

skinparam backgroundColor #1e1e1e
skinparam componentStyle rectangle

skinparam component {
  BackgroundColor<<Frontend>> #3B82F6
  BorderColor<<Frontend>> #2563EB
  BackgroundColor<<Backend>> #10B981
  BorderColor<<Backend>> #059669
  BackgroundColor<<Database>> #EF4444
  BorderColor<<Database>> #DC2626
  BackgroundColor<<External>> #F59E0B
  BorderColor<<External>> #D97706
  BackgroundColor<<Agent>> #8B5CF6
  BorderColor<<Agent>> #7C3AED
}

package "Frontend Layer" <<Frontend>> {
  [React UI] as UI
  [Agent Chat] as AUI
  [Workspace Context] as WS
  [Tutorial Animator] as ANIM
}

package "API Gateway" <<Backend>> {
  [FastAPI Router] as ROUTER
  [Authentication] as AUTH
  [CORS Handler] as CORS
}

package "Agent Intelligence" <<Agent>> {
  [Agent Service] as AGENT
  [Tool Registry\n51 Tools] as TOOLS
  [LLM Provider] as LLM
}

package "Service Layer" <<Backend>> {
  [Library Service] as LIB
  [Embedding Service] as EMBED
  [Transformation Service] as TRANS
  [Book Service] as BOOK
  [Madhyamaka Service] as MADH
  [Vision Service] as VISION
  [Workspace Service] as WORK
  [Notification Service] as NOTIF
}

package "Data Layer" <<Database>> {
  database "PostgreSQL\n+pgvector" as PG
  database "Redis\nCache" as REDIS
  storage "File Storage" as FS
}

package "External Services" <<External>> {
  [Ollama\nLocal LLM] as OLLAMA
  [Claude API] as CLAUDE
  [Voyage API] as VOYAGE
}

UI --> ROUTER
AUI --> ROUTER
WS --> UI
ANIM --> AUI

ROUTER --> AUTH
AUTH --> CORS
CORS --> AGENT

AGENT --> TOOLS
AGENT --> LLM
TOOLS --> LIB
TOOLS --> EMBED
TOOLS --> TRANS
TOOLS --> BOOK
TOOLS --> MADH
TOOLS --> VISION
TOOLS --> WORK
TOOLS --> NOTIF

LLM --> OLLAMA
LLM --> CLAUDE
EMBED --> VOYAGE
TRANS --> CLAUDE
MADH --> CLAUDE
VISION --> CLAUDE

LIB --> PG
EMBED --> PG
EMBED --> REDIS
TRANS --> PG
BOOK --> PG
MADH --> PG
VISION --> PG
VISION --> FS
WORK --> PG
NOTIF --> PG
NOTIF --> REDIS

@enduml
```

**To Render:**
1. Copy the code above
2. Go to https://www.plantuml.com/plantuml/uml/
3. Paste and click "Submit"
4. Download as PNG or SVG

---

## PlantUML: Agent Tool Execution Sequence

```plantuml
@startuml Agent-Tool-Execution
!theme plain

actor User
participant "Agent UI" as UI
participant "Agent Service" as Agent
participant "Tool Registry" as Tools
participant "LLM" as LLM
participant "API Endpoint" as API
database "PostgreSQL" as DB

User -> UI: Types "Find chunks\nabout Buddhism"
activate UI

UI -> Agent: POST /api/agent/chat
activate Agent

Agent -> DB: Load conversation
activate DB
DB --> Agent: History
deactivate DB

Agent -> LLM: Message +\nTool definitions
activate LLM
LLM --> Agent: Tool call:\nsearch_embeddings
deactivate LLM

Agent -> Tools: Get tool spec
activate Tools
Tools --> Agent: Tool definition
deactivate Tools

Agent -> API: GET /api/library/chunks?\nsearch=Buddhism
activate API

API -> DB: Vector similarity\nsearch
activate DB
DB --> API: 4,449 chunks
deactivate DB

API --> Agent: Results
deactivate API

Agent -> DB: Save conversation
activate DB
DB --> Agent: Saved
deactivate DB

Agent --> UI: Response:\n"Found 4,449 chunks"\n+\nGUI action:\nOpen ChunkBrowser
deactivate Agent

UI -> UI: Display message
UI -> UI: Open ChunkBrowser tab

opt Tutorial Mode Enabled
  UI -> UI: Animate manual workflow:\n1. Highlight Chunks menu\n2. Click\n3. Search box\n4. Type "Buddhism"\n5. Filter\n6. Search button
end

UI --> User: Shows results
deactivate UI

@enduml
```

---

## PlantUML: Tool Organization & Dependencies

```plantuml
@startuml Tool-Organization
!theme plain

skinparam packageStyle rectangle
skinparam backgroundColor #1e1e1e

package "Foundation Tools (6)" <<Foundation>> #10B981 {
  [search_conversations]
  [search_embeddings]
  [cluster_embeddings]
  [create_book]
  [add_content_to_book]
  [open_gui_component]
}

package "Book Management (8)" <<Books>> #3B82F6 {
  [list_books]
  [get_book]
  [update_book]
  [delete_book]
  [create_book_section]
  [update_book_section]
  [delete_book_section]
  [export_book]
}

package "Transformation (6)" <<Transform>> #EF4444 {
  [transform_chunk]
  [list_transformations]
  [get_transformation]
  [reapply_transformation]
  [get_transformation_lineage]
  [batch_transform]
}

package "Philosophy (7)" <<Philosophy>> #F59E0B {
  [detect_madhyamaka]
  [analyze_philosophy]
  [generate_perspectives]
  [start_contemplation]
  [list_contemplation_exercises]
  [map_beliefs]
  [socratic_dialogue]
}

package "Intelligence (5)" <<Intelligence>> #8B5CF6 {
  [find_related_conversations]
  [get_conversation_timeline]
  [trace_conversation_thread]
  [summarize_conversation]
  [extract_insights]
}

package "Framework Evolution (3)" <<Evolution>> #06B6D4 {
  [track_framework_evolution]
  [compare_frameworks]
  [detect_framework_shift]
}

package "Workspace (4)" <<Workspace>> #84CC16 {
  [save_workspace]
  [load_workspace]
  [list_workspaces]
  [create_workspace_preset]
}

' Dependencies
[search_embeddings] --> [find_related_conversations]
[search_embeddings] --> [summarize_conversation]
[cluster_embeddings] --> [track_framework_evolution]
[cluster_embeddings] --> [compare_frameworks]
[create_book] --> [list_books]
[create_book] --> [get_book]
[add_content_to_book] --> [create_book_section]
[transform_chunk] --> [list_transformations]
[transform_chunk] --> [batch_transform]

@enduml
```

---

## PlantUML: Database Schema (New Tables)

```plantuml
@startuml Database-Schema-Extensions
!theme plain

entity "workspaces" {
  * id : UUID <<PK>>
  --
  * user_id : UUID <<FK>>
  * name : VARCHAR(200)
  description : TEXT
  * state : JSONB
  is_preset : BOOLEAN
  created_at : TIMESTAMPTZ
  updated_at : TIMESTAMPTZ
  --
  UNIQUE(user_id, name)
}

entity "notifications" {
  * id : UUID <<PK>>
  --
  * user_id : UUID <<FK>>
  * type : VARCHAR(50)
  * title : VARCHAR(200)
  * message : TEXT
  data : JSONB
  is_read : BOOLEAN
  created_at : TIMESTAMPTZ
  expires_at : TIMESTAMPTZ
}

entity "workflows" {
  * id : UUID <<PK>>
  --
  * user_id : UUID <<FK>>
  * name : VARCHAR(200)
  description : TEXT
  * trigger : JSONB
  * actions : JSONB
  enabled : BOOLEAN
  last_run_at : TIMESTAMPTZ
  created_at : TIMESTAMPTZ
  updated_at : TIMESTAMPTZ
}

entity "workflow_executions" {
  * id : UUID <<PK>>
  --
  * workflow_id : UUID <<FK>>
  * status : VARCHAR(20)
  trigger_data : JSONB
  result : JSONB
  error : TEXT
  started_at : TIMESTAMPTZ
  completed_at : TIMESTAMPTZ
}

entity "framework_snapshots" {
  * id : UUID <<PK>>
  --
  * framework_id : VARCHAR(100)
  * snapshot_date : DATE
  * cluster_data : JSONB
  top_chunks : JSONB
  created_at : TIMESTAMPTZ
  --
  UNIQUE(framework_id, snapshot_date)
}

entity "related_content_cache" {
  * id : UUID <<PK>>
  --
  * source_id : UUID
  * source_type : VARCHAR(50)
  * related_items : JSONB
  computed_at : TIMESTAMPTZ
  expires_at : TIMESTAMPTZ
  --
  UNIQUE(source_id, source_type)
}

entity "users" {
  * id : UUID <<PK>>
  --
  ...existing fields...
}

users ||--o{ workspaces
users ||--o{ notifications
users ||--o{ workflows
workflows ||--o{ workflow_executions

@enduml
```

---

## Implementation Examples

### Example 1: Implementing a New Tool

```python
# backend/services/agent_service.py

# 1. Add tool definition to TOOLS array
TOOLS.append({
    "name": "list_books",
    "description": "List all books for the user, optionally filtered by type",
    "endpoint": {
        "method": "GET",
        "path": "/api/books",
        "base_url": "http://localhost:8000"
    },
    "parameters": {
        "book_type": {
            "type": "string",
            "description": "Filter by type: 'paper', 'book', 'article', 'report'",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of books to return",
            "required": False,
            "default": 50
        }
    },
    "gui_component": "BookLibrary"
})

# 2. The execute_tool method automatically handles it!
# No additional code needed - it uses the endpoint definition

# 3. Optional: Add custom formatting in _format_tool_result()
def _format_tool_result(self, tool_name, parameters, result_data, thought):
    if tool_name == "list_books":
        books = result_data if isinstance(result_data, list) else []
        return f"Found {len(books)} books. Opening Book Library..."

    # ... existing formatting
```

### Example 2: Adding GUI Action Handler

```javascript
// frontend/src/hooks/useAgentChat.js

const handleGuiAction = useCallback((guiAction) => {
  const { action, params } = guiAction;

  switch (action) {
    // ... existing cases

    case 'open_book_library':
      addTab('bookLibrary', '📚 Book Library', {
        filters: params?.filters
      });
      break;

    case 'open_framework_comparison':
      addTab('frameworkComparison', '⚖️ Compare Frameworks', {
        framework1: params?.framework_id_1,
        framework2: params?.framework_id_2
      });
      break;

    // ... more cases
  }
}, [addTab]);
```

### Example 3: Creating New API Endpoint

```python
# backend/api/library_routes.py (or new file)

@router.post("/collections/{conversation_id}/related")
async def find_related_conversations(
    conversation_id: str,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Find conversations related to this one via semantic similarity.

    Uses embedding similarity to find related content.
    """
    try:
        conv_uuid = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    # 1. Get conversation's chunks
    result = await db.execute(
        select(Message.chunks)
        .join(Collection)
        .where(Collection.id == conv_uuid)
    )
    messages = result.scalars().all()

    # 2. Get embeddings for these chunks
    chunk_ids = []
    for message in messages:
        chunk_ids.extend([c.id for c in message.chunks])

    # 3. Find similar chunks from OTHER conversations
    result = await db.execute(
        select(
            Chunk,
            func.avg(1 - (Embedding.embedding.cosine_distance(query_embedding))).label('similarity')
        )
        .join(Embedding)
        .join(Message)
        .join(Collection)
        .where(
            Chunk.id.in_(chunk_ids),
            Collection.id != conv_uuid
        )
        .group_by(Collection.id)
        .order_by(desc('similarity'))
        .limit(limit)
    )

    related = result.all()

    return [
        {
            "conversation_id": str(conv.id),
            "title": conv.title,
            "similarity": float(similarity),
            "created_at": conv.created_at.isoformat()
        }
        for conv, similarity in related
    ]
```

### Example 4: Tutorial Animation Component

```javascript
// frontend/src/components/TutorialAnimator.jsx

import React, { useState, useEffect } from 'react';

export function TutorialAnimator({ toolName, parameters, onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);

  const animations = getAnimationSteps(toolName, parameters);

  useEffect(() => {
    if (!isPlaying) return;

    const step = animations[currentStep];
    if (!step) {
      onComplete();
      return;
    }

    // Execute animation step
    executeStep(step);

    // Move to next step after duration
    const timer = setTimeout(() => {
      setCurrentStep(prev => prev + 1);
    }, step.duration);

    return () => clearTimeout(timer);
  }, [currentStep, isPlaying]);

  const executeStep = (step) => {
    switch (step.type) {
      case 'highlight':
        highlightElement(step.selector, step.caption);
        break;
      case 'click':
        animateClick(step.selector);
        break;
      case 'type':
        animateTyping(step.selector, step.text);
        break;
      case 'open':
        animateTabOpen(step.tabType, step.title);
        break;
    }
  };

  const highlightElement = (selector, caption) => {
    const element = document.querySelector(selector);
    if (!element) return;

    // Add glow effect
    element.classList.add('tutorial-highlight');

    // Show caption
    showCaption(caption, element);

    // Remove after duration
    setTimeout(() => {
      element.classList.remove('tutorial-highlight');
      hideCaption();
    }, 1000);
  };

  const animateClick = (selector) => {
    const element = document.querySelector(selector);
    if (!element) return;

    // Add ripple effect
    element.classList.add('tutorial-click');

    setTimeout(() => {
      element.classList.remove('tutorial-click');
    }, 500);
  };

  const animateTyping = async (selector, text) => {
    const input = document.querySelector(selector);
    if (!input) return;

    input.value = '';
    input.focus();

    for (const char of text) {
      input.value += char;
      await wait(100); // 100ms per character
    }
  };

  return (
    <div className="tutorial-overlay">
      <div className="tutorial-controls">
        <button onClick={() => setIsPlaying(!isPlaying)}>
          {isPlaying ? '⏸️ Pause' : '▶️ Play'}
        </button>
        <button onClick={() => setCurrentStep(0)}>
          🔄 Replay
        </button>
        <button onClick={onComplete}>
          ⏭️ Skip
        </button>
        <span>Step {currentStep + 1} / {animations.length}</span>
      </div>
    </div>
  );
}

function getAnimationSteps(toolName, parameters) {
  const animations = {
    'search_embeddings': [
      {
        type: 'highlight',
        selector: '[data-menu="chunks"]',
        caption: 'First, I open the Chunks browser',
        duration: 1000
      },
      {
        type: 'click',
        selector: '[data-menu="chunks"]',
        duration: 500
      },
      {
        type: 'open',
        tabType: 'chunks',
        title: '🧩 Chunks',
        duration: 500
      },
      {
        type: 'highlight',
        selector: '[data-search-input]',
        caption: 'Then I enter the search term',
        duration: 1000
      },
      {
        type: 'type',
        selector: '[data-search-input]',
        text: parameters.search,
        duration: 1500
      },
      {
        type: 'highlight',
        selector: '[data-filter-embedding]',
        caption: 'I filter to chunks with embeddings',
        duration: 1000
      },
      {
        type: 'click',
        selector: '[data-filter-embedding]',
        duration: 500
      },
      {
        type: 'highlight',
        selector: '[data-search-button]',
        caption: 'Finally, I search',
        duration: 800
      },
      {
        type: 'click',
        selector: '[data-search-button]',
        duration: 500
      }
    ],
    // ... more tool animations
  };

  return animations[toolName] || [];
}
```

---

## SVG Export Instructions

### For PowerPoint/Keynote Presentations

1. **Render Mermaid to SVG:**
   ```bash
   # Install mermaid CLI
   npm install -g @mermaid-js/mermaid-cli

   # Convert diagram
   mmdc -i diagram.mmd -o diagram.svg
   ```

2. **Insert in PowerPoint:**
   - Insert → Pictures → Select SVG file
   - SVG graphics remain sharp at any zoom level

3. **Edit in PowerPoint:**
   - Right-click SVG → Convert to Shape
   - Now editable as native PowerPoint shapes

### For Documentation (Markdown)

```markdown
# In GitHub/GitLab (native Mermaid support)
```mermaid
graph TD
  A[Start] --> B[End]
```

# In other platforms, use image
![Architecture Diagram](./diagrams/architecture.svg)
```

### For Confluence

1. **PlantUML Macro:**
   - Install PlantUML plugin
   - Use `/plantuml` macro
   - Paste PlantUML code directly

2. **Mermaid Macro:**
   - Install Mermaid plugin
   - Use `/mermaid` macro
   - Paste Mermaid code directly

---

## Tool Implementation Checklist

When adding a new tool, follow this checklist:

### Backend (agent_service.py)

- [ ] Add tool definition to `TOOLS` array
- [ ] Define endpoint (method, path, base_url)
- [ ] Define parameters with types and descriptions
- [ ] Specify GUI component (if any)
- [ ] Add custom formatting in `_format_tool_result()` (optional)
- [ ] Write tests in `test_agent.py`

### API Endpoint (if new)

- [ ] Create endpoint in appropriate router file
- [ ] Add request/response models (Pydantic)
- [ ] Implement endpoint logic
- [ ] Add error handling
- [ ] Write API tests
- [ ] Update API documentation

### Frontend (useAgentChat.js)

- [ ] Add GUI action handler in `handleGuiAction()`
- [ ] Map action to tab type
- [ ] Pass parameters to component

### Frontend Component (if new)

- [ ] Create component file
- [ ] Implement component logic
- [ ] Add data fetching
- [ ] Add to Workstation tab types
- [ ] Write component tests

### Tutorial Animation (if priority tool)

- [ ] Add animation steps in `getAnimationSteps()`
- [ ] Define highlight selectors
- [ ] Write step captions
- [ ] Set step durations
- [ ] Test animation flow

### Documentation

- [ ] Update tool list in documentation
- [ ] Add API endpoint to specs
- [ ] Create usage examples
- [ ] Update diagrams

---

## Performance Testing

### Load Testing Script

```python
# test_load.py
import asyncio
import time
from agent_service import AgentService

async def test_concurrent_requests(num_requests=100):
    """Test agent can handle concurrent requests"""
    agent = AgentService(model_name="mistral:7b")

    start = time.time()

    tasks = [
        agent.process_message(
            f"Find chunks about test-{i}",
            []
        )
        for i in range(num_requests)
    ]

    results = await asyncio.gather(*tasks)

    duration = time.time() - start

    print(f"Completed {num_requests} requests in {duration:.2f}s")
    print(f"Average: {duration/num_requests:.2f}s per request")
    print(f"Throughput: {num_requests/duration:.2f} requests/sec")

    # All should succeed
    assert all(r["type"] in ["tool_call", "response"] for r in results)

asyncio.run(test_concurrent_requests())
```

---

## Deployment Considerations

### Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/humanizer
      - REDIS_URL=redis://redis:6379
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - redis
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend

  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: humanizer
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama

  worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - redis
      - postgres

volumes:
  pgdata:
  redis_data:
  ollama_data:
```

---

## Summary

### What We've Provided

1. **Complete Architecture Diagrams**
   - System overview
   - Data flow
   - Tool organization
   - Database schema

2. **51 Tool Definitions**
   - 6 existing (current)
   - 30 API coverage (Priority 1)
   - 15 high-value new (Priority 2)
   - Detailed specifications for each

3. **25 New API Endpoints**
   - Related content
   - Timeline & evolution
   - Workspace management
   - Batch operations
   - Notifications

4. **Implementation Guides**
   - Adding new tools
   - Creating API endpoints
   - Building UI components
   - Tutorial animations

5. **Testing Strategies**
   - Unit tests
   - Integration tests
   - Load tests
   - E2E tests

6. **Deployment Configs**
   - Docker Compose
   - Database migrations
   - Performance optimization

### Next Actions

1. **Review & Prioritize**
   - Which 10 tools to build first?
   - Which APIs are most critical?

2. **Prototype**
   - Build top 3 tools
   - Test animation system
   - Validate architecture

3. **Plan Sprints**
   - 2-week sprints
   - 3-5 tools per sprint
   - Incremental delivery

4. **Document**
   - API docs for each endpoint
   - Tool usage examples
   - Animation scripts

---

**Ready to implement!**

All diagrams can be rendered in:
- PlantUML.com (online)
- VS Code (with extensions)
- GitHub/GitLab (native Mermaid)
- Confluence (with plugins)
- PowerPoint/Keynote (as SVG)

---

*Last Updated: October 2025*
*Visual Export Guide*
