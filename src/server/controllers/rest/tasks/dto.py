from pydantic import BaseModel, Field
from enum import Enum
from pydantic import BaseModel


class TaskType(str, Enum):
    PROFILE = "profile"
    OPTIMIZE = "optimize"


class Language(str, Enum):
    PYTHON = "python"
    C = "c"


class TaskResponse(BaseModel):
    task_id: str = Field(description="The ID of the task")
    task_status: str = Field(description="The status of the task")
    task_result: dict = Field(description="The result of the task")
