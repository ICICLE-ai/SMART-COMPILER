from fastapi import FastAPI
from server.infrastructure.controllers.rest.tasks.api import router as tasks_router
from contextlib import asynccontextmanager
from typing import AsyncIterator
from shared.logging import get_logger
from server.infrastructure.injections import get_scheduler
logger = get_logger(__name__)

@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler = get_scheduler()
    scheduler.start()
    logger.info("SmartCompiler REST API started")
    yield
    logger.info("SmartCompiler REST API stopped")
    scheduler.shutdown()
app = FastAPI(title="SmartCompiler", description="REST API for SmartCompiler", version="0.1.0", lifespan=app_lifespan)

app.include_router(tasks_router)