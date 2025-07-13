from sys import argv
from server.controllers.rest.rest_server import app as rest_server
from server.controllers.mcp.mcp_server import server as mcp_server, create_sse_server
import uvicorn
from server.config import MCP_SERVER_TRANSPORT, HOST, PORT

if __name__ == "__main__":
    if MCP_SERVER_TRANSPORT == "stdio" or (len(argv) > 1 and argv[1] == "stdio"):
        mcp_server.run_stdio_async()    
    else:
        rest_server.mount("/", create_sse_server(mcp_server))
    
    uvicorn.run(rest_server, host=HOST, port=PORT)