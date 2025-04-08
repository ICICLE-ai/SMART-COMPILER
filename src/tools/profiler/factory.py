
from turtle import st
from tools.profiler.cetus.cetus_profiler import CetusProfiler
from tools.profiler.mock.analytic_profiler import AnalyticProfiler
from tools.profiler.ollama.ollama_profiler import OllamaProfiler
from .base_profiler import ProfilingTool


class ProfilingToolFactory:
    @staticmethod
    def get_profiling_tool(tool_name: str) -> ProfilingTool:
        if tool_name == "analytic_profiler":
            return AnalyticProfiler()
        elif tool_name == "general_purpose_profiler":
            return OllamaProfiler()
        elif tool_name == "c_profiler":
            return CetusProfiler(inherit_from=OllamaProfiler())
        elif tool_name == "python_profiler":
            return OllamaProfiler()
        else:
            raise NotImplementedError(f"Profiling tool {tool_name} not found")
        
    