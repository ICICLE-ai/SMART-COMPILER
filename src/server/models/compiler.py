import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProgramRuntimeOptions:

    command: Optional[str]
    args: Optional[list[str]]
    envs: Optional[dict[str, str]]
    cwd: Optional[str]
    timeout_in_seconds: Optional[int]
    max_memory_in_mb: Optional[int]
    compilation_args: Optional[list[str]]
    compilation_envs: Optional[dict[str, str]]
    compilation_cwd: Optional[str]
    compilation_max_memory_in_mb: Optional[int]
    compilation_timeout_in_seconds: Optional[int]

    @staticmethod
    def schema_to_json(indent: int = 2) -> str:
        fields = ProgramRuntimeOptions.__dataclass_fields__
        schema = {}
        for name, field in fields.items():
            schema[name] = {
                "type": field.type.__name__,
                "description": field.metadata.get("description", ""),
                "examples": field.metadata.get("examples", []),
            }
        return json.dumps(schema, indent=indent)

    @staticmethod
    def from_json(json_dict: dict) -> "ProgramRuntimeOptions":
        return ProgramRuntimeOptions(
                command=json_dict.get("command", None),
                args=json_dict.get("args", None),
                envs=json_dict.get("envs", None),
                cwd=json_dict.get("cwd", None),
                timeout_in_seconds=json_dict.get("timeout_in_seconds", None),
                max_memory_in_mb=json_dict.get("max_memory_in_mb", None),
                compilation_args=json_dict.get("compilation_args", None),
                compilation_envs=json_dict.get("compilation_envs", None),
                compilation_cwd=json_dict.get("compilation_cwd", None),
                compilation_max_memory_in_mb=json_dict.get(
                    "compilation_max_memory_in_mb", None
                ),
                compilation_timeout_in_seconds=json_dict.get(
                    "compilation_timeout_in_seconds", None
                ),
            )
