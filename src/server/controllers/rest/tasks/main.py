from fastapi import APIRouter
from server.controllers.rest.tasks.models import SingleFileTaskRequest, TaskResponse, TaskType, Language
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()
logger.debug("Profiler router initialized")

@router.post("/tasks")
def create_compiler_task(request: SingleFileTaskRequest) -> TaskResponse:
    logger.debug(f"Profile request received: {request}")
    return TaskResponse(task_id="123", task_status="pending", task_result={"message": "Profile request received"})

