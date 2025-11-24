#!/bin/bash

# CarScout AI - Celery Management Script
# Manages Celery workers with proper resource limits

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
VENV="$SCRIPT_DIR/.venv"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

case "$1" in
    start)
        echo -e "${BLUE}Starting Celery worker...${NC}"
        
        # Kill any existing Celery workers first
        echo "Stopping existing Celery workers..."
        pkill -f "celery.*worker" 2>/dev/null || true
        sleep 2
        
        # Start optimized Celery worker
        echo "Starting optimized Celery worker (4 concurrent tasks)..."
        cd "$SCRIPT_DIR"
        nohup "$VENV/bin/celery" -A workers.pipeline.celery_app worker \
            --loglevel=info \
            --logfile="$LOGS_DIR/celery_worker.log" \
            --concurrency=4 \
            --max-tasks-per-child=100 \
            --time-limit=600 \
            > "$LOGS_DIR/celery_startup.log" 2>&1 &
        
        sleep 3
        
        # Check if started
        if ps aux | grep -v grep | grep -q "celery.*worker"; then
            echo -e "${GREEN}✅ Celery worker started successfully${NC}"
            echo "  Concurrency: 4 tasks (optimized for 4 Scrapy workers)"
            echo "  Max tasks per child: 100 (prevents memory leaks)"
            echo "  Time limit: 600s (10 min per task)"
        else
            echo -e "${RED}❌ Failed to start Celery worker${NC}"
            echo "Check logs: tail -f $LOGS_DIR/celery_startup.log"
            exit 1
        fi
        ;;
        
    stop)
        echo -e "${RED}Stopping all Celery workers...${NC}"
        
        PIDS=$(ps aux | grep "celery.*worker" | grep -v grep | awk '{print $2}')
        
        if [ -z "$PIDS" ]; then
            echo "No Celery workers running"
            exit 0
        fi
        
        COUNT=$(echo "$PIDS" | wc -l | tr -d ' ')
        echo "Found $COUNT Celery worker(s)"
        
        # Graceful shutdown
        for PID in $PIDS; do
            echo "Stopping PID $PID..."
            kill $PID 2>/dev/null || true
        done
        
        sleep 3
        
        # Force kill if still running
        REMAINING=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l | tr -d ' ')
        if [ "$REMAINING" -gt 0 ]; then
            echo "Force killing remaining workers..."
            pkill -9 -f "celery.*worker" 2>/dev/null || true
        fi
        
        echo -e "${GREEN}✅ All Celery workers stopped${NC}"
        ;;
        
    restart)
        echo "Restarting Celery worker..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        echo -e "${BLUE}Celery Worker Status:${NC}"
        echo ""
        
        COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l | tr -d ' ')
        
        if [ "$COUNT" -eq 0 ]; then
            echo -e "${RED}❌ No Celery workers running${NC}"
            echo ""
            echo "Start with: ./celery.sh start"
        else
            echo -e "${GREEN}✅ $COUNT Celery worker process(es) running${NC}"
            
            if [ "$COUNT" -gt 4 ]; then
                echo -e "${YELLOW}⚠️  Warning: Too many Celery workers!${NC}"
                echo "   Recommended: 1 main worker (4 concurrent tasks)"
                echo "   Restart with: ./celery.sh restart"
            fi
            
            echo ""
            echo "Processes:"
            ps aux | grep "celery.*worker" | grep -v grep | awk '{printf "  PID: %s | CPU: %s%% | Mem: %s%%\n", $2, $3, $4}'
            
            echo ""
            echo "Recent activity:"
            tail -10 "$LOGS_DIR/celery_worker.log" | grep -E "Task|Received" | tail -3 || echo "  No recent activity"
        fi
        ;;
        
    clean)
        echo -e "${YELLOW}Cleaning up duplicate/zombie Celery workers...${NC}"
        
        # Kill all celery processes
        pkill -9 -f "celery.*worker" 2>/dev/null || true
        
        # Clean up any stale PID files
        rm -f "$LOGS_DIR/celery*.pid" 2>/dev/null || true
        
        # Truncate old log if it's huge
        if [ -f "$LOGS_DIR/celery_worker.log" ]; then
            SIZE=$(du -k "$LOGS_DIR/celery_worker.log" | cut -f1)
            if [ $SIZE -gt 10000 ]; then
                echo "Rotating large log file..."
                mv "$LOGS_DIR/celery_worker.log" "$LOGS_DIR/celery_worker.log.old"
                touch "$LOGS_DIR/celery_worker.log"
            fi
        fi
        
        echo -e "${GREEN}✅ Cleanup complete${NC}"
        echo ""
        echo "Start fresh with: ./celery.sh start"
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start optimized Celery worker (4 concurrent tasks)"
        echo "  stop    - Stop all Celery workers"
        echo "  restart - Restart Celery worker"
        echo "  status  - Show Celery worker status"
        echo "  clean   - Kill all Celery workers and clean up"
        echo ""
        exit 1
        ;;
esac
