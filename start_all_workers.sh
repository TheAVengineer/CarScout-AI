#!/bin/bash

# CarScout AI - Start All Workers Script
# Starts 4 parallel workers to scrape all 20 brands from Mobile.bg

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKERS_DIR="$SCRIPT_DIR/workers/scrape"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting CarScout AI Workers...${NC}"
echo ""

# Check if workers are already running
RUNNING=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | wc -l | tr -d ' ')
if [ "$RUNNING" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: $RUNNING worker(s) already running!${NC}"
    echo "Please stop them first with: ./stop_all_workers.sh"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Start Worker 1 (Mercedes-Benz, BMW - High Volume)
echo -e "${GREEN}▶ Starting Worker 1${NC} (Mercedes-Benz, BMW)..."
cd "$WORKERS_DIR"
export HYBRID_CONFIG_PATH="$SCRIPT_DIR/mobile_bg_worker_1.json"
nohup ../../.venv/bin/scrapy crawl mobile_bg -a skip_login=true -a target_listings=2000 \
    > "$LOGS_DIR/worker_1.log" 2>&1 &
WORKER1_PID=$!
echo "   PID: $WORKER1_PID"

sleep 2

# Start Worker 2 (Audi, VW, Opel - Medium Volume)
echo -e "${GREEN}▶ Starting Worker 2${NC} (Audi, VW, Opel)..."
export HYBRID_CONFIG_PATH="$SCRIPT_DIR/mobile_bg_worker_2.json"
nohup ../../.venv/bin/scrapy crawl mobile_bg -a skip_login=true -a target_listings=2000 \
    > "$LOGS_DIR/worker_2.log" 2>&1 &
WORKER2_PID=$!
echo "   PID: $WORKER2_PID"

sleep 2

# Start Worker 3 (Ford, Toyota, Renault, Peugeot, Citroën - Medium Volume)
echo -e "${GREEN}▶ Starting Worker 3${NC} (Ford, Toyota, Renault, Peugeot, Citroën)..."
export HYBRID_CONFIG_PATH="$SCRIPT_DIR/mobile_bg_worker_3.json"
nohup ../../.venv/bin/scrapy crawl mobile_bg -a skip_login=true -a target_listings=2000 \
    > "$LOGS_DIR/worker_3.log" 2>&1 &
WORKER3_PID=$!
echo "   PID: $WORKER3_PID"

sleep 2

# Start Worker 4 (Remaining 10 brands - Lower Volume)
echo -e "${GREEN}▶ Starting Worker 4${NC} (Škoda, Seat, Honda, Mazda, Nissan, Hyundai, Kia, Volvo, Fiat, Alfa Romeo)..."
export HYBRID_CONFIG_PATH="$SCRIPT_DIR/mobile_bg_worker_4.json"
nohup ../../.venv/bin/scrapy crawl mobile_bg -a skip_login=true -a target_listings=2000 \
    > "$LOGS_DIR/worker_4.log" 2>&1 &
WORKER4_PID=$!
echo "   PID: $WORKER4_PID"

echo ""
echo -e "${GREEN}✅ All 4 workers started successfully!${NC}"
echo ""
echo "Worker PIDs saved to: $LOGS_DIR/worker_pids.txt"
echo "$WORKER1_PID" > "$LOGS_DIR/worker_pids.txt"
echo "$WORKER2_PID" >> "$LOGS_DIR/worker_pids.txt"
echo "$WORKER3_PID" >> "$LOGS_DIR/worker_pids.txt"
echo "$WORKER4_PID" >> "$LOGS_DIR/worker_pids.txt"

echo ""
echo "📊 Monitor progress with:"
echo "   ./status_workers.sh"
echo ""
echo "🛑 Stop all workers with:"
echo "   ./stop_all_workers.sh"
echo ""
echo -e "${BLUE}🎯 Expected completion: 6-7 hours${NC}"
echo -e "${BLUE}📱 Good deals will be posted to your Telegram channel${NC}"
