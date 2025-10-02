#!/bin/bash

# Humanizer Agent - Quick Start Script

echo "🎭 Humanizer Agent - Quick Start"
echo "================================"
echo ""

# Check if running from project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the humanizer-agent directory"
    exit 1
fi

# Check for Python 3.11
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Error: Python 3.11 is not installed"
    echo "   Install with: brew install python@3.11"
    exit 1
fi

echo "✅ Found Python 3.11: $(python3.11 --version)"

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    exit 1
fi

# Check for Anthropic API key with proper hierarchy
# Priority: 1) Environment variable, 2) macOS Keychain, 3) .env file
if [ -z "$ANTHROPIC_API_KEY" ]; then
    # Try to retrieve from macOS keychain
    echo "🔑 Checking macOS Keychain for Anthropic API key..."
    KEYCHAIN_KEY=$(security find-generic-password -w -s "anthropic-api-key" -a "$USER" 2>/dev/null)
    
    if [ -n "$KEYCHAIN_KEY" ]; then
        export ANTHROPIC_API_KEY="$KEYCHAIN_KEY"
        echo "✅ Found API key in macOS Keychain"
    else
        echo "ℹ️  API key not found in Keychain, will check .env file"
        # Check if .env exists and has the key
        if [ -f "backend/.env" ] && grep -q "ANTHROPIC_API_KEY=sk-ant-" "backend/.env" 2>/dev/null; then
            echo "✅ Found API key in .env file"
        else
            echo "⚠️  Warning: ANTHROPIC_API_KEY not found"
            echo ""
            echo "   To store securely in macOS Keychain:"
            echo "   security add-generic-password -s 'anthropic-api-key' -a '$USER' -w 'your-key-here'"
            echo ""
            echo "   Or export as environment variable:"
            echo "   export ANTHROPIC_API_KEY='your-key-here'"
            echo ""
            echo "   Or add to backend/.env file"
            echo ""
            read -p "Do you want to continue anyway? (y/n) " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
else
    echo "✅ Using ANTHROPIC_API_KEY from environment"
fi

echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist, using Python 3.11
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment with Python 3.11..."
    python3.11 -m venv venv
else
    # Check if existing venv uses Python 3.11
    if [ -f "venv/bin/python" ]; then
        venv_version=$(venv/bin/python --version 2>&1)
        if [[ ! $venv_version =~ "3.11" ]]; then
            echo "   Removing old venv (wrong Python version: $venv_version)..."
            rm -rf venv
            echo "   Creating new virtual environment with Python 3.11..."
            python3.11 -m venv venv
        fi
    fi
fi

# Activate virtual environment
source venv/bin/activate

# Verify we're using Python 3.11
current_python=$(python --version 2>&1)
echo "   Using: $current_python"

# Install dependencies
echo "   Installing Python dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "   Creating .env file..."
    cp .env.example .env
    if [ -n "$ANTHROPIC_API_KEY" ]; then
        echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> .env
    fi
fi

cd ..

echo "📦 Setting up frontend..."
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "   Installing Node dependencies..."
    npm install
fi

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting servers..."
echo ""

# Start backend in background
echo "   Starting backend on http://localhost:8000"
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "   Starting frontend on http://localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "================================"
echo "✨ Humanizer Agent is running!"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo "================================"
echo ""

# Wait for user interrupt
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT

# Keep script running
wait
