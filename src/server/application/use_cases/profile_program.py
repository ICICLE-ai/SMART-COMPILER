from server.models.task import ProgrammingLanguage, ProfilingType, ProgramRuntimeOptions
from server.tools.program_profiler.factory import ProfilerToolFactory
from typing import Optional
from pathlib import Path
import uuid
class ProfileProgram:
    
    def __init__(self, profiler_tool_factory: ProfilerToolFactory):
        self.profiler_tool_factory = profiler_tool_factory
        
        
    async def execute(self, code_snippet: str, language: ProgrammingLanguage, profiling_type: Optional[ProfilingType] = ProfilingType.CLASSICAL, runtime_options: Optional[ProgramRuntimeOptions] = None) -> Path:
        profiler_tool = await self.profiler_tool_factory.get_profiler_tool(language, profiling_type)
        
        uuid_str = str(uuid.uuid4())
        
        temp_file_path = Path(f"/tmp/{uuid_str}.{language.value}")
        
        temp_file_path.write_text(code_snippet)
        
        return await profiler_tool.execute(str(temp_file_path.absolute()), runtime_options)