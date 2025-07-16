from server.tools.program_profiler.base import Profiler, AugmentedProfiler
from server.models.compiler import ProgramRuntimeOptions
from shared.logging import get_logger
from pathlib import Path
from typing import Optional
from ollama import Client
import os
logger = get_logger(__name__)

class OllamaProfiler(AugmentedProfiler):
    def __init__(self, profiler: Optional[Profiler] = None):
        super().__init__(profiler)
        self.ollama_client = Client(host=os.getenv("OLLAMA_HOST","http://localhost:11434"))

    def _get_profiling_prompt(self, code: str, runtime_options: Optional[ProgramRuntimeOptions]) -> str:
        return f"Analyze and perform an static profiling of the following code: {code} with the following runtime options: {runtime_options}"
        

    async def _execute(self, file_path: str, runtime_options: Optional[ProgramRuntimeOptions]) -> Path:
        logger.info(f"Profiling Python program with Ollama: {file_path}")
        file_content =  Path(file_path).read_text()
        logger.debug(f"File content: {file_content}")
        
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
        
        return Path(response.message.content)
        