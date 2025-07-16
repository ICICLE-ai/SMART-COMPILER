from abc import ABC, abstractmethod
import json
from server.models.task import CompilerTask, CompilerTaskEncoder, CompilerTaskDecoder, CompilerTaskRequest, TaskId
from datetime import datetime
from server.models.task import TaskStatus
from server.models.task import TaskResult
import sqlite3
from uuid import uuid4
from shared.logging import get_logger

logger = get_logger(__name__)


class TaskRepository(ABC):
    @abstractmethod
    async def save_task(self, task_request: CompilerTaskRequest) -> CompilerTask:
        pass

    @abstractmethod
    async def get_task(self, task_id: TaskId) -> CompilerTask | None:
        pass

    @abstractmethod
    async def update_task(self, task: CompilerTask) -> CompilerTask:
        pass


class InMemoryTaskRepository(TaskRepository):
    def __init__(self):
        self.tasks = {}

    async def save_task(self, task_request: CompilerTaskRequest) -> CompilerTask:
        task_id = str(uuid4())
        task = CompilerTask(
            task_id=TaskId(value=task_id),
            task_type=task_request.task_type,
            language=task_request.language,
            runtime_options=task_request.runtime_options,
            path=task_request.path,
            created_at=datetime.now(),
            updated_at=None,
            status=TaskStatus.PENDING,
            result=None,
        )
        self.tasks[task_id] = task
        return task

    async def get_task(self, task_id: TaskId) -> CompilerTask | None:
        return self.tasks.get(task_id.value)

    async def update_task(self, task: CompilerTask) -> CompilerTask:
        self.tasks[task.task_id.value] = task
        return task