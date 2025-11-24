#!/bin/bash

# CarScout AI - Real-Time Monitoring Dashboard
# Shows live scraping progress, system metrics, and ETA

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Function to get items scraped from log
get_items_scraped() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        grep -o "item_scraped_count.*[0-9]*" "$log_file" | tail -1 | grep -o "[0-9]*" || echo "0"
    else
        echo "0"
    fi
}

# Function to get current page from log
get_current_page() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        tail -20 "$log_file" | grep -o "page [0-9]*" | tail -1 | grep -o "[0-9]*" || echo "?"
    else
        echo "?"
    fi
}

# Function to get current brand from log
get_current_brand() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        tail -20 "$log_file" | grep -E "Following|Scraped:" | tail -1 | grep -oE "(Mercedes-Benz|BMW|Audi|VW|Volkswagen|Opel|Ford|Toyota|Renault|Peugeot|Citroën|Škoda|Seat|Honda|Mazda|Nissan|Hyundai|Kia|Volvo|Fiat|Alfa Romeo)" | head -1 || echo "..."
    else
        echo "..."
    fi
}

# Function to calculate scraping rate
get_scraping_rate() {
    local log_file=$1
    if [ -f "$log_file" ]; then
        # Count "Scraped:" entries in last 60 lines (roughly last minute)
        local count=$(tail -60 "$log_file" | grep -c "Scraped:" || echo "0")
        echo "$count"
    else
        echo "0"
    fi
}

# Function to get worker uptime
get_worker_uptime() {
    local worker_num=$1
    local log_file="$LOGS_DIR/worker_${worker_num}.log"
    
    if [ -f "$log_file" ]; then
        # Get first timestamp from log
        local start_time=$(head -1 "$log_file" | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}" | head -1)
        if [ ! -z "$start_time" ]; then
            local start_epoch=$(date -j -f "%Y-%m-%d %H:%M:%S" "$start_time" +%s 2>/dev/null || echo "0")
            local current_epoch=$(date +%s)
            local uptime_seconds=$((current_epoch - start_epoch))
            
            # Format uptime
            local hours=$((uptime_seconds / 3600))
            local minutes=$(((uptime_seconds % 3600) / 60))
            echo "${hours}h ${minutes}m"
        else
            echo "?"
        fi
    else
        echo "?"
    fi
}

# Function to estimate completion time
estimate_completion() {
    local items_scraped=$1
    local uptime_minutes=$2
    local target_items=2000
    
    if [ $items_scraped -gt 0 ] && [ $uptime_minutes -gt 0 ]; then
        local rate=$(echo "scale=2; $items_scraped / $uptime_minutes" | bc)
        local remaining=$((target_items - items_scraped))
        
        if [ $remaining -gt 0 ]; then
            local eta_minutes=$(echo "scale=0; $remaining / $rate" | bc)
            local eta_hours=$((eta_minutes / 60))
            local eta_mins=$((eta_minutes % 60))
            echo "${eta_hours}h ${eta_mins}m"
        else
            echo "Complete"
        fi
    else
        echo "Calculating..."
    fi
}

# Clear screen and show dashboard
clear

echo -e "${BOLD}${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    🚀 CarScout AI - Live Monitoring Dashboard                 ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if workers are running
RUNNING=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | wc -l | tr -d ' ')

if [ "$RUNNING" -eq 0 ]; then
    echo -e "${RED}${BOLD}❌ No workers are currently running${NC}"
    echo ""
    echo "Start workers with: ./start_all_workers.sh"
    exit 0
fi

echo -e "${GREEN}${BOLD}Active Workers: $RUNNING / 4${NC}"
echo ""

# Worker details
echo -e "${CYAN}${BOLD}Worker Status:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "%-10s %-30s %-10s %-10s %-12s %-12s %s\n" "Worker" "Brands" "Items" "Page" "Rate/min" "Uptime" "ETA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TOTAL_ITEMS=0
TOTAL_RATE=0

for i in 1 2 3 4; do
    LOG_FILE="$LOGS_DIR/worker_$i.log"
    
    case $i in
        1) BRANDS="Mercedes, BMW" ;;
        2) BRANDS="Audi, VW, Opel" ;;
        3) BRANDS="Ford, Toyota, Renault, +" ;;
        4) BRANDS="Škoda, Seat, Honda, +" ;;
    esac
    
    # Check if worker log exists and has recent activity (within 5 minutes)
    WORKER_RUNNING=false
    if [ -f "$LOG_FILE" ]; then
        LOG_AGE=$(( $(date +%s) - $(stat -f %m "$LOG_FILE" 2>/dev/null || stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0) ))
        if [ $LOG_AGE -lt 300 ]; then
            WORKER_RUNNING=true
        fi
    fi
    
    if [ "$WORKER_RUNNING" = true ]; then
        ITEMS=$(get_items_scraped "$LOG_FILE")
        PAGE=$(get_current_page "$LOG_FILE")
        RATE=$(get_scraping_rate "$LOG_FILE")
        UPTIME=$(get_worker_uptime $i)
        
        # Calculate ETA (rough estimate)
        if [ "$ITEMS" -gt 0 ]; then
            PROGRESS=$((ITEMS * 100 / 2000))
            if [ $PROGRESS -ge 100 ]; then
                ETA="✅ Done"
                ITEMS_COLOR=$GREEN
            else
                ETA="~4-6h"
                ITEMS_COLOR=$YELLOW
            fi
        else
            ETA="Starting..."
            ITEMS_COLOR=$YELLOW
        fi
        
        TOTAL_ITEMS=$((TOTAL_ITEMS + ITEMS))
        TOTAL_RATE=$((TOTAL_RATE + RATE))
        
        printf "${ITEMS_COLOR}%-10s${NC} %-30s ${YELLOW}%-10s${NC} ${CYAN}%-10s${NC} ${MAGENTA}%-12s${NC} ${BLUE}%-12s${NC} %s\n" \
            "Worker $i" "$BRANDS" "$ITEMS" "p.$PAGE" "$RATE items" "$UPTIME" "$ETA"
    else
        printf "${RED}%-10s %-30s %-10s %-10s %-12s %-12s %s${NC}\n" \
            "Worker $i" "$BRANDS" "❌ Stopped" "-" "-" "-" "-"
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
printf "${BOLD}%-10s %-30s ${GREEN}%-10s${NC} %-10s ${MAGENTA}%-12s${NC} %-12s %s\n" \
    "TOTAL" "All 20 brands" "$TOTAL_ITEMS" "-" "$TOTAL_RATE items" "-" "~6-7h"
echo ""

# System resources
echo -e "${CYAN}${BOLD}System Resources:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get CPU and Memory
CPU_LINE=$(top -l 1 | grep "CPU usage:")
MEM_LINE=$(top -l 1 | grep "PhysMem:")

echo "$CPU_LINE" | sed 's/CPU usage:/  CPU:/'
echo "$MEM_LINE" | sed 's/PhysMem:/  Memory:/'

# Get load average
LOAD=$(top -l 1 | grep "Load Avg:" | awk '{print $3, $4, $5}')
echo "  Load Avg: $LOAD"

echo ""

# Database stats (if accessible)
echo -e "${CYAN}${BOLD}Database Activity:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count recent database operations in logs
INSERTS=$(tail -100 $LOGS_DIR/worker_*.log 2>/dev/null | grep -c "INSERT" || echo "?")
UPDATES=$(tail -100 $LOGS_DIR/worker_*.log 2>/dev/null | grep -c "UPDATE" || echo "?")

echo "  Recent DB Operations: $INSERTS inserts, $UPDATES updates (last 100 log lines)"

# Check Celery
CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l | tr -d ' ')
echo "  Celery Workers: $CELERY_COUNT active"

echo ""

# Recent good deals
echo -e "${CYAN}${BOLD}Recent Activity:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Show last 5 scraped items
echo -e "${GREEN}Last 5 Scraped:${NC}"
tail -200 $LOGS_DIR/worker_*.log 2>/dev/null | grep "Scraped:" | tail -5 | sed 's/.*INFO: ✅ Scraped:/  →/' | sed 's/^/  /'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Refresh: ./monitor.sh  |  Status: ./status_workers.sh  |  Stop: ./stop_all_workers.sh${NC}"
echo ""
