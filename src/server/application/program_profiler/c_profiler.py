from typing import Optional
from server.application.program_profiler.base import ProfileProgram
from shared.logging import get_logger
from pathlib import Path
from server.models.compiler import ProgramRuntimeOptions

logger = get_logger(__name__)


class ProfileCProgram(ProfileProgram):
    def __init__(self, profiler: Optional[ProfileProgram] = None):
        super().__init__(profiler)

    async def execute(self, file_path: str, profiling_options: ProgramRuntimeOptions):
        
        
        logger.info(f"Profiling C program: {file_path}")
        logger.debug(f"Profiling options: {profiling_options}")
        
        # TODO: Implement C profiling
        
