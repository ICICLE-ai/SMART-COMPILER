from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings
from mcp.server.sse import SseServerTransport
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from starlette.routing import Route, Mount
from starlette.applications import Starlette


from shared.logging import get_logger
from server.controllers.mcp.profiler import register_tools as register_profiler_tools

logger = get_logger(__name__)

mcp_settings = Settings(
    debug=True,
    log_level="DEBUG",
    host="0.0.0.0",
    port=8000,
    sse_path="/sse",
    message_path="/messages/"
)   

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Any]:
    """Manage application lifecycle with type-safe context"""
    logger.info("MCP server started")
    yield
    logger.info("MCP server stopped")


server  = FastMCP("SmartCompiler-MCP", mcp_settings, lifespan=app_lifespan)

register_profiler_tools(server)


def create_sse_server(mcp: FastMCP):
    """Create a Starlette app that handles SSE connections and message handling"""
    transport = SseServerTransport("/messages/")

    # Define handler functions
    async def handle_sse(request):
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp._mcp_server.run(
                streams[0], streams[1], mcp._mcp_server.create_initialization_options()
            )

    # Create Starlette routes for SSE and message handling
    routes = [
        Route("/sse", endpoint=handle_sse),
        Mount("/messages", app=transport.handle_post_message),
    ]

    # Create a Starlette app
    return Starlette(routes=routes)
