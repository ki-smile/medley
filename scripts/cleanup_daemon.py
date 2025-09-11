#!/usr/bin/env python3

"""
Medley Custom Cases Cleanup Daemon
Runs as a background service to periodically clean up custom case files
"""

import os
import time
import glob
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CLEANUP_INTERVAL_HOURS = int(os.getenv('CLEANUP_INTERVAL_HOURS', '24'))  # Run every 24 hours
CLEANUP_DAYS = int(os.getenv('CLEANUP_DAYS', '2'))  # Keep files for 2 days
REPORTS_DIR = Path(os.getenv('REPORTS_DIR', '/app/reports'))
CACHE_DIR = Path(os.getenv('CACHE_DIR', '/app/cache'))
FLASK_SESSION_DIR = Path(os.getenv('FLASK_SESSION_DIR', '/app/flask_session'))
LOG_FILE = Path('/app/logs/cleanup_daemon.log')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def cleanup_old_files(directory: Path, pattern: str, days: int) -> int:
    """Clean up files older than specified days"""
    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist")
        return 0
    
    deleted_count = 0
    cutoff_time = datetime.now() - timedelta(days=days)
    
    try:
        # Find files matching pattern
        files = list(directory.glob(pattern))
        logger.info(f"Found {len(files)} files matching pattern '{pattern}' in {directory}")
        
        for file_path in files:
            if file_path.is_file():
                # Check file modification time
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Error cleaning up files in {directory}: {e}")
    
    return deleted_count

def run_cleanup():
    """Run the cleanup process"""
    logger.info(f"Starting cleanup (keeping files newer than {CLEANUP_DAYS} days)")
    
    # Clean up custom reports
    deleted_reports = cleanup_old_files(REPORTS_DIR, 'custom_*', CLEANUP_DAYS)
    logger.info(f"Deleted {deleted_reports} custom report files")
    
    # Clean up custom cache files  
    deleted_cache = cleanup_old_files(CACHE_DIR, 'custom_*', CLEANUP_DAYS)
    logger.info(f"Deleted {deleted_cache} custom cache files")
    
    # Clean up any orchestrator cache files for custom cases
    deleted_orchestrator = cleanup_old_files(CACHE_DIR / 'orchestrator', 'custom_*', CLEANUP_DAYS)
    logger.info(f"Deleted {deleted_orchestrator} custom orchestrator cache files")
    
    # Clean up Flask sessions older than specified days
    deleted_sessions = cleanup_old_files(FLASK_SESSION_DIR, '*', CLEANUP_DAYS)
    logger.info(f"Deleted {deleted_sessions} Flask session files")
    
    # Clean up temporary files
    temp_dir = Path('/tmp')
    if temp_dir.exists():
        deleted_temp = cleanup_old_files(temp_dir, '*medley*', 1)  # Delete temp files older than 1 day
        deleted_temp += cleanup_old_files(temp_dir, '*custom_*', 1)
        if deleted_temp > 0:
            logger.info(f"Deleted {deleted_temp} temporary files")
    
    total_deleted = deleted_reports + deleted_cache + deleted_orchestrator + deleted_sessions
    logger.info(f"Cleanup completed. Total files deleted: {total_deleted}")
    
    return total_deleted

def main():
    """Main daemon loop"""
    logger.info("🧹 Medley Cleanup Daemon starting...")
    logger.info(f"Configuration: cleanup_interval={CLEANUP_INTERVAL_HOURS}h, keep_days={CLEANUP_DAYS}")
    
    while True:
        try:
            run_cleanup()
            
            # Sleep until next cleanup
            sleep_seconds = CLEANUP_INTERVAL_HOURS * 3600
            logger.info(f"Next cleanup in {CLEANUP_INTERVAL_HOURS} hours")
            time.sleep(sleep_seconds)
            
        except KeyboardInterrupt:
            logger.info("Cleanup daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in cleanup daemon: {e}")
            # Sleep for 1 hour before retrying
            time.sleep(3600)

if __name__ == '__main__':
    main()