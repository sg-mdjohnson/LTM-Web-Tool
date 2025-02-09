from typing import Any, Callable, Dict, Optional
import asyncio
import time
from datetime import datetime
from uuid import uuid4
from app.core.logging import logger

class BackgroundTaskManager:
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
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
        args: tuple = None,
        kwargs: dict = None,
        delay: int = 0,
        retries: int = 3,
        retry_delay: int = 5,
        timeout: int = 300
    ) -> str:
        task_id = str(uuid4())
        self._tasks[task_id] = {
            'func': func,
            'args': args or (),
            'kwargs': kwargs or {},
            'scheduled_time': time.time() + delay,
            'retries_left': retries,
            'retry_delay': retry_delay,
            'timeout': timeout,
            'status': 'scheduled',
            'result': None,
            'error': None,
            'start_time': None,
            'end_time': None
        }
        logger.info(f"Task scheduled: {task_id}")
        return task_id

    async def _process_tasks(self) -> None:
        now = time.time()
        for task_id, task in list(self._tasks.items()):
            if task['status'] == 'scheduled' and task['scheduled_time'] <= now:
                await self._execute_task(task_id, task)

    async def _execute_task(self, task_id: str, task: Dict[str, Any]) -> None:
        task['start_time'] = time.time()
        task['status'] = 'running'

        try:
            if asyncio.iscoroutinefunction(task['func']):
                result = await asyncio.wait_for(
                    task['func'](*task['args'], **task['kwargs']),
                    timeout=task['timeout']
                )
            else:
                result = await self._event_loop.run_in_executor(
                    None,
                    task['func'],
                    *task['args'],
                    **task['kwargs']
                )

            task['result'] = result
            task['status'] = 'completed'
            task['end_time'] = time.time()
            logger.info(f"Task completed: {task_id}")

        except Exception as e:
            logger.error(f"Task failed: {task_id}, error: {str(e)}")
            task['error'] = str(e)
            
            if task['retries_left'] > 0:
                task['retries_left'] -= 1
                task['scheduled_time'] = time.time() + task['retry_delay']
                task['status'] = 'scheduled'
                logger.info(f"Task rescheduled: {task_id}, retries left: {task['retries_left']}")
            else:
                task['status'] = 'failed'
                task['end_time'] = time.time()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def cleanup_completed_tasks(self, max_age: int = 3600) -> None:
        now = time.time()
        for task_id in list(self._tasks.keys()):
            task = self._tasks[task_id]
            if task['status'] in ('completed', 'failed'):
                if task['end_time'] and (now - task['end_time']) > max_age:
                    del self._tasks[task_id]

    def stop(self) -> None:
        self._running = False 