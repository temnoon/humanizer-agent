# Humanizer Agent

**AI-Powered Narrative Transformation System**

Built with Claude Agent SDK (Sonnet 4.5) for sophisticated narrative transformation using PERSONA, NAMESPACE, and STYLE parameters.

## Project Overview

Humanizer Agent is a production-ready narrative transformation system that uses Anthropic's Claude Agent SDK to modify texts while preserving core meaning and intent. It combines proven transformation techniques with state-of-the-art AI infrastructure.

## Features

- **🎭 PERSONA Transformation**: Change the voice and perspective of narratives
- **🌌 NAMESPACE Translation**: Shift conceptual frameworks and domains
- **🎨 STYLE Modification**: Adjust tone, formality, and presentation
- **💾 Memory Persistence**: Learn from previous transformations
- **⏱️ Long-Running Tasks**: Handle documents up to 50,000 words
- **📊 Checkpoint System**: Save progress and rollback if needed
- **🔢 Smart Token Validation**: Real-time token counting and tier-based limits
- **⚡ Frontend Validation**: Prevent oversized submissions before API calls
- **📊 Visual Feedback**: Live progress bars and usage indicators

## Architecture

### Backend (Python + FastAPI + Claude Agent SDK)
- **Agent Core**: Transformation agent with memory and context management
- **API Layer**: RESTful API for transformation requests
- **File Management**: Document upload, processing, and download
- **Session Management**: Track transformation history

### Frontend (React + Vite)
- **Simple Upload Interface**: Drag-and-drop document handling
- **Configuration Modal**: PERSONA/NAMESPACE/STYLE parameters
- **Real-time Progress**: Live updates with checkpoint visibility
- **History Management**: Browse and compare transformations
- **Token Counter**: Real-time word/token estimation with visual progress
- **Smart Validation**: Prevents API calls when content exceeds limits
- **Tier Management**: Supports free (4K), premium (32K), enterprise (100K) token limits

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Run server
python main.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. **Upload Document**: Drop a text file or paste content
2. **Monitor Token Usage**: Real-time counter shows word/token count and tier usage
3. **Configure Transformation**: Set PERSONA, NAMESPACE, STYLE
4. **Validate Content**: System prevents submission if content exceeds token limits
5. **Start Processing**: Agent begins transformation with checkpoints
6. **Review Results**: Compare original and transformed text
7. **Download**: Export transformed document

### Token Limits by Tier
- **Free**: 4,000 tokens (~3,000 words)
- **Premium**: 32,000 tokens (~24,000 words) 
- **Enterprise**: 100,000 tokens (~75,000 words)

## API Endpoints

- `POST /api/transform` - Start new transformation
- `GET /api/transform/{id}` - Get transformation status
- `GET /api/transform/{id}/result` - Download result
- `GET /api/history` - List transformation history
- `POST /api/checkpoint/{id}` - Create checkpoint
- `POST /api/rollback/{id}` - Rollback to checkpoint

## Development Status

**Current Phase**: MVP Development
- [x] Project structure created
- [x] Core token utilities and validation
- [x] Frontend token estimation and validation
- [x] Real-time user feedback and limits
- [x] API error handling improvements
- [ ] Core agent implementation
- [ ] Complete API endpoints
- [ ] Testing suite
- [ ] Documentation

## Technology Stack

- **Agent Framework**: Claude Agent SDK (Sonnet 4.5)
- **Backend**: FastAPI, Python 3.11
- **Frontend**: React, Vite, TailwindCSS
- **API**: Anthropic Claude API
- **Storage**: SQLite (development), PostgreSQL (production)

## License

MIT

## Credits

Built with Claude Agent SDK by Anthropic.
Inspired by the Lamish Projection Engine (LPE) framework.
