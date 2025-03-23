#!/bin/bash
# Research Article Reader Monitoring Script
# Usage: ./monitor.sh {check|alerts|detailed}

cd "$(dirname "$0")"
export PYTHONPATH=.

# Configuration
LOG_FILE="logs/app.log"
PID_FILE=".service.pid"
EMAIL=""  # Add your email to receive alerts

# Function definitions
check_running() {
    # Check if service is running
    if [ -f $PID_FILE ]; then
        pid=$(cat $PID_FILE)
        if ps -p $pid > /dev/null; then
            echo "Service is running (PID: $pid)"
            return 0
        else
            echo "WARNING: PID file exists but process is not running!"
            return 1
        fi
    else
        if ps aux | grep -q "[p]ython -m src.main"; then
            pid=$(ps aux | grep "[p]ython -m src.main" | awk '{print $2}')
            echo "Service is running (PID: $pid) but PID file is missing"
            echo $pid > $PID_FILE
            echo "Created PID file"
            return 0
        else
            echo "ERROR: Service is not running!"
            return 1
        fi
    fi
}

check_errors() {
    # Check for recent errors in logs
    if [ -f $LOG_FILE ]; then
        # Get errors from the last hour
        errors=$(grep -i "error\|exception\|warning" $LOG_FILE | grep "$(date -d '1 hour ago' +'%Y-%m-%d %H' 2>/dev/null || date -v-1H +'%Y-%m-%d %H')")
        if [ -n "$errors" ]; then
            echo "WARNING: Recent errors found in logs:"
            echo "$errors"
            return 1
        else
            echo "No recent errors found in logs"
            return 0
        fi
    else
        echo "Log file not found"
        return 0
    fi
}

check_activity() {
    # Check for recent activity
    if [ -f $LOG_FILE ]; then
        # Get timestamp of last log entry
        last_log=$(tail -n 1 $LOG_FILE)
        last_timestamp=$(echo $last_log | awk '{print $1 " " $2}')
        echo "Last activity: $last_timestamp"
        
        # Check if last activity was too long ago (more than 7 hours)
        current_timestamp=$(date +"%Y-%m-%d %H:%M:%S")
        # This is a crude check that will work in most cases
        hours_diff=$(( ($(date +%s) - $(date -d "$last_timestamp" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$last_timestamp" +%s)) / 3600 ))
        
        if [ $hours_diff -gt 7 ]; then
            echo "WARNING: No activity for $hours_diff hours!"
            return 1
        fi
    else
        echo "Log file not found"
        return 1
    fi
    
    return 0
}

check_resources() {
    # Check CPU and memory usage
    if [ -f $PID_FILE ]; then
        pid=$(cat $PID_FILE)
        if ps -p $pid > /dev/null; then
            # Check memory usage
            mem_usage=$(ps -o %mem= -p $pid | tr -d ' ')
            echo "Memory usage: $mem_usage%"
            
            # Check CPU usage
            cpu_usage=$(ps -o %cpu= -p $pid | tr -d ' ')
            echo "CPU usage: $cpu_usage%"
            
            # Alert if usage is high
            if (( $(echo "$mem_usage > 10" | bc -l) )); then
                echo "WARNING: High memory usage!"
            fi
            
            if (( $(echo "$cpu_usage > 20" | bc -l) )); then
                echo "WARNING: High CPU usage!"
            fi
        fi
    fi
}

check_disk_space() {
    # Check disk space
    data_size=$(du -sh $DATA_DIR 2>/dev/null | cut -f1)
    log_size=$(du -sh logs 2>/dev/null | cut -f1)
    
    echo "Data directory size: $data_size"
    echo "Logs directory size: $log_size"
    
    # Check free space
    free_space=$(df -h . | awk 'NR==2 {print $4}')
    echo "Free disk space: $free_space"
}

send_alert() {
    # Send email alert if email is configured
    if [ -n "$EMAIL" ]; then
        subject="Alert: Research Article Reader Service Issue"
        echo "$1" | mail -s "$subject" $EMAIL
        echo "Alert sent to $EMAIL"
    else
        echo "Alert: $1 (No email configured for alerts)"
    fi
}

detailed_status() {
    echo "=== Detailed Status Report ==="
    echo ""
    
    # Check if running
    running=true
    echo "Service status:"
    if ! check_running; then
        running=false
    fi
    echo ""
    
    # Only continue checks if service is running
    if $running; then
        # Check for errors
        echo "Error check:"
        check_errors
        echo ""
        
        # Check activity
        echo "Activity check:"
        check_activity
        echo ""
        
        # Check resources
        echo "Resource usage:"
        check_resources
        echo ""
        
        # Check disk space
        echo "Disk space:"
        check_disk_space
        echo ""
        
        # Check tracked articles
        echo "Tracked articles:"
        count=$(grep -o '"url":' data/processed_articles.json 2>/dev/null | wc -l)
        echo "Total articles tracked: $count"
        echo ""
    fi
    
    echo "=== End of Status Report ==="
}

check_all() {
    issues=0
    
    # Run all checks
    if ! check_running; then
        issues=$((issues+1))
    fi
    
    if ! check_errors; then
        issues=$((issues+1))
    fi
    
    if ! check_activity; then
        issues=$((issues+1))
    fi
    
    # Summary
    if [ $issues -eq 0 ]; then
        echo "All checks passed!"
    else
        echo "$issues issue(s) detected. Run with 'detailed' for more information."
    fi
}

alert_if_issues() {
    issues=0
    alert_msg=""
    
    # Check if running
    if ! check_running > /dev/null; then
        issues=$((issues+1))
        alert_msg="${alert_msg}- Service is not running\n"
    fi
    
    # Check for errors
    errors=$(grep -i "error\|exception\|warning" $LOG_FILE 2>/dev/null | grep "$(date -d '1 hour ago' +'%Y-%m-%d %H' 2>/dev/null || date -v-1H +'%Y-%m-%d %H')")
    if [ -n "$errors" ]; then
        issues=$((issues+1))
        alert_msg="${alert_msg}- Recent errors found in logs\n"
    fi
    
    # Check activity
    if [ -f $LOG_FILE ]; then
        last_log=$(tail -n 1 $LOG_FILE)
        last_timestamp=$(echo $last_log | awk '{print $1 " " $2}')
        hours_diff=$(( ($(date +%s) - $(date -d "$last_timestamp" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$last_timestamp" +%s)) / 3600 ))
        
        if [ $hours_diff -gt 7 ]; then
            issues=$((issues+1))
            alert_msg="${alert_msg}- No activity for $hours_diff hours\n"
        fi
    fi
    
    # Send alert if there are issues
    if [ $issues -gt 0 ]; then
        alert_msg="Research Article Reader Service has issues:\n${alert_msg}"
        send_alert "$alert_msg"
        echo "Issues found, alert sent"
    else
        echo "No issues found"
    fi
}

# Main script logic
case "$1" in
    check)
        check_all
        ;;
    alerts)
        alert_if_issues
        ;;
    detailed)
        detailed_status
        ;;
    *)
        echo "Usage: $0 {check|alerts|detailed}"
        echo ""
        echo "Commands:"
        echo "  check     - Check service status and report issues"
        echo "  alerts    - Check and send alerts if issues found"
        echo "  detailed  - Show detailed status report"
        exit 1
        ;;
esac

exit 0 