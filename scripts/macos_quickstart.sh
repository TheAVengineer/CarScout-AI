#!/usr/bin/env bash
# macOS Quick Start Script
# Handles Docker Desktop and Python 3 on macOS

set -e

echo "🚀 CarScout AI - macOS Quick Start"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python not found${NC}"
    echo "Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi
echo ""

# Check if Docker Desktop is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Docker is not running${NC}"
    echo "Starting Docker Desktop..."
    open -a Docker
    
    echo "Waiting for Docker to start (this may take 30-60 seconds)..."
    for i in {1..30}; do
        if docker info &> /dev/null 2>&1; then
            echo -e "${GREEN}✅ Docker is running${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    echo ""
    
    if ! docker info &> /dev/null 2>&1; then
        echo -e "${RED}❌ Docker failed to start${NC}"
        echo "Please start Docker Desktop manually and try again"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Docker is running${NC}"
fi
echo ""

# Start services
echo "📦 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 15
echo ""

# Check service health
echo "🔍 Checking services..."
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Services are running${NC}"
    docker-compose ps
else
    echo -e "${RED}❌ Some services failed to start${NC}"
    docker-compose ps
    exit 1
fi
echo ""

# Install Python dependencies if needed
echo "📦 Checking Python dependencies..."
if ! $PYTHON_CMD -c "import sqlalchemy" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Installing Python dependencies...${NC}"
    $PYTHON_CMD -m pip install -e ".[dev]" || {
        echo -e "${YELLOW}⚠️  pip install failed, trying with --user flag${NC}"
        $PYTHON_CMD -m pip install --user -e ".[dev]"
    }
else
    echo -e "${GREEN}✅ Dependencies installed${NC}"
fi
echo ""

# Run setup test
echo "🧪 Running setup test..."
if $PYTHON_CMD scripts/test_setup.py; then
    echo ""
    echo "=================================="
    echo -e "${GREEN}✅ Setup complete! You're ready to go!${NC}"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "  1. Run full tests: ./scripts/run_tests.sh"
    echo "  2. Monitor tasks: open http://localhost:5555"
    echo "  3. View cheatsheet: ./scripts/testing_cheatsheet.sh"
    echo ""
else
    echo ""
    echo "=================================="
    echo -e "${RED}❌ Setup test failed${NC}"
    echo "=================================="
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check logs: docker-compose logs -f"
    echo "  2. Restart services: docker-compose restart"
    echo "  3. Read QUICK-START.md for help"
    echo ""
    exit 1
fi
