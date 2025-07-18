import asyncio
from sys import argv

from server.infrastructure.controllers.rest.rest_server import app as rest_server
from server.infrastructure.controllers.mcp.mcp_server import server as mcp_server, create_sse_server
import uvicorn
from server.config import MCP_SERVER_TRANSPORT, HOST, PORT, ENABLE_REST_API
from shared.logging import get_logger

logger = get_logger()


def main():
    logger.info("Starting server")
    if MCP_SERVER_TRANSPORT == "stdio" or (len(argv) > 1 and argv[1] == "stdio"):
        logger.info("Starting MCP server in stdio mode")
        asyncio.create_task(mcp_server.run_stdio_async())
    elif ENABLE_REST_API:
        logger.info("Mounting MCP server in sse mode")
        rest_server.mount("/", create_sse_server(mcp_server))
    
    
    logger.info("Should Start REST API: " + ("Yes" if ENABLE_REST_API else "No"))
    
    if ENABLE_REST_API:
        uvicorn.run(rest_server, host=HOST, port=PORT)

    
    

if __name__ == "__main__":
    main()