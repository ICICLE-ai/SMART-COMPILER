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

    