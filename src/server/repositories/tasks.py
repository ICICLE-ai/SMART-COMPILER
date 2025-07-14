from abc import ABC, abstractmethod
from src.server.models.task import CompilerTask, CompilerTaskRequest, TaskId
from datetime import datetime
from src.server.models.task import TaskStatus
from src.server.models.task import TaskResult
import sqlite3
from uuid import uuid4


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


class SQLiteTaskRepository(TaskRepository):
    def __init__(self):
        self.conn = sqlite3.connect("tasks.db")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT,
                language TEXT,
                runtime_options JSON,
                file_path TEXT,
                created_at TEXT,
                updated_at TEXT NUL,
                status TEXT,
                result JSON NULL
            """
        )
        self.conn.commit()

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
        self.conn.execute(
            "INSERT INTO tasks (id, task_type, language, file_path, created_at, updated_at, status, result) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.task_id.value,
                task.task_type.value,
                task.language.value,
                task.path,
                task.created_at,
                task.updated_at,
                task.status.value,
                None,
            ),
        )
        self.conn.commit()
        return task

    async def update_task(self, task: CompilerTask) -> CompilerTask:
        self.conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ?, result = ? WHERE id = ?",
            (task.status.value, datetime.now(), task.result, task.task_id.value),
        )
        self.conn.commit()
        return task
    
    
    async def get_task(self, task_id: TaskId) -> CompilerTask | None:
        cursor = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.value,))
        row = cursor.fetchone()
        if row is None:
            return None
        return CompilerTask(
            task_id=TaskId(value=row[0]),
            task_type=row[1],
            language=row[2],
            runtime_options=row[3],
            path=row[4],
            created_at=row[5],
            updated_at=row[6],
            status=row[7],
            result=row[8],
        )   


singleton_task_repository = SQLiteTaskRepository()


async def get_task_repository() -> TaskRepository:
    return singleton_task_repository
