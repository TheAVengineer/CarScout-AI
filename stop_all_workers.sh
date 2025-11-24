#!/bin/bash

# CarScout AI - Stop All Workers Script
# Gracefully stops all running scrapy workers

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 Stopping CarScout AI Workers...${NC}"
echo ""

# Find all running scrapy processes
PIDS=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}No workers are currently running.${NC}"
    exit 0
fi

# Count workers
WORKER_COUNT=$(echo "$PIDS" | wc -l | tr -d ' ')
echo "Found $WORKER_COUNT running worker(s)"
echo ""

# Kill each process
for PID in $PIDS; do
    echo -e "${YELLOW}Stopping worker PID: $PID${NC}"
    kill $PID 2>/dev/null || echo "  (Process already stopped)"
done

# Wait a moment for graceful shutdown
sleep 2

# Check if any are still running
REMAINING=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | wc -l | tr -d ' ')

if [ "$REMAINING" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}Some workers didn't stop gracefully. Force killing...${NC}"
    pkill -9 -f "scrapy crawl mobile_bg" 2>/dev/null || true
    sleep 1
fi

# Verify all stopped
FINAL_CHECK=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | wc -l | tr -d ' ')

if [ "$FINAL_CHECK" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All workers stopped successfully!${NC}"
    
    # Clean up PID file
    if [ -f "$LOGS_DIR/worker_pids.txt" ]; then
        rm "$LOGS_DIR/worker_pids.txt"
        echo "Cleaned up PID tracking file"
    fi
else
    echo ""
    echo -e "${RED}❌ Warning: Some workers may still be running${NC}"
    echo "Check with: ps aux | grep scrapy"
fi
