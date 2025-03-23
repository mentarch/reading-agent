#!/bin/bash
# Research Article Reader Maintenance Script
# Usage: ./maintenance.sh {backup|cleanup|repair}

cd "$(dirname "$0")"
export PYTHONPATH=.

# Configuration
DATA_DIR="data"
BACKUP_DIR="backups"
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Function definitions
backup_data() {
    echo "Backing up data files..."
    
    # Get current date for backup filename
    date_str=$(date +%Y%m%d_%H%M%S)
    backup_file="$BACKUP_DIR/backup_$date_str.tar.gz"
    
    # Create backup
    tar -czf $backup_file $DATA_DIR
    
    if [ $? -eq 0 ]; then
        echo "Backup created successfully: $backup_file"
        echo "Backup size: $(du -h $backup_file | cut -f1)"
    else
        echo "Error: Backup failed"
    fi
}

cleanup_old_backups() {
    echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    # Find and remove old backups
    find $BACKUP_DIR -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete -print
    
    echo "Cleanup complete"
}

cleanup_old_articles() {
    echo "Cleaning up old tracked articles..."
    
    # Get retention days from config or use default
    if [ -f "config.yaml" ]; then
        config_retention=$(grep "tracking_retention_days" config.yaml | awk '{print $2}')
        if [ -n "$config_retention" ]; then
            RETENTION_DAYS=$config_retention
        fi
    fi
    
    # Run cleanup using ArticleTracker
    python -c "from src.utils.article_tracker import ArticleTracker; tracker = ArticleTracker(storage_path='$DATA_DIR'); cleared = tracker.clear_older_than($RETENTION_DAYS); print(f'Cleared {cleared} old articles')"
}

repair_tracking_db() {
    echo "Attempting to repair tracking database..."
    
    # Check if database exists
    if [ ! -f "$DATA_DIR/processed_articles.json" ]; then
        echo "Tracking database not found. Creating empty database..."
        echo "{}" > "$DATA_DIR/processed_articles.json"
        echo "Empty database created."
        return
    fi
    
    # Backup before repair
    cp "$DATA_DIR/processed_articles.json" "$DATA_DIR/processed_articles.json.bak"
    echo "Backup created at $DATA_DIR/processed_articles.json.bak"
    
    # Validate JSON structure
    if python -m json.tool "$DATA_DIR/processed_articles.json" > /dev/null 2>&1; then
        echo "Tracking database is valid JSON. No repair needed."
    else
        echo "Database is corrupted. Attempting to restore from backup..."
        if [ -f "$DATA_DIR/processed_articles.json.bak" ]; then
            cp "$DATA_DIR/processed_articles.json.bak" "$DATA_DIR/processed_articles.json"
            echo "Restored from backup."
        else
            echo "No backup found. Creating new empty database..."
            echo "{}" > "$DATA_DIR/processed_articles.json"
            echo "Reset database to empty state."
        fi
    fi
}

# Main script logic
case "$1" in
    backup)
        backup_data
        ;;
    cleanup)
        if [ "$2" == "backups" ]; then
            cleanup_old_backups
        elif [ "$2" == "articles" ]; then
            cleanup_old_articles
        else
            cleanup_old_backups
            cleanup_old_articles
        fi
        ;;
    repair)
        repair_tracking_db
        ;;
    *)
        echo "Usage: $0 {backup|cleanup|repair}"
        echo ""
        echo "Commands:"
        echo "  backup              - Create a backup of all data"
        echo "  cleanup             - Clean up old backups and tracked articles"
        echo "  cleanup backups     - Clean up only old backups"
        echo "  cleanup articles    - Clean up only old tracked articles"
        echo "  repair              - Attempt to repair tracking database if corrupted"
        exit 1
        ;;
esac

exit 0 