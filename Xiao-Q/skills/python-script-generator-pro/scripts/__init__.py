"""
Python Script Generator - SKILL Module

This module contains the main functionality for the OpenCode platform.
"""

__version__ = "2.0.0"
__author__ = "Claude"
__email__ = "claude@anthropic.com"

from .main_function import main, create_project, get_project_types, get_skill_info
from .helpers import (
    validate_project_config,
    sanitize_path,
    list_files_recursive,
    handle_platform_errors
)

__all__ = [
    'main',
    'create_project',
    'get_project_types',
    'get_skill_info',
    'validate_project_config',
    'sanitize_path',
    'list_files_recursive',
    'handle_platform_errors'
]