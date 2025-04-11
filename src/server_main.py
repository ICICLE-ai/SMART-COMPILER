from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from logging_utils.base_logger import get_logger
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.sse import SseServerTransport
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from dotenv import load_dotenv
import os

load_dotenv()

logger = get_logger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Any]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    db = {"db_name": "smart-compiler-db_mock"}
    try:
        yield db
    finally:
        # Cleanup on shutdown
        pass



mcp_server = FastMCP("smart-compiler-proxy", 
                     lifespan=app_lifespan, 
                     port=int(os.getenv("MCP_SERVER_PORT", 8000)), 
                     host=(os.getenv("MCP_SERVER_HOST","0.0.0.0")))



@mcp_server.tool("list_files")
def list_files(ctx: Context) -> str:
    
    req_session = ctx.request_context.session
    logger.debug(f"req_session: {req_session}")
    session =ctx.session
    logger.debug(f"session: {session}")
    
    json = ctx.model_dump_json()
    logger.debug(f"ctx: {json}")
    """
    List all files in the given path. Use to know what files are available for the user.
    Once, you can use the file_paths to use other tools.
    """
    files = os.listdir("/mnt/d/workspace/python/smart-compiler/examples")
    tree = os.walk("/mnt/d/workspace/python/smart-compiler/examples")
    logger.debug(f"files: {files}")
    tree_str = ""
    for root, dirs, files in tree:
        tree_str += f"{root}\n"
        for file in files:
            tree_str += f"  {file}\n"
        for dir in dirs:
            tree_str += f"  {dir}\n"
    logger.debug(f"tree_str: {tree_str}")
    return tree_str


from tools.profiler.mcp_tools import profiling_tools

for tool in profiling_tools:
    mcp_server.add_tool(tool)



if __name__ == "__main__": 
    mcp_server.run(transport="sse")
