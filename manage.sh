#!/bin/bash
# Research Article Reader Management Script
# Usage: ./manage.sh {start|stop|restart|status|logs|tracked|test}

cd "$(dirname "$0")"
export PYTHONPATH=.

# Configuration
LOG_FILE="logs/app.log"
PID_FILE=".service.pid"
PYTHON_CMD="python"
APP_MODULE="src.main"

# Create logs directory if it doesn't exist
mkdir -p logs

# Function definitions
start_service() {
    echo "Starting Research Article Reader..."
    if is_running; then
        echo "Service already running (PID: $(cat $PID_FILE))"
        return
    fi
    
    nohup $PYTHON_CMD -m $APP_MODULE > $LOG_FILE 2>&1 &
    echo $! > $PID_FILE
    echo "Service started with PID: $(cat $PID_FILE)"
}

stop_service() {
    echo "Stopping Research Article Reader..."
    if [ -f $PID_FILE ]; then
        pid=$(cat $PID_FILE)
        if ps -p $pid > /dev/null; then
            echo "Stopping process with PID: $pid"
            kill $pid
            
            # Wait for process to terminate
            for i in {1..10}; do
                if ! ps -p $pid > /dev/null; then
                    break
                fi
                echo "Waiting for process to terminate..."
                sleep 1
            done
            
            # Force kill if still running
            if ps -p $pid > /dev/null; then
                echo "Force stopping process..."
                kill -9 $pid
            fi
        else
            echo "Process not found but PID file exists. Cleaning up."
        fi
        rm -f $PID_FILE
    else
        echo "PID file not found. Searching for running process..."
        pid=$(ps aux | grep "[p]ython -m $APP_MODULE" | awk '{print $2}')
        if [ -n "$pid" ]; then
            echo "Found process with PID: $pid. Stopping..."
            kill $pid
            echo "Process stopped."
        else
            echo "Service not running."
        fi
    fi
}

restart_service() {
    echo "Restarting Research Article Reader..."
    stop_service
    sleep 2
    start_service
}

is_running() {
    if [ -f $PID_FILE ]; then
        pid=$(cat $PID_FILE)
        if ps -p $pid > /dev/null; then
            return 0  # True, is running
        fi
    fi
    
    # Double check by process name
    if ps aux | grep -q "[p]ython -m $APP_MODULE"; then
        # Service is running but PID file is missing
        pid=$(ps aux | grep "[p]ython -m $APP_MODULE" | awk '{print $2}')
        echo $pid > $PID_FILE
        return 0  # True, is running
    fi
    
    return 1  # False, not running
}

show_status() {
    if is_running; then
        pid=$(cat $PID_FILE 2>/dev/null || ps aux | grep "[p]ython -m $APP_MODULE" | awk '{print $2}')
        echo "Service is running (PID: $pid)"
        echo "Uptime: $(ps -o etime= -p $pid)"
        echo "Memory usage: $(ps -o %mem= -p $pid)%"
    else
        echo "Service is not running"
    fi
    
    # Show recent activity
    if [ -f $LOG_FILE ]; then
        echo ""
        echo "Recent activity:"
        tail -n 5 $LOG_FILE
    fi
    
    # Show tracked articles count
    if [ -f "data/processed_articles.json" ]; then
        count=$(grep -o '"url":' data/processed_articles.json | wc -l)
        echo ""
        echo "Tracked articles: $count"
    fi
}

show_logs() {
    if [ -f $LOG_FILE ]; then
        if [ "$1" == "all" ]; then
            cat $LOG_FILE
        elif [ "$1" == "errors" ]; then
            echo "Showing errors:"
            grep -i "error\|exception\|warning" $LOG_FILE
        else
            echo "Showing last 20 log entries:"
            tail -n 20 $LOG_FILE
        fi
    else
        echo "Log file not found"
    fi
}

show_tracked() {
    echo "Showing tracked articles:"
    $PYTHON_CMD -m src.utils.show_tracked_articles
}

run_test() {
    echo "Running test to check application functionality..."
    $PYTHON_CMD test_tracker.py
}

# Main script logic
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        if [ "$2" == "all" ] || [ "$2" == "errors" ]; then
            show_logs $2
        else
            show_logs
        fi
        ;;
    tracked)
        show_tracked
        ;;
    test)
        run_test
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|tracked|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the service in background"
        echo "  stop     - Stop the running service"
        echo "  restart  - Restart the service"
        echo "  status   - Check if service is running and show info"
        echo "  logs     - Show last 20 log entries"
        echo "  tracked  - Show tracked articles"
        echo "  test     - Run test script to verify functionality"
        echo ""
        echo "Additional options:"
        echo "  logs all    - Show all logs"
        echo "  logs errors - Show only errors and warnings" 
        exit 1
        ;;
esac

exit 0 