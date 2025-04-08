from abc import ABC, abstractmethod


class ProfilingTool(ABC):
    @abstractmethod
    def profile(self, code_path: str) -> str:
        pass


