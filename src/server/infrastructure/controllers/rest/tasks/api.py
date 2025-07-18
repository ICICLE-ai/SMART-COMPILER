from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from typing import Annotated
from server.infrastructure.controllers.rest.tasks.dto import (
    TaskResponse,
    get_runtime_options_from_json,
)
from server.models.task import TaskType, ProgrammingLanguage, ProgramRuntimeOptions
from server.infrastructure.services.persistence import (
    FilePersistence,
    get_file_persistence,
)
from server.application.use_cases.schedule_compiler_task import (
    ScheduleCompilerTask,
)
from server.models.task import CompilerTaskRequest, TaskId, TaskResult
from server.repositories.tasks import TaskRepository
from shared.logging import get_logger
from server.infrastructure.injections import (
    get_task_repository,
    get_file_persistence,
    get_scheduler,
    get_profiler_tool_factory,
)
from apscheduler.schedulers.base import BaseScheduler
from server.tools.program_profiler.factory import ProfilerToolFactory

logger = get_logger()

router = APIRouter(prefix="/tasks", tags=["compiler-tasks"])
logger.debug("Profiler router initialized")

def check_file_extension_and_language(filename: str, language: ProgrammingLanguage) -> None:
    file_extension = filename.split(".")[-1]
    if file_extension not in ["py", "c"]:
        logger.error(f"Invalid file extension: {file_extension}")
        raise HTTPException(status_code=400, detail=f"Invalid file extension: {file_extension}")
        
    if file_extension == "py" and language != ProgrammingLanguage.PYTHON:
        logger.error(f"Invalid language for python file: {language}")
        raise HTTPException(status_code=400, detail=f"Invalid language for python file: {language.value}")
    
    if file_extension == "c" and language != ProgrammingLanguage.C:
        logger.error(f"Invalid language for c file: {language}")
        raise HTTPException(status_code=400, detail=f"Invalid language for c file: {language.value}")

@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
    summary="Create and schedule a compiler task",
    description="Create and schedule a compiler task, the task will be processed in the background and the result will be returned to the client when it is ready.",
    responses={
        201: {
            "description": "Task created and scheduled successfully",
            "model": TaskResponse,
        },
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    },
)
async def create_compiler_task(
    task_type: Annotated[
        TaskType,
        Form(
            ...,
            description=(
                "The type of compiler task to perform. "
                f"Available values: {', '.join([task_type.value for task_type in TaskType])}"
            ),
            examples=[
                "profile",
                "optimize",
            ]
        ),
    ],
    language: Annotated[
        ProgrammingLanguage,
        Form(
            ...,
            description=(
                "The programming language of the uploaded file. "
                f"Available values: {', '.join([language.value for language in ProgrammingLanguage])}"
            ),
        ),
    ],
    file: UploadFile = File(...),
    runtime_options: Annotated[
        str | None,
        Form(
            ...,
            description=(
                "Additional runtime options for the program, if any. "
                "This should be a stringified JSON object matching the following schema:\n\n"
                f"{ProgramRuntimeOptions.schema_to_json(indent=2)}\n\n"
                f"Note: DO NOT include the filename as an argument, it will be automatically added by the server."
                f"Note: For python programs, for example, if you want to run main.py, your command_args should not contain [\"main.py\"]"
                f"Note: For C programs, do not modify -o or source input file arguments, they will be automatically added by the server."
                f"For example, if you want to compile main.c, you MUST NOT include -o main.o or main.c as compilation arguments."
            ),
            examples=[
                {
                    "summary": "Python program runtime options",
                    "value": "{\"command\": \"python\", \"args\": [\"user_input.txt\"], \"envs\": {\"DB_HOST\": \"localhost\"}, \"cwd\": \"/tmp\"}"
                },
                {
                    "summary": "C program runtime options.",
                    "value": "{\"command\": \"./program.o\", \"args\": [\"user_input.txt\"], \"compilation_command\": \"gcc\", \"compilation_args\": [\"-O2\"], \"compilation_envs\": {\"CFLAGS\": \"-O2\"}, \"compilation_cwd\": \"/tmp\"}"
                },
                {
                    "summary": "No runtime options",
                    "value": "null"
                }
            ]
        ),
    ] = None,
    file_persistence: FilePersistence = Depends(get_file_persistence),
    scheduler: BaseScheduler = Depends(get_scheduler),
    profiler_tool_factory: ProfilerToolFactory = Depends(get_profiler_tool_factory),
) -> TaskResponse:
    """
    Create and schedule a compiler task.

    This endpoint allows clients to upload a source code file and specify the type of task (e.g., compile, run, profile),
    the programming language, and optional runtime options. The task is scheduled for background processing, and a response
    is returned containing the task ID and status.

    Args:
        task_type (TaskType): The type of compiler task to perform (e.g., compile, run, profile).
        language (ProgrammingLanguage): The programming language of the uploaded file.
        file (UploadFile): The source code file to be processed.
        runtime_options (ProgramRuntimeOptions | None, optional): Additional runtime options for the program, if any.
        file_persistence (FilePersistence): Dependency-injected service for file storage.
        scheduler (BaseScheduler): Dependency-injected scheduler for background task execution.
        profiler_tool_factory (ProfilerToolFactory): Dependency-injected factory for profiler tools.

    Returns:
        TaskResponse: An object containing the task ID, status, and result (if available).

    Raises:
        HTTPException: If no file is provided or if there is an error scheduling the task.

    Example:
        curl -X POST /tasks \\
            -F "task_type=compile" \\
            -F "language=python" \\
            -F "file=@main.py" \\
            -F "runtime_options={...}"
    """
    logger.debug(f"Profile request received: {task_type} {language}")
    logger.debug(f"Runtime options: {runtime_options}")

    logger.debug(f"File: {file}")

    if not file.filename:
        logger.error("No file provided")
        raise HTTPException(status_code=400, detail="No file provided")
    
    check_file_extension_and_language(file.filename, language)

    file_content = await file.read()
    file_content_str = file_content.decode("utf-8")
    
    runtime_options_obj = get_runtime_options_from_json(runtime_options)

    try:
        file_path = file_persistence.save_file(file.filename, file_content_str)
        request = CompilerTaskRequest(
            task_type=TaskType(task_type),
            language=ProgrammingLanguage(language),
            path=file_path,
            runtime_options=runtime_options_obj,
        )
        task = await ScheduleCompilerTask(
            task_repository=get_task_repository(),
            scheduler=scheduler,
            profiler_tool_factory=profiler_tool_factory,
        ).execute(request)
    except Exception as e:
        # file_persistence.remove(file_path)
        logger.error(f"Error scheduling compiler task: {e}")
        raise e

    return TaskResponse(
        task_id=task.task_id.value,
        task_status=task.status.value,
        task_result=task.result,
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=200,
    summary="Get the status of a compiler task",
)
async def get_compiler_task(
    task_id: str, task_repository: TaskRepository = Depends(get_task_repository)
) -> TaskResponse:
    """
    Get the status of a compiler task
    """
    logger.debug(f"Getting task {task_id}")
    task = await task_repository.get_task(TaskId(task_id))
    if task is None:
        raise HTTPException(
            status_code=404, detail="We did not find the task you are looking for"
        )

    logger.debug(f"Got task: {task}")
    return TaskResponse(
        task_id=task.task_id.value,
        task_status=task.status.value,
        task_result=task.result,
    )
