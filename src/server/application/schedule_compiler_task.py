import asyncio
from datetime import datetime
from src.server.models.task import (
    CompilerTask,
    CompilerTaskRequest,
    TaskType,
    TaskStatus,
    TaskResult,
)
from src.server.repositories.tasks import TaskRepository, get_task_repository
from shared.logging import get_logger
from src.server.application.program_profiler.factory import get_profile_program_factory

logger = get_logger(__name__)


class ScheduleCompilerTask:
    def __init__(
        self,
        task_repository: TaskRepository,
    ):
        self.task_repository = task_repository

    async def execute(self, request: CompilerTaskRequest) -> CompilerTask:
        task = await self.task_repository.save_task(request)

        if request.task_type == TaskType.PROFILE:
            logger.info(f"Starting profiling task for {request.path} with task id {task.task_id}")
            asyncio.create_task(self._schedule_profiling_task(request, task))
        else:
            raise ValueError(f"Optimization tasks are not supported yet")
        
        return task

    async def _schedule_profiling_task(self, request: CompilerTaskRequest, task: CompilerTask):
        try:
            logger.info(f"Getting profile program for {request.path}")
            profile_program_factory = await get_profile_program_factory()
            profile_program = await profile_program_factory.get_profile_program(
                    request.language,
                    request.task_options.profiling_type if request.task_options else None,
                )

            result = await profile_program.execute(
                    request.path, request.runtime_options
                )
            
            logger.info(f"Finished profiling task for {request.path}")
            updated_task = CompilerTask(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=TaskResult(file_path=result, error=None),
                created_at=task.created_at, 
                updated_at=datetime.now(),
                task_type=task.task_type,
                language=task.language,
                runtime_options=task.runtime_options,
                path=task.path,
            )
            await self.task_repository.update_task(updated_task)
            
        except Exception as e:
            logger.error(f"Error scheduling profiling task for {request.path}: {e}")
            updated_task = CompilerTask(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                result=TaskResult(file_path="", error=str(e)),
                created_at=task.created_at, 
                updated_at=datetime.now(),
                task_type=task.task_type,
                language=task.language,
                runtime_options=task.runtime_options,
                path=task.path,
            )
            await self.task_repository.update_task(updated_task)
        

async def get_schedule_compiler_task() -> ScheduleCompilerTask:
    return ScheduleCompilerTask(
        await get_task_repository()
    )
