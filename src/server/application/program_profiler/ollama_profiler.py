from server.application.program_profiler.base import ProfileProgram
from server.models.compiler import ProgramRuntimeOptions
from shared.logging import get_logger
from pathlib import Path
from typing import Optional

logger = get_logger(__name__)

class OllamaProfiler(ProfileProgram):
    def __init__(self, profiler: Optional[ProfileProgram] = None):
        super().__init__(profiler)

    async def execute(self, file_path: str, profiling_options: ProgramRuntimeOptions):
        logger.info(f"Profiling Python program with Ollama: {file_path}")
        file_content =  Path(file_path).read_text()
        logger.debug(f"File content: {file_content}")
        