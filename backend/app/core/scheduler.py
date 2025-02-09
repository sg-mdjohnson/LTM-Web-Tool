from typing import Dict, Any, Callable
import asyncio
import time
from datetime import datetime, timedelta
from threading import Lock
import uuid
from app.core.logging import logger

class TaskScheduler:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self._running = True
        self._event_loop = None

    async def start(self) -> None:
        self._event_loop = asyncio.get_event_loop()
        while self._running:
            await self._process_tasks()
            await asyncio.sleep(1)

    def schedule_task(
        self,
        func: Callable,
        delay: int = 0,
        interval: int = None,
        name: str = None
    ) -> str:
        task_id = str(uuid.uuid4())
        with self._lock:
            self._tasks[task_id] = {
                'func': func,
                'next_run': time.time() + delay,
                'interval': interval,
                'name': name or func.__name__,
                'status': 'scheduled',
                'last_run': None,
                'last_error': None
            }
        return task_id

    async def _process_tasks(self) -> None:
        now = time.time()
        with self._lock:
            for task_id, task in list(self._tasks.items()):
                if task['next_run'] <= now:
                    try:
                        if asyncio.iscoroutinefunction(task['func']):
                            await task['func']()
                        else:
                            task['func']()
                        
                        task['last_run'] = now
                        task['status'] = 'completed'
                        
                        if task['interval']:
                            task['next_run'] = now + task['interval']
                        else:
                            del self._tasks[task_id]
                            
                    except Exception as e:
                        logger.error(
                            f"Task {task['name']} failed: {str(e)}",
                            exc_info=True
                        )
                        task['status'] = 'failed'
                        task['last_error'] = str(e)
                        if task['interval']:
                            task['next_run'] = now + task['interval']
                        else:
                            del self._tasks[task_id]

    def stop(self) -> None:
        self._running = False 