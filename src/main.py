from client.factory.base_factory import ClientFactory
from client.main import main as client_main
import asyncio
# import uvicorn
# from server.main import server_app

from dotenv import load_dotenv
import os

from logging_utils.base_logger import get_logger

load_dotenv()

logger = get_logger(__name__)


curr_proj_path = os.path.dirname(os.path.abspath(__file__))
default_server_script_path = os.path.join(curr_proj_path, "server", "main.py")

server_script_path = os.getenv("MCP_SERVER_SCRIPT_PATH", default_server_script_path)

logger.debug(f"Server script path: {server_script_path}")

async def main():
    # # Start the server in the background
    # server_config = uvicorn.Config(server_app, host="0.0.0.0", port=8000)
    # server = uvicorn.Server(server_config)
    # server_task = asyncio.create_task(server.serve())
    
    # # Give the server a moment to start
    # await asyncio.sleep(2)
    
    # Start the client
    client_factory = ClientFactory()
    client = client_factory.create_client("ollama")
    
    await client_main(client, server_script_path)
    
    # Wait for server to finish (this won't happen normally)
    # await server_task


if __name__ == "__main__":
    asyncio.run(main())