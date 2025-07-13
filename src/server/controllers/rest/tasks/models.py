from pydantic import BaseModel, Field
from enum import Enum
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
from typing import Annotated

class TaskType(str, Enum):
    PROFILE = "profile",
    OPTIMIZE = "optimize",


class Language(str, Enum):
    PYTHON = "python"
    C = "c"

class SingleFileTaskRequest(BaseModel):
    task_type: Annotated[TaskType, Form(...)]
    language: Annotated[Language, Form(...)]
    file: Annotated[UploadFile, File(...)]
    
class TaskResponse(BaseModel):
    task_id: str = Field(description="The ID of the task")
    task_status: str = Field(description="The status of the task")
    task_result: dict = Field(description="The result of the task")