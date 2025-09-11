#!/bin/bash

# Setup cron job for custom cases cleanup
# This script is run during container startup

echo "Setting up cron job for custom cases cleanup..."

# Install cron if not present (some minimal containers don't have it)
if ! command -v cron &> /dev/null; then
    echo "Installing cron..."
    apt-get update && apt-get install -y cron
fi

# Create cron job entry
# Run cleanup daily at 2:00 AM
CRON_JOB="0 2 * * * /app/scripts/cleanup_custom_cases.sh >/dev/null 2>&1"

# Add to crontab
echo "$CRON_JOB" | crontab -

# Start cron service
service cron start

# Verify cron job was added
echo "Current crontab:"
crontab -l

echo "Cron job setup completed. Custom cases will be cleaned up daily at 2:00 AM."
echo "Files older than \$CLEANUP_DAYS days will be deleted (default: 7 days)"