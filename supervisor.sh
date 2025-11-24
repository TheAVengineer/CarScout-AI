#!/bin/bash

# CarScout AI - Worker Supervisor
# Monitors all workers and auto-restarts them if they crash
# Run this in background: nohup ./supervisor.sh > logs/supervisor.log 2>&1 &

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
WORKERS_DIR="$SCRIPT_DIR/workers/scrape"
PID_FILE="$LOGS_DIR/supervisor.pid"
CHECK_INTERVAL=60  # Check every 60 seconds

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}"
}

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if supervisor is already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        log_error "Supervisor already running with PID $OLD_PID"
        exit 1
    else
        log_warning "Removing stale PID file"
        rm "$PID_FILE"
    fi
fi

# Save supervisor PID
echo $$ > "$PID_FILE"
log_info "Supervisor started with PID $$"

# Expected worker configurations
declare -A WORKER_CONFIGS
WORKER_CONFIGS[1]="$SCRIPT_DIR/mobile_bg_worker_1.json"
WORKER_CONFIGS[2]="$SCRIPT_DIR/mobile_bg_worker_2.json"
WORKER_CONFIGS[3]="$SCRIPT_DIR/mobile_bg_worker_3.json"
WORKER_CONFIGS[4]="$SCRIPT_DIR/mobile_bg_worker_4.json"

# Worker names for logging
declare -A WORKER_NAMES
WORKER_NAMES[1]="Mercedes-Benz, BMW"
WORKER_NAMES[2]="Audi, VW, Opel"
WORKER_NAMES[3]="Ford, Toyota, Renault, Peugeot, Citroën"
WORKER_NAMES[4]="Škoda, Seat, Honda, Mazda, Nissan, etc."

# Track worker restarts
declare -A RESTART_COUNT
declare -A LAST_RESTART_TIME

# Initialize restart counters
for i in 1 2 3 4; do
    RESTART_COUNT[$i]=0
    LAST_RESTART_TIME[$i]=0
done

# Function to check if worker is running
is_worker_running() {
    local worker_num=$1
    local config_path="${WORKER_CONFIGS[$worker_num]}"
    
    # Check if any process is using this config file
    if ps aux | grep "scrapy crawl mobile_bg" | grep -q "$config_path"; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to start a worker
start_worker() {
    local worker_num=$1
    local config_path="${WORKER_CONFIGS[$worker_num]}"
    local worker_name="${WORKER_NAMES[$worker_num]}"
    local log_file="$LOGS_DIR/worker_${worker_num}.log"
    
    log_info "Starting Worker $worker_num ($worker_name)..."
    
    cd "$WORKERS_DIR"
    export HYBRID_CONFIG_PATH="$config_path"
    nohup ../../.venv/bin/scrapy crawl mobile_bg -a skip_login=true -a target_listings=2000 \
        > "$log_file" 2>&1 &
    
    local worker_pid=$!
    
    # Wait a moment to ensure it started
    sleep 3
    
    if ps -p "$worker_pid" > /dev/null 2>&1; then
        log_success "Worker $worker_num started with PID $worker_pid"
        
        # Update restart tracking
        RESTART_COUNT[$worker_num]=$((RESTART_COUNT[$worker_num] + 1))
        LAST_RESTART_TIME[$worker_num]=$(date +%s)
        
        return 0
    else
        log_error "Worker $worker_num failed to start"
        return 1
    fi
}

# Function to check worker health
check_worker_health() {
    local worker_num=$1
    local log_file="$LOGS_DIR/worker_${worker_num}.log"
    
    # Check if log file exists
    if [ ! -f "$log_file" ]; then
        return 1  # Unhealthy
    fi
    
    # Check if log has recent activity (within last 5 minutes)
    local last_log_time=$(stat -f %m "$log_file" 2>/dev/null || stat -c %Y "$log_file" 2>/dev/null)
    local current_time=$(date +%s)
    local time_diff=$((current_time - last_log_time))
    
    if [ $time_diff -gt 300 ]; then
        log_warning "Worker $worker_num log not updated for $time_diff seconds"
        return 1  # Unhealthy
    fi
    
    # Check for error patterns in recent logs
    local recent_errors=$(tail -50 "$log_file" | grep -E "ERROR|CRITICAL|Traceback" | wc -l)
    
    if [ $recent_errors -gt 5 ]; then
        log_warning "Worker $worker_num has $recent_errors errors in recent logs"
        return 1  # Unhealthy
    fi
    
    return 0  # Healthy
}

# Function to handle restart throttling
should_restart_worker() {
    local worker_num=$1
    local current_time=$(date +%s)
    local last_restart=${LAST_RESTART_TIME[$worker_num]}
    local time_since_restart=$((current_time - last_restart))
    
    # Don't restart if restarted less than 5 minutes ago
    if [ $last_restart -gt 0 ] && [ $time_since_restart -lt 300 ]; then
        log_warning "Worker $worker_num was restarted $time_since_restart seconds ago. Waiting..."
        return 1
    fi
    
    # Don't restart if too many restarts (more than 10 in this session)
    if [ ${RESTART_COUNT[$worker_num]} -gt 10 ]; then
        log_error "Worker $worker_num has been restarted ${RESTART_COUNT[$worker_num]} times. Giving up."
        return 1
    fi
    
    return 0
}

# Cleanup function
cleanup() {
    log_info "Supervisor shutting down..."
    rm -f "$PID_FILE"
    exit 0
}

# Trap signals
trap cleanup SIGINT SIGTERM

log_success "Supervisor initialized. Monitoring workers every $CHECK_INTERVAL seconds..."
log_info "Workers will auto-restart if they crash"
log_info "Press Ctrl+C to stop supervisor"
echo ""

# Main monitoring loop
while true; do
    # Check each worker
    for worker_num in 1 2 3 4; do
        if is_worker_running $worker_num; then
            # Worker is running, check health
            if check_worker_health $worker_num; then
                # All good
                :
            else
                log_warning "Worker $worker_num is unhealthy but still running"
            fi
        else
            # Worker not running
            log_error "Worker $worker_num is not running!"
            
            if should_restart_worker $worker_num; then
                log_info "Attempting to restart Worker $worker_num..."
                start_worker $worker_num
            fi
        fi
    done
    
    # Report status every 10 checks (10 minutes)
    if [ $((SECONDS % 600)) -lt $CHECK_INTERVAL ]; then
        log_info "=== STATUS REPORT ==="
        for worker_num in 1 2 3 4; do
            if is_worker_running $worker_num; then
                log_success "Worker $worker_num: ✅ Running (restarts: ${RESTART_COUNT[$worker_num]})"
            else
                log_error "Worker $worker_num: ❌ Stopped (restarts: ${RESTART_COUNT[$worker_num]})"
            fi
        done
        echo ""
    fi
    
    sleep $CHECK_INTERVAL
done
