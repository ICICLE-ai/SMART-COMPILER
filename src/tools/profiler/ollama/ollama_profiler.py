from logging_utils.base_logger import get_logger
from tools.profiler.base_profiler import ProfilingTool
from ollama import Client

from dotenv import load_dotenv
import os

load_dotenv()

logger = get_logger(__name__)

class OllamaProfiler(ProfilingTool):
    def __init__(self):
        super().__init__()
        self.ollama_client = Client(host=os.getenv("OLLAMA_HOST","http://localhost:11434"))

    def _load_code(self, code_path: str) -> str:
        with open(code_path, "r") as file:
            return file.read()

    def _get_profiling_prompt(self, code: str) -> str:
        return f"Analyze and perform an static profiling of the following code: {code}"

    def profile(self, code_path: str) -> str:
        """
        Profiling tool for general purpose code.
        Use this tool to profile general purpose code.
        
        Args:
            code_path: Path to the code to profile.
        
        Returns:
            str: Profile of the code.
        """
        
        code = self._load_code(code_path)
        prompt = self._get_profiling_prompt(code)
        response = self.ollama_client.chat(
            model=os.getenv("MCP_SERVER_OLLAMA_MODEL","llama3.1:latest"),
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        logger.debug(f"Ollama profiler response: {response}")
        
        if response.message.content is None:
            raise ValueError("No response from ollama")
        

        return response.message.content
