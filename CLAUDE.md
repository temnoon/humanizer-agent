# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

Use the provided script for setup and running:
```bash
./start.sh
```

This script handles Python 3.11 virtual environment setup, dependency installation, and starts both backend and frontend servers.

## Development Commands

### Backend (Python 3.11 + FastAPI)
```bash
cd backend
source venv/bin/activate  # Ensure Python 3.11 venv is activated
python main.py            # Start development server on :8000
```

### Frontend (React + Vite)
```bash
cd frontend
npm run dev               # Start development server on :5173
npm run build            # Build for production
npm run lint             # Run ESLint
```

### Testing
```bash
cd backend
pytest                   # Run backend tests
black . --check         # Check code formatting
ruff check .            # Run linting
mypy .                  # Type checking
```

## Architecture

**Backend Structure:**
- `main.py` - FastAPI application with CORS and global exception handling
- `config.py` - Pydantic settings with environment variable support
- `agents/transformation_agent.py` - Core Claude Agent SDK integration
- `api/routes.py` - REST API endpoints for transformations
- `models/` - Database models for sessions and transformations
- `utils/` - Shared utilities and helpers

**Frontend Structure:**
- `src/App.jsx` - Main React application with transformation interface and real-time token validation
- `src/main.jsx` - React entry point
- `src/utils/tokenEstimator.js` - Frontend token estimation and validation utilities
- Built with Vite, TailwindCSS, and Axios for API calls

## Key Configuration

**Environment Variables (.env):**
- `ANTHROPIC_API_KEY` - Required for Claude API access
- `DEFAULT_MODEL=claude-sonnet-4-5-20250929` - Claude model for transformations
- `HOST=127.0.0.1` and `PORT=8000` - Backend server configuration
- `DATABASE_URL=sqlite+aiosqlite:///./humanizer.db` - SQLite database

**API Endpoints:**
- `POST /api/transform` - Start transformation with PERSONA/NAMESPACE/STYLE
- `GET /api/transform/{id}` - Check transformation status
- `GET /api/transform/{id}/result` - Download completed result
- `GET /api/history` - List transformation history
- `POST /api/transform/{id}/checkpoint` - Create checkpoint
- `POST /api/transform/{id}/rollback` - Rollback to checkpoint

## Core Functionality

This is a narrative transformation system using Claude Agent SDK with three key parameters:
- **PERSONA** - Voice and perspective (e.g., "Scholar", "Poet", "Scientist")
- **NAMESPACE** - Conceptual framework (e.g., "quantum-physics", "mythology", "business")
- **STYLE** - Tone and presentation (e.g., "formal", "casual", "academic", "creative")

Transformations preserve meaning while changing voice, domain context, and presentation style. The system supports long-running tasks with checkpoints and progress tracking.

## Token Validation System

The application includes comprehensive token validation to prevent API errors and provide immediate user feedback:

**Frontend Token Estimation** (`src/utils/tokenEstimator.js`):
- Real-time token counting based on character and word analysis
- Conservative estimation with 10% safety buffer
- Tier-based limits: Free (4K), Premium (32K), Enterprise (100K) tokens

**Real-time Validation Features:**
- Live word/token counter with visual progress bar
- Color-coded indicators (green/yellow/red) based on usage
- Automatic form validation prevents oversized submissions
- Transform button disabled when content exceeds limits
- Clear error messages with specific token counts

**Benefits:**
- Prevents unnecessary API calls for oversized content
- Immediate user feedback without backend requests
- Reduced server load and API costs
- Better user experience with clear visual indicators

## Python Version Requirement

This project requires Python 3.11+. The start.sh script specifically uses `python3.11` and will create a virtual environment with the correct version. If deployment issues occur, verify Python 3.11 is installed and the virtual environment uses the correct version.