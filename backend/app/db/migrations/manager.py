from typing import List, Optional
import alembic.config
import alembic.command
from pathlib import Path
from app.core.logging import logger
from app.core.errors import MigrationError

class MigrationManager:
    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.alembic_cfg = self._create_alembic_config()

    def _create_alembic_config(self) -> alembic.config.Config:
        cfg = alembic.config.Config()
        cfg.set_main_option("script_location", str(self.migrations_dir))
        cfg.set_main_option("sqlalchemy.url", "driver://user:pass@localhost/dbname")
        return cfg

    def upgrade(self, revision: str = "head") -> None:
        try:
            logger.info(f"Starting database upgrade to {revision}")
            alembic.command.upgrade(self.alembic_cfg, revision)
            logger.info("Database upgrade completed successfully")
        except Exception as e:
            logger.error(f"Database upgrade failed: {str(e)}")
            raise MigrationError(f"Upgrade failed: {str(e)}")

    def downgrade(self, revision: str) -> None:
        try:
            logger.info(f"Starting database downgrade to {revision}")
            alembic.command.downgrade(self.alembic_cfg, revision)
            logger.info("Database downgrade completed successfully")
        except Exception as e:
            logger.error(f"Database downgrade failed: {str(e)}")
            raise MigrationError(f"Downgrade failed: {str(e)}")

    def check_current(self) -> str:
        try:
            return alembic.command.current(self.alembic_cfg)
        except Exception as e:
            logger.error(f"Failed to get current revision: {str(e)}")
            raise MigrationError(f"Version check failed: {str(e)}") 