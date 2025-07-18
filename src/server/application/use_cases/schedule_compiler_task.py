import asyncio
from apscheduler.schedulers.base import BaseScheduler
from datetime import datetime, timedelta
from server.models.task import (
    CompilerTask,
    CompilerTaskRequest,
    TaskType,
    TaskStatus,
    TaskResult,
    TaskId,

)
from server.repositories.tasks import TaskRepository
from shared.logging import get_logger
from server.tools.program_profiler.factory import ProfilerToolFactory
from server.infrastructure.injections import get_profiler_tool_factory, get_task_repository


logger = get_logger()

def _start_profiling_process(request: CompilerTaskRequest, taskId: TaskId):
    asyncio.run(_start_profiling_task(request, taskId))

async def _start_profiling_task(request: CompilerTaskRequest, taskId: TaskId):
    logger.info(f"Starting profiling task for task id {taskId} with request {request}")
    
    tasks_repository = get_task_repository()
    task = await tasks_repository.get_task(taskId)
    if not task:
        logger.error(f"Task {taskId} not found")
        return
    

    try:
        task.status = TaskStatus.RUNNING
        task.updated_at = datetime.now()
        await tasks_repository.update_task(task)
        logger.info(f"Getting profile program for {task.path}")
        profiler_tool_factory = get_profiler_tool_factory()
        profiler_tool = await profiler_tool_factory.get_profiler_tool(
                task.language,
                request.task_options.profiling_type if request.task_options else None,
            )

        logger.info(f"Profiler tool: {profiler_tool}")
        logger.info(f"Executing profiler tool for {task.path}")
        profile_file_path = await profiler_tool.execute(
                task.path, task.runtime_options
            )
        
        
        logger.info(f"Finished profiling task for {task.path}")
        logger.info(f"Profiler tool result: {profile_file_path}")

        task.status = TaskStatus.COMPLETED
        task.result = TaskResult(file_path=str(profile_file_path), error=None)
        task.updated_at = datetime.now()
        
        try:
            await tasks_repository.update_task(task)
            logger.info(f"Updated task: {task}")
        except Exception as e:
            logger.error(f"Error updating task: {e}")
        
    except Exception as e:
        logger.error(f"Error scheduling profiling task for {taskId}: {e}")
        task.status = TaskStatus.FAILED
        task.result = TaskResult(file_path="", error=str(e))
        task.updated_at = datetime.now()
        
        await tasks_repository.update_task(task)
        logger.error(f"Updated task with error: {task}")
    



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
            logger.debug(f"Scheduler state: {self.scheduler.state}")
            job = self.scheduler.add_job(_start_profiling_process, 'date', run_date=datetime.now() + timedelta(seconds=10), args=[request, task.task_id])
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

    
async def get_schedule_compiler_task(task_repository: TaskRepository, scheduler: BaseScheduler, profiler_tool_factory: ProfilerToolFactory) -> ScheduleCompilerTask:
    return ScheduleCompilerTask(
        task_repository,
        scheduler,
        profiler_tool_factory
    )
