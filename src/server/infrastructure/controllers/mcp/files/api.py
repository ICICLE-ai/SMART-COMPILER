from mcp.server import FastMCP
from typing import Annotated
from pydantic import Field
from pathlib import Path

def get_file_content(
    path: Annotated[str, Field(description="The path to the file to get the content of")],
) -> str:
    """
    This tool is used to get the content of a file.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return "The file you are trying to access does not exist"
    return path_obj.read_text()


def list_files_in_directory(
    path: Annotated[str, Field(description="The path to the directory to list the files of")],
) -> list[str] | str:
    """
    This tool is used to list the files in a given directory.
    
    
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return f"The directory you are trying to access does not exist: {path}"
    
    files = [file.name for file in path_obj.iterdir() if file.is_file()]
    return files


def register_api(server: FastMCP) -> None:
    server.add_tool(get_file_content)
    server.add_tool(list_files_in_directory)


