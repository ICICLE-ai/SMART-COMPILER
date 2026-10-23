import os
from urllib.parse import urlsplit

from client.ollama.client import OllamaMCPClient
from client.openai.client import OpenAIResponsesMCPClient


class ClientFactory:
    def create_client(self, client_type: str = "llm"):
        """Select local Ollama or the OpenAI Responses API from LLM_HOST."""
        host = os.getenv("LLM_HOST") or os.getenv(
            "OLLAMA_HOST", "http://localhost:11434"
        )
        parsed = urlsplit(host)
        if (
            parsed.hostname in {"localhost", "127.0.0.1", "::1"}
            and parsed.port == 11434
            and not parsed.path.rstrip("/").endswith("/v1")
        ):
            return OllamaMCPClient()
        if client_type in {"llm", "ollama", "openai"}:
            return OpenAIResponsesMCPClient()
        raise ValueError(f"Unsupported client type: {client_type}")
