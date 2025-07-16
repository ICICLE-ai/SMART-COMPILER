from typing import Optional
from server.tools.program_profiler.base import Profiler, AugmentedProfiler
from shared.logging import get_logger
from pathlib import Path
import resource
from server.models.compiler import ProgramRuntimeOptions
import os
from subprocess import run as run_command, CalledProcessError
import traceback
from typing import Optional

logger = get_logger(__name__)


class ProfileCProgram(AugmentedProfiler):
    def __init__(self, profiler: Optional[Profiler] = None):
        super().__init__(profiler)
        
    def _set_compilation_limits(self,  runtime_options: ProgramRuntimeOptions):
        if runtime_options.compilation_max_memory_in_mb:
            resource.setrlimit(resource.RLIMIT_AS, (runtime_options.compilation_max_memory_in_mb * 1024 * 1024, runtime_options.compilation_max_memory_in_mb * 1024 * 1024))
        if runtime_options.compilation_timeout:
            resource.setrlimit(resource.RLIMIT_CPU, (runtime_options.compilation_timeout, runtime_options.compilation_timeout))

    async def _execute(self, file_path: str, runtime_options: ProgramRuntimeOptions) -> Path:
        
        """
        Profiling tool for C code.
        Use this tool to profile C code.
        
        Args:
            code_path: Path to the C code to profile.
        
        Returns:
            str: Profile of the C code.
        """
        
        
        try:
            source_file_name = os.path.basename(file_path)
            
            logger.debug(f"Source file name: {source_file_name}")
            
            source_file_dir = os.path.dirname(file_path)
            logger.debug(f"Source file dir: {source_file_dir}")
            
            profile_name = source_file_name.split(".")[0]+"-profile"
            profile_dir = os.path.join(source_file_dir)
            profile_path = os.path.join(profile_dir, profile_name)
            
            #compile using gcc
            compile_cmd = ["gcc", "-pg", "-o", profile_path, file_path]
            envs ={}
            cwd = "."
            
            if runtime_options.compilation_args:
                compile_cmd.extend(runtime_options.compilation_args)
            if runtime_options.compilation_envs:
                envs.update(runtime_options.compilation_envs)
            if runtime_options.compilation_cwd:
                cwd = runtime_options.compilation_cwd
            
            
            logger.debug(f"Compile command: {compile_cmd}")
            compile_result = run_command(compile_cmd, capture_output=True, text=True, cwd=cwd, env=envs)
            logger.debug(f"Compile result: {compile_result.stdout}")
            
            #run the compiled program
            run_cmd = [f"cd {profile_dir} && {profile_path}"]
            logger.debug(f"Run command: {run_cmd}")
            
            run_result = run_command(run_cmd, capture_output=True, text=True, shell=True)
            logger.debug(f"Run result: {run_result.stdout}")
            
            
            #create analysis file
            analysis_file_path = os.path.join(profile_dir, "cetus_analysis.txt")
            
            #create file if it doesn't exist
            if not os.path.exists(analysis_file_path):
                open(analysis_file_path, "w").close()
        
            logger.debug(f"Analysis file path: {analysis_file_path}")
            
            gmon_file_path = os.path.join(profile_dir, "gmon.out")
            logger.debug(f"Gmon file path: {gmon_file_path}")
            
            cmd = [f"gprof {profile_path} {gmon_file_path} > {analysis_file_path}"]
            
            logger.debug(f"Gprof command: {cmd}")
            result = run_command(cmd, capture_output=True, text=True, shell=True, preexec_fn=self._set_compilation_limits(runtime_options))
            
            logger.debug(f"Cetus profile result: {result.stdout}")
            
            with open(analysis_file_path, "r") as file:
                analysis = file.read()
                
            logger.debug(f"Analysis: {analysis}")
                        
            profile_result = analysis
            
        except CalledProcessError as e:
            logger.error(f"Error profiling C code during COMMANDS execution: {e}")
            traceback.print_exc()
            raise e
            
        except OSError as e:
            logger.error(f"Error profiling C code during OS Runtime execution: {e}")
            traceback.print_exc()
            raise e
        
        except Exception as e:
            logger.error(f"Error profiling C code during profiling process: {e}")
            traceback.print_exc()
            raise e
        
        return Path(profile_result)        
