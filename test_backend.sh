#!/bin/bash

echo "🧪 Testing Backend Configuration..."
echo ""

cd backend

# Activate venv
source venv/bin/activate

# Start server in background
echo "Starting backend server..."
python main.py > /tmp/humanizer_test.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test health endpoint
echo "Testing health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
echo "Health check: $HEALTH"

# Test root endpoint  
echo ""
echo "Testing root endpoint..."
ROOT=$(curl -s http://localhost:8000/ | jq -r '.name')
echo "API Name: $ROOT"

# Kill server
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo ""
echo "✅ Backend configuration test complete!"
echo ""
echo "To run full stack:"
echo "  ./start.sh"
