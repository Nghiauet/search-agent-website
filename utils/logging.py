"""
Centralized logging configuration for the MCP Agent.
"""
import os
import sys
from loguru import logger

def setup_logging(log_file="agent_logs.log", 
                 console_level="INFO", 
                 file_level="DEBUG",
                 rotation="10 MB",
                 retention=3):
    """
    Set up logging configuration for the application.
    
    Args:
        log_file: Log file path
        console_level: Logging level for console output
        file_level: Logging level for file output
        rotation: When to rotate log files
        retention: Number of log files to keep
    """
    # Remove default logger
    logger.remove()
    
    # Configure console logger with colors
    logger.add(
        sys.stderr,
        level=console_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # Configure file logger for more detailed logging
    logger.add(
        log_file,
        level=file_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention
    )
    
    return logger

# Create a default logger instance
logger = setup_logging()
