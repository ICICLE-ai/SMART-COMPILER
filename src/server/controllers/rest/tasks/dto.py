from pydantic import BaseModel, Field
from server.models.task import TaskResult

class TaskResponse(BaseModel):
    task_id: str = Field(description="The ID of the task")
    task_status: str = Field(description="The status of the task")
    task_result: TaskResult | None = Field(description="The result of the task")
