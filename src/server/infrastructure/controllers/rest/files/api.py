from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

def get_media_type(file_extension: str) -> str:
    if file_extension == ".txt":
        return "text/plain"
    elif file_extension == ".html":
        return "text/html"
    elif file_extension == ".pdf":
        return "application/pdf"
    elif file_extension == ".docx":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif file_extension == ".doc":
        return "application/msword"
    else:
        return "application/octet-stream"

@router.get("/files/{file_path}", response_class=FileResponse, summary="Download a file", description="Download a file from the server")
async def download_file(file_path: str):
    path = Path(file_path)
    
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")
    
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    file_extension = path.suffix
    media_type = get_media_type(file_extension)
    
    return FileResponse(path.absolute(), filename=path.name, media_type=media_type)