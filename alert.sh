#!/usr/bin/env bash

# CarScout AI - Alert System
# Sends notifications when critical events occur

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# Telegram settings (optional - set these if you want Telegram alerts)
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

# Function to send Telegram alert
send_telegram_alert() {
    local message="$1"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ]; then
        # No Telegram configured, just log
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $message"
        return
    fi
    
    # Send to Telegram
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="🚨 CarScout Alert: $message" \
        -d parse_mode="HTML" > /dev/null 2>&1
}

# Function to log alert to file
log_alert() {
    local alert_type="$1"
    local message="$2"
    local alert_log="$LOGS_DIR/alerts.log"
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$alert_type] $message" >> "$alert_log"
}

# Main alert function
alert() {
    local alert_type="$1"  # ERROR, WARNING, INFO, SUCCESS
    local message="$2"
    
    # Log to file
    log_alert "$alert_type" "$message"
    
    # Send Telegram notification for errors
    if [ "$alert_type" = "ERROR" ]; then
        send_telegram_alert "$message"
    fi
    
    # Also print to stdout
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$alert_type] $message"
}

# Export functions for use in other scripts
export -f alert
export -f send_telegram_alert
export -f log_alert

# If called directly with arguments, send alert
if [ $# -gt 0 ]; then
    alert "$@"
fi
