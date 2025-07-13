from server.controllers.mcp.profiler.models import ProfileSingleCodeSnippetRequest, ProfileProjectRequest

def profile_single_code_file(request: ProfileSingleCodeSnippetRequest) -> str:
    """
    This tool is used to profile the code.
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

def profile_project(project_path: str) -> str:
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







