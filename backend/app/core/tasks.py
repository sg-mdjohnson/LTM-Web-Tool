from typing import Any, Dict, Optional, List, Callable, Awaitable
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid
from app.core.logging import logger

@dataclass
class Task:
    """Background task definition"""
    id: str
    name: str
    func: Callable[..., Awaitable[Any]]
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    interval: Optional[int] = None  # Seconds between runs for periodic tasks
    max_retries: int = 3
    retry_delay: int = 5  # Seconds between retries
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: str = "pending"
    result: Any = None
    error: Optional[str] = None

class TaskManager:
    """Manages background tasks and scheduling"""
    
    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._running: bool = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._scheduler_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the task manager"""
        if self._running:
            return
            
        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler())
        logger.info("Task manager started")

    async def stop(self) -> None:
        """Stop the task manager"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Task manager stopped")

    async def add_task(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any
    ) -> str:
        """Add a one-time task"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs
        )
        self._tasks[task_id] = task
        await self._task_queue.put(task)
        logger.info(f"Added task: {name} ({task_id})")
        return task_id

    async def add_periodic_task(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        interval: int,
        *args: Any,
        **kwargs: Any
    ) -> str:
        """Add a periodic task"""
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            interval=interval,
            next_run=datetime.utcnow()
        )
        self._tasks[task_id] = task
        await self._task_queue.put(task)
        logger.info(f"Added periodic task: {name} ({task_id})")
        return task_id

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = "cancelled"
            logger.info(f"Cancelled task: {task.name} ({task_id})")
            return True
        return False

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task status"""
        return self._tasks.get(task_id)

    def list_tasks(self) -> List[Task]:
        """List all tasks"""
        return list(self._tasks.values())

    async def _scheduler(self) -> None:
        """Main scheduler loop"""
        while self._running:
            try:
                # Process periodic tasks
                now = datetime.utcnow()
                for task in self._tasks.values():
                    if (
                        task.interval and
                        task.status != "cancelled" and
                        task.next_run and
                        now >= task.next_run
                    ):
                        await self._task_queue.put(task)
                        task.next_run = now + timedelta(seconds=task.interval)

                # Process task queue
                try:
                    task = await asyncio.wait_for(
                        self._task_queue.get(),
                        timeout=1.0
                    )
                    asyncio.create_task(self._execute_task(task))
                except asyncio.TimeoutError:
                    continue

            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(1)

    async def _execute_task(self, task: Task) -> None:
        """Execute a task with retry logic"""
        for attempt in range(task.max_retries):
            try:
                task.status = "running"
                task.last_run = datetime.utcnow()
                
                task.result = await task.func(*task.args, **task.kwargs)
                task.status = "completed"
                task.error = None
                
                logger.info(
                    f"Task completed: {task.name} ({task.id})",
                    extra={"task_id": task.id}
                )
                break
                
            except Exception as e:
                task.error = str(e)
                if attempt < task.max_retries - 1:
                    task.status = "retrying"
                    await asyncio.sleep(task.retry_delay)
                else:
                    task.status = "failed"
                    logger.error(
                        f"Task failed: {task.name} ({task.id}): {str(e)}",
                        extra={"task_id": task.id}
                    )

# Global task manager instance
task_manager = TaskManager() 