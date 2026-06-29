#!/usr/bin/env python3
"""
Test suite for the main functionality
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from main_function import PythonScriptGenerator
from helpers import validate_project_config, get_project_types_info

class TestPythonScriptGenerator:
    """Test cases for PythonScriptGenerator"""

    def setup_method(self, method):
        """Setup test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.generator = PythonScriptGenerator()

    def teardown_method(self, method):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir)

    def test_generate_cli_project(self):
        """Test generating a CLI project"""
        result = self.generator.create_project(
            name="test-cli",
            project_type="cli",
            output_dir=str(self.test_dir),
            with_tests=False,  # Disable tests for faster testing
            with_docker=False,
            with_ci=False
        )

        assert result['success'] is True
        assert "Project 'test-cli' created successfully!" in result['message']
        assert result['path'] == str(self.test_dir / "test-cli")

        # Check if main files exist
        project_path = Path(result['path'])
        assert (project_path / "test-cli" / "__main__.py").exists()
        assert (project_path / "pyproject.toml").exists()
        assert (project_path / "requirements.txt").exists()
        assert (project_path / "README.md").exists()

    def test_generate_fastapi_project(self):
        """Test generating a FastAPI project"""
        result = self.generator.create_project(
            name="test-api",
            project_type="fastapi",
            description="Test API",
            output_dir=str(self.test_dir),
            with_tests=False,
            with_docker=False,
            with_ci=False
        )

        assert result['success'] is True
        assert "Project 'test-api' created successfully!" in result['message']

        # Check for FastAPI-specific files
        project_path = Path(result['path'])
        assert (project_path / "test_api" / "main.py").exists()

    def test_invalid_project_type(self):
        """Test error handling for invalid project type"""
        result = self.generator.create_project(
            name="test",
            project_type="invalid-type",
            output_dir=str(self.test_dir)
        )

        assert result['success'] is False
        assert "Invalid project type" in result['error']

    def test_force_overwrite(self):
        """Test force overwrite functionality"""
        # First creation
        result1 = self.generator.create_project(
            name="test-overwrite",
            project_type="cli",
            output_dir=str(self.test_dir),
            with_tests=False
        )
        assert result1['success'] is True

        # Second creation without force should fail
        result2 = self.generator.create_project(
            name="test-overwrite",
            project_type="cli",
            output_dir=str(self.test_dir),
            with_tests=False
        )
        assert result2['success'] is False

        # Third creation with force should succeed
        result3 = self.generator.create_project(
            name="test-overwrite",
            project_type="cli",
            output_dir=str(self.test_dir),
            force=True,
            with_tests=False
        )
        assert result3['success'] is True

    def test_custom_author(self):
        """Test custom author setting"""
        author_name = "Test Author"
        result = self.generator.create_project(
            name="test-author",
            project_type="cli",
            author=author_name,
            output_dir=str(self.test_dir),
            with_tests=False
        )

        assert result['success'] is True

        # Check if author is in README
        readme_path = Path(result['path']) / "README.md"
        content = readme_path.read_text()
        assert author_name in content


class TestValidation:
    """Test cases for validation functions"""

    def test_validate_project_config_valid(self):
        """Test validation of valid project config"""
        config = {
            'name': 'test-project',
            'type': 'cli',
            'description': 'Test project'
        }
        errors = validate_project_config(config)
        assert len(errors) == 0

    def test_validate_project_config_missing_required(self):
        """Test validation with missing required fields"""
        config = {
            'description': 'Test project'
        }
        errors = validate_project_config(config)
        assert "Missing required field: name" in errors
        assert "Missing required field: type" in errors

    def test_validate_project_config_invalid_type(self):
        """Test validation with invalid project type"""
        config = {
            'name': 'test-project',
            'type': 'invalid-type'
        }
        errors = validate_project_config(config)
        assert "Invalid project type" in errors[0]

    def test_validate_project_config_invalid_name(self):
        """Test validation with invalid project name"""
        config = {
            'name': '123-invalid',
            'type': 'cli'
        }
        errors = validate_project_config(config)
        assert "Project name must be a valid Python identifier" in errors[0]


class TestProjectTypes:
    """Test cases for project types"""

    def test_get_project_types_info(self):
        """Test retrieving project types information"""
        types_info = get_project_types_info()
        assert isinstance(types_info, dict)
        assert len(types_info) > 0
        assert 'cli' in types_info
        assert 'fastapi' in types_info
        assert 'flask' in types_info

        # Check structure of each type
        for pt_name, pt_info in types_info.items():
            assert 'description' in pt_info
            assert 'category' in pt_info
            assert 'features' in pt_info
            assert 'default_requirements' in pt_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])