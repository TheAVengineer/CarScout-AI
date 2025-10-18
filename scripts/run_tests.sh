#!/usr/bin/env bash
# Quick Test Runner
# Runs all tests in sequence and reports results

set -e

# Detect Python command (python3 on macOS, python on Linux)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

echo "🧪 CarScout AI - Quick Test Suite"
echo "=================================="
echo "Using Python: $PYTHON_CMD"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if services are running
echo "📋 Checking services..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services not running. Starting...${NC}"
    docker-compose up -d
    sleep 10
fi
echo -e "${GREEN}✅ Services running${NC}"
echo ""

# Test 1: Setup verification
echo "1️⃣  Testing setup..."
if $PYTHON_CMD scripts/test_setup.py; then
    echo -e "${GREEN}✅ Setup test passed${NC}"
else
    echo -e "${RED}❌ Setup test failed${NC}"
    exit 1
fi
echo ""

# Test 2: Pipeline test
echo "2️⃣  Testing pipeline..."
if $PYTHON_CMD scripts/test_pipeline.py; then
    echo -e "${GREEN}✅ Pipeline test passed${NC}"
else
    echo -e "${RED}❌ Pipeline test failed${NC}"
    exit 1
fi
echo ""

# Test 3: Alert matcher test
echo "3️⃣  Testing alert matcher..."
if $PYTHON_CMD scripts/test_alert_matcher.py; then
    echo -e "${GREEN}✅ Alert matcher test passed${NC}"
else
    echo -e "${RED}❌ Alert matcher test failed${NC}"
    exit 1
fi
echo ""

# Summary
echo "=================================="
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test with real data: docker-compose exec worker scrapy crawl mobile_bg -a pages=1"
echo "  2. Monitor in Flower: open http://localhost:5555"
echo "  3. Check database: docker-compose exec db psql -U carscout_user -d carscout_db"
echo ""
