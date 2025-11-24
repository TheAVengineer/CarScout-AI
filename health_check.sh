#!/bin/bash

# CarScout AI - System Health Check
# Comprehensive system diagnostics

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           🏥 CarScout AI - System Health Check                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

ISSUES=0
WARNINGS=0

# Check Scrapy Workers
echo -e "${BOLD}1. Scrapy Workers:${NC}"
SCRAPY_COUNT=$(ps aux | grep "scrapy crawl mobile_bg" | grep -v grep | wc -l | tr -d ' ')
if [ "$SCRAPY_COUNT" -eq 4 ]; then
    echo -e "  ${GREEN}✅ All 4 workers running${NC}"
elif [ "$SCRAPY_COUNT" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  Only $SCRAPY_COUNT/4 workers running${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${RED}❌ No workers running${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check Celery Workers
echo -e "${BOLD}2. Celery Workers:${NC}"
CELERY_COUNT=$(ps aux | grep "celery.*worker" | grep -v grep | wc -l | tr -d ' ')
if [ "$CELERY_COUNT" -eq 1 ] || [ "$CELERY_COUNT" -eq 2 ]; then
    echo -e "  ${GREEN}✅ Celery running (${CELERY_COUNT} process)${NC}"
elif [ "$CELERY_COUNT" -gt 2 ]; then
    echo -e "  ${YELLOW}⚠️  Too many Celery workers: $CELERY_COUNT${NC}"
    echo "     Run: ./celery.sh restart"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${RED}❌ Celery not running${NC}"
    echo "     Run: ./celery.sh start"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check Database Connection
echo -e "${BOLD}3. Database:${NC}"
if [ -n "$DATABASE_URL" ]; then
    echo -e "  ${GREEN}✅ DATABASE_URL configured${NC}"
else
    echo -e "  ${YELLOW}⚠️  DATABASE_URL not set in environment${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# Check recent database activity
RECENT_DB=$(tail -100 $LOGS_DIR/worker_*.log 2>/dev/null | grep -c "INSERT\|UPDATE" || echo "0")
if [ "$RECENT_DB" -gt 0 ]; then
    echo -e "  ${GREEN}✅ Database active (${RECENT_DB} operations in recent logs)${NC}"
else
    echo -e "  ${YELLOW}⚠️  No recent database activity${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check Disk Space
echo -e "${BOLD}4. Disk Space:${NC}"
DISK_USAGE=$(df -h "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "  ${GREEN}✅ Disk usage: ${DISK_USAGE}%${NC}"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "  ${YELLOW}⚠️  Disk usage: ${DISK_USAGE}%${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${RED}❌ Disk usage critical: ${DISK_USAGE}%${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check Log Files
echo -e "${BOLD}5. Log Files:${NC}"
if [ -d "$LOGS_DIR" ]; then
    LOG_SIZE=$(du -sh "$LOGS_DIR" | cut -f1)
    LOG_COUNT=$(ls "$LOGS_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${GREEN}✅ Logs directory exists${NC}"
    echo "     Size: $LOG_SIZE | Files: $LOG_COUNT"
    
    # Check if any logs are huge
    LARGE_LOGS=$(find "$LOGS_DIR" -name "*.log" -size +100M 2>/dev/null)
    if [ -n "$LARGE_LOGS" ]; then
        echo -e "  ${YELLOW}⚠️  Large log files found (>100MB):${NC}"
        echo "$LARGE_LOGS" | sed 's/^/     /'
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "  ${RED}❌ Logs directory missing${NC}"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check System Resources
echo -e "${BOLD}6. System Resources:${NC}"
CPU_IDLE=$(top -l 1 | grep "CPU usage:" | awk '{print $7}' | sed 's/%//')
MEM_UNUSED=$(top -l 1 | grep "PhysMem:" | awk '{print $10}' | sed 's/[MG].*//')

# Check if CPU is reasonable
if [ $(echo "$CPU_IDLE > 30" | bc) -eq 1 ]; then
    echo -e "  ${GREEN}✅ CPU healthy (${CPU_IDLE}% idle)${NC}"
elif [ $(echo "$CPU_IDLE > 10" | bc) -eq 1 ]; then
    echo -e "  ${YELLOW}⚠️  CPU under load (${CPU_IDLE}% idle)${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${RED}❌ CPU overloaded (${CPU_IDLE}% idle)${NC}"
    ISSUES=$((ISSUES + 1))
fi

# Memory check (simplified - just show status)
echo "     Memory available: ${MEM_UNUSED}M"
echo ""

# Check Worker Logs for Errors
echo -e "${BOLD}7. Recent Errors:${NC}"
ERROR_COUNT=$(tail -500 $LOGS_DIR/worker_*.log 2>/dev/null | grep -c "ERROR\|CRITICAL" || echo "0")
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✅ No recent errors${NC}"
elif [ "$ERROR_COUNT" -lt 10 ]; then
    echo -e "  ${YELLOW}⚠️  ${ERROR_COUNT} errors in recent logs${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${RED}❌ ${ERROR_COUNT} errors in recent logs${NC}"
    echo "     Check: tail -100 $LOGS_DIR/worker_*.log | grep ERROR"
    ISSUES=$((ISSUES + 1))
fi
echo ""

# Check if workers are making progress
echo -e "${BOLD}8. Worker Progress:${NC}"
RECENT_SCRAPES=$(tail -200 $LOGS_DIR/worker_*.log 2>/dev/null | grep -c "Scraped:" || echo "0")
if [ "$RECENT_SCRAPES" -gt 10 ]; then
    echo -e "  ${GREEN}✅ Workers actively scraping (${RECENT_SCRAPES} items in recent logs)${NC}"
elif [ "$RECENT_SCRAPES" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  Slow scraping rate (${RECENT_SCRAPES} items in recent logs)${NC}"
    WARNINGS=$((WARNINGS + 1))
elif [ "$SCRAPY_COUNT" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠️  Workers running but not scraping${NC}"
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "  ${BLUE}ℹ️  Workers not running${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ SYSTEM HEALTHY - All checks passed!${NC}"
elif [ $ISSUES -eq 0 ]; then
    echo -e "${YELLOW}${BOLD}⚠️  MINOR ISSUES - $WARNINGS warning(s)${NC}"
else
    echo -e "${RED}${BOLD}❌ ISSUES DETECTED - $ISSUES critical, $WARNINGS warnings${NC}"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Quick Actions
if [ $ISSUES -gt 0 ] || [ $WARNINGS -gt 0 ]; then
    echo -e "${BOLD}Quick Fixes:${NC}"
    
    if [ "$SCRAPY_COUNT" -eq 0 ]; then
        echo "  • Start workers: ./start_all_workers.sh"
    fi
    
    if [ "$CELERY_COUNT" -eq 0 ]; then
        echo "  • Start Celery: ./celery.sh start"
    elif [ "$CELERY_COUNT" -gt 2 ]; then
        echo "  • Fix Celery: ./celery.sh restart"
    fi
    
    if [ "$ERROR_COUNT" -gt 10 ]; then
        echo "  • Check errors: tail -100 $LOGS_DIR/worker_*.log | grep ERROR"
    fi
    
    echo ""
fi

echo "Full monitoring: ./monitor.sh"
echo "Worker status: ./status_workers.sh"
echo ""

# Exit with appropriate code
if [ $ISSUES -gt 0 ]; then
    exit 2
elif [ $WARNINGS -gt 0 ]; then
    exit 1
else
    exit 0
fi
