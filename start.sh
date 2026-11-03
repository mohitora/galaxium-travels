#!/bin/bash

# Galaxium Travels - Start Script
# Starts both backend and frontend servers

echo "🚀 Starting Galaxium Travels..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if uv is installed (used for Python env management)
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' is not installed. Please install it with: brew install uv"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${BLUE}📡 Starting Backend Server...${NC}"
cd booking_system_backend

# Create venv with Python 3.11+ via uv and install dependencies
uv sync --python 3.11 --quiet 2>/dev/null || uv venv --python 3.11 .venv && uv pip install -q -r requirements.txt

# Activate virtual environment
source .venv/bin/activate

# Start backend server in background
python server.py &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}✅ Backend started on http://localhost:8080${NC}"
echo ""

# Wait a moment for backend to start
sleep 2

# Start Frontend
echo -e "${BLUE}🎨 Starting Frontend Server...${NC}"
cd booking_system_frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start frontend server in background
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✅ Frontend started on http://localhost:5173${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌟 Galaxium Travels is running!"
echo ""
echo "   Backend:  http://localhost:8080"
echo "   Frontend: http://localhost:5173"
echo "   API Docs: http://localhost:8080/docs"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID

# Made with Bob
