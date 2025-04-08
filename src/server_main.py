from contextlib import asynccontextmanager
from typing import Any, AsyncIterator
from logging_utils.base_logger import get_logger
from mcp.server.fastmcp import FastMCP, Context
from tools.profiler.factory import ProfilingToolFactory

from dotenv import load_dotenv
import os

load_dotenv()

logger = get_logger(__name__)

# from starlette.applications import Starlette
# from starlette.routing import Mount

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



mcp_server = FastMCP("smart-compiler-proxy", lifespan=app_lifespan)



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

# @mcp_server.tool("profiling")
# def profiling(profiling_tool: str, code_path: str) -> str:
#     """

#     Args:
#         profiling_tool (str): name of the profiling tool to use. Available tools: analytic_profiler (fake profiler for testing) | general_purpose_profiler (recommended)
#         code_path (str): path to the code to profile

#     Returns:
#         str: profiling results
#     """
#     profiling_factory = ProfilingToolFactory()
#     profiler = profiling_factory.get_profiling_tool(profiling_tool)
#     return profiler.profile(code_path)

# @mcp_server.tool("code_review")
# def code_review(code_path: str) -> str:
#     """
#     Code review tool not implemented
#     """
#     return "Code review tool not implemented"

from tools.profiler.mcp_tools import profiling_tools

for tool in profiling_tools:
    mcp_server.add_tool(tool)


# TODO: NEED TO BE REVIEWED FOR PROPER IMPLEMENTATION
# server_app = Starlette(
#     routes=[
#         Mount("/", app=mcp_server.sse_app()),
#     ]
# )

if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(server_app, host=os.getenv("MCP_SERVER_HOST"), port=os.getenv("MCP_SERVER_PORT"))
    transport_str = os.getenv("MCP_SERVER_TRANSPORT", "stdio")
    
    # Use direct literals based on the environment value
    if transport_str == "sse":
        mcp_server.run(transport="sse")
    else:
        mcp_server.run(transport="stdio")
