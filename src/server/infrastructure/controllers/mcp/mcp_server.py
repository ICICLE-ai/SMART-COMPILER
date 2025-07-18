from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings
from mcp.server.sse import SseServerTransport
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Literal
from starlette.routing import Route, Mount
from starlette.applications import Starlette
from server.config import LOG_LEVEL, PORT, HOST

from shared.logging import get_logger
from server.infrastructure.controllers.mcp.profiler.api import register_api as register_profiler_api

logger = get_logger()

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Any]:
    """Manage application lifecycle with type-safe context"""
    logger.info("MCP server started")
    yield
    logger.info("MCP server stopped")


def get_mcp_log_level(log_level: str) -> Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    """Get the MCP log level from the log level"""
    return "INFO" if log_level == "INFO" else "WARNING" if log_level == "WARNING" else "CRITICAL" if log_level == "CRITICAL" else "DEBUG" if log_level == "DEBUG" else "ERROR"

mcp_settings = Settings(
    debug=True if LOG_LEVEL == "DEBUG" else False,
    log_level=get_mcp_log_level(LOG_LEVEL),
    host=HOST,
    port=PORT,
    lifespan=app_lifespan
)   


server  = FastMCP("SmartCompiler-MCP", settings=mcp_settings)

register_profiler_api(server)


def create_sse_server(mcp: FastMCP):
    """Create a Starlette app that handles SSE connections and message handling"""
    transport = SseServerTransport("/messages")

    # Define handler functions
    async def handle_sse(request):
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp._mcp_server.run(
                streams[0], streams[1], mcp._mcp_server.create_initialization_options()
            )

    routes = [
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=transport.handle_post_message),
    ]

    # Create a Starlette app
    return Starlette(routes=routes)
