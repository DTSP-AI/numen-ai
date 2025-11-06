#!/bin/bash

# HypnoAgent Development Server Startup Script
# Starts both backend and frontend in parallel

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  HypnoAgent Development Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your credentials."
    echo ""
    echo "Run: cp .env.example .env"
    exit 1
fi

# Check if backend dependencies are installed
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    echo -e "${RED}WARNING: Backend virtual environment not found.${NC}"
    echo "Run: scripts/install.sh first"
    echo ""
fi

# Check if frontend dependencies are installed
if [ ! -d "$PROJECT_ROOT/frontend/node_modules" ]; then
    echo -e "${RED}WARNING: Frontend node_modules not found.${NC}"
    echo "Run: scripts/install.sh first"
    echo ""
fi

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Shutting down servers...${NC}"
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start backend
echo -e "${GREEN}Starting backend on port 8003...${NC}"
cd "$PROJECT_ROOT/backend"

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
fi

# Start backend in background
uvicorn main:app --reload --port 8003 --host 0.0.0.0 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start frontend
echo -e "${GREEN}Starting frontend on port 3003...${NC}"
cd "$PROJECT_ROOT/frontend"

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

# Display info
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Services Started Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Backend API:      ${BLUE}http://localhost:8003${NC}"
echo -e "API Docs:         ${BLUE}http://localhost:8003/docs${NC}"
echo -e "Health Check:     ${BLUE}http://localhost:8003/health${NC}"
echo ""
echo -e "Frontend:         ${BLUE}http://localhost:3003${NC}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop all services${NC}"
echo ""

# Wait for both processes
wait
