# Import Error Fix

## Problem
The backend was failing with `ModuleNotFoundError: No module named 'backend'` because we were using absolute imports like:

```python
from backend.config import settings
from backend.api.routes import router
```

But when running `python main.py` from within the `backend/` directory, Python doesn't know about the `backend` package.

## Solution
Changed all imports to relative imports:

```python
from config import settings
from api.routes import router
```

## Files Updated
- `backend/main.py` - Changed to relative imports
- `backend/api/routes.py` - Changed to relative imports  
- `backend/agents/transformation_agent.py` - Changed to relative imports
- `backend/utils/storage.py` - Changed to relative imports
- `backend/models/schemas.py` - Fixed duplicate enum definition

## How to Restart

### Stop Current Servers
Press `Ctrl+C` in the terminal running `ha-start` to stop both servers.

### Start Fresh

**Option 1: Use the start script**
```bash
ha-start
```

**Option 2: Manual start (two terminals)**

Terminal 1 - Backend:
```bash
cd ~/humanizer-agent/backend
source venv/bin/activate
python main.py
```

Terminal 2 - Frontend:
```bash
cd ~/humanizer-agent/frontend
npm run dev
```

## Verify It Works

1. **Check backend is running:**
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "model": "claude-sonnet-4-5-20250929"
}
```

2. **Open frontend:**
```
http://localhost:5173
```

3. **Try a simple transformation:**
- Content: "Hello world"
- Persona: "Poet"
- Namespace: "nature"
- Style: "creative"
- Click Transform

## If You Still See Errors

### Backend won't start
```bash
cd ~/humanizer-agent/backend
source venv/bin/activate
python main.py
```

Check the error message. Common issues:
- Missing dependencies: `pip install -r requirements.txt`
- Wrong Python version: `python --version` should show 3.11
- API key not set: Check with `echo $ANTHROPIC_API_KEY`

### Frontend can't connect
Make sure backend is running first. Check:
```bash
curl http://localhost:8000/health
```

If backend is running but frontend still can't connect, check the browser console for errors.

## Understanding the Fix

**Why absolute imports failed:**
When you run `python main.py` from inside the `backend/` directory:
- Python's current working directory is `backend/`
- Python doesn't know about a package called `backend`
- Import like `from backend.config import settings` fails

**Why relative imports work:**
- Relative imports use the current module's location
- `from config import settings` looks for `config.py` in the same directory
- This works when running from within the `backend/` directory

**Alternative solutions we didn't use:**
1. Run from parent directory: `python -m backend.main`
2. Add to PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:/Users/tem/humanizer-agent"`
3. Install as package: `pip install -e .`

We chose relative imports because it's the simplest solution for this project structure.
