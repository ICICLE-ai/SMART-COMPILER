from client.factory.base_factory import ClientFactory
from client.main import main as client_main
import asyncio
from dotenv import load_dotenv
from shared.logging import get_logger

load_dotenv()

logger = get_logger()


async def main():
    logger.info("Starting client")

    client_factory = ClientFactory()
    client = client_factory.create_client("ollama")
    
    await client_main(client)
    


if __name__ == "__main__":
    asyncio.run(main())