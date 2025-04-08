import os
from logging_utils.base_logger import get_logger
from typing import Dict
from .factory import ProfilingToolFactory

logger = get_logger(__name__)

def c_profiler(code_path: str) -> str:
    """
    Profiling tool for C code.
    Use this tool to profile C code.
    
    Args:
        code_path: Path to the C code to profile. This contains only a single .c file. This does not support other file types or directories.
        
    Returns:
        str: Profile of the C code.
    """
    profiling_tool = ProfilingToolFactory.get_profiling_tool(tool_name="c_profiler")
    profiling_info = profiling_tool.profile(code_path)

    base_dir = os.path.dirname(code_path)
    analysis_file_path = os.path.join(base_dir, "c_analysis.txt")
    
    
    with open(analysis_file_path, "w") as file:
        file.write(profiling_info)
    
    logger.info(f"Profiling info stored in {analysis_file_path}")
    return profiling_info

def python_profiler(code_path: str) -> str:
    """
    Profiling tool for Python code.
    Use this tool to profile Python code.
    
    Args:
        code_path: Path to the Python code to profile. This contains only a single .py file. This does not support other file types or directories.
        
    Returns:
        str: Profile of the Python code.
    """
    profiling_tool = ProfilingToolFactory.get_profiling_tool("python_profiler")
    profiling_info = profiling_tool.profile(code_path)
    
    base_dir = os.path.dirname(code_path)
    analysis_file_path = os.path.join(base_dir, "python_analysis.txt")
    
    
    with open(analysis_file_path, "w") as file:
        file.write(profiling_info)
        
    logger.info(f"Profiling info stored in {analysis_file_path}")
    
    return profiling_info

def general_purpose_profiler(code_path: str) -> str:
    """
    Profiling tool for general purpose code.
    Use this tool to profile general purpose code.
    
    Args:
        code_path: Path to the code to profile. This contains only a single file. This does not support other file types or directories.
        
    Returns:
        str: Profile of the code.
    """
    profiling_tool = ProfilingToolFactory.get_profiling_tool("general_purpose_profiler")
    profiling_info = profiling_tool.profile(code_path)

    base_dir = os.path.dirname(code_path)
    analysis_file_path = os.path.join(base_dir, "general_purpose_analysis.txt")
    
    
    with open(analysis_file_path, "w") as file:
        file.write(profiling_info)
    
    logger.info(f"Profiling info stored in {analysis_file_path}")
    
    return profiling_info

def python_bulk_profiler(directory: str) -> Dict[str, str]:
    """
    Profile multiple Python files in a directory. Also, profiles a Python project as a whole.
    This is ideal for bulk profiling, profiling projects with multiple files or directories.
    
    Args:   
        directory: Path to the directory containing the Python code to profile.
        
    Returns:
        Dict[str, str]: A dictionary where the key is the path of the original file and the value is the path to the profiling info.
    """
    
    profiling_tool = ProfilingToolFactory.get_profiling_tool("python_profiler")
    
    base_dir = os.path.dirname(directory)
    
    profiled_files = {}
    # Process each Python file in the directory
    if os.path.isdir(directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    file_name = os.path.basename(file_path)
                    file_dir = os.path.dirname(file_path)
                    
                    logger.debug(f"Profiling Python file: {file_path}")
                    try:
                        file_profiling_info = profiling_tool.profile(file_path)
                        
                        profiling_file_path = os.path.join(base_dir, f"{file_dir}/{file_name}_profiling_info.txt")
                        
                        logger.debug(f"Profiling info stored at {profiling_file_path}")
                            
                        with open(profiling_file_path, "w") as file:
                            file.write(file_profiling_info)
                        
                        profiled_files[file_path] = profiling_file_path
                        
                    except Exception as e:
                        logger.error(f"Error profiling {file_path}: {str(e)}")
                        profiled_files[file_path] = f"Error profiling {file_path}: {str(e)}\n{'='*80}\n"
        
    else:
        # If code_dir is actually a single file
        logger.warning(f"{directory} is not a directory. Profiling as a single file.")
        return {"error": f"{directory} is not a directory."}
    
    
    return profiled_files
    
    
    
    


profiling_tools = [
   c_profiler,
   python_profiler,
   general_purpose_profiler,
   python_bulk_profiler
]