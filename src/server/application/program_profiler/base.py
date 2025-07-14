from typing import Optional
from shared.logging import get_logger
from abc import ABC, abstractmethod
from server.models.compiler import ProgramRuntimeOptions
from server.application.program_profiler.base import ProfileProgram
from pathlib import Path

logger = get_logger(__name__)

class ProfileProgram(ABC):
    def __init__(self, profiler: Optional[ProfileProgram] = None):
        self.profiler = profiler
    
    async def execute(self, file_path: str, profiling_options: ProgramRuntimeOptions) -> str:
        
        profiling_path_result = None
        if self.profiler:
            profiling_path_result = await self.profiler.execute(file_path, profiling_options)
            

        
        local_profiling_path = await self._execute(file_path, profiling_options)
        
        base_path = Path(file_path).parent
        profiling_path = f"{base_path}/profiling.txt"
        profiling_content = ""
        
        if profiling_path_result:
            with open(profiling_path_result, "r") as f:
                profiling_content += f.read()
        
        with open(local_profiling_path, "r") as f:
            profiling_content += f.read()
            
        with open(profiling_path, "w") as f:
            f.write(profiling_content)
                
        return profiling_path
    
    async def _execute(self, file_path: str, profiling_options: ProgramRuntimeOptions) -> str:
        raise NotImplementedError("Subclasses must implement this method")
        pass
