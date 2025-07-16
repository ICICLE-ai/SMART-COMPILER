from json import JSONEncoder, JSONDecoder
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

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
    runtime_options: Optional[ProgramRuntimeOptions]
    path: str
    created_at: datetime
    updated_at: datetime | None
    status: TaskStatus
    result: TaskResult | None
    internal_job_id: Optional[str] = None


class ProfilingType(Enum):
    CLASSICAL = "classical"
    LLM = "llm"
    AUGMENTED = "augmented"
    
    

@dataclass
class TaskOptions():
    profiling_type: Optional[ProfilingType]


@dataclass
class CompilerTaskRequest():
    task_type: TaskType
    language: ProgrammingLanguage
    path: str
    runtime_options: Optional[ProgramRuntimeOptions] = None
    task_options: Optional[TaskOptions] = None
    
    
class CompilerTaskEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, CompilerTask):
            return o.__dict__
        elif isinstance(o, ProgramRuntimeOptions):
            return o.__dict__
        elif isinstance(o, TaskResult):
            return o.__dict__
        elif isinstance(o, TaskId):
            return o.value
        elif isinstance(o, TaskType):
            return o.value
        elif isinstance(o, ProgrammingLanguage):
            return o.value
        elif isinstance(o, TaskStatus):
            return o.value
        elif isinstance(o, ProfilingType):
            return o.value
        return super().default(o)
    
class CompilerTaskDecoder(JSONDecoder):
    def default(self, o):
        if isinstance(o, dict):
            return CompilerTask(**o)
        elif isinstance(o, dict):
            return ProgramRuntimeOptions(**o)
        elif isinstance(o, dict):
            return TaskResult(**o)
        elif isinstance(o, str):
            return TaskId(o)
        elif isinstance(o, str):
            return TaskType(o)
        elif isinstance(o, str):
            return ProgrammingLanguage(o)
        elif isinstance(o, str):
            return TaskStatus(o)
        elif isinstance(o, str):
            return ProfilingType(o)
        return o