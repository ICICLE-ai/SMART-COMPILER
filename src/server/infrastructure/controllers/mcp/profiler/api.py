from mcp.server import FastMCP
from typing import Annotated
from pydantic import Field
from server.models.task import ProgrammingLanguage, ProfilingType
from server.infrastructure.injections import get_profile_use_case
from server.models.task import ProgramRuntimeOptions


async def profile_code_snippet(
    code_snippet: Annotated[str, Field(description="The code snippet to profile")],
    language: Annotated[
        ProgrammingLanguage,
        Field(
            description=(
                f"The language of the code snippet." f"Possible values are: python, c."
            ),
        ),
    ],
    profiling_type: Annotated[
        ProfilingType | None,
        Field(
            description=(
                f"The type of profiling to use."
                f"Possible values are: classical, augmented (for using classical and llm), llm"
            ),
            default=ProfilingType.CLASSICAL,
        ),
    ],
    runtime_options: Annotated[
        ProgramRuntimeOptions | None,
        Field(
            description="The runtime options to use for the profiling.",
            default=None,
        ),
    ],
) -> str:
    """
    This tool is used to profile a certain code snippet. You must specify the programming language of the code snippet.
    """

    profile_result_path = await get_profile_use_case().execute(
        code_snippet, language, profiling_type, runtime_options
    )
    
    profile_content = profile_result_path.read_text()

    return profile_content


def profile_project(
    path: Annotated[str, Field(description="The path to the project to profile")],
) -> str:
    """
    This tool is used to profile the project.
    """
    return """
    Profiler mock info:
    - 100 lines of code
    - 1000 lines of code
    - 10000 lines of code
    - 100000 lines of code
    - 1000000 lines of code
    - 10000000 lines of code
"""


def register_api(server: FastMCP) -> None:
    server.add_tool(profile_code_snippet)
    server.add_tool(profile_project)
