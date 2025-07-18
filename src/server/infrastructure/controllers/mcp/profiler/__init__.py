from server.infrastructure.controllers.mcp.profiler.api import  profile_project, profile_code_snippet
from mcp.server.fastmcp import FastMCP

tools = [
    profile_code_snippet,
    profile_project
]


def register_tools(server: FastMCP):
    for tool_function in tools:
        server.add_tool(tool_function)



