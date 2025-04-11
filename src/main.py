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


async def main():

    # Start the client
    client_factory = ClientFactory()
    client = client_factory.create_client("ollama")
    
    #await client_main(client, server_script_path)
    await client_main(client)
    


if __name__ == "__main__":
    asyncio.run(main())