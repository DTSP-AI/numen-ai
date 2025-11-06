#!/bin/bash

# HypnoAgent Installation Script
# Installs all dependencies for backend and frontend

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  HypnoAgent Installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo -e "${RED}ERROR: Python 3.11+ is required. Found: $PYTHON_VERSION${NC}"
    echo "Please install Python 3.11 or higher."
    exit 1
fi

echo -e "${GREEN}Python version OK: $PYTHON_VERSION${NC}"
echo ""

# Check Node version
echo -e "${BLUE}Checking Node.js version...${NC}"
NODE_VERSION=$(node --version 2>&1)

if ! command -v node &> /dev/null; then
    echo -e "${RED}ERROR: Node.js is not installed.${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org"
    exit 1
fi

echo -e "${GREEN}Node.js version OK: $NODE_VERSION${NC}"
echo ""

# Check if .env exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}WARNING: .env file not found.${NC}"
    echo "Copying .env.example to .env..."
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo -e "${GREEN}Done! Please edit .env with your credentials.${NC}"
    echo ""
fi

# Install backend dependencies
echo -e "${BLUE}Installing backend dependencies...${NC}"
cd "$PROJECT_ROOT/backend"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

echo -e "${GREEN}Backend dependencies installed!${NC}"
echo ""

# Install frontend dependencies
echo -e "${BLUE}Installing frontend dependencies...${NC}"
cd "$PROJECT_ROOT/frontend"

echo "Installing npm packages..."
npm install

echo -e "${GREEN}Frontend dependencies installed!${NC}"
echo ""

# Create necessary directories
echo -e "${BLUE}Creating necessary directories...${NC}"
mkdir -p "$PROJECT_ROOT/backend/audio_files"
mkdir -p "$PROJECT_ROOT/backend/avatars"
mkdir -p "$PROJECT_ROOT/backend/prompts"

echo -e "${GREEN}Directories created!${NC}"
echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "   - SUPABASE_DB_URL (required)"
echo "   - OPENAI_API_KEY (required)"
echo "   - Optional: ELEVENLABS_API_KEY, DEEPGRAM_API_KEY, LIVEKIT_*"
echo ""
echo "2. Start development servers:"
echo "   ./scripts/dev.sh"
echo ""
echo "3. Visit:"
echo "   - Frontend: http://localhost:3003"
echo "   - Backend API: http://localhost:8003/docs"
echo "   - Health Check: http://localhost:8003/health"
echo ""
