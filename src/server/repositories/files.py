from pathlib import Path
from shared.logging import get_logger
from abc import ABC, abstractmethod
from uuid import uuid4

logger = get_logger(__name__)

class FileRepository(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_file_path(self, file_id: str, user_id: str = "default") -> str:
        pass

    @abstractmethod
    def save_file(self, file_name: str, file_content: str, user_id: str = "default") -> str:
        pass


class InMemoryFileRepository(FileRepository):
    def __init__(self):
        self.files = {}


    def get_file_path(self, file_id: str, user_id: str = "default") -> str:
        logger.debug(f"Getting file: {file_id} for user: {user_id}")
        file_path = self.files[file_id]
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_id} not found")
        
        if not path.is_file():
            raise IsADirectoryError(f"File {file_id} is a directory")
        
        return file_path

    def save_file(self, file_name: str, file_content: str, user_id: str = "default") -> str:
        logger.debug(f"Saving file: {file_name} for user: {user_id}")
        file_id = str(uuid4())
        file_path = f"files/{user_id}/{file_id}_{file_name}"
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(file_content)
            
        self.files[file_id] = file_path
        return file_id


def get_file_repository() -> FileRepository:
    return InMemoryFileRepository()