import json
from pydantic import BaseModel, Field
from server.models.compiler import ProgramRuntimeOptions
from server.models.task import TaskResult, CompilerTaskDecoder

class TaskResponse(BaseModel):
    task_id: str = Field(description="The ID of the task")
    task_status: str = Field(description="The status of the task")
    task_result: TaskResult | None = Field(description="The result of the task")


def get_runtime_options_from_json(json_str: str | None) -> ProgramRuntimeOptions | None:
    if json_str is None or json_str == "null":
        return None
    
    try:
        json_obj = json.loads(json_str, cls=CompilerTaskDecoder)
        return ProgramRuntimeOptions.from_json(json_obj)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string for runtime options: {json_str}")
    
    