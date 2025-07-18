import uvicorn
import logging
import sys
import os

from dotenv import load_dotenv

load_dotenv()

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages and time"""

    # ANSI color codes
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    DARK_BLUE = '\033[34m'
    RESET = '\033[0m'

    def format(self, record):
        original_levelname = record.levelname
        original_asctime = getattr(record, "asctime", None)

        # Color the levelname
        if record.levelno == logging.INFO:
            record.levelname = f"{self.GREEN}{original_levelname}:{self.RESET}"
            color_for_time = self.DARK_BLUE
        elif record.levelno == logging.ERROR:
            record.levelname = f"{self.RED}{original_levelname}:{self.RESET}"
            color_for_time = self.RED
        elif record.levelno == logging.WARNING:
            record.levelname = f"{self.YELLOW}{original_levelname}:{self.RESET}"
            color_for_time = self.YELLOW
        else:
            color_for_time = self.DARK_BLUE

        # Color the asctime (time) if present
        result = super().format(record)
        if hasattr(record, "asctime"):
            # Replace only the first occurrence of asctime in the output
            colored_time = f"{color_for_time}[{record.asctime}]{self.RESET}"
            result = result.replace(str(record.asctime), colored_time, 1)

        # Restore original values to avoid side effects
        record.levelname = original_levelname
        if original_asctime is not None:
            record.asctime = original_asctime

        return result
    

logger = logging.getLogger("smart_compiler_logger")
handler = logging.StreamHandler(sys.stdout)

uvicorn_loggers = [
    logging.getLogger("uvicorn"),
    logging.getLogger("uvicorn.access"),
    logging.getLogger("uvicorn.error"),
]

formatter = ColoredFormatter(
    fmt="%(asctime)s-%(levelname)-8s %(message)-80s",
    datefmt="%Y-%m-%d %H:%M"
)


handler.setFormatter(formatter)


for uvicorn_logger in uvicorn_loggers:
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(logging.INFO)


logger.handlers.clear()
logger.addHandler(handler)
logger.setLevel(os.getenv("LOG_LEVEL","INFO"))
logger.propagate = False



    
def get_logger() -> logging.Logger:
    return logger
