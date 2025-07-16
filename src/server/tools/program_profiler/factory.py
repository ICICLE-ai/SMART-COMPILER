from server.tools.program_profiler.base import Profiler
from server.tools.program_profiler.python_profiler import PythonProfiler
from server.tools.program_profiler.ollama_profiler import OllamaProfiler
from server.tools.program_profiler.c_profiler import ProfileCProgram
from server.models.task import ProgrammingLanguage, ProfilingType
from typing import Optional
from shared.logging import get_logger

logger = get_logger(__name__)


class ProfilerToolFactory:

    async def get_profiler_tool(
        self, language: ProgrammingLanguage, profiling_type: Optional[ProfilingType]
    ) -> Profiler:

        if profiling_type is None:
            logger.warning("Profiling type is not set, using default: AUGMENTED")
            profiling_type = ProfilingType.AUGMENTED

        logger.info(
            f"Getting profiler tool for language: {language} and profiling type: {profiling_type}"
        )

        if profiling_type == ProfilingType.LLM:
            return OllamaProfiler()

        augmented_profiler = OllamaProfiler()

        if language == ProgrammingLanguage.PYTHON:
            return PythonProfiler(
                profiler=(
                    augmented_profiler
                    if profiling_type == ProfilingType.AUGMENTED
                    else None
                )
            )
        elif language == ProgrammingLanguage.C:
            return ProfileCProgram(
                profiler=(
                    augmented_profiler
                    if profiling_type == ProfilingType.AUGMENTED
                    else None
                )
            )
        else:
            raise ValueError(f"Unsupported language: {language}")
    