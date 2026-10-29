#!/usr/bin/env python3

"""
Medley Custom Cases Cleanup Daemon
Runs as a background service to periodically clean up custom case files
"""

import os
import time
import glob
import shutil
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
CLEANUP_INTERVAL_HOURS = int(os.getenv('CLEANUP_INTERVAL_HOURS', '24'))  # Run every 24 hours
CLEANUP_DAYS = int(os.getenv('CLEANUP_DAYS', '2'))  # Keep files for 2 days
REPORTS_DIR = Path(os.getenv('REPORTS_DIR', '/app/reports'))
CACHE_DIR = Path(os.getenv('CACHE_DIR', '/app/cache'))
USECASES_DIR = Path(os.getenv('USECASES_DIR', '/app/usecases'))
DB_PATH = Path(os.getenv('MEDLEY_DB_PATH', '/app/medley.db'))  # web_app opens sqlite:///medley.db from /app
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

def cleanup_old_files(directory: Path, pattern: str, days: int, dirs: bool = False) -> int:
    """Clean up files (or, with dirs=True, whole folders) older than specified days"""
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
            if file_path.is_file() or (dirs and file_path.is_dir() and not file_path.is_symlink()):
                # Check file modification time
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_time:
                    try:
                        if file_path.is_dir():
                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Error cleaning up files in {directory}: {e}")
    
    return deleted_count

def cleanup_old_db_analyses(db_path: Path, days: int) -> int:
    """Delete custom analyses older than specified days, with their responses, ratings and share links"""
    if not db_path.exists():
        logger.warning(f"Database {db_path} does not exist")
        return 0
    # created_at is written as naive UTC by the SQLAlchemy models ('YYYY-MM-DD HH:MM:SS.ffffff')
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S.%f')
    old = "SELECT id FROM analyses WHERE id LIKE 'custom\\_%' ESCAPE '\\' AND created_at < ?"
    try:
        with sqlite3.connect(db_path, timeout=30) as conn:
            for table in ('model_responses', 'diagnosis_ratings', 'shareable_links'):
                conn.execute(f"DELETE FROM {table} WHERE analysis_id IN ({old})", (cutoff,))
            deleted = conn.execute(f"DELETE FROM analyses WHERE id IN ({old})", (cutoff,)).rowcount
        conn.close()
        return deleted
    except sqlite3.Error as e:
        logger.error(f"Error cleaning up database {db_path}: {e}")
        return 0

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
    # Orchestrator results and model responses for custom cases are folders, one per case
    deleted_orchestrator = cleanup_old_files(CACHE_DIR / 'orchestrator', 'custom_*', CLEANUP_DAYS, dirs=True)
    logger.info(f"Deleted {deleted_orchestrator} custom orchestrator cache folders")
    deleted_responses = cleanup_old_files(CACHE_DIR / 'responses', 'custom_*', CLEANUP_DAYS, dirs=True)
    logger.info(f"Deleted {deleted_responses} custom response cache folders")

    # Case text submitted by users (usecases/custom; older versions wrote to usecases/ itself).
    # Only custom_* is matched, so the predefined case_### files are never touched.
    deleted_case_text = cleanup_old_files(USECASES_DIR / 'custom', 'custom_*', CLEANUP_DAYS)
    deleted_case_text += cleanup_old_files(USECASES_DIR, 'custom_*', CLEANUP_DAYS)
    logger.info(f"Deleted {deleted_case_text} custom case text files")

    # Stored analyses (case text, diagnoses, model responses) in the app database
    deleted_db = cleanup_old_db_analyses(DB_PATH, CLEANUP_DAYS)
    logger.info(f"Deleted {deleted_db} custom analyses from the database")
    
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
    
    total_deleted = (deleted_reports + deleted_cache + deleted_orchestrator + deleted_responses
                     + deleted_case_text + deleted_db + deleted_sessions)
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