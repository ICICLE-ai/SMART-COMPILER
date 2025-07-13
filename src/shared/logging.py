import logging
import sys
import os

from dotenv import load_dotenv

load_dotenv()

class ColoredFormatter(logging.Formatter):
    """Custom formatter to add colors to log messages"""
    
    # ANSI color codes
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    RESET = '\033[0m'
    
    def format(self, record):
        original_levelname = record.levelname
        
        if record.levelno == logging.INFO:
            record.levelname = f"{self.GREEN}{original_levelname}{self.RESET}"
        elif record.levelno == logging.ERROR:
            record.levelname = f"{self.RED}{original_levelname}{self.RESET}"
        elif record.levelno == logging.WARNING:
            record.levelname = f"{self.YELLOW}{original_levelname}{self.RESET}"
            
        result = super().format(record)
        
        record.levelname = original_levelname
        
        return result
    
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL","INFO"))
    return logger
