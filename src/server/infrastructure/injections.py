from server.repositories.tasks import TaskRepository
from server.infrastructure.services.persistence import FilePersistence, InDiskFileRepository
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import BaseScheduler
from server.tools.program_profiler.factory import ProfilerToolFactory
from server.infrastructure.repositories.sqlite_tasks import SQLiteTaskRepository
from server.application.use_cases.profile_program import ProfileProgram
from server.infrastructure.repositories.jobs_repository import SQLiteJobsRepository
from apscheduler.executors.pool import ProcessPoolExecutor

tasks_repository = SQLiteTaskRepository()
file_persistence = InDiskFileRepository()

jobstores = {
    'default': SQLiteJobsRepository(),
}
executors = {
    'default': ProcessPoolExecutor(),
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3,
    'misfire_grace_time': None
}


scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)


profiler_tool_factory = ProfilerToolFactory()

def get_task_repository() -> TaskRepository:
    return tasks_repository

def get_file_persistence() -> FilePersistence:
    return file_persistence

def get_scheduler() -> BaseScheduler:
    return scheduler

def get_profiler_tool_factory() -> ProfilerToolFactory:
    return profiler_tool_factory

def get_profile_use_case() -> ProfileProgram:
    return ProfileProgram(get_profiler_tool_factory())