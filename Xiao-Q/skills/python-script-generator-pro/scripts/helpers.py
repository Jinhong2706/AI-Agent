"""
Helper functions for the Python Script Generator SKILL
"""

import os
import sys
import logging
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

def validate_project_config(config: Dict[str, Any]) -> List[str]:
    """Validate project configuration."""
    errors = []

    # Validate required fields
    required_fields = ['name', 'type']
    for field in required_fields:
        if field not in config:
            errors.append(f"Missing required field: {field}")

    # Validate project type
    if 'type' in config:
        valid_types = [
            'cli', 'flask', 'fastapi', 'fastapi-crud',
            'django-app', 'django-cmd', 'scraper', 'scraper-async',
            'bot', 'discord-bot', 'data-analysis', 'ml-model', 'automation'
        ]
        if config['type'] not in valid_types:
            errors.append(f"Invalid project type: {config['type']}. Valid types: {', '.join(valid_types)}")

    # Validate project name
    if 'name' in config:
        name = config['name']
        if not isinstance(name, str) or not name.isidentifier():
            errors.append("Project name must be a valid Python identifier")

    # Validate requirements format
    if 'requirements' in config:
        requirements = config['requirements']
        if isinstance(requirements, str):
            # Split comma-separated string
            config['requirements'] = [req.strip() for req in requirements.split(',')]
        elif not isinstance(requirements, list):
            errors.append("Requirements must be a list or comma-separated string")

    return errors

def sanitize_path(path: str) -> str:
    """Sanitize file path for platform security."""
    # Remove potential path traversal
    normalized = os.path.normpath(path)
    # Ensure path is within allowed directory
    if not normalized.startswith('./'):
        normalized = './' + normalized
    return normalized

def get_safe_output_directory() -> Path:
    """Get safe output directory for project generation."""
    # Use platform-specific temp or allow user to specify
    base_dir = Path(os.getenv('OPENCODE_OUTPUT_DIR', os.getcwd()))
    return base_dir

def list_files_recursive(path: Path) -> List[str]:
    """List all files in a directory recursively."""
    files = []
    try:
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                rel_path = os.path.relpath(os.path.join(root, filename), str(path))
                files.append(rel_path)
    except (OSError, PermissionError) as e:
        logger.warning(f"Error listing files: {e}")
        files = [str(name) for name in path.glob('**/*') if name.is_file()]
    return files

def load_config_file() -> Dict[str, Any]:
    """Load configuration file."""
    config_files = [
        Path.cwd() / 'config.yaml',
        Path.home() / '.python-script-generator' / 'config.yaml',
        Path(__file__).parent.parent / 'config.yaml'
    ]

    for config_file in config_files:
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"Error loading config {config_file}: {e}")

    return {}

def handle_platform_errors(error: Exception) -> Dict[str, Any]:
    """Handle platform-specific error responses."""
    error_response = {
        'success': False,
        'error': str(error),
        'error_type': type(error).__name__,
    }

    # Add platform-specific error handling
    if isinstance(error, PermissionError):
        error_response['suggestion'] = "Please check file permissions or use a different output directory"
    elif isinstance(error, FileNotFoundError):
        error_response['suggestion'] = "Required file not found"
    elif isinstance(error, OSError) and 'Disk quota' in str(error):
        error_response['suggestion'] = "Disk space limit reached"
    elif isinstance(error, ValueError) and 'Invalid project type' in str(error):
        error_response['suggestion'] = "Use --list-types to see available project types"

    return error_response

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    return True

def ensure_directory_exists(path: Path) -> None:
    """Ensure directory exists, create if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def safe_copy_file(src: Path, dst: Path) -> None:
    """Safely copy file from src to dst."""
    try:
        ensure_directory_exists(dst.parent)
        shutil.copy2(src, dst)
    except Exception as e:
        logger.error(f"Failed to copy file {src} to {dst}: {e}")
        raise

def get_project_types_info() -> Dict[str, Any]:
    """Get information about available project types."""
    return {
        'cli': {
            'description': 'Command line tool',
            'category': 'utility',
            'features': ['argparse', 'logging', 'entry point'],
            'default_requirements': []
        },
        'flask': {
            'description': 'Flask web application',
            'category': 'web',
            'features': ['Flask', 'basic routing', 'templates', 'static files'],
            'default_requirements': ['Flask>=2.0.0']
        },
        'fastapi': {
            'description': 'FastAPI web application',
            'category': 'web',
            'features': ['FastAPI', 'async support', 'automatic docs', 'Pydantic models'],
            'default_requirements': ['fastapi>=0.100.0', 'uvicorn[standard]>=0.20.0']
        },
        'fastapi-crud': {
            'description': 'FastAPI with CRUD operations',
            'category': 'web',
            'features': ['FastAPI', 'SQLAlchemy', 'CRUD endpoints', 'authentication'],
            'default_requirements': ['fastapi>=0.100.0', 'uvicorn[standard]>=0.20.0', 'sqlalchemy>=2.0.0', 'pydantic>=2.0.0']
        },
        'django-app': {
            'description': 'Django application',
            'category': 'web',
            'features': ['Django', 'MVC architecture', 'admin interface', 'ORM'],
            'default_requirements': ['Django>=4.0.0']
        },
        'django-cmd': {
            'description': 'Django management command',
            'category': 'django',
            'features': ['Django command', 'custom management utilities'],
            'default_requirements': ['Django>=4.0.0']
        },
        'scraper': {
            'description': 'Web scraper',
            'category': 'data',
            'features': ['requests', 'BeautifulSoup', 'data extraction'],
            'default_requirements': ['requests>=2.28.0', 'beautifulsoup4>=4.11.0']
        },
        'scraper-async': {
            'description': 'Async web scraper',
            'category': 'data',
            'features': ['aiohttp', 'asyncio', 'concurrent scraping'],
            'default_requirements': ['aiohttp>=3.8.0', 'beautifulsoup4>=4.11.0']
        },
        'bot': {
            'description': 'Telegram bot',
            'category': 'bot',
            'features': ['python-telegram-bot', 'webhooks', 'inline keyboards'],
            'default_requirements': ['python-telegram-bot>=20.0.0']
        },
        'discord-bot': {
            'description': 'Discord bot',
            'category': 'bot',
            'features': ['discord.py', 'intents', 'slash commands'],
            'default_requirements': ['discord.py>=2.3.0']
        },
        'data-analysis': {
            'description': 'Data analysis project',
            'category': 'data',
            'features': ['pandas', 'numpy', 'matplotlib', 'jupyter'],
            'default_requirements': ['pandas>=1.5.0', 'numpy>=1.24.0', 'matplotlib>=3.6.0']
        },
        'ml-model': {
            'description': 'Machine learning model',
            'category': 'ml',
            'features': ['scikit-learn', 'tensorflow/pytorch', 'model training'],
            'default_requirements': ['scikit-learn>=1.2.0', 'pandas>=1.5.0', 'numpy>=1.24.0']
        },
        'automation': {
            'description': 'Automation script',
            'category': 'utility',
            'features': ['scheduling', 'file operations', 'system integration'],
            'default_requirements': []
        }
    }

def format_help() -> str:
    """Format help message."""
    project_types = get_project_types_info()

    help_text = """Python Script Generator Help

This skill generates professional Python project templates.

Usage Examples:
  - Create a CLI tool
    python-script-generator mycli --type cli

  - Create a FastAPI project
    python-script-generator myapi --type fastapi --description "REST API" --with-docker --with-ci

  - Create a scraper with specific requirements
    python-script-generator scraper --type scraper-async -r "aiohttp,beautifulsoup4"

Available Project Types:"""

    for pt, info in project_types.items():
        help_text += f"\n  {pt:15} - {info['description']}"
        help_text += f"\n                   Category: {info['category']}"
        help_text += f"\n                   Features: {', '.join(info['features'])}"

    help_text += """

Configuration Options:
  -n, --name NAME          Project name (required)
  -t, --type TYPE          Project type (required)
  -d, --description DESC   Project description
  -r, --requirements PKGS  Dependencies (comma-separated)
  -a, --author AUTHOR      Author name
  -l, --license LICENSE    License type (default: MIT)
  -v, --version VERSION    Project version
  --output DIR             Output directory
  --force                  Overwrite existing directory
  --no-tests               Skip test files
  --no-docker              Skip Docker files
  --no-ci                  Skip CI/CD files
  --template PATH          Custom template path
  -h, --help               Show this help

Return Values:
  - success: Boolean indicating success
  - message: Status message
  - path: Path to created project
  - files: List of created files
  - warnings: Any warnings
  - errors: Any errors

For more information, see: README.md or OPENCODE-README.md"""

    return help_text