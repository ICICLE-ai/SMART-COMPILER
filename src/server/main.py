import asyncio
from sys import argv

from server.infrastructure.controllers.rest.rest_server import app as rest_server
from server.infrastructure.controllers.mcp.mcp_server import server as mcp_server, create_sse_server
from uvicorn import Server, Config
from server.config import MCP_SERVER_TRANSPORT, HOST, PORT, ENABLE_REST_API
from shared.logging import get_logger

logger = get_logger()

class SmartCompilerServer(Server):    
    async def run(self, sockets=None):
        self.config.setup_event_loop()
        return await self.serve(sockets=sockets)


async def main():
    logger.info("Starting server")
    
    server_tasks = []
    
    if MCP_SERVER_TRANSPORT == "stdio" or (len(argv) > 1 and argv[1] == "stdio"):
        logger.info("Starting MCP server in stdio mode")
        server_tasks.append(mcp_server.run_stdio_async())
        
    elif ENABLE_REST_API:
        logger.info("Mounting MCP server in sse mode")
        rest_server.mount("/", create_sse_server(mcp_server))
    
    
    logger.info("Should Start REST API: " + ("Yes" if ENABLE_REST_API else "No"))
    
    if ENABLE_REST_API:
        server_config = Config(rest_server, host=HOST, port=PORT)
        smart_compiler_server = SmartCompilerServer(server_config)
        server_tasks.append(smart_compiler_server.run())
    
    if len(server_tasks) > 0:
        logger.info(f"Starting {len(server_tasks)} server tasks")
        await asyncio.gather(*server_tasks)


