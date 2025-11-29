#!/usr/bin/env bash

# CarScout AI - Worker Supervisor (macOS Compatible)
# Monitors all workers and auto-restarts them if they crash  
# Run: nohup ./supervisor.sh > logs/supervisor.log 2>&1 &

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
WORKERS_DIR="$SCRIPT_DIR/workers/scrape"
CHECK_INTERVAL=60
AUTO_RESTART_ON_COMPLETE=true  # Set to false to disable auto-restart

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

# Check if worker log is active
is_worker_running() {
    local log_file="$LOGS_DIR/worker_$1.log"
    if [ -f "$log_file" ]; then
        local log_age=$(( $(date +%s) - $(stat -f %m "$log_file" 2>/dev/null || echo 0) ))
        [ $log_age -lt 300 ] && return 0
    fi
    return 1
}

# Check if worker completed successfully
is_worker_completed() {
    local log_file="$LOGS_DIR/worker_$1.log"
    if [ -f "$log_file" ]; then
        tail -20 "$log_file" | grep -q "Spider closed\|finish_reason"
        return $?
    fi
    return 1
}

# Start a worker
start_worker() {
    local num=$1
    local configs=("" "mobile_bg_worker_1.json" "mobile_bg_worker_2.json" "mobile_bg_worker_3.json" "mobile_bg_worker_4.json" "cars_bg_config_worker_5.json")
    local spiders=("" "mobile_bg" "mobile_bg" "mobile_bg" "mobile_bg" "cars_bg")
    local config="$SCRIPT_DIR/${configs[$num]}"
    local spider="${spiders[$num]}"
    
    log "Starting Worker $num (Spider: $spider)..."
    cd "$WORKERS_DIR"
    export HYBRID_CONFIG_PATH="$config"
    
    # Worker 5 uses cars_bg spider, others use mobile_bg
    if [ "$num" -eq 5 ]; then
        nohup ../../.venv/bin/scrapy crawl cars_bg \
            > "$LOGS_DIR/worker_${num}.log" 2>&1 &
    else
        nohup ../../.venv/bin/scrapy crawl mobile_bg -a skip_login=true \
            > "$LOGS_DIR/worker_${num}.log" 2>&1 &
    fi
    
    sleep 2
    log "Worker $num started"
}

log "Supervisor started (PID $$)"
log "Monitoring every $CHECK_INTERVAL seconds..."
log "Auto-restart on completion: $AUTO_RESTART_ON_COMPLETE"

while true; do
    for i in 1 2 3 4 5; do
        if ! is_worker_running $i; then
            if [ "$AUTO_RESTART_ON_COMPLETE" = true ] && is_worker_completed $i; then
                log "Worker $i completed cycle. Restarting for next cycle..."
                start_worker $i
            else
                log "ERROR: Worker $i stopped! Restarting..."
                start_worker $i
            fi
        fi
    done
    sleep $CHECK_INTERVAL
done
