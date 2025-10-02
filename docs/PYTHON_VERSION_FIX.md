# Python Version Fix Guide

## Problem

The initial setup attempted to use Python 3.13, which is too new. The `pydantic-core` package doesn't have pre-built wheels for Python 3.13 yet, causing it to try building from source. This failed because:

1. Building from source requires Rust 1.65+
2. Your system has Rust 1.63.0
3. This is a compatibility issue, not a fundamental problem

## Solution

Use **Python 3.11** (which you already have installed and prefer) instead of Python 3.13.

## Quick Fix Steps

### 1. Reload Your Shell Configuration

```bash
source ~/.zshrc
```

This loads the updated configuration that uses Python 3.11 explicitly.

### 2. Remove the Old Virtual Environment

```bash
cd ~/humanizer-agent/backend
rm -rf venv
```

### 3. Create New Virtual Environment with Python 3.11

Use the new helper function:

```bash
ha-fix-venv
```

Or manually:

```bash
cd ~/humanizer-agent/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Verify Python Version

```bash
cd ~/humanizer-agent/backend
source venv/bin/activate
python --version
```

Should output: `Python 3.11.x`

### 5. Complete Setup

```bash
# If you haven't already, set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Complete the setup
ha-setup
```

Or manually:

```bash
# Backend
cd ~/humanizer-agent/backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> .env

# Frontend
cd ~/humanizer-agent/frontend
npm install
```

## What Was Changed

### 1. Updated requirements.txt

Changed:
```
pydantic==2.5.3  # Old version
```

To:
```
pydantic==2.6.0  # Better Python 3.11 support
```

### 2. Updated .zshrc

All aliases now explicitly use `python3.11`:

```bash
# Old
alias ha-install-backend="cd ... && python3 -m venv venv ..."

# New
alias ha-install-backend="cd ... && python3.11 -m venv venv ..."
```

### 3. Added Helper Functions

New functions in .zshrc:

- `ha-fix-venv` - Recreates venv with Python 3.11
- `ha-quickstart` - Checks for Python 3.11 and sets up properly

### 4. Updated start.sh

Now explicitly uses Python 3.11 and checks/fixes venv if wrong version.

## Verification Commands

After setup, verify everything:

```bash
# Check environment
check_env

# Should show:
#   Python: /opt/homebrew/opt/python@3.11/bin/python3 -> Python 3.11.x
#   Python 3.11: /opt/homebrew/opt/python@3.11/bin/python3.11 -> Python 3.11.x

# Check project status
ha-status

# Should show all green checkmarks:
#   ✅ Backend code present
#   ✅ Virtual environment created
#   ℹ️  Using: Python 3.11.x
```

## If You Still Have Issues

### Issue: Can't find python3.11

**Solution**: Install it with Homebrew:
```bash
brew install python@3.11
```

### Issue: Still getting Python 3.13 errors

**Solution**: Make sure you're using the updated shell config:
```bash
source ~/.zshrc
which python3.11  # Should point to /opt/homebrew/opt/python@3.11/bin/python3.11
```

### Issue: Virtual environment still has wrong Python

**Solution**: Completely remove and recreate:
```bash
cd ~/humanizer-agent/backend
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
python --version  # Verify it's 3.11
pip install -r requirements.txt
```

### Issue: Rust version error still appears

**Solution**: This should not happen with Python 3.11, as pre-built wheels are available. If it does:
```bash
# Update Rust (optional, but good practice)
brew install rust

# Or just ensure you're using Python 3.11
cd ~/humanizer-agent/backend
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Testing the Fix

Once setup is complete:

```bash
# Terminal 1 - Start backend
ha-api

# Terminal 2 - Start frontend
ha-web

# Or use the unified start script
ha-start
```

Then open http://localhost:5173 in your browser.

## Understanding the Issue

**Why Python 3.13 was a problem:**
- Python 3.13 was released recently (October 2024)
- Package maintainers need time to build wheels for new Python versions
- `pydantic-core` 2.14.6 (from December 2023) predates Python 3.13
- Without pre-built wheels, pip tries to compile from source
- Source compilation requires Rust 1.65+, but your system has 1.63

**Why Python 3.11 works:**
- Python 3.11 was released October 2022
- All packages have mature, pre-built wheels for 3.11
- No source compilation needed
- Fast, reliable installation

**Best practice:**
- Use Python 3.11 or 3.12 for production projects
- Wait 6-12 months after a new Python release before using it in projects
- This allows time for ecosystem to catch up with wheels and compatibility

## Next Steps

After successful setup:

1. **Test the system**:
   ```bash
   ha-status
   ha-start
   ```

2. **Try a transformation**: Open http://localhost:5173 and test the interface

3. **Check the logs**: If issues occur, check terminal output for errors

4. **Proceed with development**: The MVP is ready to use!
