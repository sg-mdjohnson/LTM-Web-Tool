from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.logging import logger

@contextmanager
def transaction(session: Session) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Transaction failed: {str(e)}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in transaction: {str(e)}")
        raise 