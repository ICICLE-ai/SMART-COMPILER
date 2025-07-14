from typing import Optional
from server.application.program_profiler.base import ProfileProgram
from shared.logging import get_logger
from pathlib import Path
import subprocess 
from server.models.compiler import ProgramRuntimeOptions

logger = get_logger(__name__)

class ProfilePythonProgram(ProfileProgram):
    def __init__(self, profiler: Optional[ProfileProgram]):
        super().__init__(profiler)

    async def _execute(self, file_path: str, profiling_options: ProgramRuntimeOptions):
        

        logger.info(f"Profiling Python program: {file_path}")
        logger.debug(f"File path: {file_path}")
        
        logger.info("Profiling Python program with cProfile")
        
        run_command = "python"
        if profiling_options.command:
            run_command = profiling_options.command
            
        base_path = Path(file_path).parent
        profile_file_path = f"{base_path}/profile.prof"
        
        run_args = ["-m", "cProfile", "-o", profile_file_path, file_path]
        if profiling_options.args:
            run_args.extend(profiling_options.args)
            
        env = {}
        if profiling_options.envs:
            env.update(profiling_options.envs)
        
        cwd = "."
        if profiling_options.cwd:
            cwd = profiling_options.cwd
        
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
        
        return profile_file_path
