from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from typing import Annotated
from server.controllers.rest.tasks.dto import (
    TaskResponse,
)
from src.server.models.task import TaskType, ProgrammingLanguage, ProgramRuntimeOptions
from server.infrastructure.persistence import FilePersistence, get_file_persistence
from src.server.application.schedule_compiler_task import (
    ScheduleCompilerTask,
    get_schedule_compiler_task,
)
from src.server.models.task import CompilerTaskRequest, TaskId, TaskResult
from src.server.repositories.tasks import TaskRepository, get_task_repository
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
    language: Annotated[ProgrammingLanguage, Form(...)],
    runtime_options: Annotated[ProgramRuntimeOptions, Form(...)],
    file: UploadFile = File(...),
    file_persistence: FilePersistence = Depends(get_file_persistence),
    schedule_compiler_task: ScheduleCompilerTask = Depends(get_schedule_compiler_task),
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

    try:
        file_path = file_persistence.save_file(file.filename, file_content_str)
        request = CompilerTaskRequest(
            task_type=TaskType(task_type),
            language=ProgrammingLanguage(language),
            path=file_path,
            runtime_options=runtime_options,
        )
        task = await schedule_compiler_task.execute(
            request
        )
    except Exception as e:
        file_persistence.delete_file(file_path)
        logger.error(f"Error scheduling compiler task: {e}")
        raise e

    return TaskResponse(
        task_id=task.task_id.value,
        task_status=task.status.value,
        task_result=TaskResult(file_path=task.result.file_path) if task.result else TaskResult(file_path=""),
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=200,
    summary="Get the status of a compiler task",
)
async def get_compiler_task(task_id: str) -> TaskResponse:
    task_repository: TaskRepository = await get_task_repository()
    """
    Get the status of a compiler task
    """
    task = await task_repository.get_task(TaskId(task_id))
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(
        task_id=task.task_id.value,
        task_status=task.status.value,
        task_result=task.result,
    )
