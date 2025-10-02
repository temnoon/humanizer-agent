# Humanizer Agent - Quick Reference

## 🚀 Quick Start Commands

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key-here"
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/transform` | POST | Start new transformation |
| `/api/transform/{id}` | GET | Get transformation status |
| `/api/transform/{id}/result` | GET | Get completed result |
| `/api/history` | GET | List transformation history |
| `/api/transform/{id}/checkpoint` | POST | Create checkpoint |
| `/api/transform/{id}/rollback` | POST | Rollback to checkpoint |
| `/api/analyze` | POST | Analyze content |
| `/health` | GET | Health check |

## 🎯 Transformation Parameters

### Persona
The voice and perspective through which the narrative is told.

**Examples:**
- `Scholar` - Academic, authoritative voice
- `Poet` - Lyrical, metaphorical expression
- `Scientist` - Precise, methodical analysis
- `Child` - Simple, wonder-filled perspective
- `Oracle` - Mystical, prophetic tone

### Namespace
The conceptual framework and domain context.

**Examples:**
- `quantum-physics` - Scientific/physics concepts
- `mythology` - Mythological references
- `business` - Corporate/commercial context
- `nature` - Natural world metaphors
- `technology` - Digital/computational framing

### Style
The writing tone and presentation approach.

**Options:**
- `formal` - Professional, structured
- `casual` - Conversational, relaxed
- `academic` - Scholarly, rigorous
- `creative` - Artistic, expressive
- `technical` - Precise, specialized
- `journalistic` - News-like, factual

### Depth (0.0 - 1.0)
How extensively to transform the content.

- `0.0 - 0.3` - Minimal (subtle voice shift)
- `0.3 - 0.7` - Moderate (clear transformation)
- `0.7 - 1.0` - Deep (substantial reframing)

### Preserve Structure
- `true` - Maintain paragraphs, headings, format
- `false` - Allow reorganization

## 💡 Usage Examples

### Example 1: Technical to Poetic
```json
{
  "content": "The database connection failed due to timeout.",
  "persona": "Poet",
  "namespace": "nature",
  "style": "creative",
  "depth": 0.7,
  "preserve_structure": true
}
```

### Example 2: Casual to Academic
```json
{
  "content": "The team really struggled with this problem.",
  "persona": "Researcher",
  "namespace": "scientific-inquiry",
  "style": "academic",
  "depth": 0.6,
  "preserve_structure": true
}
```

### Example 3: Business to Mythological
```json
{
  "content": "Our Q3 revenue exceeded expectations.",
  "persona": "Oracle",
  "namespace": "ancient-mythology",
  "style": "creative",
  "depth": 0.8,
  "preserve_structure": false
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=your_key_here

# Optional
HOST=127.0.0.1
PORT=8000
DEFAULT_MODEL=claude-sonnet-4-5-20250929
MAX_TOKENS=4096
TEMPERATURE=1.0
```

### Frontend Proxy
Edit `frontend/vite.config.js` to change backend URL:
```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

## 📊 Response Format

### Transformation Response
```json
{
  "id": "uuid",
  "status": "pending|processing|completed|failed",
  "created_at": "2025-10-01T00:00:00Z",
  "message": "Transformation started"
}
```

### Status Response
```json
{
  "id": "uuid",
  "status": "completed",
  "progress": 1.0,
  "original_content": "...",
  "transformed_content": "...",
  "persona": "Scholar",
  "namespace": "academic",
  "style": "formal",
  "created_at": "2025-10-01T00:00:00Z",
  "completed_at": "2025-10-01T00:01:30Z"
}
```

## 🐛 Troubleshooting

### Backend won't start
- Check Python version: `python3 --version` (need 3.11+)
- Verify API key is set: `echo $ANTHROPIC_API_KEY`
- Check port availability: `lsof -i :8000`

### Frontend won't connect
- Ensure backend is running
- Check proxy configuration in `vite.config.js`
- Verify backend URL: `curl http://localhost:8000/health`

### Transformation fails
- Check API key has credits
- Verify content isn't too long (max ~8000 words)
- Check logs in backend terminal

### Slow transformations
- Normal for long texts (30-60 seconds)
- Claude Sonnet 4.5 is thorough but may take time
- Consider reducing content length for faster testing

## 📈 Performance

**Typical Response Times:**
- 500 words: 15-30 seconds
- 1000 words: 30-60 seconds
- 2000 words: 60-120 seconds

**Cost per Transformation:**
- 500 words: ~$0.01-0.02
- 1000 words: ~$0.02-0.05
- 2000 words: ~$0.05-0.10

## 🔒 Security Notes

- Never commit `.env` files with API keys
- Keep API keys secure
- Use environment variables in production
- Monitor API usage in Anthropic Console
- Set up rate limiting for production deployments

## 📚 Resources

- **Claude Agent SDK**: https://docs.anthropic.com/claude/docs/agents
- **API Reference**: http://localhost:8000/docs
- **Anthropic Console**: https://console.anthropic.com/
- **Support**: Check logs and API documentation

## 🎨 Customization

### Add New Transformation Types
Edit `backend/agents/transformation_agent.py`:
- Modify `_build_system_prompt()` for custom instructions
- Add new analysis methods
- Implement specialized transformation logic

### Modify UI
Edit `frontend/src/App.jsx`:
- Add new input fields
- Customize styling
- Add visualization components

### Extend API
Edit `backend/api/routes.py`:
- Add new endpoints
- Implement additional features
- Add authentication/authorization
