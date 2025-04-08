import os
from tools.profiler.base_profiler import ProfilingTool
from subprocess import run as run_command
from logging_utils.base_logger import get_logger

logger = get_logger(__name__)

class CetusProfiler(ProfilingTool):
    
    def __init__(self, inherit_from: ProfilingTool | None = None):
        super().__init__()
        
        self.inherit_from = inherit_from

    def profile(self, code_path: str) -> str:
        """
        Profiling tool for C code.
        Use this tool to profile C code.
        
        Args:
            code_path: Path to the C code to profile.
        
        Returns:
            str: Profile of the C code.
        """
        
        
        try:
            source_file_name = os.path.basename(code_path)
            
            logger.debug(f"Source file name: {source_file_name}")
            
            source_file_dir = os.path.dirname(code_path)
            logger.debug(f"Source file dir: {source_file_dir}")
            
            profile_name = source_file_name.split(".")[0]+"-profile"
            profile_dir = os.path.join(source_file_dir)
            profile_path = os.path.join(profile_dir, profile_name)
            
            #compile using gcc
            compile_cmd = ["gcc", "-pg", "-o", profile_path, code_path]
            logger.debug(f"Compile command: {compile_cmd}")
            compile_result = run_command(compile_cmd, capture_output=True, text=True)
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
            result = run_command(cmd, capture_output=True, text=True, shell=True)
            
            logger.debug(f"Cetus profile result: {result.stdout}")
            
            with open(analysis_file_path, "r") as file:
                analysis = file.read()
                
            logger.debug(f"Analysis: {analysis}")
            
            inherit_profile = ""
            
            if self.inherit_from is not None:
                inherit_profile = self.inherit_from.profile(code_path)
                
            logger.debug(f"Inherit profile: {inherit_profile}")
            
            profile_result = f"""FROM STATIC ANALYSIS:
            {inherit_profile}
            FROM DYNAMIC ANALYSIS:
            {analysis}
            """
        except Exception as e:
            logger.error(f"Error profiling C code: {e}")
            raise e
        
        return profile_result
