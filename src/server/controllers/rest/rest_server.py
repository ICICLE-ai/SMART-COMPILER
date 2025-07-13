from fastapi import FastAPI
from server.controllers.rest.tasks.main import router as tasks_router
from contextlib import asynccontextmanager
from typing import AsyncIterator
from shared.logging import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("SmartCompiler REST API started")
    yield
    logger.info("SmartCompiler REST API stopped")

app = FastAPI(title="SmartCompiler", description="REST API for SmartCompiler", version="0.1.0", lifespan=app_lifespan)

app.include_router(tasks_router)