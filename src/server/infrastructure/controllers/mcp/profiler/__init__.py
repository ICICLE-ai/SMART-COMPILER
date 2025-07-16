from server.infrastructure.controllers.mcp.profiler.main import profile_single_code_file, profile_project
from mcp.server.fastmcp import FastMCP

tools = [
    profile_single_code_file,
    profile_project
]


def register_tools(server: FastMCP):
    for tool_function in tools:
        server.add_tool(tool_function)



