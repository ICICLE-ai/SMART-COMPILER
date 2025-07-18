import os   
from typing import Optional
from server.tools.program_profiler.base import Profiler, AugmentedProfiler
from shared.logging import get_logger
from pathlib import Path
import subprocess 
from server.models.compiler import ProgramRuntimeOptions
import pstats

logger = get_logger()

DEFAULT_PYTHON_PROF_FILE_NAME = "python_profile.prof"
DEFAULT_PYTHON_PROF_TXT_FILE_NAME = "python_profile_stats.txt"

class PythonProfiler(AugmentedProfiler):
    def __init__(self, profiler: Optional[Profiler]):
        super().__init__(profiler)

    async def _execute(self, file_path_str: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        
        file_path = Path(file_path_str)

        logger.info(f"Profiling Python program: {file_path.absolute()}")
        logger.debug(f"File path: {file_path.absolute()}")
        
        logger.info("Profiling Python program with cProfile")
        
        run_command = "python"
        
        # if not runtime_options:
        #     raise ValueError("Runtime options is None. Default value should've been default")
        
        # if runtime_options.args is None:
        #     raise ValueError("Runtime options args is None")
        
        
  
        if runtime_options and runtime_options.command:
            run_command = runtime_options.command
            
        base_path = file_path.parent
        profile_file_path = Path(base_path) / DEFAULT_PYTHON_PROF_FILE_NAME
        
        if not profile_file_path.exists():
            profile_file_path.touch()
        
        run_args = ["-m", "cProfile", "-o", str(profile_file_path.absolute()), str(file_path.absolute())]
        if runtime_options and runtime_options.args:
            run_args.extend(runtime_options.args)        
                
        env = os.environ.copy()
        if runtime_options and runtime_options.envs:
            env.update(runtime_options.envs)
        
        cwd = file_path.parent.absolute()
        if runtime_options and runtime_options.cwd:
            cwd = Path(cwd) / runtime_options.cwd
        
        run_command = f"{run_command} {' '.join(run_args)}"
        
        logger.debug(f"CWD: {cwd}")
        
        cmd = run_command.split(" ")

        try:
            logger.debug(f"Running command: {run_command}")
            
            result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
            
            logger.debug(f"Result from running command: {result}")
            
            if not Path(profile_file_path).exists():
                logger.error(f"Profile file does not exist: {profile_file_path}")
                raise RuntimeError(f"Profile file does not exist: {profile_file_path}")
            
  
            logger.info(f"Printing profile stats to {DEFAULT_PYTHON_PROF_TXT_FILE_NAME}")
            profile_txt_file_path = base_path / DEFAULT_PYTHON_PROF_TXT_FILE_NAME
            with open(profile_txt_file_path, 'w') as f:
                profiler_stats = pstats.Stats(str(profile_file_path.absolute()), stream=f)
                profiler_stats.sort_stats('cumulative')
                profiler_stats.print_stats()
            

            if result.returncode != 0:
                logger.error(f"Failed to profile Python program: {result.stderr}")
                raise RuntimeError(f"Failed to profile Python program: {result.stderr}")
            
            logger.info(f"Profiling Python program: {profile_txt_file_path.absolute()}")
            logger.debug(f"File path: {profile_txt_file_path.absolute()}")
            
            return Path(profile_txt_file_path)
            
        except Exception as e:
            logger.error(f"Failed to profile Python program: {e}")
            raise RuntimeError(f"Failed to profile Python program: {e}")
        
        
        
