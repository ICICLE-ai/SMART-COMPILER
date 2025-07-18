import os
from shared.logging import get_logger

logger = get_logger()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HOST = os.getenv("HOST", "0.0.0.0")
try:
    PORT = int(os.getenv("PORT", "8000"))
except ValueError:
    logger.warning("Invalid PORT environment variable, falling back to 8000")
    PORT = 8000
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
MCP_SERVER_TRANSPORT = os.getenv("MCP_SERVER_TRANSPORT", "sse")
ENABLE_REST_API = bool(os.getenv("ENABLE_REST_API", "false"))

logger.debug(f"Server config: LOG_LEVEL={LOG_LEVEL}, HOST={HOST}, PORT={PORT}, OLLAMA_HOST={OLLAMA_HOST}, OLLAMA_MODEL={OLLAMA_MODEL}, MCP_SERVER_TRANSPORT={MCP_SERVER_TRANSPORT}")
