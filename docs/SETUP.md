# Humanizer Agent Setup Guide

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file from example
cp .env.example .env

# Edit .env and add your Anthropic API key
# You can get one at: https://console.anthropic.com/

# Run the server
python main.py
```

The backend will start on http://localhost:8000

API documentation available at: http://localhost:8000/docs

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will start on http://localhost:5173

## API Key Setup

You need an Anthropic API key to use this application.

### Getting an API Key

1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key

### Setting the API Key

**Option 1: Environment Variable (Recommended)**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**Option 2: .env File**
Edit `backend/.env`:
```
ANTHROPIC_API_KEY=your-api-key-here
```

**Option 3: macOS Keychain (Optional)**
If you have the key stored in macOS Keychain:
```bash
export ANTHROPIC_API_KEY="$(security find-generic-password -a 'your-email@example.com' -s 'anthropic API key' -w)"
```

## Testing the System

### 1. Test Backend API

```bash
# Check health
curl http://localhost:8000/health

# Test transformation (after setting API key)
curl -X POST http://localhost:8000/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The project deadline is approaching rapidly.",
    "persona": "Scholar",
    "namespace": "academic-research",
    "style": "academic",
    "depth": 0.5,
    "preserve_structure": true
  }'
```

### 2. Test Frontend

1. Open http://localhost:5173 in your browser
2. Enter some text in the "Content" field
3. Fill in Persona (e.g., "Poet")
4. Fill in Namespace (e.g., "nature")
5. Select a Style
6. Click "Transform"
7. Watch the progress and see the result

## Example Transformations

### Example 1: Technical to Poetic

**Input:**
```
Content: The database connection failed due to timeout.
Persona: Poet
Namespace: nature
Style: creative
```

**Expected Output:**
Something like: "The river of data, seeking its destination, found the bridge of connection had faded into mist..."

### Example 2: Casual to Academic

**Input:**
```
Content: The team really struggled with this problem for weeks.
Persona: Researcher
Namespace: scientific-inquiry
Style: academic
```

**Expected Output:**
Something like: "The research team encountered significant methodological challenges over an extended investigation period..."

### Example 3: Business to Mythological

**Input:**
```
Content: Our Q3 revenue exceeded expectations by 15%.
Persona: Oracle
Namespace: ancient-mythology
Style: creative
```

**Expected Output:**
Something like: "In the third season of harvest, the treasures gathered surpassed even the prophecies of the elders, growing by thrice five portions..."

## Troubleshooting

### Backend Issues

**Problem: "Module not found" errors**
```bash
# Make sure you're in the backend directory and virtual environment is activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Problem: "ANTHROPIC_API_KEY not set"**
```bash
# Check if the key is set
echo $ANTHROPIC_API_KEY

# Set it if needed
export ANTHROPIC_API_KEY="your-key-here"
```

**Problem: "Address already in use"**
```bash
# Change the port in backend/.env
PORT=8001
```

### Frontend Issues

**Problem: "Cannot connect to backend"**
- Make sure backend is running on port 8000
- Check `vite.config.js` proxy settings
- Try accessing http://localhost:8000/health directly

**Problem: "npm install fails"**
```bash
# Clear npm cache and try again
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Problem: Transformation takes too long**
- Claude Sonnet 4.5 is a large model and may take 30-60 seconds for long texts
- Check the network connection
- Verify API key has sufficient credits

## Project Structure

```
humanizer-agent/
├── backend/
│   ├── agents/
│   │   └── transformation_agent.py  # Core transformation logic
│   ├── api/
│   │   └── routes.py               # API endpoints
│   ├── models/
│   │   ├── schemas.py              # Pydantic models
│   │   └── database.py             # Database models
│   ├── utils/
│   │   └── storage.py              # Storage utilities
│   ├── config.py                   # Configuration
│   ├── main.py                     # FastAPI app
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main React component
│   │   ├── main.jsx                # Entry point
│   │   └── index.css               # Styles
│   ├── index.html                  # HTML template
│   ├── package.json                # NPM dependencies
│   └── vite.config.js              # Vite configuration
├── docs/
│   └── SETUP.md                    # This file
└── README.md                       # Project overview
```

## Development Tips

### Backend Development

1. **Enable Debug Mode**: Set `RELOAD=true` in `.env` for auto-reload
2. **View API Docs**: Visit http://localhost:8000/docs for interactive API documentation
3. **Check Logs**: The FastAPI server prints detailed logs to the console
4. **Test Endpoints**: Use the `/docs` interface or curl for testing

### Frontend Development

1. **Hot Reload**: Vite provides instant hot module replacement
2. **React DevTools**: Install React DevTools browser extension for debugging
3. **Network Tab**: Use browser DevTools to inspect API requests
4. **Console Logs**: Check browser console for errors

## Next Steps

1. **Test Core Functionality**: Try various transformations to understand capabilities
2. **Experiment with Parameters**: Adjust depth, style, and preservation settings
3. **Review Code**: Explore the agent implementation in `transformation_agent.py`
4. **Customize**: Modify prompts and add new transformation types
5. **Deploy**: Consider deployment options (see DEPLOYMENT.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API documentation at http://localhost:8000/docs
3. Inspect browser and server console logs
4. Review the Claude Agent SDK documentation at https://docs.anthropic.com/

## Cost Considerations

Claude Sonnet 4.5 pricing:
- Input: $3 per million tokens
- Output: $15 per million tokens

Typical transformation costs:
- 500 word input + 500 word output: ~$0.01-0.02
- 2000 word input + 2000 word output: ~$0.05-0.10

Monitor usage in the Anthropic Console.
