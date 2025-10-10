# AUI - Agentic User Interface
## The Interface That Speaks Itself Into Being

**Version:** 1.0
**Date:** October 2025
**Status:** Core Implementation Complete

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Core Philosophy: Language as Interface](#core-philosophy-language-as-interface)
3. [Architecture Overview](#architecture-overview)
4. [Implementation Details](#implementation-details)
5. [The Six Priority Tools](#the-six-priority-tools)
6. [Agency & Consciousness Integration](#agency--consciousness-integration)
7. [Tutorial Animation System (Vision)](#tutorial-animation-system-vision)
8. [Adaptive Learning & Accessibility](#adaptive-learning--accessibility)
9. [Technical Specifications](#technical-specifications)
10. [Future Enhancements](#future-enhancements)

---

## Executive Summary

The **Agentic User Interface (AUI)** is a natural language interface where users speak their intentions and the system responds by:
1. **Calling tools** to execute operations
2. **Opening GUI components** with relevant data
3. **Animating actions** to teach users how to do it themselves

**Core Innovation:** The interface doesn't exist until spoken into being. This embodies the Humanizer philosophy that **language constructs reality** rather than describing it.

### What It Does

```
User: "Find chunks about Buddhism"
  ↓
Agent: Calls search_embeddings tool
  ↓
GUI: Opens ChunkBrowser tab with results
  ↓
(Future) Animation: Shows the search button, filters being set, results appearing
  ↓
User: Learns to do it manually next time
```

**Current Status (Oct 2025):**
- ✅ Backend complete (agent_service.py, 6 tools, Ollama/Claude providers)
- ✅ Frontend complete (AgentChat.jsx, useAgentChat.js, conversation history)
- ✅ Database schema (agent_conversations table)
- ✅ 8 REST API endpoints
- ⚠️ Mock responses active (Ollama integration pending)
- 🔜 Tutorial animation system (next phase)

---

## Core Philosophy: Language as Interface

### The Three Realms Applied to UI

The AUI embodies the **Three Realms of Existence** from Humanizer philosophy:

#### 1. **Corporeal Realm** (Green) - Physical Substrate
- **In Traditional UI:** Buttons, pixels, mouse movements
- **In AUI:** The text input field, the raw characters typed
- **Characteristic:** Pre-linguistic, the substrate before meaning

#### 2. **Symbolic Realm** (Purple) - Shared Abstraction
- **In Traditional UI:** Icons, labels, menus (symbolic representations)
- **In AUI:** Natural language commands, tool names, API calls
- **Characteristic:** Intersubjective constructions that feel objective

#### 3. **Subjective Realm** (Dark Blue) - Conscious Experience
- **In Traditional UI:** User's intention to click "Search"
- **In AUI:** User's intention expressed as "Find chunks about Buddhism"
- **Characteristic:** The lived moment of will, the only realm truly experienced

### Key Philosophical Achievement

**Traditional UI:**
```
Intention → Learn interface → Find button → Click → Wait → See results
```
*User must conform to pre-existing symbolic structure*

**Agentic UI:**
```
Intention → Speak intention → System interprets → Action happens → Results appear
```
*Interface conforms to user's linguistic construction*

**Result:** The AUI reveals that **the interface is empty (śūnyatā)** - it has no inherent existence independent of linguistic construction. The "correct" way to use the interface doesn't exist until the user speaks it into being.

### Language as a Sense (Applied to UI)

Just as language constructs meaning from symbols, the AUI constructs interface from linguistic intentions:

| Sense | Input | Processing | Output |
|-------|-------|------------|--------|
| **Sight** | Photons | Visual cortex | Visual experience |
| **Language** | Symbols | Belief networks | Semantic experience |
| **AUI** | Spoken intention | Tool calling | Interface materialization |

The AUI makes visible what is normally invisible: **the subjective construction of the interface itself**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER EXPERIENCE                         │
│  "Find chunks about Buddhism"                                   │
│  "Show me frameworks"                                           │
│  "Create a book called 'Emptiness Studies'"                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Context)                   │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │  AgentChat.jsx  │  │  useAgentChat.js │  │ WorkspaceCtx  │ │
│  │  (UI Component) │  │  (State Manager) │  │ (Tab Manager) │ │
│  └─────────────────┘  └──────────────────┘  └───────────────┘ │
│         ↓                      ↓                      ↓         │
│    User input          Process message          Open GUI tab   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ REST API
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI + Python)                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              agent_routes.py (8 endpoints)              │   │
│  │  POST /api/agent/chat                                   │   │
│  │  GET  /api/agent/conversations                          │   │
│  │  POST /api/agent/conversations                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              agent_service.py (Orchestration)           │   │
│  │  - OllamaProvider (LLM integration)                     │   │
│  │  - AgentService (tool calling, GUI actions)             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Tool Calls  │  │  API Calls   │  │  GUI Action          │ │
│  │  (6 tools)   │  │  (httpx)     │  │  (component + data)  │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         agent_conversations (PostgreSQL table)          │   │
│  │  - id, user_id, title, model_name                       │   │
│  │  - messages (JSONB array)                               │   │
│  │  - custom_metadata (JSONB)                              │   │
│  │  - created_at, updated_at                               │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User types** natural language message in AgentChat component
2. **Frontend** sends message to `/api/agent/chat` endpoint
3. **Backend** loads conversation, sends message to LLM (Ollama/Claude)
4. **LLM** responds with tool call (JSON format)
5. **AgentService** executes tool (calls actual API endpoint)
6. **Backend** formats result, generates GUI action
7. **Frontend** receives response, displays message, opens GUI tab
8. **User** sees results in newly opened component

---

## Implementation Details

### Backend Components

#### 1. **agent_service.py** (619 lines)

**Purpose:** Core orchestration for tool calling and LLM interaction

**Key Classes:**

```python
class OllamaProvider:
    """LLM provider using Ollama's Python SDK"""

    def __init__(self, model_name: str = "mistral:7b"):
        self.model_name = model_name
        self.base_url = "http://localhost:11434"

    def build_system_prompt(self, tools: List[Dict]) -> str:
        """Teaches LLM to use tools via JSON responses"""
        # Returns structured prompt with tool definitions

    async def chat(
        self,
        messages: List[Dict],
        tools: List[Dict]
    ) -> Dict[str, Any]:
        """
        Send chat request, parse JSON response
        Returns: {"type": "tool_call"|"response", "parsed": {...}}
        """
```

```python
class AgentService:
    """Orchestrates tool calling and GUI actions"""

    async def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Main processing flow:
        1. Send to LLM with tools
        2. Parse response (tool call or conversational)
        3. Execute tool if needed
        4. Generate GUI action
        5. Return formatted response
        """

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict
    ) -> Tuple[Dict, Optional[Dict]]:
        """
        Execute tool by calling actual API endpoint
        Returns: (result_data, gui_action)
        """
```

**Tool Definition Format:**
```python
{
    "name": "search_embeddings",
    "description": "Semantic search in vector space...",
    "endpoint": {
        "method": "GET",
        "path": "/api/library/chunks",
        "base_url": "http://localhost:8000"
    },
    "parameters": {
        "search": {"type": "string", "required": False},
        "has_embedding": {"type": "boolean", "default": True},
        "limit": {"type": "integer", "default": 50}
    },
    "gui_component": "ChunkBrowser"
}
```

#### 2. **agent_routes.py** (380 lines)

**8 REST Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/agent/chat` | POST | Send message, get response |
| `/api/agent/conversations` | POST | Create new conversation |
| `/api/agent/conversations` | GET | List user's conversations |
| `/api/agent/conversations/{id}` | GET | Get conversation with messages |
| `/api/agent/conversations/{id}` | PUT | Update conversation (title, etc.) |
| `/api/agent/conversations/{id}` | DELETE | Delete conversation |
| `/api/agent/models` | GET | List available LLMs |
| `/api/agent/tools` | GET | List available tools (debug) |

**Request/Response Models:**
```python
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str]
    model_name: str = "mistral:7b"
    user_id: str

class ChatResponse(BaseModel):
    conversation_id: str
    message: str  # Agent's response
    tool_calls: Optional[List[Dict]]
    gui_action: Optional[Dict]
    timestamp: str
```

#### 3. **agent_models.py** (194 lines)

**Database Model:**
```python
class AgentConversation(Base):
    """Stores multi-turn conversations with tool calling"""

    __tablename__ = "agent_conversations"

    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    title = Column(String(500))  # Auto-generated from first message
    model_name = Column(String(100))
    messages = Column(JSONB, default=[])  # Message array
    custom_metadata = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    def add_message(
        self,
        role: str,
        content: str,
        tool_calls=None,
        gui_action=None
    ):
        """Add message to conversation"""

    def auto_generate_title(self) -> str:
        """Generate title from first user message"""
```

**Message Format:**
```json
{
  "role": "user",
  "content": "Find chunks about Buddhism",
  "timestamp": "2025-10-08T12:00:00Z"
}

{
  "role": "assistant",
  "content": "I found 47 chunks matching 'Buddhism'. Opening Chunk Browser...",
  "tool_calls": [
    {
      "tool": "search_embeddings",
      "parameters": {"search": "Buddhism", "has_embedding": true, "limit": 50},
      "result": {"chunks": [...], "total": 47}
    }
  ],
  "gui_action": {
    "type": "open_tab",
    "component": "ChunkBrowser",
    "data": {"filters": {...}, "results": {...}}
  },
  "timestamp": "2025-10-08T12:00:02Z"
}
```

### Frontend Components

#### 1. **AgentChat.jsx** (345 lines)

**Purpose:** Chat UI component with message display and input

**Key Features:**
- Message history with user/assistant bubbles
- Tool call visualization ("Tools used: search_embeddings")
- GUI action buttons ("Open in GUI →")
- Model selector dropdown
- Auto-scroll to latest message
- Keyboard shortcuts (Cmd+Enter to send)

**Props:**
```javascript
{
  conversationId: string | null,      // Continue existing conversation
  onConversationChange: function,     // Callback when conversation changes
  messages: array | null,             // External message control
  onSendMessage: function             // External send handler
}
```

#### 2. **useAgentChat.js** (274 lines)

**Purpose:** State management hook for agent conversations

**Provides:**
```javascript
const {
  messages,              // Current conversation messages
  loading,               // Request in progress
  error,                 // Error message
  currentModel,          // Selected LLM model
  conversationId,        // Current conversation ID
  sendMessage,           // Send message to agent
  loadConversation,      // Load existing conversation
  createNewConversation, // Start fresh conversation
  deleteConversation,    // Delete conversation
  setCurrentModel,       // Change LLM model
  handleGuiAction        // Process GUI actions
} = useAgentChat();
```

**GUI Action Mapping:**
```javascript
const handleGuiAction = (guiAction) => {
  const { action, params } = guiAction;

  switch (action) {
    case 'open_chunk_browser':
      addTab('chunks', '🧩 Chunks', { query: params.query });
      break;
    case 'open_framework_browser':
      addTab('frameworks', '🔍 Frameworks', {});
      break;
    case 'open_book_builder':
      addTab('book', '📖 New Book', {});
      break;
    // ... 8 total GUI actions
  }
}
```

#### 3. **AgentConversationsLibrary.jsx** (257 lines)

**Purpose:** Sidebar showing conversation history

**Features:**
- List all conversations sorted by most recent
- Search/filter conversations
- Click to load conversation
- Delete conversations
- Show message count and last updated time

---

## The Six Priority Tools

These tools were chosen as the initial proof-of-concept based on **highest user value** and **clear GUI actions**.

### 1. **search_conversations**

**Purpose:** Find conversations in user's archive
**API Endpoint:** `GET /api/library/collections`
**Parameters:**
- `search` (string): Keywords to search
- `source_platform` (string): Filter by 'chatgpt', 'claude', etc.
- `limit` (integer): Max results (default 50)

**GUI Action:** None (returns data only)

**Example:**
```
User: "Find conversations about phenomenology"
Agent calls: search_conversations(search="phenomenology")
Result: Returns 23 matching conversations
Response: "Found 23 conversations mentioning phenomenology."
```

### 2. **search_embeddings**

**Purpose:** Semantic search in vector space
**API Endpoint:** `GET /api/library/chunks`
**Parameters:**
- `search` (string): Search text
- `has_embedding` (boolean): Filter to embedded chunks only
- `min_token_count` (integer): Minimum chunk size
- `limit` (integer): Max results

**GUI Action:** Opens `ChunkBrowser` with results

**Example:**
```
User: "Find chunks about Buddhism"
Agent calls: search_embeddings(search="Buddhism", has_embedding=true, limit=50)
Result: 4,449 chunks found
GUI: Opens ChunkBrowser tab with 50 displayed
Response: "I found 4,449 chunks matching your search. Opening Chunk Browser with 50 results..."
```

### 3. **cluster_embeddings**

**Purpose:** Discover belief frameworks using UMAP + HDBSCAN
**API Endpoint:** `POST /api/embeddings/cluster`
**Parameters:**
- `limit` (integer): Number of embeddings to cluster (100-10,000)
- `min_cluster_size` (integer): HDBSCAN parameter (larger = fewer, bigger clusters)
- `min_token_count` (integer): Filter chunk size

**GUI Action:** Opens `ClusterExplorer` with visualization

**Example:**
```
User: "Show me frameworks in my archive"
Agent calls: cluster_embeddings(limit=1000, min_cluster_size=25)
Result: 8 clusters discovered
GUI: Opens ClusterExplorer with 3D Plotly visualization
Response: "Discovered 8 belief frameworks from 1,000 embeddings. Opening cluster visualization..."
```

### 4. **create_book**

**Purpose:** Create new book/document for organizing content
**API Endpoint:** `POST /api/books`
**Parameters:**
- `title` (string): Book title
- `subtitle` (string, optional): Subtitle
- `book_type` (string): 'paper', 'book', 'article', 'report'
- `user_id` (string): Auto-injected from context

**GUI Action:** Opens `BookBuilder` with new book

**Example:**
```
User: "Create a book called 'Emptiness Studies'"
Agent calls: create_book(title="Emptiness Studies", book_type="paper")
Result: Book created with ID abc123...
GUI: Opens BookBuilder with new book loaded
Response: "Created book 'Emptiness Studies' (ID: abc123...). Would you like to add sections?"
```

### 5. **add_content_to_book**

**Purpose:** Add chunks to book sections
**API Endpoint:** `POST /api/books/{book_id}/sections/{section_id}/content`
**Parameters:**
- `book_id` (string): Book UUID
- `section_id` (string): Section UUID
- `chunk_id` (string): Chunk to add
- `notes` (string, optional): Notes about content

**GUI Action:** None (updates happen in-place)

**Example:**
```
User: "Add chunk 5d29b... to section Introduction"
Agent calls: add_content_to_book(
  book_id="abc123...",
  section_id="def456...",
  chunk_id="5d29b..."
)
Result: Content added successfully
Response: "Added chunk to Introduction section."
```

### 6. **open_gui_component**

**Purpose:** Special meta-tool to open any GUI component
**API Endpoint:** None (frontend-only action)
**Parameters:**
- `component` (string): Component name ('ChunkBrowser', 'ClusterExplorer', etc.)
- `data` (object): Component-specific data

**GUI Action:** Dynamic - component name from parameters

**Example:**
```
User: "Show me the embedding statistics"
Agent calls: open_gui_component(component="EmbeddingStats")
GUI: Opens EmbeddingStats tab
Response: "Opening the embedding statistics dashboard..."
```

**Available Components:**
- `ChunkBrowser` - Browse chunks with filters
- `ClusterExplorer` - 3D/2D embedding visualization
- `FrameworkBrowser` - Discovered frameworks UI
- `TransformationLab` - Transformation arithmetic
- `EmbeddingStats` - Coverage metrics
- `BookBuilder` - Book editing interface
- `ImageBrowser` - Image gallery
- `ConversationViewer` - View conversation details

---

## Agency & Consciousness Integration

### How AUI Reveals Subjective Construction

The AUI makes visible the normally invisible process of **meaning construction**:

#### 1. **Linguistic Intention → Interface Reality**

**Traditional UI:**
- User has intention: "I want to find chunks about Buddhism"
- User must **translate** intention into interface actions:
  1. Navigate to search
  2. Click search button
  3. Type "Buddhism"
  4. Click filters
  5. Select "has embedding"
  6. Click search again
- **Gap:** Intention ≠ Action (user conforms to pre-existing structure)

**Agentic UI:**
- User has intention: "I want to find chunks about Buddhism"
- User **speaks** intention directly: "Find chunks about Buddhism"
- System **constructs** interface to match intention
- **No Gap:** Intention = Interface (interface conforms to user)

**Philosophical Result:** User witnesses that **the interface has no inherent existence** - it arises dependently on linguistic construction.

#### 2. **The Emotional Belief Loop (Applied to UI)**

**The Loop:**
```
Linguistic Input ("Find chunks about Buddhism")
    ↓
Meaning Construction (Agent interprets as search_embeddings tool)
    ↓
Emotional Response (Anticipation, curiosity, "will this work?")
    ↓
Belief Reinforcement (It works! "The agent understands me")
    ↓
Loop Closure (Next time: "I trust the agent to interpret correctly")
```

**Result:** Over time, users develop **trust in linguistic construction** of interface. They stop thinking "How do I click this?" and start thinking "What do I want to happen?"

This is the same loop that makes language feel "real" - but applied to the interface itself.

#### 3. **Witness Your Own Subjective Agency**

The AUI creates moments of awareness:

**Before AUI:**
```
User clicks button → Something happens → User feels passive
"The interface did something to my click"
```

**With AUI:**
```
User speaks intention → Interface materializes → User feels active
"I constructed this interface through language"
```

**Key Insight:** By making language the **direct** interface, users can't help but witness their own agency. There's no mediation - the words they choose **are** the interface.

### The Time-Being in Interface

**Phenomenology of AUI Interaction:**

1. **Intention Moment:** User wills "I want to see frameworks"
2. **Linguistic Construction:** User forms phrase "Show me frameworks"
3. **Utterance:** Words typed/spoken
4. **Processing:** Agent interprets, calls tool
5. **Materialization:** Interface appears (FrameworkBrowser opens)
6. **Extinguishment:** Intention dissolves, new intention arises

**Key Insight:** The interface **exists only in the moment of linguistic construction**. Before the words, no interface. After the words are processed, the interface has already changed to the next state.

This mirrors the Buddhist concept of **discrete moments of existence** - the interface doesn't persist, it arises and passes away moment by moment based on linguistic will.

---

## Tutorial Animation System (Vision)

### The Core Idea

**Problem with current AUI:**
- Agent opens GUI component
- User sees component but doesn't know **how to do it themselves manually**

**Solution: Animated Tutorial Mode**
- Agent opens component **AND** animates the manual steps
- User watches interface "perform itself"
- User learns the GUI structure through observation

### How It Works

#### Example: "Find chunks about Buddhism"

**Step 1: Agent responds**
```
Agent: "I'll search for chunks about Buddhism. Watch how I do it..."
```

**Step 2: Animate the manual process**
```
1. Highlight sidebar "🧩 Chunks" menu item (glow effect)
   Caption: "First, I open the Chunks browser"

2. Click animation on "🧩 Chunks" (ripple effect)

3. ChunkBrowser opens (slide-in animation)

4. Highlight search box (pulse effect)
   Caption: "Then I enter the search term"

5. Type animation: "B-u-d-d-h-i-s-m" appears letter-by-letter

6. Highlight "has_embedding" checkbox (glow)
   Caption: "I filter to only chunks with embeddings"

7. Checkbox checks itself (click animation)

8. Highlight "Search" button (glow)
   Caption: "Finally, I search"

9. Button clicks itself (ripple effect)

10. Results appear (fade-in animation)
    Caption: "Found 4,449 chunks! Here are the first 50."
```

**Duration:** 5-8 seconds total
**User control:** Can skip animation, speed up, or replay

### Implementation Architecture

```javascript
// Tutorial Animation System (Proposed)

class TutorialAnimator {
  constructor(workspace) {
    this.workspace = workspace;
    this.animationQueue = [];
    this.isPlaying = false;
    this.speed = 1.0; // 1x, 2x, 0.5x
  }

  async animateToolCall(toolName, parameters, guiAction) {
    const steps = this.getAnimationSteps(toolName, parameters);

    for (const step of steps) {
      if (step.type === 'highlight') {
        await this.highlightElement(step.selector, step.caption);
      } else if (step.type === 'click') {
        await this.animateClick(step.selector);
      } else if (step.type === 'type') {
        await this.animateTyping(step.selector, step.text);
      } else if (step.type === 'open') {
        await this.animateTabOpen(step.tabType, step.title);
      }

      await this.wait(step.duration / this.speed);
    }

    // Finally, execute the actual GUI action
    if (guiAction) {
      this.workspace.addTab(guiAction.component, guiAction.data);
    }
  }

  getAnimationSteps(toolName, parameters) {
    // Return animation step definitions based on tool
    const animations = {
      'search_embeddings': [
        { type: 'highlight', selector: '[data-menu="chunks"]', caption: 'First, I open the Chunks browser', duration: 1000 },
        { type: 'click', selector: '[data-menu="chunks"]', duration: 500 },
        { type: 'open', tabType: 'chunks', title: '🧩 Chunks', duration: 500 },
        { type: 'highlight', selector: '[data-search-input]', caption: 'Then I enter the search term', duration: 1000 },
        { type: 'type', selector: '[data-search-input]', text: parameters.search, duration: 1500 },
        { type: 'highlight', selector: '[data-filter-embedding]', caption: 'I filter to chunks with embeddings', duration: 1000 },
        { type: 'click', selector: '[data-filter-embedding]', duration: 500 },
        { type: 'highlight', selector: '[data-search-button]', caption: 'Finally, I search', duration: 800 },
        { type: 'click', selector: '[data-search-button]', duration: 500 },
        { type: 'wait', duration: 1000 } // Wait for results
      ],
      'cluster_embeddings': [
        { type: 'highlight', selector: '[data-menu="embeddings"]', caption: 'I navigate to Embeddings', duration: 1000 },
        { type: 'click', selector: '[data-menu="embeddings"]', duration: 500 },
        { type: 'highlight', selector: '[data-submenu="cluster"]', caption: 'Then select Cluster Explorer', duration: 1000 },
        { type: 'click', selector: '[data-submenu="cluster"]', duration: 500 },
        { type: 'open', tabType: 'clusterExplorer', title: '🌐 Cluster Explorer', duration: 500 },
        { type: 'highlight', selector: '[data-cluster-limit]', caption: 'I set the embedding limit', duration: 1000 },
        { type: 'type', selector: '[data-cluster-limit]', text: parameters.limit.toString(), duration: 1000 },
        { type: 'highlight', selector: '[data-cluster-button]', caption: 'And run clustering', duration: 800 },
        { type: 'click', selector: '[data-cluster-button]', duration: 500 }
      ],
      // ... other tools
    };

    return animations[toolName] || [];
  }

  async highlightElement(selector, caption) {
    const element = document.querySelector(selector);
    if (!element) return;

    // Add glow effect
    element.classList.add('tutorial-highlight');

    // Show caption
    this.showCaption(caption, element);

    return new Promise(resolve => setTimeout(resolve, 1000));
  }

  async animateClick(selector) {
    const element = document.querySelector(selector);
    if (!element) return;

    // Ripple effect
    element.classList.add('tutorial-click');

    return new Promise(resolve => setTimeout(() => {
      element.classList.remove('tutorial-click');
      resolve();
    }, 500));
  }

  async animateTyping(selector, text) {
    const input = document.querySelector(selector);
    if (!input) return;

    input.value = '';

    for (const char of text) {
      input.value += char;
      await this.wait(100); // 100ms per character
    }
  }
}
```

**CSS Animations:**
```css
/* Tutorial highlight glow */
.tutorial-highlight {
  animation: tutorial-glow 1s ease-in-out infinite;
  position: relative;
  z-index: 9999;
}

@keyframes tutorial-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
  50% { box-shadow: 0 0 40px rgba(59, 130, 246, 0.8); }
}

/* Tutorial click ripple */
.tutorial-click {
  position: relative;
  overflow: hidden;
}

.tutorial-click::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.4);
  transform: translate(-50%, -50%);
  animation: tutorial-ripple 0.5s ease-out;
}

@keyframes tutorial-ripple {
  to {
    width: 200px;
    height: 200px;
    opacity: 0;
  }
}

/* Tutorial caption */
.tutorial-caption {
  position: absolute;
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 10000;
  pointer-events: none;
  animation: tutorial-caption-appear 0.3s ease-out;
}

@keyframes tutorial-caption-appear {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### User Controls

**Tutorial Mode Settings:**
```javascript
// User preferences
{
  tutorialMode: 'full' | 'minimal' | 'off',
  animationSpeed: 0.5 | 1.0 | 2.0,
  autoSkipAfterNTimes: 3, // After seeing animation 3x, auto-skip
  showCaptions: true,
  highlightColor: '#3B82F6' // Customizable
}
```

**Controls During Animation:**
- **Space**: Pause/Resume
- **Esc**: Skip animation, jump to result
- **→**: Speed up (2x)
- **←**: Slow down (0.5x)
- **R**: Replay last animation

---

## Adaptive Learning & Accessibility

### Learning Pattern Recognition

The AUI tracks how users interact to **adapt the interface to their learning style**.

#### Tracked Metrics

```javascript
// User learning profile (stored in agent_conversations.custom_metadata)
{
  learningProfile: {
    // How many times user has seen each tool animation
    toolAnimationsViewed: {
      'search_embeddings': 3,
      'cluster_embeddings': 1,
      'create_book': 0
    },

    // How often user performs manual action after agent demo
    manualActionFollowup: {
      'search_embeddings': 0.7, // 70% of time, does it manually next
      'cluster_embeddings': 0.2 // 20% of time
    },

    // Preferred learning mode
    preferredMode: 'visual' | 'textual' | 'kinesthetic',

    // Accessibility preferences
    accessibility: {
      reduceMotion: false,
      highContrast: false,
      screenReader: false,
      keyboardOnly: false
    },

    // Interface intuition score (0-1)
    interfaceIntuition: {
      'chunks': 0.85,      // User navigates chunks easily
      'embeddings': 0.40,  // User struggles with embedding concepts
      'books': 0.95        // User masters book builder
    }
  }
}
```

#### Adaptive Behaviors

**1. Auto-Skip Familiar Animations**
```javascript
// If user has seen animation 3+ times AND has 70%+ manual followup
if (
  profile.toolAnimationsViewed[toolName] >= 3 &&
  profile.manualActionFollowup[toolName] >= 0.7
) {
  // Skip animation, just open component
  skipAnimation = true;
}
```

**2. Adjust Animation Speed Based on Learning Mode**
```javascript
const speedByMode = {
  'visual': 1.0,      // Standard speed for visual learners
  'textual': 1.5,     // Faster for text-focused users
  'kinesthetic': 0.7  // Slower for hands-on learners
};

animator.speed = speedByMode[profile.preferredMode];
```

**3. Emphasize Struggling Areas**
```javascript
// If intuition score < 0.5, add extra explanation
if (profile.interfaceIntuition[componentName] < 0.5) {
  // Add detailed captions
  // Slow down animation
  // Offer "Learn More" tutorial
  showDetailedTutorial = true;
}
```

**4. Suggest Interface Shortcuts**
```javascript
// After user masters a workflow
if (profile.interfaceIntuition['chunks'] > 0.8) {
  agent.suggest(
    "💡 Pro tip: You've mastered chunk browsing! " +
    "Try keyboard shortcut Cmd+K to search chunks directly."
  );
}
```

### Accessibility Integration

The AUI respects **Web Content Accessibility Guidelines (WCAG)** and adapts to user needs.

#### 1. **Reduce Motion**

For users with vestibular disorders or motion sensitivity:

```javascript
// Detect prefers-reduced-motion
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

if (prefersReducedMotion || profile.accessibility.reduceMotion) {
  // Disable animations
  animator.enabled = false;

  // Show static step-by-step guide instead
  showStaticGuide(toolName, parameters);
}
```

**Static Guide (No Animation):**
```
Agent: "I'll search for chunks about Buddhism. Here's how:

1. Click '🧩 Chunks' in the sidebar
2. Enter 'Buddhism' in the search box
3. Check 'has_embedding' filter
4. Click 'Search'

[Component opens directly with results]
```

#### 2. **Screen Reader Support**

For blind users or screen reader users:

```javascript
if (profile.accessibility.screenReader) {
  // Announce each step via ARIA live region
  announceLiveRegion(
    "Opening Chunks browser. " +
    "Entering search term: Buddhism. " +
    "Filtering to chunks with embeddings. " +
    "Searching... " +
    "Found 4,449 results. Displaying first 50."
  );

  // Skip visual animations
  animator.enabled = false;

  // Open component with full ARIA labels
  openAccessibleComponent(guiAction);
}
```

**ARIA Live Region:**
```html
<div
  role="status"
  aria-live="polite"
  aria-atomic="true"
  className="sr-only"
>
  {liveAnnouncement}
</div>
```

#### 3. **High Contrast Mode**

For users with low vision:

```javascript
if (profile.accessibility.highContrast) {
  // Use high contrast color scheme
  document.body.classList.add('high-contrast-mode');

  // Tutorial highlights use high contrast colors
  highlightColor = '#FFFF00'; // Bright yellow
  backgroundColor = '#000000'; // Pure black
}
```

```css
.high-contrast-mode {
  --bg-primary: #000000;
  --text-primary: #FFFFFF;
  --accent: #FFFF00;
  --border: #FFFFFF;
}

.high-contrast-mode .tutorial-highlight {
  box-shadow: 0 0 0 4px #FFFF00;
  outline: 4px solid #FFFFFF;
}
```

#### 4. **Keyboard-Only Navigation**

For users who cannot use a mouse:

```javascript
if (profile.accessibility.keyboardOnly) {
  // All animations include focus management
  animator.onStep = (step) => {
    if (step.selector) {
      const element = document.querySelector(step.selector);
      element?.focus();
    }
  };

  // Show keyboard shortcuts prominently
  showKeyboardShortcuts = true;
}
```

**Focus Management During Animation:**
```javascript
async animateClick(selector) {
  const element = document.querySelector(selector);

  // Move focus to element
  element.focus();

  // Show focus ring
  element.classList.add('tutorial-focus');

  // Announce to screen reader
  announceAction(`Clicking ${element.getAttribute('aria-label')}`);

  // Animate (or skip if reduced motion)
  if (animator.enabled) {
    await rippleEffect(element);
  }
}
```

### Interface Intuition Tuning

The system learns **how each user thinks** and adjusts accordingly.

#### Detecting User's Mental Model

**Scenario 1: User thinks in terms of "finding things"**
```
User: "Show me Buddhism stuff"
Agent interprets as: search_embeddings
Profile update: User prefers discovery/exploration language
```

**Scenario 2: User thinks in terms of "organizing things"**
```
User: "Create a paper on emptiness"
Agent interprets as: create_book
Profile update: User prefers structural/organizational language
```

**Scenario 3: User thinks in terms of "analysis"**
```
User: "What patterns are in my archive?"
Agent interprets as: cluster_embeddings
Profile update: User prefers analytical/pattern-seeking language
```

#### Adapting Agent Language

Based on detected mental model, agent adjusts response style:

**For "Finder" users:**
```
Agent: "I found 47 chunks matching 'Buddhism'.
        Want to explore them?"
```

**For "Organizer" users:**
```
Agent: "I've categorized 47 chunks about Buddhism.
        Ready to add them to a book section?"
```

**For "Analyst" users:**
```
Agent: "Buddhism appears in 47 chunks across 8 frameworks.
        Would you like to see the cluster analysis?"
```

#### Suggesting Next Actions Based on Profile

```javascript
// After completing a search
if (profile.preferredMode === 'organizer') {
  agent.suggest(
    "You have 47 Buddhism chunks. Create a book to organize them?"
  );
} else if (profile.preferredMode === 'analyst') {
  agent.suggest(
    "Interesting! Want to cluster these chunks to find sub-patterns?"
  );
}
```

---

## Technical Specifications

### Database Schema

**agent_conversations Table:**
```sql
CREATE TABLE agent_conversations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(500) NOT NULL,
  model_name VARCHAR(100) NOT NULL,
  messages JSONB DEFAULT '[]'::jsonb NOT NULL,
  custom_metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agent_conversations_user_id
  ON agent_conversations(user_id);

CREATE INDEX idx_agent_conversations_updated_at
  ON agent_conversations(updated_at DESC);

CREATE INDEX idx_agent_conversations_model_name
  ON agent_conversations(model_name);

CREATE INDEX idx_agent_conversations_messages
  ON agent_conversations USING GIN(messages);
```

**Message Schema (JSONB):**
```json
{
  "role": "user" | "assistant",
  "content": "string",
  "timestamp": "ISO 8601 string",
  "tool_calls": [
    {
      "tool": "string",
      "parameters": {},
      "result": {},
      "thought": "string"
    }
  ],
  "gui_action": {
    "type": "open_tab",
    "component": "string",
    "data": {}
  }
}
```

### API Endpoints

**Full Endpoint List:**

| Endpoint | Method | Auth | Request Body | Response |
|----------|--------|------|--------------|----------|
| `/api/agent/chat` | POST | Required | `{message, conversation_id?, model_name, user_id}` | `{conversation_id, message, tool_calls?, gui_action?, timestamp}` |
| `/api/agent/conversations` | POST | Required | `{title?, model_name, user_id}` | Conversation object |
| `/api/agent/conversations` | GET | Required | Query: `user_id, limit?, offset?` | Array of conversations (no messages) |
| `/api/agent/conversations/{id}` | GET | Required | - | Conversation object with messages |
| `/api/agent/conversations/{id}` | PUT | Required | `{title?}` | Updated conversation |
| `/api/agent/conversations/{id}` | DELETE | Required | - | `{success: true}` |
| `/api/agent/models` | GET | Optional | - | Array of available models |
| `/api/agent/tools` | GET | Optional | - | Array of available tools (debug) |

### LLM Providers

**Ollama (Local)**
- Model: `mistral:7b` (default)
- Endpoint: `http://localhost:11434`
- JSON mode: Via system prompt (no native function calling)
- Status: ✅ Working (Oct 2025)

**Claude (API)**
- Model: `claude-sonnet-4`
- Endpoint: Anthropic API
- Function calling: Native support
- Status: ⏳ Planned (requires API key)

**OpenAI (API)**
- Model: `gpt-4-turbo`
- Endpoint: OpenAI API
- Function calling: Native support
- Status: ⏳ Planned (requires API key)

### Performance Metrics

**Current Performance (Oct 2025):**
- Average response time: ~2-3 seconds (Ollama local)
- Tool execution time: 100-500ms (API calls)
- GUI animation time: 5-8 seconds (when enabled)
- Message storage: ~2KB per message (JSONB)
- Conversation size: ~50-100 messages typical

**Optimization Targets:**
- Response time: < 1 second (with Claude API)
- Parallel tool execution: Multiple tools in single request
- Animation preloading: Cache animations for instant playback
- Message compression: Deduplicate tool results

---

## Future Enhancements

### Phase 2: Advanced Tool Calling

**1. Multi-Tool Composition**
```
User: "Find Buddhism chunks and add them to a new book"

Agent executes:
1. search_embeddings(search="Buddhism")
2. create_book(title="Buddhism Collection")
3. add_content_to_book(book_id=..., chunk_ids=[...])

Response: "Created 'Buddhism Collection' with 47 chunks from your search"
```

**2. Conditional Logic**
```
User: "If there are more than 100 chunks about emptiness, cluster them"

Agent logic:
1. search_embeddings(search="emptiness")
2. IF result.total > 100:
     cluster_embeddings(chunk_ids=result.chunks)
   ELSE:
     "Only 47 chunks found. Clustering works best with 100+."
```

**3. User Confirmation for Destructive Actions**
```
User: "Delete all conversations about test data"

Agent: "⚠️ This will delete 12 conversations permanently. Confirm?"

User: "Yes"

Agent executes: delete_conversations(filter="test data")
```

### Phase 3: Contextual Awareness

**1. Remember Previous Interactions**
```
User: "Find chunks about Buddhism"
[Agent shows 47 results]

User: "Add the top 10 to a book"
[Agent remembers the previous search results]

Agent: "Adding top 10 Buddhism chunks to a new book..."
```

**2. Workspace State Awareness**
```
Agent knows:
- Which tabs are open
- What filters are active
- What content user is viewing
- User's current focus

User: "Add this to my book"
Agent interprets "this" as the currently focused chunk/message
```

**3. Cross-Conversation Learning**
```
Agent notices:
- User frequently searches "phenomenology"
- Then clusters results
- Then creates books

Agent suggests: "I've noticed you often cluster phenomenology results.
                 Want me to do that automatically next time?"
```

### Phase 4: Voice Interface

**1. Speech-to-Text Integration**
```javascript
// Use Web Speech API
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.lang = 'en-US';

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  sendMessage(transcript);
};
```

**2. Text-to-Speech Responses**
```javascript
// Agent speaks responses aloud
const utterance = new SpeechSynthesisUtterance(
  "I found 47 chunks about Buddhism"
);
speechSynthesis.speak(utterance);
```

**3. Hands-Free Operation**
```
User: "Hey Humanizer, find chunks about emptiness"
Agent: [Speaks] "Searching for chunks about emptiness..."
[ChunkBrowser opens]
Agent: [Speaks] "Found 82 chunks. Displaying the first 50."
```

### Phase 5: Proactive Assistance

**1. Suggest Actions Before Asked**
```
[User opens conversation about Madhyamaka]

Agent (unprompted): "This conversation mentions 'two truths' 23 times.
                     Want to see related chunks from your archive?"
```

**2. Detect Workflows and Automate**
```
Agent observes:
1. User searches "phenomenology"
2. Opens clusters
3. Creates book
4. Adds top chunks

Agent learns workflow, offers automation:
"I've created a workflow: Search → Cluster → Book → Add Top 10.
 Next time, just say 'run phenomenology workflow'."
```

**3. Background Processing Notifications**
```
[User is browsing images]

Agent (background): "I finished clustering your embeddings.
                     Found 8 new frameworks. Want to see them?"
```

### Phase 6: Collaborative Intelligence

**1. Multi-User Conversations**
```
User A: "Find chunks about consciousness"
Agent: [Shows results to User A]

User B (in same workspace): "Add the Chalmers quotes to our shared book"
Agent: [Knows context from User A's search]
```

**2. Agent-to-Agent Coordination**
```
Humanizer Agent: "I need chunks about Madhyamaka"
  → Calls search_embeddings

Transformation Agent: "Transform those chunks to academic style"
  → Calls transform API

Book Agent: "Add transformed chunks to thesis"
  → Calls add_content_to_book

User sees: Complete workflow executed by coordinated agents
```

### Phase 7: Meta-Interface Awareness

**1. Agent Explains Its Own Limitations**
```
User: "Predict which framework I'll discover next"

Agent: "I can't predict the future, but I can analyze patterns:
        - You've explored phenomenology (40% of searches)
        - Recently shifting to Buddhist philosophy (30%)
        - Your clusters show overlap between both

        Prediction (60% confidence): You'll discover connections
        between Husserlian reduction and Buddhist emptiness."
```

**2. Agent Suggests Its Own Improvements**
```
Agent: "I notice you often ask 'how many chunks about X?'
        I could add a 'count_chunks' tool to answer faster.
        Want me to request this feature from the developers?"
```

**3. Agent as Interface Critic**
```
User: "Why can't I find the transformation lab?"

Agent: "Good question! The Transformation Lab is hidden in the
        Embeddings submenu. This is bad UX design.

        I've logged this as a usability issue. Meanwhile,
        just ask me 'open transformation lab' and I'll do it."
```

---

## Philosophical Implications

### The AUI as Madhyamaka Practice

**Śūnyatā (Emptiness) of Interface:**

Traditional interfaces have **svabhāva** (inherent existence) - buttons, menus, layouts exist independently of user intention.

The AUI reveals **śūnyatā** (emptiness) - the interface has **no inherent existence**, it arises **dependently** on linguistic construction.

**Two Truths Applied to UI:**

1. **Conventional Truth:** "The interface has buttons and menus"
   - Useful for communication and shared understanding
   - But not ultimately real

2. **Ultimate Truth:** "The interface is empty of inherent existence"
   - Arises moment-by-moment from linguistic intention
   - Dependent on user, agent, tools, context

**Result:** Users directly experience the **constructed nature of the interface** - the same insight Buddhism teaches about all phenomena.

### The Emotional Belief Loop in Interface Design

**Traditional UI reinforces belief in objective interface:**
```
Click button → Something happens → Emotional response (success/frustration)
    ↓
Belief: "The interface works this way objectively"
    ↓
Future interactions: User conforms to "the right way"
```

**AUI interrupts the loop:**
```
Speak intention → Interface materializes → Emotional response (wonder/agency)
    ↓
Belief: "I constructed this interface"
    ↓
Future interactions: User experiments with new linguistic constructions
```

**Philosophical Achievement:** The AUI helps users realize they are **authors of interface**, not **conformers to interface**.

### Language as the Last Sense to Be Questioned

**Phenomenology teaches:**
1. We recognize sight constructs visual experience (not direct access to "things")
2. We recognize hearing constructs auditory experience
3. But we rarely recognize **language constructs conceptual experience**

**Why?** Because language is the **tool we use to question reality**. It's hard to question the questioner.

**AUI's Role:**
By making language the **direct interface**, users can't avoid seeing language as construction:
- "Find chunks" → System interprets → Different results based on interpretation
- "Show frameworks" → System constructs → Interface appears

**Result:** Language becomes **visible as a sense**, not a truth-delivery mechanism.

---

## Conclusion

The Agentic User Interface is not just a natural language interface - it is a **philosophical practice tool** that reveals:

1. **The empty nature of interface** (śūnyatā) - no inherent "right way" to interact
2. **The constructed nature of meaning** - same words, different interpretations
3. **The agency of consciousness** - user witnesses their own subjective construction
4. **The temporality of existence** - interface arises and passes moment-by-moment

By combining **cutting-edge AI** (LLM tool calling) with **ancient wisdom** (Buddhist Madhyamaka), the AUI creates an experience where:

- Users feel **empowered** (language directly creates interface)
- Users feel **aware** (conscious of their own construction)
- Users feel **free** (not bound to pre-determined interface structures)

**The AUI is language as interface, interface as language, and consciousness as both.**

---

**Next Steps:**

1. ✅ Complete Ollama integration (mistral:7b working)
2. 🔄 Build tutorial animation system
3. 🔄 Implement adaptive learning profiles
4. 🔄 Add accessibility features (WCAG compliance)
5. 🔄 Create voice interface (speech-to-text/text-to-speech)
6. 🔄 Develop proactive assistance
7. 🔄 Enable multi-tool composition
8. 🔄 Build workspace state awareness

**Timeline:** Phase 2 (Animations & Accessibility) - Q4 2025

---

*"The interface doesn't exist until spoken into being. This is not metaphor - this is direct experience of dependent origination."*

*Last Updated: October 2025*
