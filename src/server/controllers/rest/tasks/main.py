from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from typing import Annotated
from server.controllers.rest.tasks.dto import (
    TaskResponse,
    TaskType,
    Language,
)
from server.repositories.files import FileRepository, get_file_repository
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["compiler-tasks"])
logger.debug("Profiler router initialized")


@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
    summary="Create and schedule a compiler task",
    description="Create and schedule a compiler task, the task will be processed in the background and the result will be returned to the client when it is ready.",
)
async def create_compiler_task(
    task_type: Annotated[TaskType, Form(...)],
    language: Annotated[Language, Form(...)],
    file: UploadFile = File(...),
    file_repository: FileRepository = Depends(get_file_repository),
) -> TaskResponse:
    """
    Create and schedule a compiler task
    """
    logger.debug(f"Profile request received: {task_type} {language}")

    logger.debug(f"File: {file}")

    if not file.filename:
        logger.error("No file provided")
        raise HTTPException(status_code=400, detail="No file provided")

    file_content = await file.read()
    file_content_str = file_content.decode("utf-8")
    logger.debug(f"File content: {file_content_str}")

    file_id = file_repository.save_file(file.filename, file_content_str)

    logger.debug(f"File ID: {file_id}")

    return TaskResponse(
        task_id="123",
        task_status="pending",
        task_result={"message": "Profile request received"},
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=200,
    summary="Get the status of a compiler task",
)
def get_compiler_task(task_id: str) -> TaskResponse:
    """
    Get the status of a compiler task
    """
    return TaskResponse(
        task_id=task_id,
        task_status="pending",
        task_result={"message": "Profile request received"},
    )
