from pathlib import Path
from shared.logging import get_logger
from abc import ABC, abstractmethod
from uuid import uuid4

logger = get_logger(__name__)

class FilePersistence(ABC):
    @abstractmethod
    def save_file(self, file_name: str, file_content: str) -> str:
        """
        Save a file to the repository.
        
        Args:
            file_name: The name of the file to save.
            file_content: The content of the file to save.
            
        Returns:
            The path to the saved file.
        """
        pass

    @abstractmethod
    def remove(self, path_str: str) -> None:
        pass


class InDiskFileRepository(FilePersistence):

    def save_file(self, file_name: str, file_content: str) -> str:
        logger.debug(f"Saving file: {file_name}")
        file_id = str(uuid4())
        file_path = f"files/{file_id}/{file_name}"
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(file_content)
            
        return file_path

    def remove(self, path_str: str) -> None:
        logger.debug(f"Deleting file: {path_str}")
        path = Path(path_str)
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
        else:
            raise FileNotFoundError(f"File or directory not found: {path_str}")

singleton_file_persistence = InDiskFileRepository()


async def get_file_persistence() -> FilePersistence:
    return singleton_file_persistence