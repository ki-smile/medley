#!/bin/bash

# Medley Custom Cases Cleanup Script
# Deletes custom case files older than specified days

# Configuration
REPORTS_DIR="/app/reports"
CACHE_DIR="/app/cache"
FLASK_SESSION_DIR="/app/flask_session"
DAYS_TO_KEEP=${CLEANUP_DAYS:-2}  # Default 2 days, can be overridden by env var
LOG_FILE="/var/log/medley_cleanup.log"

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_message "Starting custom cases cleanup (keeping files newer than $DAYS_TO_KEEP days)"

# Count files before cleanup
custom_reports_before=$(find "$REPORTS_DIR" -name "custom_*" -type f 2>/dev/null | wc -l)
custom_cache_before=$(find "$CACHE_DIR" -name "custom_*" -type f 2>/dev/null | wc -l)
session_files_before=$(find "$FLASK_SESSION_DIR" -type f 2>/dev/null | wc -l)

log_message "Found $custom_reports_before custom report files, $custom_cache_before custom cache files, and $session_files_before session files"

# Clean up custom reports older than specified days
if [ -d "$REPORTS_DIR" ]; then
    deleted_reports=$(find "$REPORTS_DIR" -name "custom_*" -type f -mtime +$DAYS_TO_KEEP -delete -print 2>/dev/null | wc -l)
    log_message "Deleted $deleted_reports custom report files from $REPORTS_DIR"
else
    log_message "Reports directory $REPORTS_DIR not found"
fi

# Clean up custom cache files older than specified days
if [ -d "$CACHE_DIR" ]; then
    deleted_cache=$(find "$CACHE_DIR" -name "custom_*" -type f -mtime +$DAYS_TO_KEEP -delete -print 2>/dev/null | wc -l)
    log_message "Deleted $deleted_cache custom cache files from $CACHE_DIR"
else
    log_message "Cache directory $CACHE_DIR not found"
fi

# Clean up Flask session files older than specified days
if [ -d "$FLASK_SESSION_DIR" ]; then
    deleted_sessions=$(find "$FLASK_SESSION_DIR" -type f -mtime +$DAYS_TO_KEEP -delete -print 2>/dev/null | wc -l)
    log_message "Deleted $deleted_sessions Flask session files from $FLASK_SESSION_DIR"
else
    log_message "Flask session directory $FLASK_SESSION_DIR not found"
fi

# Clean up any temporary files
temp_files=$(find /tmp -name "*medley*" -o -name "*custom_*" -type f -mtime +1 -delete -print 2>/dev/null | wc -l)
if [ "$temp_files" -gt 0 ]; then
    log_message "Deleted $temp_files temporary files"
fi

# Count files after cleanup
custom_reports_after=$(find "$REPORTS_DIR" -name "custom_*" -type f 2>/dev/null | wc -l)
custom_cache_after=$(find "$CACHE_DIR" -name "custom_*" -type f 2>/dev/null | wc -l)
session_files_after=$(find "$FLASK_SESSION_DIR" -type f 2>/dev/null | wc -l)

log_message "Cleanup completed. Remaining: $custom_reports_after report files, $custom_cache_after cache files, $session_files_after session files"

# Optional: Clean up old log entries (keep only last 100 lines)
tail -n 100 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"

exit 0