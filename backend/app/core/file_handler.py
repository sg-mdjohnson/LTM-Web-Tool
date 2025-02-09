from pathlib import Path
from typing import Optional, List
import shutil
import hashlib
from datetime import datetime
import aiofiles
from app.core.logging import logger
from app.core.errors import FileError

class FileHandler:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_path: Path, content: bytes, make_backup: bool = True) -> None:
        file_path = self.base_dir / file_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if make_backup and file_path.exists():
            await self._create_backup(file_path)

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
            raise FileError(f"Failed to save file: {e}")

    async def _create_backup(self, file_path: Path) -> None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_suffix(f'.{timestamp}.bak')
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            logger.error(f"Error creating backup of {file_path}: {e}")
            raise FileError(f"Failed to create backup: {e}")

    def get_file_hash(self, file_path: Path) -> str:
        file_path = self.base_dir / file_path
        if not file_path.exists():
            raise FileError(f"File not found: {file_path}")

        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            raise FileError(f"Failed to calculate file hash: {e}") 