import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from app.core.logging import logger
from app.core.config import settings

class ResourceCleaner:
    def __init__(self):
        self.temp_dir = Path(settings.TEMP_DIR)
        self.log_dir = Path(settings.LOG_DIR)
        self.backup_dir = Path(settings.BACKUP_DIR)

    def cleanup_temp_files(self, max_age_hours: int = 24):
        threshold = datetime.now() - timedelta(hours=max_age_hours)
        try:
            for item in self.temp_dir.glob('*'):
                if item.stat().st_mtime < threshold.timestamp():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
        except Exception as e:
            logger.error(f"Error cleaning temp files: {e}")

    def rotate_logs(self, max_size_mb: int = 100, max_files: int = 5):
        try:
            for log_file in self.log_dir.glob('*.log'):
                if log_file.stat().st_size > max_size_mb * 1024 * 1024:
                    self._rotate_file(log_file, max_files)
        except Exception as e:
            logger.error(f"Error rotating logs: {e}")

    def _rotate_file(self, file_path: Path, max_files: int):
        for i in range(max_files - 1, 0, -1):
            old = file_path.with_suffix(f'.log.{i}')
            new = file_path.with_suffix(f'.log.{i + 1}')
            if old.exists():
                old.rename(new)
        if file_path.exists():
            file_path.rename(file_path.with_suffix('.log.1')) 