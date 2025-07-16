from apscheduler.schedulers.base import BaseScheduler
from datetime import datetime, timedelta
from server.models.task import (
    CompilerTask,
    CompilerTaskRequest,
    TaskType,
    TaskStatus,
    TaskResult,
)
from server.repositories.tasks import TaskRepository
from shared.logging import get_logger
from server.tools.program_profiler.factory import ProfilerToolFactory

logger = get_logger(__name__)


class ScheduleCompilerTask:
    
    def __init__(
        self,
        task_repository: TaskRepository,
        scheduler: BaseScheduler,
        profiler_tool_factory: ProfilerToolFactory,
    ):
        self.task_repository = task_repository
        self.scheduler = scheduler
        self.profiler_tool_factory = profiler_tool_factory
        
        
    async def execute(self, request: CompilerTaskRequest) -> CompilerTask:
        task = await self.task_repository.save_task(request)

        if request.task_type == TaskType.PROFILE:
            logger.info(f"Starting profiling task for {request.path} with task id {task.task_id}")
            job = self.scheduler.add_job(self._start_profiling_task, 'date', run_date=datetime.now() + timedelta(seconds=10), args=[request, task])
            updated_task = CompilerTask(
                task_id=task.task_id,
                status=TaskStatus.PENDING,
                result=TaskResult(file_path="", error=None),
                created_at=task.created_at, 
                updated_at=datetime.now(),
                task_type=task.task_type,
                language=task.language,
                runtime_options=task.runtime_options,
                path=task.path,
                internal_job_id=job.id
            )
            await self.task_repository.update_task(updated_task)
        else:
            raise ValueError(f"Optimization tasks are not supported yet")
        
        return task

    async def _start_profiling_task(self, request: CompilerTaskRequest, task: CompilerTask):
        try:
            task.status = TaskStatus.RUNNING
            task.updated_at = datetime.now()
            await self.task_repository.update_task(task)
            logger.info(f"Getting profile program for {request.path}")
            profiler_tool = await self.profiler_tool_factory.get_profiler_tool(
                    request.language,
                    request.task_options.profiling_type if request.task_options else None,
                )

            result = await profiler_tool.execute(
                    request.path, request.runtime_options
                )
            
            logger.info(f"Finished profiling task for {request.path}")
            task.status = TaskStatus.COMPLETED
            task.result = TaskResult(file_path=str(result), error=None)
            task.updated_at = datetime.now()
            
            try:
                await self.task_repository.update_task(task)
                logger.debug(f"Updated task: {task}")
            except Exception as e:
                logger.error(f"Error updating task: {e}")
            
        except Exception as e:
            logger.error(f"Error scheduling profiling task for {request.path}: {e}")
            task.status = TaskStatus.FAILED
            task.result = TaskResult(file_path="", error=str(e))
            task.updated_at = datetime.now()
            
            await self.task_repository.update_task(task)
        

async def get_schedule_compiler_task(task_repository: TaskRepository, scheduler: BaseScheduler, profiler_tool_factory: ProfilerToolFactory) -> ScheduleCompilerTask:
    return ScheduleCompilerTask(
        task_repository,
        scheduler,
        profiler_tool_factory
    )
