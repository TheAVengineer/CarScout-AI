#!/bin/bash

# CarScout AI - Worker Status Script
# Shows real-time status of all workers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}📊 CarScout AI - Worker Status${NC}"
echo "=================================="
echo ""

# Check if workers are running
RUNNING=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep)
WORKER_COUNT=$(echo "$RUNNING" | grep -c "scrapy" || echo "0")

if [ "$WORKER_COUNT" -eq 0 ]; then
    echo -e "${RED}❌ No workers are currently running${NC}"
    echo ""
    echo "Start workers with: ./start_all_workers.sh"
    exit 0
fi

echo -e "${GREEN}✅ Active Workers: $WORKER_COUNT${NC}"
echo ""

# Show worker processes
echo -e "${CYAN}Running Processes:${NC}"
ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | awk '{printf "  PID: %s | CPU: %s%% | Mem: %s%%\n", $2, $3, $4}'
echo ""

# Show progress from each worker log
echo -e "${CYAN}Worker Progress:${NC}"
echo ""

for i in 1 2 3 4; do
    LOG_FILE="$LOGS_DIR/worker_$i.log"
    
    if [ ! -f "$LOG_FILE" ]; then
        continue
    fi
    
    # Get worker brands
    case $i in
        1) BRANDS="Mercedes-Benz, BMW" ;;
        2) BRANDS="Audi, VW, Opel" ;;
        3) BRANDS="Ford, Toyota, Renault, Peugeot, Citroën" ;;
        4) BRANDS="Škoda, Seat, Honda, Mazda, Nissan, Hyundai, Kia, Volvo, Fiat, Alfa Romeo" ;;
    esac
    
    echo -e "${YELLOW}Worker $i${NC} ($BRANDS):"
    
    # Get latest scraping activity
    LATEST=$(tail -10 "$LOG_FILE" | grep -E "Scraped|Found.*page|item_scraped_count" | tail -2)
    
    if [ -z "$LATEST" ]; then
        echo "  Starting up..."
    else
        echo "$LATEST" | sed 's/^/  /'
    fi
    
    echo ""
done

# Show system resources
echo -e "${CYAN}System Resources:${NC}"
top -l 1 | head -10 | tail -6

echo ""
echo "=================================="
echo "Refresh with: ./status_workers.sh"
echo "Stop workers: ./stop_all_workers.sh"
