"""Main FastAPI application for Humanizer Agent."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from api.routes import router as api_router

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
    yield
    logger.info("Shutting down Humanizer Agent API")


# Create FastAPI application
app = FastAPI(
    title="Humanizer Agent API",
    description="AI-powered narrative transformation using Claude Agent SDK",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Humanizer Agent API",
        "version": "0.1.0",
        "status": "operational",
        "model": settings.default_model,
        "docs": "/docs"
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
