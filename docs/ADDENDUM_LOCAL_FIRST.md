# ADDENDUM: Local-First Architecture with Ollama Integration

**Addendum to:** INTEGRATED_DEVELOPMENT_PLAN.md  
**Version:** 1.0  
**Date:** October 2, 2025  
**Focus:** Easy & Medium Difficulty Features for Localhost API and Archive Processing

---

## Table of Contents

1. [Vision: Truly Free Tier](#vision-truly-free-tier)
2. [Local API Architecture](#local-api-architecture)
3. [Ollama Integration](#ollama-integration)
4. [LM Studio Integration](#lm-studio-integration)
5. [HuggingFace Integration](#huggingface-integration)
6. [Archive Parsing System](#archive-parsing-system)
7. [Browser Extension Strategy](#browser-extension-strategy)
8. [Electron Packaging](#electron-packaging)
9. [Model Management UX](#model-management-ux)
10. [Integration with Existing Work](#integration-with-existing-work)
11. [Revised Implementation Timeline](#revised-implementation-timeline)

---

## 1. Vision: Truly Free Tier

### Philosophy

**"Install once, use forever"** - A truly free, open-source local application with no time limits, no forced updates, no deactivation. The local tier is not a crippled demo - it's a complete, powerful tool that respects user privacy and autonomy.

### Architecture Split

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL TIER (FREE FOREVER)                    │
│                                                                 │
│  Localhost API (http://localhost:8000)                         │
│  ├── Archive Processing (all formats)                          │
│  ├── Pattern Detection                                         │
│  ├── Socratic Dialogue (via Ollama)                           │
│  ├── Narrative Bridges (via Ollama)                           │
│  ├── Translation Analysis                                      │
│  ├── Text Transformation (via Ollama)                         │
│  └── LaTeX/Markdown Rendering                                 │
│                                                                 │
│  Storage: SQLite + IndexedDB (browser)                        │
│  Models: User's choice (Ollama, LM Studio, HuggingFace)      │
│  Privacy: Everything stays on device                           │
└─────────────────────────────────────────────────────────────────┘
                                ↕
                    (Optional Connection)
                                ↕
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUD TIER (PREMIUM $29/mo)                   │
│                                                                 │
│  Humanizer.com Backend (https://humanizer.com/api)            │
│  ├── Claude API Integration (highest quality)                 │
│  ├── Cross-Device Sync (encrypted)                            │
│  ├── Social Features (Discourse)                               │
│  ├── Cloud Backup                                              │
│  └── Advanced Analytics                                        │
│                                                                 │
│  Storage: PostgreSQL                                           │
│  Models: Claude Sonnet 4.5 (best quality)                     │
│  Benefits: Convenience, quality, community                     │
└─────────────────────────────────────────────────────────────────┘
```

### Value Proposition

**Local Tier:**
- "Everything you need, nothing you don't want"
- Complete privacy (no data leaves device)
- No subscription, no tracking, no accounts
- Open source, auditable
- Works offline
- Fast (no network latency)

**Cloud Tier:**
- "When you want the best, and to share"
- Claude API (superior quality vs local models)
- Sync across devices
- Social/community features
- Professional support

---

## 2. Local API Architecture

### Overview

A FastAPI server running on localhost, providing RESTful API for browser-based frontend and browser extensions.

### Directory Structure

```
humanizer-local/
├── local_api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Local configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── archives.py         # Archive processing
│   │   ├── transform.py        # Text transformation
│   │   ├── socratic.py         # Socratic dialogue
│   │   ├── bridge.py           # Narrative bridges
│   │   ├── translation.py      # Translation analysis
│   │   └── health.py           # Health checks
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ollama_service.py   # Ollama integration
│   │   ├── lmstudio_service.py # LM Studio integration
│   │   ├── hf_service.py       # HuggingFace integration
│   │   ├── archive_service.py  # Archive parsing
│   │   ├── pattern_service.py  # Pattern detection
│   │   └── vector_service.py   # Vector search (ChromaDB)
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py             # Base parser class
│   │   ├── facebook.py         # Facebook archive
│   │   ├── twitter.py          # Twitter/X archive
│   │   ├── instagram.py        # Instagram archive
│   │   ├── reddit.py           # Reddit archive
│   │   ├── claude.py           # Claude conversations
│   │   ├── chatgpt.py          # ChatGPT conversations
│   │   └── generic.py          # Generic text/markdown
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   └── static/
│       └── frontend/           # Web UI (React)
├── tests/
│   ├── test_parsers.py
│   ├── test_ollama.py
│   └── test_api.py
├── data/                       # Local user data
│   ├── archives/               # Uploaded archives
│   ├── processed/              # Processed data
│   └── humanizer.db            # SQLite database
├── models/                     # Downloaded models (optional)
│   └── .gitkeep
├── requirements.txt
├── setup.py
├── README.md
└── run.sh                      # Start script
```

### Core FastAPI Application

```python
# local_api/main.py
"""
Humanizer Local API
Localhost-only server for privacy-first archive processing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .routes import archives, transform, socratic, bridge, translation, health
from .services.ollama_service import OllamaService
from .models.database import init_db

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Humanizer Local API...")
    
    # Initialize database
    await init_db()
    
    # Check Ollama availability
    ollama = OllamaService()
    if await ollama.is_available():
        print("✅ Ollama detected and ready")
        models = await ollama.list_models()
        print(f"📦 Available models: {', '.join(models)}")
    else:
        print("⚠️  Ollama not detected - AI features will be limited")
        print("   Install from: https://ollama.ai")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Humanizer Local API")


# Create FastAPI app
app = FastAPI(
    title="Humanizer Local API",
    description="Privacy-first archive processing and AI-powered insights",
    version="1.0.0",
    lifespan=lifespan,
    # Localhost only - no external access
    docs_url="/docs" if __debug__ else None,
    redoc_url="/redoc" if __debug__ else None,
)

# CORS - Allow requests from browser frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React dev server
        "http://localhost:8000",    # Self (for extensions)
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(archives.router, prefix="/api/archives", tags=["archives"])
app.include_router(transform.router, prefix="/api/transform", tags=["transform"])
app.include_router(socratic.router, prefix="/api/socratic", tags=["socratic"])
app.include_router(bridge.router, prefix="/api/bridge", tags=["bridge"])
app.include_router(translation.router, prefix="/api/translation", tags=["translation"])

# Serve static frontend files
app.mount("/", StaticFiles(directory="local_api/static/frontend", html=True), name="frontend")


# Root endpoint
@app.get("/api")
async def root():
    """API root with status information."""
    return {
        "name": "Humanizer Local API",
        "version": "1.0.0",
        "status": "running",
        "mode": "local",
        "privacy": "All data stays on your device",
        "documentation": "/docs"
    }
```

### Configuration

```python
# local_api/config.py
"""Local API configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Local API settings."""
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    ARCHIVES_DIR: Path = DATA_DIR / "archives"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    MODELS_DIR: Path = BASE_DIR / "models"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/humanizer.db"
    
    # Server
    HOST: str = "127.0.0.1"  # localhost only
    PORT: int = 8000
    RELOAD: bool = True  # Auto-reload on code changes
    
    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.2:3b"
    
    # LM Studio
    LMSTUDIO_HOST: str = "http://localhost:1234"
    
    # Processing
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    CHUNK_SIZE: int = 1000  # Tokens per chunk
    
    # ChromaDB
    CHROMA_PERSIST_DIR: Path = DATA_DIR / "chroma"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.ARCHIVES_DIR.mkdir(parents=True, exist_ok=True)
settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
```

### Health Check Route

```python
# local_api/routes/health.py
"""Health check and status endpoints."""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from ..services.ollama_service import OllamaService
from ..services.lmstudio_service import LMStudioService

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Check system health and available services.
    
    Returns status of:
    - API server
    - Ollama
    - LM Studio
    - Database
    """
    health_status = {
        "api": "healthy",
        "services": {}
    }
    
    # Check Ollama
    ollama = OllamaService()
    if await ollama.is_available():
        models = await ollama.list_models()
        health_status["services"]["ollama"] = {
            "status": "available",
            "models": models,
            "host": ollama.host
        }
    else:
        health_status["services"]["ollama"] = {
            "status": "unavailable",
            "message": "Install from https://ollama.ai"
        }
    
    # Check LM Studio
    lmstudio = LMStudioService()
    if await lmstudio.is_available():
        health_status["services"]["lmstudio"] = {
            "status": "available",
            "host": lmstudio.host
        }
    else:
        health_status["services"]["lmstudio"] = {
            "status": "unavailable",
            "message": "Start LM Studio server"
        }
    
    # Database check would go here
    health_status["services"]["database"] = {"status": "healthy"}
    
    return health_status


@router.get("/models")
async def list_available_models() -> Dict[str, Any]:
    """List all available models across all providers."""
    
    available_models = {
        "ollama": [],
        "lmstudio": [],
        "huggingface": []
    }
    
    # Ollama models
    ollama = OllamaService()
    if await ollama.is_available():
        available_models["ollama"] = await ollama.list_models()
    
    # LM Studio models
    lmstudio = LMStudioService()
    if await lmstudio.is_available():
        available_models["lmstudio"] = await lmstudio.list_models()
    
    # HuggingFace models (common ones user might have)
    # This would check local cache
    available_models["huggingface"] = []  # TODO: implement
    
    return available_models
```

---

## 3. Ollama Integration

### Ollama Service

```python
# local_api/services/ollama_service.py
"""Ollama local LLM integration."""

import httpx
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from pydantic import BaseModel

from ..config import settings


class Message(BaseModel):
    """Chat message."""
    role: str  # 'user', 'assistant', 'system'
    content: str


class OllamaService:
    """
    Service for interacting with Ollama local LLM.
    
    Ollama must be running separately (installed from ollama.ai).
    This service communicates with Ollama's HTTP API.
    """
    
    def __init__(self, host: str = None, model: str = None):
        self.host = host or settings.OLLAMA_HOST
        self.default_model = model or settings.OLLAMA_DEFAULT_MODEL
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for long generations
    
    async def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List installed models."""
        try:
            response = await self.client.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception:
            return []
    
    async def pull_model(self, model_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Pull/download a model from Ollama registry.
        
        Yields progress updates as the model downloads.
        """
        async with self.client.stream(
            "POST",
            f"{self.host}/api/pull",
            json={"name": model_name},
            timeout=None  # No timeout for downloads
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    yield json.loads(line)
    
    async def generate(
        self,
        prompt: str,
        model: str = None,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate text completion.
        
        Args:
            prompt: User prompt
            model: Model name (defaults to default_model)
            system: System prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: If True, return generator for streaming
        
        Returns:
            Generated text or async generator for streaming
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system:
            payload["system"] = system
        
        if stream:
            return self._stream_generate(payload)
        else:
            response = await self.client.post(
                f"{self.host}/api/generate",
                json=payload
            )
            result = response.json()
            return result.get("response", "")
    
    async def _stream_generate(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream generation (internal helper)."""
        async with self.client.stream(
            "POST",
            f"{self.host}/api/generate",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
    
    async def chat(
        self,
        messages: List[Message],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """
        Chat completion with conversation history.
        
        Args:
            messages: List of Message objects (conversation history)
            model: Model name
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: If True, return generator for streaming
        
        Returns:
            Generated response or async generator for streaming
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": [msg.dict() for msg in messages],
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if stream:
            return self._stream_chat(payload)
        else:
            response = await self.client.post(
                f"{self.host}/api/chat",
                json=payload
            )
            result = response.json()
            return result.get("message", {}).get("content", "")
    
    async def _stream_chat(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Stream chat completion (internal helper)."""
        async with self.client.stream(
            "POST",
            f"{self.host}/api/chat",
            json=payload
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "message" in data:
                        content = data["message"].get("content", "")
                        if content:
                            yield content
    
    async def embed(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """
        Generate embeddings for text.
        
        Useful for semantic search in archives.
        """
        response = await self.client.post(
            f"{self.host}/api/embeddings",
            json={
                "model": model,
                "prompt": text
            }
        )
        result = response.json()
        return result.get("embedding", [])
```

### Example Transformation Route

```python
# local_api/routes/transform.py
"""Text transformation endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..services.ollama_service import OllamaService, Message

router = APIRouter()


class TransformRequest(BaseModel):
    content: str
    persona: str = "Scholar"
    namespace: str = "academic"
    style: str = "formal"
    model: Optional[str] = None


class TransformResponse(BaseModel):
    original: str
    transformed: str
    model: str
    tokens_used: int


@router.post("/", response_model=TransformResponse)
async def transform_text(request: TransformRequest):
    """
    Transform text using specified persona, namespace, and style.
    
    This is the core "AI humanization" feature, now powered by local Ollama.
    """
    ollama = OllamaService()
    
    if not await ollama.is_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama not available. Please install from https://ollama.ai"
        )
    
    # Construct transformation prompt
    system_prompt = f"""You are a text transformation assistant. Transform the user's text according to these parameters:
    
Persona: {request.persona}
Namespace: {request.namespace}
Style: {request.style}

Transform the text while preserving its meaning but adapting the voice, tone, and style to match these parameters. Make it feel natural and human-written, not AI-generated.

Return ONLY the transformed text, no explanations."""
    
    # Generate transformation
    messages = [
        Message(role="system", content=system_prompt),
        Message(role="user", content=request.content)
    ]
    
    transformed = await ollama.chat(
        messages=messages,
        model=request.model,
        temperature=0.8  # Higher creativity for transformation
    )
    
    return TransformResponse(
        original=request.content,
        transformed=transformed,
        model=request.model or ollama.default_model,
        tokens_used=len(request.content.split()) + len(transformed.split())  # Rough estimate
    )
```

### Model Recommendations

```python
# local_api/services/model_recommendations.py
"""Recommend Ollama models based on user's hardware."""

import psutil
from typing import Dict, List
from pydantic import BaseModel


class ModelRecommendation(BaseModel):
    """Model recommendation with metadata."""
    name: str
    display_name: str
    size_gb: float
    ram_required_gb: int
    speed: str  # "Very Fast", "Fast", "Medium", "Slow"
    quality: str  # "Basic", "Good", "Excellent"
    use_cases: List[str]
    ollama_command: str


class ModelRecommendations:
    """Recommend appropriate models based on system resources."""
    
    MODELS = [
        ModelRecommendation(
            name="tinyllama:1.1b-q4_0",
            display_name="TinyLlama (Fastest)",
            size_gb=0.6,
            ram_required_gb=2,
            speed="Very Fast",
            quality="Basic",
            use_cases=[
                "Quick pattern detection",
                "Simple transformations",
                "Low-end hardware"
            ],
            ollama_command="ollama pull tinyllama:1.1b-q4_0"
        ),
        ModelRecommendation(
            name="llama3.2:3b-q4_K_M",
            display_name="Llama 3.2 3B (Balanced)",
            size_gb=2.0,
            ram_required_gb=8,
            speed="Fast",
            quality="Good",
            use_cases=[
                "General transformation",
                "Socratic dialogue",
                "Archive analysis",
                "Most tasks"
            ],
            ollama_command="ollama pull llama3.2:3b"
        ),
        ModelRecommendation(
            name="llama3.2:7b-q4_K_M",
            display_name="Llama 3.2 7B (High Quality)",
            size_gb=4.5,
            ram_required_gb=16,
            speed="Medium",
            quality="Excellent",
            use_cases=[
                "Complex narrative bridges",
                "Nuanced transformations",
                "Philosophical dialogue",
                "Best quality"
            ],
            ollama_command="ollama pull llama3.2:7b"
        ),
        ModelRecommendation(
            name="nomic-embed-text",
            display_name="Nomic Embed (Search)",
            size_gb=0.3,
            ram_required_gb=2,
            speed="Very Fast",
            quality="N/A",
            use_cases=[
                "Semantic search",
                "Archive indexing",
                "Pattern clustering"
            ],
            ollama_command="ollama pull nomic-embed-text"
        )
    ]
    
    @staticmethod
    def get_system_info() -> Dict:
        """Get system RAM and available resources."""
        memory = psutil.virtual_memory()
        return {
            "total_ram_gb": memory.total / (1024 ** 3),
            "available_ram_gb": memory.available / (1024 ** 3)
        }
    
    @classmethod
    def get_recommendations(cls) -> List[ModelRecommendation]:
        """Get models suitable for current system."""
        system = cls.get_system_info()
        total_ram = system["total_ram_gb"]
        
        # Recommend models that require <= 50% of system RAM
        # (Conservative to leave room for OS and other apps)
        suitable_models = [
            model for model in cls.MODELS
            if model.ram_required_gb <= (total_ram * 0.5)
        ]
        
        return suitable_models
    
    @classmethod
    def get_best_for_system(cls) -> ModelRecommendation:
        """Get the best quality model that fits system resources."""
        recommendations = cls.get_recommendations()
        
        if not recommendations:
            return cls.MODELS[0]  # Return smallest model as fallback
        
        # Return highest quality model that fits
        # (Models are ordered by quality in MODELS list)
        return recommendations[-1]
```

---

## 4. LM Studio Integration

### LM Studio Service

```python
# local_api/services/lmstudio_service.py
"""LM Studio integration."""

import httpx
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..config import settings


class LMStudioMessage(BaseModel):
    """Chat message for LM Studio."""
    role: str
    content: str


class LMStudioService:
    """
    Service for LM Studio local server.
    
    LM Studio provides an OpenAI-compatible API, so we use
    the same interface as OpenAI.
    """
    
    def __init__(self, host: str = None):
        self.host = host or settings.LMSTUDIO_HOST
        self.client = httpx.AsyncClient(timeout=300.0)
    
    async def is_available(self) -> bool:
        """Check if LM Studio server is running."""
        try:
            response = await self.client.get(f"{self.host}/v1/models")
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """List loaded models in LM Studio."""
        try:
            response = await self.client.get(f"{self.host}/v1/models")
            if response.status_code == 200:
                data = response.json()
                return [model["id"] for model in data.get("data", [])]
            return []
        except Exception:
            return []
    
    async def chat(
        self,
        messages: List[LMStudioMessage],
        model: str = "local-model",  # LM Studio uses generic identifier
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Chat completion via LM Studio.
        
        Uses OpenAI-compatible API format.
        """
        payload = {
            "model": model,
            "messages": [msg.dict() for msg in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = await self.client.post(
            f"{self.host}/v1/chat/completions",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"LM Studio error: {response.status_code}")
    
    async def generate(
        self,
        prompt: str,
        model: str = "local-model",
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Generate text completion."""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = await self.client.post(
            f"{self.host}/v1/completions",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["text"]
        else:
            raise Exception(f"LM Studio error: {response.status_code}")
```

### Model Provider Abstraction

```python
# local_api/services/model_provider.py
"""Unified interface for different model providers."""

from typing import List, Optional
from enum import Enum

from .ollama_service import OllamaService, Message as OllamaMessage
from .lmstudio_service import LMStudioService, LMStudioMessage


class ModelProvider(str, Enum):
    """Available model providers."""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    HUGGINGFACE = "huggingface"


class ModelService:
    """
    Unified interface for all model providers.
    
    Automatically selects best available provider or uses specified one.
    """
    
    def __init__(self, provider: Optional[ModelProvider] = None):
        self.provider = provider
        self._ollama = None
        self._lmstudio = None
    
    async def get_available_provider(self) -> Optional[ModelProvider]:
        """Find first available provider."""
        # Try Ollama first (preferred)
        ollama = OllamaService()
        if await ollama.is_available():
            return ModelProvider.OLLAMA
        
        # Try LM Studio
        lmstudio = LMStudioService()
        if await lmstudio.is_available():
            return ModelProvider.LMSTUDIO
        
        return None
    
    async def chat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Chat completion using best available provider.
        
        messages format: [{"role": "user", "content": "..."}]
        """
        provider = self.provider or await self.get_available_provider()
        
        if not provider:
            raise Exception("No model provider available. Install Ollama or start LM Studio.")
        
        if provider == ModelProvider.OLLAMA:
            ollama = OllamaService()
            ollama_messages = [OllamaMessage(**msg) for msg in messages]
            return await ollama.chat(
                messages=ollama_messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        elif provider == ModelProvider.LMSTUDIO:
            lmstudio = LMStudioService()
            lms_messages = [LMStudioMessage(**msg) for msg in messages]
            return await lmstudio.chat(
                messages=lms_messages,
                model=model or "local-model",
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        else:
            raise NotImplementedError(f"Provider {provider} not implemented")
    
    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """Text generation using best available provider."""
        provider = self.provider or await self.get_available_provider()
        
        if not provider:
            raise Exception("No model provider available")
        
        if provider == ModelProvider.OLLAMA:
            ollama = OllamaService()
            return await ollama.generate(
                prompt=prompt,
                system=system,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        elif provider == ModelProvider.LMSTUDIO:
            lmstudio = LMStudioService()
            return await lmstudio.generate(
                prompt=prompt,
                model=model or "local-model",
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        else:
            raise NotImplementedError(f"Provider {provider} not implemented")
```

---

## 5. HuggingFace Integration

### HuggingFace Service (For Advanced Users)

```python
# local_api/services/hf_service.py
"""
HuggingFace Transformers integration for advanced users.

This requires more setup than Ollama but gives users direct control
over model loading, quantization, and acceleration.
"""

from typing import Optional, List, Dict
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
    BitsAndBytesConfig
)


class HuggingFaceService:
    """
    Direct HuggingFace Transformers integration.
    
    For users who want:
    - Direct model control
    - Custom quantization
    - GPU acceleration (CUDA/Metal)
    - Latest models from HuggingFace Hub
    """
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = self._detect_device()
        self.loaded_model_id = None
    
    def _detect_device(self) -> str:
        """Detect best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():  # Apple Silicon
            return "mps"
        else:
            return "cpu"
    
    async def load_model(
        self,
        model_id: str,
        quantize: bool = True,
        load_in_4bit: bool = True
    ):
        """
        Load model from HuggingFace Hub.
        
        Args:
            model_id: HuggingFace model identifier (e.g., "meta-llama/Llama-2-7b-chat-hf")
            quantize: Whether to use quantization (recommended)
            load_in_4bit: Use 4-bit quantization (saves RAM)
        """
        print(f"Loading {model_id} on {self.device}...")
        
        # Quantization config (if enabled)
        quantization_config = None
        if quantize and load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map="auto",
            torch_dtype=torch.float16 if quantize else torch.float32
        )
        
        self.loaded_model_id = model_id
        print(f"✅ Model loaded: {model_id}")
    
    async def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50
    ) -> str:
        """Generate text completion."""
        if not self.model or not self.tokenizer:
            raise Exception("No model loaded. Call load_model() first.")
        
        # Encode input
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode output
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        # Remove input prompt from output
        generated_text = generated_text[len(prompt):].strip()
        
        return generated_text
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """
        Chat completion using HuggingFace model.
        
        messages format: [{"role": "user", "content": "..."}]
        """
        if not self.model or not self.tokenizer:
            raise Exception("No model loaded")
        
        # Convert messages to prompt
        # This depends on model's chat template
        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # Fallback: simple concatenation
            prompt = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in messages
            ]) + "\nassistant: "
        
        return await self.generate(
            prompt=prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature
        )
    
    def unload_model(self):
        """Unload model from memory."""
        if self.model:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            self.loaded_model_id = None
            
            # Clear CUDA cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            print("✅ Model unloaded")


# Recommended models for different use cases
RECOMMENDED_MODELS = {
    "small": {
        "id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "size": "~0.6GB (4-bit)",
        "ram_required": "2GB",
        "use_case": "Quick tasks, low-end hardware"
    },
    "medium": {
        "id": "meta-llama/Llama-2-7b-chat-hf",
        "size": "~4GB (4-bit)",
        "ram_required": "8GB",
        "use_case": "Balanced performance and quality"
    },
    "large": {
        "id": "meta-llama/Llama-2-13b-chat-hf",
        "size": "~7GB (4-bit)",
        "ram_required": "16GB",
        "use_case": "Best quality, powerful hardware"
    }
}
```

---

## 6. Archive Parsing System

### Base Parser Architecture

```python
# local_api/parsers/base.py
"""Base archive parser."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
import hashlib


class ParsedMessage(BaseModel):
    """Standardized message format across all platforms."""
    id: str  # Unique identifier
    platform: str  # "facebook", "twitter", "instagram", etc.
    timestamp: datetime
    author: str  # User who wrote it
    content: str  # Main text content
    media: List[str] = []  # URLs or paths to media
    metadata: Dict[str, Any] = {}  # Platform-specific data
    conversation_id: Optional[str] = None  # Thread/conversation grouping


class ParsedArchive(BaseModel):
    """Standardized archive format."""
    platform: str
    user: str  # Archive owner
    date_range: tuple[datetime, datetime]  # (start, end)
    messages: List[ParsedMessage]
    summary: Dict[str, Any]  # Statistics and metadata


class ArchiveParser(ABC):
    """Base class for platform-specific parsers."""
    
    platform_name: str = "unknown"
    
    def __init__(self):
        self.messages: List[ParsedMessage] = []
    
    @abstractmethod
    def detect_format(self, file_path: Path) -> bool:
        """
        Detect if file is valid archive for this platform.
        
        Returns True if this parser can handle the file.
        """
        pass
    
    @abstractmethod
    async def parse(self, file_path: Path) -> ParsedArchive:
        """
        Parse archive file into standardized format.
        
        Must be implemented by each platform parser.
        """
        pass
    
    def generate_id(self, content: str, timestamp: datetime) -> str:
        """Generate unique ID for message."""
        unique_string = f"{self.platform_name}_{timestamp.isoformat()}_{content}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    def extract_date_range(self, messages: List[ParsedMessage]) -> tuple[datetime, datetime]:
        """Extract earliest and latest dates from messages."""
        if not messages:
            now = datetime.now()
            return (now, now)
        
        timestamps = [msg.timestamp for msg in messages]
        return (min(timestamps), max(timestamps))
    
    def generate_summary(self, messages: List[ParsedMessage]) -> Dict[str, Any]:
        """Generate summary statistics."""
        return {
            "total_messages": len(messages),
            "total_words": sum(len(msg.content.split()) for msg in messages),
            "date_range": self.extract_date_range(messages),
            "authors": list(set(msg.author for msg in messages)),
            "has_media": any(msg.media for msg in messages)
        }
```

### Facebook Archive Parser

```python
# local_api/parsers/facebook.py
"""Facebook archive parser."""

import json
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List

from .base import ArchiveParser, ParsedMessage, ParsedArchive


class FacebookParser(ArchiveParser):
    """
    Parser for Facebook data exports.
    
    Handles both JSON format (newer) and HTML format (older).
    Facebook export structure:
    - messages/inbox/person_xxx/*.json (DMs)
    - posts/your_posts_1.json (Posts)
    - comments/comments.json (Comments)
    """
    
    platform_name = "facebook"
    
    def detect_format(self, file_path: Path) -> bool:
        """Detect Facebook archive format."""
        if file_path.suffix == '.zip':
            try:
                with zipfile.ZipFile(file_path) as zf:
                    # Check for Facebook-specific files
                    namelist = zf.namelist()
                    return any('messages/inbox' in name for name in namelist)
            except:
                return False
        return False
    
    async def parse(self, file_path: Path) -> ParsedArchive:
        """Parse Facebook archive."""
        messages = []
        user_name = "Unknown"
        
        with zipfile.ZipFile(file_path) as zf:
            # Parse messages
            messages.extend(await self._parse_messages(zf))
            
            # Parse posts
            messages.extend(await self._parse_posts(zf))
            
            # Parse comments
            messages.extend(await self._parse_comments(zf))
        
        return ParsedArchive(
            platform="facebook",
            user=user_name,
            date_range=self.extract_date_range(messages),
            messages=messages,
            summary=self.generate_summary(messages)
        )
    
    async def _parse_messages(self, zf: zipfile.ZipFile) -> List[ParsedMessage]:
        """Parse Facebook messages (DMs)."""
        messages = []
        
        # Find all message JSON files
        message_files = [
            name for name in zf.namelist()
            if 'messages/inbox' in name and name.endswith('.json')
        ]
        
        for file_name in message_files:
            with zf.open(file_name) as f:
                data = json.load(f)
                
                # Facebook JSON uses 'messages' array
                for msg in data.get('messages', []):
                    # Fix Facebook's encoding (Latin-1 encoded as UTF-8)
                    content = self._fix_encoding(msg.get('content', ''))
                    
                    if not content:
                        continue
                    
                    timestamp = datetime.fromtimestamp(msg['timestamp_ms'] / 1000)
                    
                    messages.append(ParsedMessage(
                        id=self.generate_id(content, timestamp),
                        platform="facebook",
                        timestamp=timestamp,
                        author=msg.get('sender_name', 'Unknown'),
                        content=content,
                        media=[
                            photo.get('uri', '')
                            for photo in msg.get('photos', [])
                        ],
                        metadata={
                            "conversation": data.get('title', 'Unknown'),
                            "participants": [
                                p.get('name')
                                for p in data.get('participants', [])
                            ]
                        },
                        conversation_id=self._extract_conversation_id(file_name)
                    ))
        
        return messages
    
    async def _parse_posts(self, zf: zipfile.ZipFile) -> List[ParsedMessage]:
        """Parse Facebook posts."""
        messages = []
        
        post_files = [
            name for name in zf.namelist()
            if 'posts/your_posts' in name and name.endswith('.json')
        ]
        
        for file_name in post_files:
            with zf.open(file_name) as f:
                data = json.load(f)
                
                for post in data:
                    timestamp = datetime.fromtimestamp(post['timestamp'])
                    content = self._fix_encoding(
                        post.get('data', [{}])[0].get('post', '')
                    )
                    
                    if not content:
                        continue
                    
                    messages.append(ParsedMessage(
                        id=self.generate_id(content, timestamp),
                        platform="facebook",
                        timestamp=timestamp,
                        author="You",  # Posts are by archive owner
                        content=content,
                        media=post.get('attachments', []),
                        metadata={
                            "type": "post",
                            "title": post.get('title', '')
                        }
                    ))
        
        return messages
    
    async def _parse_comments(self, zf: zipfile.ZipFile) -> List[ParsedMessage]:
        """Parse Facebook comments."""
        # Similar to posts, parse comments.json
        # Implementation omitted for brevity
        return []
    
    def _fix_encoding(self, text: str) -> str:
        """
        Fix Facebook's encoding issue.
        
        Facebook exports use Latin-1 encoding but save as UTF-8,
        causing mojibake with non-ASCII characters.
        """
        try:
            return text.encode('latin-1').decode('utf-8')
        except:
            return text
    
    def _extract_conversation_id(self, file_path: str) -> str:
        """Extract conversation ID from file path."""
        # messages/inbox/person_abc123/message_1.json → person_abc123
        parts = file_path.split('/')
        for part in parts:
            if part.startswith('person_') or 'inbox' in file_path:
                return part
        return "unknown"
```

### Twitter/X Archive Parser

```python
# local_api/parsers/twitter.py
"""Twitter/X archive parser."""

import json
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List
import re

from .base import ArchiveParser, ParsedMessage, ParsedArchive


class TwitterParser(ArchiveParser):
    """
    Parser for Twitter/X data exports.
    
    Twitter archive structure:
    - data/tweets.js (Your tweets)
    - data/direct-messages.js (DMs)
    - data/like.js (Liked tweets)
    """
    
    platform_name = "twitter"
    
    def detect_format(self, file_path: Path) -> bool:
        """Detect Twitter archive format."""
        if file_path.suffix == '.zip':
            try:
                with zipfile.ZipFile(file_path) as zf:
                    namelist = zf.namelist()
                    return 'data/tweets.js' in namelist or 'data/tweet.js' in namelist
            except:
                return False
        return False
    
    async def parse(self, file_path: Path) -> ParsedArchive:
        """Parse Twitter archive."""
        messages = []
        user_name = "Unknown"
        
        with zipfile.ZipFile(file_path) as zf:
            # Parse tweets
            tweets = await self._parse_tweets(zf)
            messages.extend(tweets)
            
            # Parse DMs
            dms = await self._parse_dms(zf)
            messages.extend(dms)
            
            # Extract username from account.js
            user_name = await self._extract_username(zf)
        
        return ParsedArchive(
            platform="twitter",
            user=user_name,
            date_range=self.extract_date_range(messages),
            messages=messages,
            summary=self.generate_summary(messages)
        )
    
    async def _parse_tweets(self, zf: zipfile.ZipFile) -> List[ParsedMessage]:
        """Parse tweets."""
        messages = []
        
        # Try both filenames (Twitter changed it)
        for tweets_file in ['data/tweets.js', 'data/tweet.js']:
            if tweets_file not in zf.namelist():
                continue
            
            with zf.open(tweets_file) as f:
                content = f.read().decode('utf-8')
                
                # Twitter JS files start with "window.YTD.tweets.part0 = "
                # Need to extract JSON
                json_match = re.search(r'= (\[.*\])', content, re.DOTALL)
                if not json_match:
                    continue
                
                tweets_data = json.loads(json_match.group(1))
                
                for item in tweets_data:
                    tweet = item.get('tweet', {})
                    
                    timestamp = datetime.strptime(
                        tweet['created_at'],
                        '%a %b %d %H:%M:%S %z %Y'
                    )
                    
                    content = tweet.get('full_text', '')
                    
                    if not content:
                        continue
                    
                    messages.append(ParsedMessage(
                        id=tweet.get('id_str', self.generate_id(content, timestamp)),
                        platform="twitter",
                        timestamp=timestamp,
                        author="You",
                        content=content,
                        media=[
                            media.get('media_url', '')
                            for media in tweet.get('extended_entities', {}).get('media', [])
                        ],
                        metadata={
                            "type": "tweet",
                            "retweet_count": tweet.get('retweet_count', 0),
                            "favorite_count": tweet.get('favorite_count', 0),
                            "in_reply_to": tweet.get('in_reply_to_screen_name')
                        }
                    ))
        
        return messages
    
    async def _parse_dms(self, zf: zipfile.ZipFile) -> List[ParsedMessage]:
        """Parse direct messages."""
        messages = []
        
        dm_file = 'data/direct-messages.js'
        if dm_file not in zf.namelist():
            return messages
        
        with zf.open(dm_file) as f:
            content = f.read().decode('utf-8')
            json_match = re.search(r'= (\[.*\])', content, re.DOTALL)
            
            if not json_match:
                return messages
            
            dm_data = json.loads(json_match.group(1))
            
            for conversation in dm_data:
                conv = conversation.get('dmConversation', {})
                
                for message in conv.get('messages', []):
                    msg = message.get('messageCreate', {})
                    
                    timestamp = datetime.fromtimestamp(
                        int(msg.get('createdAt', 0)) / 1000
                    )
                    
                    content = msg.get('text', '')
                    
                    if not content:
                        continue
                    
                    messages.append(ParsedMessage(
                        id=msg.get('id', self.generate_id(content, timestamp)),
                        platform="twitter",
                        timestamp=timestamp,
                        author=msg.get('senderId', 'Unknown'),
                        content=content,
                        metadata={
                            "type": "direct_message",
                            "conversation_id": conv.get('conversationId')
                        },
                        conversation_id=conv.get('conversationId')
                    ))
        
        return messages
    
    async def _extract_username(self, zf: zipfile.ZipFile) -> str:
        """Extract username from account.js."""
        try:
            with zf.open('data/account.js') as f:
                content = f.read().decode('utf-8')
                json_match = re.search(r'= (\[.*\])', content, re.DOTALL)
                
                if json_match:
                    account_data = json.loads(json_match.group(1))
                    return account_data[0].get('account', {}).get('username', 'Unknown')
        except:
            pass
        
        return "Unknown"
```

### Claude Conversations Parser

```python
# local_api/parsers/claude.py
"""
Claude conversation parser.

Parses exports from:
1. Claude.ai web interface (JSON)
2. Your existing carchive format
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List

from .base import ArchiveParser, ParsedMessage, ParsedArchive


class ClaudeParser(ArchiveParser):
    """Parser for Claude conversation exports."""
    
    platform_name = "claude"
    
    def detect_format(self, file_path: Path) -> bool:
        """Detect Claude conversation format."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check for Claude-specific fields
                return (
                    'messages' in data or
                    'chat_messages' in data or
                    'conversation' in data
                )
        except:
            return False
    
    async def parse(self, file_path: Path) -> ParsedArchive:
        """Parse Claude conversation."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        messages = []
        
        # Handle different export formats
        if 'messages' in data:
            # Standard Claude export format
            messages = await self._parse_standard_format(data)
        elif 'chat_messages' in data:
            # Alternative format
            messages = await self._parse_alternative_format(data)
        
        return ParsedArchive(
            platform="claude",
            user=data.get('user_id', 'Unknown'),
            date_range=self.extract_date_range(messages),
            messages=messages,
            summary=self.generate_summary(messages)
        )
    
    async def _parse_standard_format(self, data: dict) -> List[ParsedMessage]:
        """Parse standard Claude export format."""
        messages = []
        
        for msg in data.get('messages', []):
            timestamp = datetime.fromisoformat(
                msg.get('created_at', datetime.now().isoformat())
            )
            
            # Extract content
            content = ''
            if isinstance(msg.get('content'), str):
                content = msg['content']
            elif isinstance(msg.get('content'), list):
                # Handle multi-part content
                content = '\n'.join([
                    part.get('text', '')
                    for part in msg['content']
                    if part.get('type') == 'text'
                ])
            
            if not content:
                continue
            
            messages.append(ParsedMessage(
                id=msg.get('id', self.generate_id(content, timestamp)),
                platform="claude",
                timestamp=timestamp,
                author=msg.get('role', 'unknown'),  # 'user' or 'assistant'
                content=content,
                metadata={
                    "model": msg.get('model', 'unknown'),
                    "tokens": msg.get('usage', {})
                }
            ))
        
        return messages
    
    async def _parse_alternative_format(self, data: dict) -> List[ParsedMessage]:
        """Parse alternative Claude format (e.g., from carchive)."""
        # Implementation for your existing carchive format
        # This would parse the format you've been using
        messages = []
        
        for msg in data.get('chat_messages', []):
            # Adapt to your specific format
            timestamp = datetime.fromisoformat(msg.get('timestamp', ''))
            
            messages.append(ParsedMessage(
                id=msg.get('id', ''),
                platform="claude",
                timestamp=timestamp,
                author=msg.get('sender', 'unknown'),
                content=msg.get('text', ''),
                metadata=msg.get('metadata', {})
            ))
        
        return messages
```

### Archive Service (Orchestration)

```python
# local_api/services/archive_service.py
"""Archive processing service."""

from pathlib import Path
from typing import List, Optional

from ..parsers.base import ArchiveParser, ParsedArchive
from ..parsers.facebook import FacebookParser
from ..parsers.twitter import TwitterParser
from ..parsers.claude import ClaudeParser


class ArchiveService:
    """Service for processing archives."""
    
    def __init__(self):
        self.parsers: List[ArchiveParser] = [
            FacebookParser(),
            TwitterParser(),
            ClaudeParser(),
            # Add more parsers as implemented
        ]
    
    async def detect_format(self, file_path: Path) -> Optional[ArchiveParser]:
        """Detect which parser can handle this archive."""
        for parser in self.parsers:
            if parser.detect_format(file_path):
                return parser
        return None
    
    async def parse_archive(self, file_path: Path) -> ParsedArchive:
        """Parse archive using appropriate parser."""
        parser = await self.detect_format(file_path)
        
        if not parser:
            raise ValueError(f"Unknown archive format: {file_path}")
        
        print(f"Detected format: {parser.platform_name}")
        return await parser.parse(file_path)
```

---

## 7. Browser Extension Strategy

### Single Extension with Modular Architecture

Rather than multiple extensions, build **one extension** with **lazy-loaded modules** per platform.

### Extension Structure

```
humanizer-extension/
├── manifest.json
├── background/
│   ├── service-worker.js      # Background tasks
│   ├── auth-manager.js         # Auth with local API
│   └── sync-manager.js         # Archive sync
├── content/
│   ├── content-script.js       # Injected into pages
│   └── platforms/              # Platform-specific modules
│       ├── facebook.js         # Lazy-loaded
│       ├── twitter.js
│       ├── instagram.js
│       └── reddit.js
├── popup/
│   ├── popup.html
│   ├── popup.js
│   └── popup.css
├── options/
│   ├── options.html            # Extension settings
│   └── options.js
└── lib/
    ├── api-client.js           # Talk to localhost API
    └── platform-detector.js    # Detect current platform
```

### Manifest

```json
{
  "manifest_version": 3,
  "name": "Humanizer Archive Assistant",
  "version": "1.0.0",
  "description": "Process your social media archives locally with privacy",
  
  "permissions": [
    "storage",
    "downloads",
    "tabs"
  ],
  
  "host_permissions": [
    "http://localhost:8000/*",
    "http://127.0.0.1:8000/*"
  ],
  
  "background": {
    "service_worker": "background/service-worker.js"
  },
  
  "content_scripts": [
    {
      "matches": [
        "*://www.facebook.com/*",
        "*://facebook.com/*",
        "*://twitter.com/*",
        "*://x.com/*",
        "*://www.instagram.com/*",
        "*://instagram.com/*",
        "*://www.reddit.com/*",
        "*://reddit.com/*"
      ],
      "js": ["content/content-script.js"],
      "run_at": "document_idle"
    }
  ],
  
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  
  "options_page": "options/options.html",
  
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### Platform Detector

```javascript
// lib/platform-detector.js
/**
 * Detect which platform the user is currently on.
 */

class PlatformDetector {
  static detect() {
    const hostname = window.location.hostname
    
    // Facebook
    if (hostname.includes('facebook.com')) {
      return {
        platform: 'facebook',
        module: 'content/platforms/facebook.js'
      }
    }
    
    // Twitter/X
    if (hostname.includes('twitter.com') || hostname.includes('x.com')) {
      return {
        platform: 'twitter',
        module: 'content/platforms/twitter.js'
      }
    }
    
    // Instagram
    if (hostname.includes('instagram.com')) {
      return {
        platform: 'instagram',
        module: 'content/platforms/instagram.js'
      }
    }
    
    // Reddit
    if (hostname.includes('reddit.com')) {
      return {
        platform: 'reddit',
        module: 'content/platforms/reddit.js'
      }
    }
    
    return { platform: 'unknown', module: null }
  }
}
```

### Background Service Worker

```javascript
// background/service-worker.js
/**
 * Background service worker for extension.
 * Handles downloads, API communication, and notifications.
 */

import { APIClient } from '../lib/api-client.js'

const api = new APIClient('http://localhost:8000')

// Watch for downloads
chrome.downloads.onChanged.addListener(async (delta) => {
  if (delta.state && delta.state.current === 'complete') {
    // Download completed
    const download = await chrome.downloads.search({ id: delta.id })
    const file = download[0]
    
    // Check if it's an archive we care about
    if (isArchiveFile(file.filename)) {
      // Notify user
      chrome.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon48.png',
        title: 'Archive Downloaded',
        message: 'Would you like to import this to Humanizer?',
        buttons: [
          { title: 'Import Now' },
          { title: 'Later' }
        ]
      })
    }
  }
})

// Handle notification clicks
chrome.notifications.onButtonClicked.addListener(async (notifId, buttonIndex) => {
  if (buttonIndex === 0) {
    // "Import Now" clicked
    // Open local API upload page
    chrome.tabs.create({
      url: 'http://localhost:8000/upload'
    })
  }
})

function isArchiveFile(filename) {
  // Check if filename suggests it's a social media archive
  const lowerFilename = filename.toLowerCase()
  return (
    lowerFilename.includes('facebook') ||
    lowerFilename.includes('twitter') ||
    lowerFilename.includes('instagram') ||
    lowerFilename.endsWith('.zip') ||
    lowerFilename.includes('archive')
  )
}

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'watchDownloads') {
    console.log(`Watching for ${message.platform} downloads`)
    sendResponse({ status: 'watching' })
  }
  
  return true  // Keep channel open for async response
})
```

---

## 8. Electron Packaging

### Main Process

```javascript
// main.js
/**
 * Electron main process.
 * Starts local API server and manages application lifecycle.
 */

const { app, BrowserWindow, Menu, Tray, dialog } = require('electron')
const path = require('path')
const { startServer, stopServer } = require('./src/server')
const { OllamaManager } = require('./src/ollama-manager')

let mainWindow = null
let tray = null
let serverProcess = null

// Initialize Ollama manager
const ollamaManager = new OllamaManager()

async function createWindow() {
  // Create the browser window
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    },
    title: 'Humanizer',
    icon: path.join(__dirname, 'build/icon.png')
  })
  
  // Load the local server
  mainWindow.loadURL('http://localhost:8000')
  
  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools()
  }
  
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

async function startLocalServer() {
  console.log('Starting local API server...')
  
  try {
    serverProcess = await startServer()
    console.log('✅ Local API server started')
    return true
  } catch (error) {
    console.error('❌ Failed to start server:', error)
    
    // Show error dialog
    dialog.showErrorBox(
      'Server Start Failed',
      'Could not start the local API server. Please check the logs.'
    )
    
    return false
  }
}

async function checkOllama() {
  const isInstalled = await ollamaManager.isInstalled()
  
  if (!isInstalled) {
    // Show dialog offering to install Ollama
    const result = await dialog.showMessageBox({
      type: 'question',
      buttons: ['Install Ollama', 'Skip', 'Learn More'],
      defaultId: 0,
      title: 'Ollama Not Found',
      message: 'Ollama is required for AI features',
      detail: 'Ollama lets you run AI models locally on your computer. Would you like to install it now?'
    })
    
    if (result.response === 0) {
      // Install Ollama
      await ollamaManager.downloadAndInstall()
    } else if (result.response === 2) {
      // Open Ollama website
      require('electron').shell.openExternal('https://ollama.ai')
    }
  } else {
    console.log('✅ Ollama is installed')
    
    // Check if any models are installed
    const models = await ollamaManager.listModels()
    
    if (models.length === 0) {
      // Offer to download a model
      const result = await dialog.showMessageBox({
        type: 'question',
        buttons: ['Download Model', 'Later'],
        defaultId: 0,
        title: 'No Models Installed',
        message: 'You need to download an AI model',
        detail: 'We recommend Llama 3.2 3B (~2GB download). Would you like to download it now?'
      })
      
      if (result.response === 0) {
        await ollamaManager.downloadModel('llama3.2:3b')
      }
    }
  }
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'build/icon.png'))
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open Humanizer',
      click: () => {
        if (mainWindow) {
          mainWindow.show()
        } else {
          createWindow()
        }
      }
    },
    {
      label: 'Check Ollama Status',
      click: async () => {
        const isRunning = await ollamaManager.isRunning()
        const models = await ollamaManager.listModels()
        
        dialog.showMessageBox({
          type: 'info',
          title: 'Ollama Status',
          message: isRunning ? 'Ollama is running' : 'Ollama is not running',
          detail: `Installed models: ${models.length > 0 ? models.join(', ') : 'None'}`
        })
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        app.quit()
      }
    }
  ])
  
  tray.setToolTip('Humanizer')
  tray.setContextMenu(contextMenu)
}

// App lifecycle
app.whenReady().then(async () => {
  // Check Ollama first
  await checkOllama()
  
  // Start local server
  const serverStarted = await startLocalServer()
  
  if (serverStarted) {
    // Create main window
    await createWindow()
    
    // Create system tray icon
    createTray()
  }
})

app.on('window-all-closed', () => {
  // Don't quit on window close (run in background)
  // Use Cmd+Q or tray menu to quit
})

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

app.on('before-quit', async () => {
  console.log('Shutting down...')
  
  // Stop the server
  if (serverProcess) {
    await stopServer(serverProcess)
  }
})
```

---

## 9. Model Management UX

### Model Selection UI

```jsx
// renderer/components/ModelSelector.jsx
/**
 * User-friendly model selection interface.
 */

import React, { useState, useEffect } from 'react'
import { APIClient } from '../lib/api-client'

export function ModelSelector() {
  const [systemInfo, setSystemInfo] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)
  const [downloading, setDownloading] = useState(false)
  const [progress, setProgress] = useState(0)
  
  const api = new APIClient()
  
  useEffect(() => {
    loadRecommendations()
  }, [])
  
  async function loadRecommendations() {
    const system = await api.get('/api/system-info')
    const models = await api.get('/api/models/recommendations')
    
    setSystemInfo(system)
    setRecommendations(models)
  }
  
  async function downloadModel(model) {
    setDownloading(true)
    setProgress(0)
    
    // Stream download progress
    const response = await fetch('/api/models/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: model.name })
    })
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const text = decoder.decode(value)
      const update = JSON.parse(text)
      
      if (update.status === 'downloading') {
        setProgress(update.progress)
      } else if (update.status === 'complete') {
        setDownloading(false)
        setSelectedModel(model)
        alert(`${model.display_name} is ready!`)
      }
    }
  }
  
  return (
    <div className="model-selector">
      <h2>Choose Your AI Model</h2>
      
      {systemInfo && (
        <div className="system-info">
          <p>Your System: {systemInfo.total_ram_gb.toFixed(1)}GB RAM</p>
          <p>Available: {systemInfo.available_ram_gb.toFixed(1)}GB</p>
        </div>
      )}
      
      <div className="model-grid">
        {recommendations.map(model => (
          <div key={model.name} className="model-card">
            <h3>{model.display_name}</h3>
            
            <div className="model-specs">
              <div className="spec">
                <span className="label">Size:</span>
                <span className="value">{model.size_gb}GB</span>
              </div>
              <div className="spec">
                <span className="label">Requires:</span>
                <span className="value">{model.ram_required_gb}GB RAM</span>
              </div>
              <div className="spec">
                <span className="label">Speed:</span>
                <span className="value">{model.speed}</span>
              </div>
              <div className="spec">
                <span className="label">Quality:</span>
                <span className="value">{model.quality}</span>
              </div>
            </div>
            
            <div className="use-cases">
              <p className="label">Best for:</p>
              <ul>
                {model.use_cases.map((useCase, i) => (
                  <li key={i}>{useCase}</li>
                ))}
              </ul>
            </div>
            
            {selectedModel?.name === model.name ? (
              <button className="selected" disabled>
                ✓ Installed
              </button>
            ) : (
              <button
                onClick={() => downloadModel(model)}
                disabled={downloading}
              >
                {downloading ? `Downloading... ${progress}%` : 'Download'}
              </button>
            )}
          </div>
        ))}
      </div>
      
      {downloading && (
        <div className="progress-overlay">
          <div className="progress-dialog">
            <h3>Downloading Model...</h3>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p>{progress}% complete</p>
            <p className="note">
              This may take a few minutes depending on your internet speed.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## 10. Integration with Existing Work

### Leveraging Your Existing Repos

#### From `carchive`

Your carchive repo contains archive processing logic. We can:

1. **Import existing parsers** directly into `local_api/parsers/`
2. **Adapt format detection** to our `ArchiveParser` base class
3. **Reuse vector search logic** with our ChromaDB integration

```python
# local_api/parsers/carchive_adapter.py
"""
Adapter for existing carchive functionality.
"""

# Import your existing carchive modules
from carchive import (
    parse_conversation,
    extract_themes,
    detect_patterns
)

class CArchiveAdapter(ArchiveParser):
    """Adapter to use existing carchive functionality."""
    
    platform_name = "carchive"
    
    async def parse(self, file_path: Path) -> ParsedArchive:
        # Use your existing parsing logic
        conversation = parse_conversation(str(file_path))
        
        # Convert to our standard format
        messages = [
            ParsedMessage(
                id=msg['id'],
                platform="carchive",
                timestamp=datetime.fromisoformat(msg['timestamp']),
                author=msg['role'],
                content=msg['content'],
                metadata=msg.get('metadata', {})
            )
            for msg in conversation['messages']
        ]
        
        return ParsedArchive(
            platform="carchive",
            user=conversation['user_id'],
            date_range=self.extract_date_range(messages),
            messages=messages,
            summary=self.generate_summary(messages)
        )
```

#### From `humanizer_app`

Your existing humanizer app has:

1. **Personas system** - we keep this!
2. **Vector search with ChromaDB** - we integrate directly
3. **Transformation logic** - becomes part of our local API

```python
# local_api/services/persona_service.py
"""
Persona management - ported from humanizer_app.
"""

from typing import List, Dict
import json
from pathlib import Path

class PersonaService:
    """Manage transformation personas."""
    
    def __init__(self, personas_file: Path = None):
        self.personas_file = personas_file or Path(__file__).parent / "personas.json"
        self.personas = self.load_personas()
    
    def load_personas(self) -> Dict:
        """Load personas from your existing format."""
        if self.personas_file.exists():
            with open(self.personas_file) as f:
                return json.load(f)
        return {}
    
    def get_persona(self, name: str) -> Dict:
        """Get persona configuration."""
        return self.personas.get(name, {})
    
    def list_personas(self) -> List[str]:
        """List available personas."""
        return list(self.personas.keys())
```

---

## 11. Revised Implementation Timeline

### Updated Timeline (28 Weeks)

Including local-first features adds ~4 weeks to original 24-week timeline:

#### Weeks 1-3: Foundation (Auth & Payments) - UNCHANGED

#### Weeks 4-6: Core API - MODIFIED
- **Week 4:** Usage tracking + Local API structure
- **Week 5:** Ollama integration
- **Week 6:** LM Studio + Model provider abstraction

#### Weeks 7-10: Archive System - NEW
- **Week 7:** Base parser architecture + Facebook parser
- **Week 8:** Twitter + Instagram parsers
- **Week 9:** Reddit + Claude parsers
- **Week 10:** Archive service orchestration + testing

#### Weeks 11-14: Browser Extension - NEW
- **Week 11:** Extension framework + platform detection
- **Week 12:** Facebook & Twitter modules
- **Week 13:** Instagram & Reddit modules
- **Week 14:** Download assistant + testing

#### Weeks 15-18: Electron Desktop App - NEW
- **Week 15:** Basic Electron wrapper + server management
- **Week 16:** Ollama manager + model downloader
- **Week 17:** UI polish + system tray
- **Week 18:** Cross-platform build + installers

#### Weeks 19-22: Pedagogical Features - ADJUSTED
- **Week 19:** Socratic dialogue (using Ollama)
- **Week 20:** Translation analysis
- **Week 21:** Narrative bridge builder
- **Week 22:** Integration + testing

#### Weeks 23-26: Social Integration - ADJUSTED
- **Week 23:** Discourse plugin
- **Week 24:** Extension ↔ Social flow
- **Week 25:** Trust circles
- **Week 26:** End-to-end testing

#### Weeks 27-28: Launch Prep - ADJUSTED
- **Week 27:** Production deployment + monitoring
- **Week 28:** Beta testing + launch

---

## Conclusion

This addendum details a **comprehensive local-first architecture** that:

1. ✅ **Runs entirely on localhost** for privacy
2. ✅ **Integrates with Ollama** for free local AI
3. ✅ **Supports LM Studio & HuggingFace** for power users
4. ✅ **Parses 5+ platform archives** (Facebook, Twitter, Instagram, Reddit, Claude)
5. ✅ **Provides browser extension** for seamless archive downloads
6. ✅ **Packages as Electron app** for non-technical users
7. ✅ **Includes model management UX** that's user-friendly

**Key Advantages:**

- **Privacy:** Archives never leave user's device by default
- **Cost:** No API costs for local processing
- **Open Source:** Can be "install once, use forever"
- **Quality:** Can upgrade to Claude API when desired
- **Integration:** Builds on your existing work

**Implementation Estimate:** 28 weeks with 1-2 developers

This creates a **truly free tier** that's genuinely useful, not just a demo to force upgrades. Users can stay local forever if they want, and upgrade to cloud features when they need:
- Sync across devices
- Claude API quality
- Social features

The local tier isn't compromised - it's **fully featured** using Ollama.

Ready to start building?
