#!/usr/bin/env bash

# CarScout AI - Daily Summary Report
# Generates a summary of scraping activity

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        📊 CarScout AI - Daily Summary Report                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Report Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Worker Performance
echo "### 1. Worker Performance (Last 24 Hours)"
echo ""

for i in 1 2 3 4; do
    LOG_FILE="$LOGS_DIR/worker_$i.log"
    
    case $i in
        1) BRANDS="Mercedes-Benz, BMW" ;;
        2) BRANDS="Audi, VW, Opel" ;;
        3) BRANDS="Ford, Toyota, Renault, Peugeot, Citroën" ;;
        4) BRANDS="Škoda, Seat, Honda, Mazda, Nissan, Hyundai, Kia, Volvo, Fiat, Alfa Romeo" ;;
    esac
    
    if [ -f "$LOG_FILE" ]; then
        # Count scraped items in last 24h
        SCRAPED=$(find "$LOG_FILE" -mtime -1 -exec grep -c "Scraped:" {} \; 2>/dev/null || echo "0")
        
        # Check for errors
        ERRORS=$(find "$LOG_FILE" -mtime -1 -exec grep -c "ERROR" {} \; 2>/dev/null || echo "0")
        
        echo "Worker $i ($BRANDS):"
        echo "  ✅ Listings scraped: $SCRAPED"
        echo "  ⚠️  Errors encountered: $ERRORS"
        echo ""
    fi
done

# 2. Good Deals Found
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "### 2. Good Deals Found (Score >= 7.5)"
echo ""

if [ -f "$LOGS_DIR/celery_worker.log" ]; then
    GOOD_DEALS=$(find "$LOGS_DIR/celery_worker.log" -mtime -1 -exec grep -c "Score: [7-9]\." {} \; 2>/dev/null || echo "0")
    echo "Total good deals found: $GOOD_DEALS"
    echo ""
    
    if [ $GOOD_DEALS -gt 0 ]; then
        echo "Recent high-scoring deals:"
        find "$LOGS_DIR/celery_worker.log" -mtime -1 -exec grep "Score: [7-9]\." {} \; 2>/dev/null | tail -5 || echo "None found"
        echo ""
    fi
else
    echo "Celery log not found"
    echo ""
fi

# 3. System Health
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "### 3. System Health"
echo ""

# Check if workers are currently running
RUNNING=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | wc -l | tr -d ' ')
echo "Active workers: $RUNNING / 4"

# Check Celery
CELERY=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l | tr -d ' ')
echo "Celery workers: $CELERY"

# Check supervisor
if ps aux | grep "supervisor.sh" | grep -v grep > /dev/null; then
    echo "Supervisor: ✅ Running"
else
    echo "Supervisor: ❌ Not running"
fi

echo ""

# 4. Disk Usage
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "### 4. Disk Usage"
echo ""

LOGS_SIZE=$(du -sh "$LOGS_DIR" 2>/dev/null | cut -f1 || echo "Unknown")
echo "Logs directory size: $LOGS_SIZE"

# List largest logs
echo ""
echo "Largest log files:"
ls -lh "$LOGS_DIR"/*.log 2>/dev/null | awk '{print $5, $9}' | sort -rh | head -5 || echo "No logs found"

echo ""

# 5. Alerts & Errors
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "### 5. Critical Issues (Last 24 Hours)"
echo ""

CRITICAL_ERRORS=0

# Check for critical errors in worker logs
for i in 1 2 3 4; do
    LOG_FILE="$LOGS_DIR/worker_$i.log"
    if [ -f "$LOG_FILE" ]; then
        WORKER_ERRORS=$(find "$LOG_FILE" -mtime -1 -exec grep -c "CRITICAL\|Traceback" {} \; 2>/dev/null || echo "0")
        if [ $WORKER_ERRORS -gt 0 ]; then
            echo "⚠️  Worker $i: $WORKER_ERRORS critical errors"
            CRITICAL_ERRORS=$((CRITICAL_ERRORS + WORKER_ERRORS))
        fi
    fi
done

if [ $CRITICAL_ERRORS -eq 0 ]; then
    echo "✅ No critical errors detected"
fi

echo ""

# 6. Recommendations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "### 6. Recommendations"
echo ""

# Check if logs need rotation
LOGS_SIZE_MB=$(du -sm "$LOGS_DIR" 2>/dev/null | cut -f1 || echo "0")
if [ $LOGS_SIZE_MB -gt 10000 ]; then
    echo "⚠️  Logs directory > 10GB - consider cleanup"
    echo "   Run: find logs/ -name '*.log' -mtime +7 -delete"
    echo ""
fi

# Check if workers have been running
if [ $RUNNING -eq 0 ]; then
    echo "⚠️  No workers currently running"
    echo "   Run: ./start_all_workers.sh"
    echo ""
fi

# Check supervisor
if ! ps aux | grep "supervisor.sh" | grep -v grep > /dev/null; then
    echo "💡 Consider starting supervisor for auto-recovery"
    echo "   Run: nohup ./supervisor.sh > logs/supervisor.log 2>&1 &"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Report generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
