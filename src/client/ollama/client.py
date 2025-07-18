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
        
        env = os.environ.copy()
                
        server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

  
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
        """Process a query using LLM and available tools"""
        system_prompt = f"""
            You are a helpful assistant expert in compilers. You're name is SColer.
        """
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": query
            }
        ]
        # Process response and handle tool calls
        tool_results = []
        final_text = []
        

        response = self._internal_ollama_client.chat(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
            messages=messages,
            tools=self.tools,
        )
        
        logger.debug(f"response: {response}")

   
        
        if(self.session is None):
            raise ValueError("Session not initialized")

        if response.message.content:
            final_text.append(response.message.content)
            
        elif response.message.tool_calls:
            for tool in response.message.tool_calls:
                tool_name = tool.function.name
                tool_args = tool.function.arguments

                # Execute tool call
                result = await self.session.call_tool(tool_name, dict(tool_args))
                tool_results.append({"call": tool_name, "result": result})
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                content = result.content[0]
                if(content.type == "text"):
                    # Continue conversation with tool results
                    messages.append({
                        "role": "user",
                        "content": content.text
                    })
                    
                elif(content.type == "image"):
                    # Continue conversation with tool results
                    messages.append({
                        "role": "user",
                        "content": content.data
                    })
                elif(content.type == "resource"):
                    resource = content.resource
                    content_data = resource.text if isinstance(resource, TextResourceContents) else resource.blob
                    # Continue conversation with tool results
                    messages.append({
                        "role": "user",
                        "content": content_data
                    })

                response = self._internal_ollama_client.chat(
                    model=os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
                    messages=messages,
                )

                final_text.append(response.message.content)

        return "\n".join(final_text)




    async def chat_loop(self):
        """Run an interactive chat loop"""
        logger.debug("\nMCP Client Started!")
        logger.info("Type your queries or 'quit' to exit.")

        while True:
            try:
                               
                folderProject = input("\nPlease provide the folder of your project: ").strip()
                print("this is the folder project", folderProject)
                
                # TODO: Add the folder tree as a tool
                # folderTree = FolderTree(folderProject)
                # folderFile = input("\nPlease provide the file you want to analyze: ").strip()
                # foundFile = folderTree.find_file(folderFile)
                # if foundFile is None:
                #     print(f"File '{folderFile}' not found in the project.")
                #     continue
                # print(f"File '{folderFile}' found in the project.")
                
                instruction = input("\nWhat do you want to do with the file? (Profile or Optimize): ").strip()
                
                #query = input("Escribe algo...\n")
                # query = f"Please {instruction} the file {foundFile['path']}"
                query = f"Please {instruction}"
                print(f"Query: {query}")
                

                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + response)

            except Exception as e:
                logger.error(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()