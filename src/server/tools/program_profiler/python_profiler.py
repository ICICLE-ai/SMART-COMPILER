from typing import Optional
from server.tools.program_profiler.base import Profiler, AugmentedProfiler
from shared.logging import get_logger
from pathlib import Path
import subprocess 
from server.models.compiler import ProgramRuntimeOptions

logger = get_logger(__name__)

class PythonProfiler(AugmentedProfiler):
    def __init__(self, profiler: Optional[Profiler]):
        super().__init__(profiler)

    async def _execute(self, file_path: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        

        logger.info(f"Profiling Python program: {file_path}")
        logger.debug(f"File path: {file_path}")
        
        logger.info("Profiling Python program with cProfile")
        
        run_command = "python"
        
        if not runtime_options:
            raise ValueError("Runtime options is None. Default value should've been default")
        
        if runtime_options.args is None:
            raise ValueError("Runtime options args is None")
        
  
        if runtime_options.command:
            run_command = runtime_options.command
            
        base_path = Path(file_path).parent
        profile_file_path = f"{base_path}/profile.prof"
        
        run_args = ["-m", "cProfile", "-o", profile_file_path, file_path]
        if runtime_options.args:
            run_args.extend(runtime_options.args)        
                
        env = {}
        if runtime_options.envs:
            env.update(runtime_options.envs)
        
        cwd = "."
        if runtime_options.cwd:
            cwd = runtime_options.cwd
        
        run_command = f"{run_command} {run_args}"
        if env:
            run_command = f"env {env} {run_command}"
        
        logger.debug(f"Running command: {run_command}")
        result = subprocess.run(run_command, cwd=cwd, env=env, capture_output=True, text=True)
        
        logger.debug(f"Result: {result}")
        
        if result.returncode != 0:
            logger.error(f"Failed to profile Python program: {result.stderr}")
            raise RuntimeError(f"Failed to profile Python program: {result.stderr}")
        
        logger.info(f"Profiling Python program: {file_path}")
        logger.debug(f"File path: {file_path}")
        
        return Path(profile_file_path)
