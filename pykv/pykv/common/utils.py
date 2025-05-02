"""
Utility functions for PyKV
"""
import os
import json
import logging
from typing import Dict, Any


def setup_logging(log_level=logging.INFO):
    """Set up logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger('pykv')


def ensure_directory(path: str):
    """Ensure a directory exists"""
    os.makedirs(path, exist_ok=True)


def get_file_size(file_path: str) -> int:
    """Get the size of a file in bytes"""
    try:
        return os.path.getsize(file_path)
    except (FileNotFoundError, OSError):
        return 0


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "status": "error",
        "code": status_code,
        "message": message
    }


def success_response(data: Any = None) -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {"status": "success"}
    if data is not None:
        response["data"] = data
    return response 