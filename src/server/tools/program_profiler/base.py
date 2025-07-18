from typing import Optional
from shared.logging import get_logger
from abc import ABC, abstractmethod
from server.models.compiler import ProgramRuntimeOptions
from pathlib import Path

logger = get_logger()


DEFAULT_PROFILING_FILE_NAME = "profiling.txt"

class Profiler(ABC):
    @abstractmethod
    async def execute(self, file_path: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        """
        This method is used to profile a program.

        Args:
            file_path (str): The path to the file to profile.
            runtime_options (Optional[ProgramRuntimeOptions]): The runtime options to use for the profiling.

        Returns:
            Path: result_path: The path to the file containing the result of the profiling.
        """
        pass
    

class AugmentedProfiler(Profiler, ABC):
    def __init__(self, profiler: Optional[Profiler] = None):
        self.profiler = profiler
    
    async def execute(self, file_path: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        
        profiling_path_result = None
        if self.profiler:
            profiling_path_result = await self.profiler.execute(file_path, runtime_options)
            

        
        local_profiling_path = await self._execute(file_path, runtime_options)
        
        base_path = Path(file_path).parent
        profiling_path = f"{base_path}/{DEFAULT_PROFILING_FILE_NAME}"
        profiling_content = ""
        
        if profiling_path_result:
            with open(profiling_path_result, "r") as f:
                profiling_content += f.read()
        
        with open(local_profiling_path, "r") as f:
            profiling_content += f.read()
            
        with open(profiling_path, "w") as f:
            f.write(profiling_content)
                
        return Path(profiling_path)
    
    @abstractmethod
    async def _execute(self, file_path: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        raise NotImplementedError("Subclasses must implement this method")
