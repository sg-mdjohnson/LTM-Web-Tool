from typing import Callable, TypeVar, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from sqlalchemy.exc import OperationalError, IntegrityError
from app.core.logging import logger

T = TypeVar("T")

def with_retry(
    func: Callable[..., T],
    max_attempts: int = 3,
    exclude_exceptions: tuple = (IntegrityError,)
) -> T:
    @retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (OperationalError,)
        ),
        before_sleep=lambda retry_state: logger.warning(
            f"Retrying database operation: {retry_state.attempt_number}/{max_attempts}"
        ),
    )
    def wrapped(*args: Any, **kwargs: Any) -> T:
        try:
            return func(*args, **kwargs)
        except exclude_exceptions:
            raise
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise
    return wrapped 