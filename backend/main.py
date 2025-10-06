"""Main FastAPI application for Humanizer Agent."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# CRITICAL: Validate dependencies BEFORE any imports that use them
from core_dependencies import validate_dependencies
validate_dependencies()

from config import settings
from api.routes import router as api_router
from api.philosophical_routes import router as philosophical_router
from api.session_routes import router as session_router
from api.madhyamaka_routes import router as madhyamaka_router
from api.import_routes import router as import_router
from api.library_routes import router as library_router
from api.gizmo_routes import router as gizmo_router
from api.pipeline_routes import router as pipeline_router
from api.book_routes import router as book_router
from api.vision_routes import router as vision_router
from database import init_db, close_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Humanizer Agent API")
    logger.info(f"Model: {settings.default_model}")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    yield

    # Cleanup
    await close_db()
    logger.info("Shutting down Humanizer Agent API")


# Create FastAPI application
app = FastAPI(
    title="Humanizer API - Language as a Sense",
    description=(
        "Witness language as a constructed sense through which consciousness creates meaning. "
        "Transform narratives across belief frameworks (PERSONA/NAMESPACE/STYLE) while revealing "
        "the subjective ontological nature of linguistic reality. "
        "\n\nNot just transformation—awakening to your role as meaning's author."
    ),
    version="0.2.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000"
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)
app.include_router(philosophical_router)
app.include_router(session_router)
app.include_router(madhyamaka_router)
app.include_router(import_router)
app.include_router(library_router)
app.include_router(gizmo_router)
app.include_router(pipeline_router)
app.include_router(book_router)
app.include_router(vision_router)


@app.get("/")
async def root():
    """Root endpoint with philosophical framing."""
    return {
        "name": "Humanizer API - Language as a Sense",
        "version": "0.2.0",
        "status": "operational",
        "paradigm": "Realizing our subjective ontological nature",
        "philosophy": {
            "core_insight": "Language is not objective reality—it's a sense through which consciousness constructs meaning",
            "three_realms": {
                "corporeal": "Physical substrate (text before interpretation)",
                "symbolic": "Constructed frameworks (PERSONA/NAMESPACE/STYLE)",
                "subjective": "Conscious experience (the only truly 'lived' realm)"
            },
            "goal": "Shift from linguistic identification to self-awareness"
        },
        "model": settings.default_model,
        "endpoints": {
            "transformation": "/api/transform - Transform narratives across belief frameworks",
            "perspectives": "/api/philosophical/perspectives - Generate multiple perspectives simultaneously",
            "contemplate": "/api/philosophical/contemplate - Contemplative exercises (word dissolution, Socratic dialogue)",
            "archive_analysis": "/api/philosophical/archive/analyze - Map your belief structures",
            "sessions": "/api/sessions - Manage user sessions and history",
            "madhyamaka": "/api/madhyamaka - Middle Path detection, transformation, and contemplation (Nagarjuna)",
            "pipeline": "/api/pipeline - Batch transformation jobs, lineage tracking, and graph visualization",
            "docs": "/docs - Interactive API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test agent initialization
        from agents.transformation_agent import TransformationAgent
        test_agent = TransformationAgent()
        
        return {
            "status": "healthy",
            "model": settings.default_model,
            "api_key_present": bool(settings.anthropic_api_key),
            "agent_initialized": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level="info"
    )
