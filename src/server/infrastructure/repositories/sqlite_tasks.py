import sqlite3
from datetime import datetime
from server.models.task import CompilerTask, CompilerTaskRequest, ProgrammingLanguage, TaskId, TaskStatus, TaskType
from server.repositories.tasks import TaskRepository
from server.models.task import CompilerTaskEncoder, CompilerTaskDecoder, ProgramRuntimeOptions
from shared.logging import get_logger
from uuid import uuid4
import json

logger = get_logger()



class SQLiteTaskRepository(TaskRepository):
    def __init__(self):
        self.conn = sqlite3.connect("db/tasks.db")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT,
                language TEXT,
                path TEXT,
                created_at TEXT,
                updated_at TEXT NULL,
                status TEXT,
                runtime_options JSON NULL,
                result JSON NULL,
                internal_job_id TEXT NULL
            );
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
            "INSERT INTO tasks (id, task_type, language, path, created_at, updated_at, status, runtime_options, result, internal_job_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task.task_id.value,
                task.task_type.value,
                task.language.value,
                task.path,
                task.created_at,
                task.updated_at,
                task.status.value,
                json.dumps(task.runtime_options, cls=CompilerTaskEncoder) if task.runtime_options else None,
                None,
                task.internal_job_id,
            ),
        )
        self.conn.commit()
        return task

    async def update_task(self, task: CompilerTask) -> CompilerTask:
        task.updated_at = datetime.now()
        self.conn.execute(
            "UPDATE tasks SET status = ?, updated_at = ?, result = ?, runtime_options = ?, internal_job_id = ? WHERE id = ?",
            (
                task.status.value,
                task.updated_at,
                json.dumps(task.result, cls=CompilerTaskEncoder) if task.result else None,
                json.dumps(task.runtime_options, cls=CompilerTaskEncoder) if task.runtime_options else None,
                task.internal_job_id,
                task.task_id.value,
            ),
        )
        self.conn.commit()
        return task

    async def get_task(self, task_id: TaskId) -> CompilerTask | None:
        cursor = self.conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id.value,))
        row = cursor.fetchone()
        if row is None:
            return None
                
        runtime_options = json.loads(row[7], cls=CompilerTaskDecoder) if row[7] else None
        result = json.loads(row[8], cls=CompilerTaskDecoder) if row[8] else None
        internal_job_id = row[9] if row[9] else None
        
        return CompilerTask(
            task_id=TaskId(value=row[0]),
            task_type=TaskType(value=row[1]),
            language= ProgrammingLanguage(value=row[2]),
            path=row[3],
            created_at=datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f"),
            updated_at=datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S.%f") if row[5] else None,
            status=TaskStatus(value=row[6]),
            runtime_options=ProgramRuntimeOptions.from_json(runtime_options) if runtime_options else None,
            result=result,
            internal_job_id=internal_job_id,
        )
    