from server.tools.program_profiler.base import Profiler
from server.tools.program_profiler.python_profiler import PythonProfiler
from server.tools.program_profiler.ollama_profiler import OllamaProfiler
from server.tools.program_profiler.c_profiler import ProfileCProgram
from server.models.task import ProgrammingLanguage, ProfilingType
from typing import Optional
from shared.logging import get_logger

logger = get_logger()


class ProfilerToolFactory:

    async def get_profiler_tool(
        self, language: ProgrammingLanguage, profiling_type: Optional[ProfilingType]
    ) -> Profiler:

        if profiling_type is None:
            logger.warning("Profiling type is not set, using default: CLASSICAL")
            profiling_type = ProfilingType.CLASSICAL

        logger.info(
            f"Getting profiler tool for language: {language} and profiling type: {profiling_type}"
        )

        if profiling_type == ProfilingType.LLM:
            return OllamaProfiler()

        augmented_profiler = OllamaProfiler()
        profiler = None
        match language:
            case ProgrammingLanguage.PYTHON:
                profiler = PythonProfiler(
                    profiler=augmented_profiler
                    if profiling_type == ProfilingType.AUGMENTED
                    else None
                )
            case ProgrammingLanguage.C:
                profiler = ProfileCProgram(
                    profiler=augmented_profiler
                    if profiling_type == ProfilingType.AUGMENTED
                    else None
                )
        
        if profiler is None:
            logger.warning(f"No profiler tool found for language: {language} and profiling type: {profiling_type}")
            logger.warning(f"Using augmented profiler class: {augmented_profiler.__class__.__name__}")
            return augmented_profiler
        
        return profiler

        
        