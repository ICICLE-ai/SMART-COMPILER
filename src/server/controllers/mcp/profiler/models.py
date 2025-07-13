from pydantic import BaseModel, Field

class ProfileSingleCodeSnippetRequest(BaseModel):
    code_snippet: str = Field(description="The code snippet to profile")
    
class ProfileProjectRequest(BaseModel):
    project_path: str = Field(description="The path to the project to profile")
    
