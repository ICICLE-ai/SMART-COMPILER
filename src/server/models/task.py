from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from server.models.compiler import ProgramRuntimeOptions

class TaskType(Enum):
    PROFILE = "profile"
    OPTIMIZE = "optimize"
    
class ProgrammingLanguage(Enum):
    PYTHON = "python"
    C = "c"
    

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class TaskId():
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Task ID cannot be empty")

@dataclass
class TaskResult():
    file_path: str
    error: Optional[str] = None

@dataclass
class CompilerTask():
    task_id: TaskId
    task_type: TaskType
    language: ProgrammingLanguage
    runtime_options: ProgramRuntimeOptions
    path: str
    created_at: datetime
    updated_at: datetime | None
    status: TaskStatus
    result: TaskResult | None


class ProfilingType(Enum):
    CLASSICAL = "classical"
    LLM = "llm"
    AGUMENTED = "augmented"
    
    

@dataclass
class TaskOptions():
    profiling_type: Optional[ProfilingType]


@dataclass
class CompilerTaskRequest():
    task_type: TaskType
    language: ProgrammingLanguage
    path: str
    runtime_options: ProgramRuntimeOptions
    task_options: Optional[TaskOptions] = None