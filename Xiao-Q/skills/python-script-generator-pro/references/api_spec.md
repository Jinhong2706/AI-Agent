# Python Script Generator API Specification

## Overview

The Python Script Generator SKILL provides an interface for creating professional Python project templates programmatically.

## Description

This skill allows users to generate complete Python project structures with best practices, including testing frameworks, Docker support, CI/CD pipelines, and comprehensive documentation.

## Main Functions

### create_project()

Creates a new Python project with the specified configuration.

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | Yes | - | Project name (must be a valid Python identifier) |
| `type` | string | Yes | - | Project type (see [Project Types](#project-types)) |
| `description` | string | No | - | Project description |
| `output_dir` | string | No | "." | Output directory for the project |
| `requirements` | list/string | No | | List of dependencies or comma-separated string |
| `author` | string | No | "Unknown" | Author name |
| `license` | string | No | "MIT" | License type |
| `version` | string | No | "0.1.0" | Project version |
| `template_path` | string | No | - | Path to custom template |
| `force` | boolean | No | false | Overwrite existing directory |
| `with_tests` | boolean | No | true | Include test files |
| `with_docker` | boolean | No | false | Include Docker configuration |
| `with_ci` | boolean | No | false | Include CI/CD configuration |

#### Return Value

Returns an object with the following structure:

```typescript
{
  success: boolean,
  message: string,
  path?: string,
  files?: string[],
  warnings?: string[],
  errors?: string[],
  suggestion?: string
}
```

#### Example

```python
result = create_project(
  name="my-api",
  type="fastapi",
  description="REST API service",
  withDocker=true,
  withCI=true
)
```

#### Error Handling

The function handles various error conditions:

- `FileExistsError`: Target directory already exists (use `force=true`)
- `ValueError`: Invalid project type or configuration
- `PermissionError`: Filesystem permission issues
- `OSError`: System-level errors

### get_project_types()

Returns information about all available project types.

#### Return Value

Returns an object with project type information:

```typescript
{
  success: boolean,
  count: number,
  projectTypes: {
    [typeName: string]: {
      description: string,
      category: string,
      features: string[],
      defaultRequirements: string[]
    }
  }
}
```

#### Example

```python
project_types = get_project_types()
print(project_types.projectTypes.fastapi.description)
```

### get_skill_info()

Returns information about the SKILL itself.

#### Return Value

```typescript
{
  skill_name: string,
  display_name: string,
  version: string,
  description: string,
  author: string,
  category: string,
  keywords: string[],
  examples: object[]
}
```

## Project Types

### Overview

The skill supports the following project types:

| Type | Category | Default Requirements | Description |
|------|----------|---------------------|-------------|
| `cli` | utility | [] | Command-line interface tools |
| `flask` | web | ["Flask>=2.0.0"] | Flask web applications |
| `fastapi` | web | ["fastapi>=0.100.0", "uvicorn[standard]>=0.20.0"] | FastAPI web applications |
| `fastapi-crud` | web | ["fastapi>=0.100.0", "uvicorn[standard]>=0.20.0", "sqlalchemy>=2.0.0", "pydantic>=2.0.0"] | FastAPI with CRUD operations |
| `django-app` | web | ["Django>=4.0.0"] | Django applications |
| `django-cmd` | django | ["Django>=4.0.0"] | Django management commands |
| `scraper` | data | ["requests>=2.28.0", "beautifulsoup4>=4.11.0"] | Web scrapers |
| `scraper-async` | data | ["aiohttp>=3.8.0", "beautifulsoup4>=4.11.0"] | Async web scrapers |
| `bot` | bot | ["python-telegram-bot>=20.0.0"] | Telegram bots |
| `discord-bot` | bot | ["discord.py>=2.3.0"] | Discord bots |
| `data-analysis` | data | ["pandas>=1.5.0", "numpy>=1.24.0", "matplotlib>=3.6.0"] | Data analysis projects |
| `ml-model` | ml | ["scikit-learn>=1.2.0", "pandas>=1.5.0", "numpy>=1.24.0"] | Machine learning models |
| `automation` | utility | [] | Automation scripts |

### Project Structure Details

Each project type generates a standardized structure:

#### Common Files
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules
- `pyproject.toml` - Python project configuration
- `requirements.txt` - Dependencies
- `{project_name}/` - Main package directory
- `{project_name}/__init__.py` - Package init file
- `{project_name}/{main_file}` - Main application file

#### Optional Files
- `tests/` - Test directory (when `with_tests=true`)
- `.docker/` - Docker configuration (when `with_docker=true`)
- `.github/workflows/` - CI/CD pipelines (when `with_ci=true`)
- `config/` - Application configuration
- `data/` - Data directory
- `docs/` - Documentation directory

## Configuration Options

### Environment Variables

The skill respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENCODE_OUTPUT_DIR` | Default output directory | Current directory |
| `PYTHON_SCRIPT_GENERATOR_LOG_LEVEL` | Logging level | "INFO" |

### Configuration File

The skill looks for configuration files in:
1. `config.yaml` in current directory
2. `~/.python-script-generator/config.yaml`

Example configuration:
```yaml
defaults:
  license: "MIT"
  with_docker: false
  with_ci: false

project_types:
  custom-type:
    description: "Custom project type"
    default_requirements: ["custom-package>=1.0.0"]
```

## Best Practices

### Project Naming
- Use lowercase letters
- Use underscores instead of spaces
- Avoid special characters
- Must be a valid Python identifier
- Example: `my_project`, `api_server`, `data_tool`

### Requirements Management
- Use semantic versioning for dependencies
- Specify minimum versions (e.g., `fastapi>=0.100.0`)
- Group related dependencies logically
- Consider development vs production dependencies

### Error Handling
- Always check the `success` field in returned objects
- Handle `errors` array appropriately
- Consider suggestions when errors occur
- Use `force` parameter carefully

## Performance Considerations

- The tool creates projects in a temporary directory first, then moves to the final location
- Large projects may take longer to generate
- File system operations are optimized for speed
- Consider using `force=false` to avoid unnecessary overwrites

## Security Notes

- All file paths are sanitized to prevent path traversal
- Project names are validated to ensure they're valid Python identifiers
- The tool does not execute code during project generation
- No network calls are made during project creation

## Integration Examples

### OpenCode Platform Integration

```typescript
// Basic usage
const result = await pythonScriptGeneratorSkill.createProject({
  name: "my-project",
  type: "fastapi"
});

// Advanced usage
const project = await pythonScriptGeneratorSkill.createProject({
  name: "advanced-api",
  type: "fastapi-crud",
  description: "Advanced CRUD API with authentication",
  withDocker: true,
  withCI: true,
  withTests: true,
  requirements: [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0",
    "sqlalchemy>=2.0.0",
    "python-jose>=3.3.0"
  ]
});
```

### Shell Integration

```bash
#!/bin/bash
# Generate multiple projects
for type in fastapi(flask scraper; do
  python-script-generator "project-$type" --type "$type" --with-docker
done
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate project
  id: generate
  run: |
    result=$(python -c "
    from scripts.main_function import create_project
    import json
    result = create_project(type='fastapi', name='ci-project', withCI=true)
    print(json.dumps(result))
    ")
    echo "::set-output name=result::$result"
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check output directory permissions
   - Use `output_dir` parameter with a writable location
   - Verify file system access

2. **Invalid Project Type**
   - Use `get_project_types()` to see available types
   - Check spelling and case sensitivity
   - Refer to the documentation

3. **Requirements Installation Failure**
   - Verify requirement format
   - Check network connectivity
   - Consider using compatible package versions

4. **Directory Already Exists**
   - Use `force=true` to overwrite
   - Choose a different `output_dir`
   - Backup existing content before overwriting

### Debug Mode

Enable debug logging by setting the environment variable:
```bash
export PYTHON_SCRIPT_GENERATOR_LOG_LEVEL=DEBUG
```

### Testing

Run the test suite to verify functionality:
```bash
pytest tests/
```

## Version History

### Version 2.0.0
- Complete rewrite with enhanced features
- Added support for 13 project types
- Improved error handling and validation
- Added Docker and CI/CD support
- Enhanced documentation and examples

## Support

For issues and questions:
- GitHub Issues: [Project Repository](https://github.com/python-script-generator/python-script-generator/issues)
- Documentation: [ReadTheDocs](https://python-script-generator.readthedocs.io/)
- Examples: See `examples/` directory in the project