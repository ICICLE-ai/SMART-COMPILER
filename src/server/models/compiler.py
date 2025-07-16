from dataclasses import dataclass
from typing import Optional

@dataclass
class ProgramRuntimeOptions():
    command: Optional[str]
    args: Optional[list[str]]
    envs: Optional[dict[str, str]]
    cwd: Optional[str]
    timeout: Optional[int]
    max_memory: Optional[int]
    compilation_args: Optional[list[str]]
    compilation_envs: Optional[dict[str, str]]
    compilation_cwd: Optional[str]
    compilation_max_memory_in_mb: Optional[int]
    compilation_timeout: Optional[int]

    