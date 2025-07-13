from fastapi import FastAPI
from server.controllers.rest.tasks.main import router as profiler_router
from contextlib import asynccontextmanager
from typing import AsyncIterator
from shared.logging import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("REST server started")
    yield
    logger.info("REST server stopped")

app = FastAPI(title="SmartCompiler-REST", description="REST API for SmartCompiler", version="0.1.0", lifespan=app_lifespan)

app.include_router(profiler_router)