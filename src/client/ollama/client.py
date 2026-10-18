from typing import Any
from mcp import ClientSession
#from mcp.client.stdio import stdio_client
from mcp.types import TextResourceContents
from mcp.client.sse import sse_client

from ollama import Client
from client.abstract.base_client import AbstractMCPClient

from shared.logging import get_logger

from dotenv import load_dotenv
import os
import sys
import pathlib

from mcp.client.session import ListRootsFnT

from mcp.shared.context import RequestContext
from mcp.types import ListRootsResult, ErrorData, Root
from pydantic import FileUrl
# from Preparation.preparation import FolderTree


load_dotenv()

logger = get_logger()

class OllamaListRootsFnT(ListRootsFnT):
    async def __call__(self, context: RequestContext[ClientSession, Any]) -> ListRootsResult | ErrorData:
        return ListRootsResult(
            roots=[
                Root(
                    name="smart-compiler-db_mock",
                    uri=FileUrl(os.getenv("ALLOWED_PATHS", "")),
                )
            ]
        )

class OllamaMCPClient(AbstractMCPClient):
    def __init__(self):
        # Initialize session and client objects
        super().__init__()

        self._internal_ollama_client = Client(host=os.getenv("OLLAMA_HOST"))
        self.tools = []


    async def connect_to_server(self):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        

        server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")
        logger.debug(f"connecting to server at {server_url}")
  
        self.stdio, self.write = await self.exit_stack.enter_async_context(
            sse_client(server_url)
        )
        
        self.list_roots_callback=OllamaListRootsFnT()

        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write, list_roots_callback=self.list_roots_callback))
        
        if self.session is None:
            raise ValueError("Failed to create session")
   
        logger.debug(f"client session: {self.session}")
        
        
        await self.session.initialize()
        
        logger.debug(f"client session initialized")

        # List available tools
        response = await self.session.list_tools()
        
        logger.debug(f"\nConnected to server with tools: {[tool['function']['name'] for tool in self.tools]}")
        logger.debug("Tools' details")
        for tool in response.tools:
            logger.debug(f"Tool: {tool.name}")
            logger.debug(f"Description: {tool.description}")
            logger.debug(f"Input Schema: {tool.inputSchema}")
            logger.debug("\n")

        self.tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    },
                } for tool in response.tools]


    async def process_query(self, query: str) -> str:
        """Process a query with Ollama, executing MCP tool calls as needed."""
        system_prompt = """
You are SColer, an assistant specializing in compilers and C optimization.
Use the provided MCP tools whenever they can perform the requested work.
For a request to optimize a C file by path, call get_file_content with the exact path first, then call optimize_code_snippet with the returned C source and the requested profile. Never pass a file path or tool name as code_snippet. If the model mistakenly asks to optimize a path directly, the client will read that file before calling Cetus.
Available profiles include parallel, paw_tiling_nt, paw_tiling_lrw, paw_tiling_fixed32, reuse_analysis, and loop_interchange. Use parallel when the request does not name a profile.
Do not substitute GCC or LLVM shell commands for Cetus. Do not invent tool results or claim an optimization succeeded unless the tool returned the result.
""".strip()

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        if self.session is None:
            raise ValueError("Session not initialized")

        model = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        final_text = []
        last_file_read = None

        def result_text(result: Any) -> str:
            parts = []
            for item in result.content:
                if item.type == "text":
                    parts.append(item.text)
                elif item.type == "image":
                    parts.append("[Tool returned an image]")
                elif item.type == "resource":
                    resource = item.resource
                    parts.append(
                        resource.text
                        if isinstance(resource, TextResourceContents)
                        else str(resource.blob)
                    )
            return "\n".join(parts) or "Tool returned no text."

        for _ in range(8):
            response = self._internal_ollama_client.chat(
                model=model,
                messages=messages,
                tools=self.tools,
            )
            message = response.message
            logger.debug(f"response: {response}")

            if not message.tool_calls:
                if message.content:
                    final_text.append(message.content)
                break

            messages.append(message.model_dump(exclude_none=True))
            for tool in message.tool_calls:
                tool_name = tool.function.name
                tool_args = dict(tool.function.arguments)
                if tool_name == "optimize_code_snippet" and "profile" in tool_args:
                    tool_args.setdefault("optimization_profile", tool_args.pop("profile"))
                if tool_name == "optimize_code_snippet" and last_file_read is not None:
                    tool_args["code_snippet"] = last_file_read

                if tool_name == "optimize_code_snippet":
                    snippet = str(tool_args.get("code_snippet") or "").strip()
                    path = tool_args.pop("path", None)
                    file_placeholder = not snippet or (
                        len(snippet) < 256
                        and ("get_file_content" in snippet.lower() or snippet == "read_file")
                    )
                    if not path and (file_placeholder or snippet.endswith(".c")):
                        for token in query.split():
                            candidate = token.strip(" \t\r\n\"'`.,:;()[]{}<>")
                            if candidate.startswith("/") and candidate.endswith(".c"):
                                path = candidate
                                break

                    if path and (file_placeholder or snippet == str(path)):
                        path = str(path)
                        read_result = await self.session.call_tool(
                            "get_file_content", {"path": path}
                        )
                        read_text = result_text(read_result)
                        final_text.append(
                            f"[Calling tool get_file_content with path {path}]"
                        )
                        if getattr(read_result, "isError", False):
                            final_text.append(read_text)
                            return "\n".join(final_text)

                        profile = tool_args.get("optimization_profile", "parallel")
                        result = await self.session.call_tool(
                            "optimize_code_snippet",
                            {
                                "code_snippet": read_text,
                                "optimization_profile": profile,
                            },
                        )
                        final_text.append(
                            f"[Calling tool optimize_code_snippet with profile {profile}]"
                        )
                        final_text.append(result_text(result))
                        return "\n".join(final_text)

                result = await self.session.call_tool(tool_name, tool_args)
                text = result_text(result)
                if tool_name == "get_file_content" and not getattr(result, "isError", False):
                    last_file_read = text
                if tool_name == "optimize_code_snippet":
                    profile = tool_args.get("optimization_profile", "parallel")
                    final_text.append(
                        f"[Calling tool optimize_code_snippet with profile {profile}]"
                    )
                else:
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")
                final_text.append(text)
                messages.append({"role": "tool", "content": text})
                if tool_name == "optimize_code_snippet":
                    return "\n".join(final_text)
        else:
            final_text.append("Stopped after 8 MCP tool rounds.")

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        logger.debug("\nMCP Client Started!")
        logger.info("Type your queries or 'quit' to exit.")

        while True:
            try:
                               
                # folderProject = input("\nPlease provide the folder of your project: ").strip()
                # print("this is the folder project", folderProject)
                
                # TODO: Add the folder tree as a tool
                # folderTree = FolderTree(folderProject)
                # folderFile = input("\nPlease provide the file you want to analyze: ").strip()
                # foundFile = folderTree.find_file(folderFile)
                # if foundFile is None:
                #     print(f"File '{folderFile}' not found in the project.")
                #     continue
                # print(f"File '{folderFile}' found in the project.")
                
                # instruction = input("\nWhat do you want to do with the file? (Profile or Optimize): ").strip()
                
                #query = input("Escribe algo...\n")
                # query = f"Please {instruction} the file {foundFile['path']}"
                # query = f"Please {instruction}"
                # print(f"Query: {query}")
                
                print("Start chatting... Type quit to exit\n")  
                
                query = input("You: ")

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response + "\n")

            except Exception as e:
                logger.error(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()