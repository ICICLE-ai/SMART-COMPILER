from json import JSONEncoder, JSONDecoder
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List

from server.models.compiler import ProgramRuntimeOptions
from shared.logging import get_logger

logger = get_logger()

class TaskType(Enum):
    PROFILE = "profile"
    OPTIMIZE = "optimize"
    
    def __repr__(self):
        return self.value
    
    def __str__(self):
        return self.value

    
class ProgrammingLanguage(Enum):
    PYTHON = "python"
    C = "c"
    

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

    def __repr__(self):
        return self.value
    
    def __str__(self):
        return self.value

@dataclass(frozen=True)
class TaskId():
    value: str
    
    def __repr__(self):
        return self.value
    
    def __str__(self):
        return self.value
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("Task ID cannot be empty")

@dataclass
class TaskResult():
    file_path: Optional[str] = None
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
    
    def __repr__(self):
        return self.value
    
    def __str__(self):
        return self.value
    
    

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
        logger.debug(f"CompilerTaskDecoder default: {o}")
        if not isinstance(o, dict):
            return o

        # TODO: from here everything is dict.
        if "file_path" in o and "error" in o:
            logger.debug(f"TaskResult decoder: {o}")
            return TaskResult(file_path=o.get("file_path", None), error=o.get("error", None))
        
        elif "command" in o or "args" in o or "envs" in o or "cwd" in o or "timeout_in_seconds" in o or "max_memory_in_mb" in o or "compilation_args" in o or "compilation_command" in o or "compilation_envs" in o or "compilation_cwd" in o or "compilation_max_memory_in_mb" in o or "compilation_timeout_in_seconds" in o or "compilation_max_memory" in o:
            logger.debug(f"ProgramRuntimeOptions decoder: {o}")
            return ProgramRuntimeOptions(
                command=o.get("command", None),
                args=o.get("args", None),
                envs=o.get("envs", None),
                cwd=o.get("cwd", None),
                timeout_in_seconds=o.get("timeout", None),
                max_memory_in_mb=o.get("max_memory", None),
                compilation_args=o.get("compilation_args", None),
                compilation_envs=o.get("compilation_envs", None),
                compilation_cwd=o.get("compilation_cwd", None),
                compilation_max_memory_in_mb=o.get("compilation_max_memory_in_mb", None),
                compilation_timeout_in_seconds=o.get("compilation_timeout", None),
            )
        
        raise ValueError(f"Unknown decoder: {o}")
    
    