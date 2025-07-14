from server.application.program_profiler.base import ProfileProgram
from server.application.program_profiler.python_profiler import ProfilePythonProgram
from server.application.program_profiler.ollama_profiler import OllamaProfiler
from server.application.program_profiler.c_profiler import ProfileCProgram
from src.server.models.task import ProgrammingLanguage, ProfilingType
from typing import Optional


class ProfileProgramFactory():

    async def get_profile_program(self, language: ProgrammingLanguage, profiling_type: Optional[ProfilingType]) -> ProfileProgram:
        
        
        
        if profiling_type == ProfilingType.LLM or profiling_type is None:
            return OllamaProfiler()
        
                
        augmented_profiler = OllamaProfiler()
        
        if language == ProgrammingLanguage.PYTHON:
            return ProfilePythonProgram(profiler=augmented_profiler if profiling_type == ProfilingType.AGUMENTED else None)
        elif language == ProgrammingLanguage.C:
            return ProfileCProgram(profiler=augmented_profiler if profiling_type == ProfilingType.AGUMENTED else None)
        else:
            raise ValueError(f"Unsupported language: {language}")
       
            
singleton_profile_program_factory = ProfileProgramFactory()
            
async def get_profile_program_factory() -> ProfileProgramFactory:
    return singleton_profile_program_factory