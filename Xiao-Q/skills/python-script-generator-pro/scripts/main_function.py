"""
Main function for Python Script Generator SKILL

This script provides the primary entry point for the skill and can be
executed directly or imported as a module.
"""

import argparse
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# yaml is optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import helpers

class PythonScriptGenerator:
    """Main class for generating Python project templates."""

    def __init__(self):
        """Initialize the generator."""
        self.script_dir = Path(__file__).parent.parent.absolute()
        self.data_dir = self.script_dir / "data"
        self.templates_dir = self.script_dir / "assets" / "templates"

    def create_project(self,
                      name: str,
                      project_type: str,
                      description: str = "",
                      output_dir: str = "",
                      requirements: List[str] = None,
                      author: str = "",
                      license_type: str = "MIT",
                      version: str = "0.1.0",
                      template_path: str = "",
                      force: bool = False,
                      with_tests: bool = True,
                      with_docker: bool = False,
                      with_ci: bool = False) -> Dict[str, Any]:
        """
        Create a new Python project.

        Args:
            name: Project name
            project_type: Type of project
            description: Project description
            output_dir: Output directory
            requirements: List of requirements
            author: Author name
            license_type: License type
            version: Project version
            template_path: Custom template path
            force: Force overwrite existing directory
            with_tests: Include test files
            with_docker: Include Docker files
            with_ci: Include CI/CD files

        Returns:
            Dictionary with project creation result
        """
        result = {
            'success': False,
            'message': '',
            'path': '',
            'files': [],
            'warnings': [],
            'errors': []
        }

        try:
            # Validate inputs
            if not name:
                raise ValueError("Project name is required")

            if not project_type:
                raise ValueError("Project type is required")

            # Validate Python version
            if not check_python_version():
                raise ValueError("Python 3.8 or higher is required")

            # Get project types
            project_types = helpers.get_project_types_info()
            if project_type not in project_types:
                raise ValueError(f"Invalid project type: {project_type}")

            # Prepare paths
            if output_dir:
                safe_output_dir = sanitize_path(output_dir)
                base_output_dir = Path(safe_output_dir)
            else:
                base_output_dir = get_safe_output_directory()

            # Set default values
            description = description or project_types[project_type]['description']
            author = author or self._get_git_user() or "Unknown"
            requirements = requirements or []

            # Create temporary directory for generation
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Generate basic project structure
                self._generate_basic_structure(
                    temp_path, name, project_type, description,
                    author, license_type, version, with_tests,
                    with_docker, with_ci
                )

                # Process template files
                self._process_templates(
                    temp_path, name, project_type, description,
                    author, license_type, version, project_types[project_type]
                )

                # Add requirements
                if requirements:
                    self._add_requirements(temp_path, requirements, project_type)
                else:
                    self._generate_default_requirements(temp_path, project_type)

                # Move to final location
                final_output_dir = base_output_dir / name
                if final_output_dir.exists() and not force:
                    raise FileExistsError(
                        f"Directory '{final_output_dir}' already exists. Use --force to overwrite."
                    )

                if final_output_dir.exists():
                    shutil.rmtree(final_output_dir)

                ensure_directory_exists(final_output_dir.parent)
                shutil.move(str(temp_path / name), str(final_output_dir))

                # Initialize git repository
                self._init_git_repo(final_output_dir)

                # Update result
                result.update({
                    'success': True,
                    'message': f"Project '{name}' created successfully!",
                    'path': str(final_output_dir),
                    'files': list_files_recursive(final_output_dir),
                    'warnings': []
                })

                logger.info(f"Project generated at: {final_output_dir}")
                return result

        except Exception as e:
            error_result = handle_platform_errors(e)
            result.update(error_result)
            return result

    def _generate_basic_structure(self,
                                 base_dir: Path,
                                 name: str,
                                 project_type: str,
                                 description: str,
                                 author: str,
                                 license_type: str,
                                 version: str,
                                 with_tests: bool,
                                 with_docker: bool,
                                 with_ci: bool) -> None:
        """Generate the basic project structure."""

        # Main project directory
        project_dir = base_dir / name
        project_dir.mkdir()

        # Root files
        files_to_create = {
            "README.md": self._generate_readme_template(name, description, project_type),
            ".gitignore": self._generate_gitignore(),
        }

        # Add license if specified
        if license_type == "MIT":
            files_to_create["LICENSE"] = self._generate_mit_license(author)

        # Create pyproject.toml
        files_to_create["pyproject.toml"] = self._generate_pyproject_toml(
            name, description, author, license_type, version
        )

        # Create source directory
        src_dir = project_dir / name
        src_dir.mkdir()

        # Create __init__.py
        (src_dir / "__init__.py").write_text(
            f'"""{description}"""\n\n__version__ = "{version}"\n'
        )

        # Main application file
        main_file = self._get_main_file_content(project_type)
        (src_dir / self._get_main_file_name(project_type)).write_text(main_file)

        # Create requirements.txt
        requirements = self._get_default_requirements(project_type)
        req_content = "# Project dependencies\n" + "\n".join(requirements) + "\n"
        (project_dir / "requirements.txt").write_text(req_content)

        # Create tests directory if requested
        if with_tests:
            tests_dir = project_dir / "tests"
            tests_dir.mkdir()

            (tests_dir / "__init__.py").write_text("")
            (tests_dir / "test_main.py").write_text(
                self._generate_test_template(project_type)
            )

        # Create scripts directory
        scripts_dir = project_dir / "scripts"
        scripts_dir.mkdir()

        # Create other directories
        for dir_name in ["config", "data", "docs"]:
            (project_dir / dir_name).mkdir()
            (project_dir / dir_name / ".gitkeep").write_text("")

        # Create all files
        for filename, content in files_to_create.items():
            (project_dir / filename).write_text(content)

        # Create additional files based on project type
        if project_type in ['flask', 'fastapi', 'fastapi-crud']:
            # Create .env file
            env_content = """# Environment variables
DEBUG=True
SECRET_KEY=your-secret-key-here
"""
            (project_dir / ".env.example").write_text(env_content)

        if with_docker and project_type in ['flask', 'fastapi']:
            # Create Docker files
            docker_dir = project_dir / ".docker"
            docker_dir.mkdir()

            (docker_dir / "Dockerfile").write_text(self._generate_dockerfile(project_type))
            (docker_dir / "docker-compose.yml").write_text(self._generate_docker_compose())

        if with_ci:
            # Create GitHub Actions workflow
            gh_dir = project_dir / ".github" / "workflows"
            ensure_directory_exists(gh_dir)

            (gh_dir / "ci.yml").write_text(self._generate_github_actions())

    def _generate_readme_template(self, name: str, description: str, project_type: str) -> str:
        """Generate README template."""
        project_types = helpers.get_project_types_info()
        features = project_types[project_type]['features']

        return f"""# {name}

{description}

## Features

{chr(10).join(f"- {feature}" for feature in features)}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m {name} --help
```

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
black src/
isort src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Unknown (author not specified)
"""

    def _generate_gitignore(self) -> str:
        """Generate .gitignore template."""
        return """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
Pipfile.lock

# PEP 582
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# Documentation
docs/_build/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local
.env.*.local
"""

    def _generate_mit_license(self, author: str) -> str:
        """Generate MIT License."""
        from datetime import datetime
        year = datetime.now().year
        return f"""MIT License

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

    def _generate_pyproject_toml(self, name: str, description: str,
                                author: str, license_type: str,
                                version: str) -> str:
        """Generate pyproject.toml file."""
        normalized_name = name.replace('-', '_')
        return f"""[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "{version}"
description = "{description}"
readme = "README.md"
requires-python = ">=3.8"
license = {{text = "{license_type}"}}
authors = [
    {{name = "{author}"}},
]

[project.urls]
Homepage = "https://github.com/{{author}}/{name}"
Repository = "https://github.com/{{author}}/{name}.git"
Issues = "https://github.com/{{author}}/{name}/issues"

[project.scripts]
{name} = "{normalized_name}.main:main"

[tool.black]
line-length = 88
target-version = ['py38']
include = '\\\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
"""

    def _get_main_file_content(self, project_type: str) -> str:
        """Get main file content based on project type."""
        templates = {
            'cli': '''#!/usr/bin/env python3
"""CLI tool implementation"""

import argparse
import logging
import sys
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description='CLI tool description'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--example',
        help='Example argument'
    )
    return parser

def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        if args.example:
            logger.info(f"Example: {args.example}")
        logger.info("Starting the application")
        print("Hello from the CLI tool!")
        return 0
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
''',
            'fastapi': '''#!/usr/bin/env python3
"""FastAPI application implementation"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(
    title="API Title",
    description="API description",
    version="0.1.0"
)

class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None

items_db = []

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    items_db.append(item)
    return item

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
''',
            'flask': '''#!/usr/bin/env python3
"""Flask application implementation"""

from flask import Flask, jsonify
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return jsonify({
        'message': 'Welcome to the Flask application',
        'version': '0.1.0'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(debug=True, host='0.0.0.0', port=5000)
''',
        }

        return templates.get(project_type, templates['cli'])

    def _get_main_file_name(self, project_type: str) -> str:
        """Get main file name based on project type."""
        names = {
            'cli': '__main__.py',
            'flask': 'app.py',
            'fastapi': 'main.py',
            'fastapi-crud': 'main.py',
            'scraper': 'scraper.py',
            'scraper-async': 'scraper.py',
            'bot': 'bot.py',
            'discord-bot': 'bot.py',
            'data-analysis': 'analysis.py',
            'ml-model': 'model.py',
            'automation': 'automation.py',
            'django-app': 'app.py',
            'django-cmd': 'management/commands/command.py'
        }
        return names.get(project_type, 'main.py')

    def _generate_test_template(self, project_type: str) -> str:
        """Generate test template."""
        return '''#!/usr/bin/env python3
"""Test module"""

import pytest

def test_example():
    """Example test."""
    assert True

def main():
    """Run tests."""
    pytest.main([__file__])

if __name__ == "__main__":
    main()
'''

    def _add_requirements(self, project_dir: Path, requirements: List[str], project_type: str) -> None:
        """Add requirements to the project."""
        req_file = project_dir / "requirements.txt"
        content = req_file.read_text()

        # Add new requirements
        for req in requirements:
            req = req.strip()
            if req and req not in content:
                content += f"{req}\\n"

        req_file.write_text(content)

    def _generate_default_requirements(self, project_dir: Path, project_type: str) -> None:
        """Generate default requirements."""
        project_types = helpers.get_project_types_info()
        defaults = project_types[project_type]['default_requirements']

        # Add basic development requirements
        all_reqs = defaults + [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=5.0.0"
        ]

        req_file = project_dir / "requirements.txt"
        content = "# Project dependencies\\n"
        content += "\\n".join(all_reqs) + "\\n"
        req_file.write_text(content)

        # Create requirements-dev.txt
        dev_file = project_dir / "requirements-dev.txt"
        dev_content = """# Development dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
black>=22.0.0
isort>=5.10.0
flake8>=5.0.0
mypy>=0.991
pre-commit>=2.20.0
"""
        dev_file.write_text(dev_content)

    def _get_default_requirements(self, project_type: str) -> List[str]:
        """Get default requirements for project type."""
        project_types = helpers.get_project_types_info()
        return project_types[project_type]['default_requirements']

    def _process_templates(self, base_dir: Path, name: str,
                          project_type: str, description: str,
                          author: str, license_type: str,
                          version: str, project_info: Dict[str, Any]) -> None:
        """Process template files and replace placeholders."""
        # Define placeholders
        placeholders = {
            '{{name}}': name,
            '{{description}}': description,
            '{{author}}': author,
            '{{license}}': license_type,
            '{{version}}': version,
            '{{features}}': ', '.join(project_info['features']),
        }

        # Process all text files
        for root, files, _ in os.walk(base_dir):
            root_path = Path(root)

            for file in files:
                if file.endswith(('.py', '.md', '.txt', '.toml', 'yml', 'yaml')):
                    file_path = root_path / file

                    try:
                        content = file_path.read_text()
                        for placeholder, value in placeholders.items():
                            content = content.replace(placeholder, str(value))
                        file_path.write_text(content)
                    except Exception as e:
                        logger.warning(f"Failed to process {file_path}: {e}")

    def _generate_dockerfile(self, project_type: str) -> str:
        """Generate Dockerfile."""
        return '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
'''

    def _generate_docker_compose(self) -> str:
        """Generate docker-compose.yml."""
        return '''version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=development
    volumes:
      - .:/app
    restart: unless-stopped
'''

    def _generate_github_actions(self) -> str:
        """Generate GitHub Actions workflow."""
        return '''name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.9', '3.10', '3.11']

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov black isort flake8
        pip install -r requirements.txt

    - name: Lint with black
      run: |
        black --check .

    - name: Lint with isort
      run: |
        isort --check-only .

    - name: Lint with flake8
      run: |
        flake8 .

    - name: Test with pytest
      run: |
        pytest --cov=. --cov-report=xml
'''

    def _init_git_repo(self, project_path: Path) -> None:
        """Initialize git repository."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'init'],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and git_configured():
                result = subprocess.run(
                    ['git', 'add', '.'],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
                result = subprocess.run(
                    ['git', 'commit', '-m', 'Initial commit'],
                    cwd=project_path,
                    capture_output=True,
                    text=True
                )
        except FileNotFoundError:
            logger.warning("Git not found, skipping repository initialization")
        except Exception as e:
            logger.warning(f"Failed to initialize git repository: {e}")

    def _get_git_user(self) -> Optional[str]:
        """Get git user name."""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

def ensure_directory_exists(path: Path) -> None:
    """Ensure directory exists, create if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def git_configured() -> bool:
    """Check if git is configured."""
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

# Create global instance
_generator = PythonScriptGenerator()

def create_project(**kwargs) -> Dict[str, Any]:
    """Create project function for OpenCode platform."""
    return _generator.create_project(**kwargs)

def get_project_types() -> Dict[str, Any]:
    """Get project types info."""
    types_info = helpers.get_project_types_info()
    return {
        'success': True,
        'count': len(types_info),
        'project_types': types_info
    }

def get_skill_info() -> Dict[str, Any]:
    """Get skill information."""
    return {
        'success': True,
        'skill_name': 'python-script-generator',
        'display_name': 'Python Script Generator Pro',
        'version': '2.0.0',
        'description': 'Professional Python project template generator',
        'author': 'Claude',
        'category': 'Development',
        'keywords': ['python', 'generator', 'templates'],
        'examples': []
    }

def main() -> None:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Python Script Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=format_help()
    )

    parser.add_argument(
        'name',
        help='Project name'
    )

    parser.add_argument(
        '-t', '--type',
        default='cli',
        help='Project type (default: cli)'
    )

    parser.add_argument(
        '-d', '--description',
        help='Project description'
    )

    parser.add_argument(
        '-o', '--output',
        default='.',
        help='Output directory (default: current directory)'
    )

    parser.add_argument(
        '-r', '--requirements',
        help='Comma-separated list of requirements'
    )

    parser.add_argument(
        '-a', '--author',
        help='Author name'
    )

    parser.add_argument(
        '-l', '--license',
        default='MIT',
        help='License type (default: MIT)'
    )

    parser.add_argument(
        '-v', '--version',
        default='0.1.0',
        help='Project version (default: 0.1.0)'
    )

    parser.add_argument(
        '--template',
        help='Custom template path'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Force overwrite existing directory'
    )

    parser.add_argument(
        '--no-tests',
        action='store_true',
        help='Do not include test files'
    )

    parser.add_argument(
        '--no-docker',
        action='store_true',
        help='Do not include Docker files'
    )

    parser.add_argument(
        '--no-ci',
        action='store_true',
        help='Do not include CI/CD files'
    )

    parser.add_argument(
        '--list-types',
        action='store_true',
        help='List all available project types'
    )

    args = parser.parse_args()

    if args.list_types:
        project_types = get_project_types()
        print("Available project types:")
        for pt, info in project_types.items():
            print(f"  {pt}: {info['description']}")
        return

    # Parse requirements
    requirements = []
    if args.requirements:
        requirements = [r.strip() for r in args.requirements.split(',')]

    # Create project
    result = _generator.create_project(
        name=args.name,
        project_type=args.type,
        description=args.description,
        output_dir=args.output,
        requirements=requirements,
        author=args.author,
        license_type=args.license,
        version=args.version,
        template_path=args.template,
        force=args.force,
        with_tests=not args.no_tests,
        with_docker=not args.no_docker,
        with_ci=not args.no_ci
    )

    # Print result
    if result['success']:
        print(f"✅ {result['message']}")
        if result['path']:
            print(f"📁 Project location: {result['path']}")
        if result['files']:
            print(f"📄 Files created: {len(result['files'])}")
    else:
        print(f"❌ Error: {result['error']}")
        if result.get('suggestion'):
            print(f"💡 {result['suggestion']}")
        sys.exit(1)

if __name__ == "__main__":
    main()