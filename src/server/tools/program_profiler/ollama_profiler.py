from server.tools.program_profiler.base import Profiler, AugmentedProfiler
from server.models.compiler import ProgramRuntimeOptions
from shared.logging import get_logger
from pathlib import Path
from typing import Optional
from ollama import Client
import os
logger = get_logger()

DEFAULT_PROFILING_FILE_NAME = "ollama_profiling.txt"

PROMPT_TEMPLATE = """
Analyze and perform an static profiling of the following code.

Code:
{code}

Runtime options:
{runtime_options}

Return the profiling results in the following format:

{profiling_results}

""" 

class OllamaProfiler(AugmentedProfiler):
    def __init__(self, profiler: Optional[Profiler] = None):
        super().__init__(profiler)
        self.ollama_client = Client(host=os.getenv("OLLAMA_HOST","http://localhost:11434"))

    def _get_profiling_prompt(self, code: str, runtime_options: Optional[ProgramRuntimeOptions]) -> str:
        if not runtime_options:
            return f"Analyze and perform an static profiling of the following code: {code}"
        else:
            return f"Analyze and perform an static profiling of the following code: {code} considering the following runtime options: {runtime_options}"
        

    async def _execute(self, file_path: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        logger.info(f"Profiling program with Ollama: {file_path}")
        file_content =  Path(file_path).read_text()
        
        prompt = self._get_profiling_prompt(file_content, runtime_options)
        
        response = self.ollama_client.chat(
            model=os.getenv("MCP_SERVER_OLLAMA_MODEL","llama3.1:latest"),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        logger.debug(f"Ollama profiler response: {response}")
        
        if response.message.content is None:
            raise ValueError("No response from ollama")
        
        profile_file_path = Path(file_path).parent / DEFAULT_PROFILING_FILE_NAME
        profile_file_path.write_text(response.message.content)
        return profile_file_path
        