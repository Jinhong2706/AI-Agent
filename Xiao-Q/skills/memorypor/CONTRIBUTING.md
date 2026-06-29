# Contributing — Self-Improving Skill

Thank you for your interest in contributing to this skill!

## How to Contribute

### Reporting Issues

If you find a bug or have a suggestion:

1. Check existing issues to avoid duplicates
2. Use the issue template if available
3. Describe the problem clearly with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (OS, agent version, etc.)

### Submitting Changes

#### Before You Start

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Run existing tests/scripts to establish baseline

#### Code Style

- **Shell Scripts**: Follow POSIX standards for portability
  - Use `#!/bin/bash` with `set -euo pipefail` when appropriate
  - Test on Linux, macOS, and Windows (Git Bash)
  - Keep lines under 100 characters

- **Markdown**: Follow CommonMark spec
  - Use ATX-style headers (`#`, `##`, etc.)
  - Code blocks with language hints
  - Tables for structured data

#### Documentation

- Update `SKILL.md` for behavioral changes
- Update `metadata.json` for new features
- Add entries to `CHANGELOG.md` under `[Unreleased]`
- Add examples for new features

#### Commit Messages

Format: `type(scope): description`

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Examples:
```
feat(memory): add compression for HOT tier
fix(corrections): handle empty corrections.md
docs(faq): add troubleshooting section
```

### Testing Your Changes

#### Manual Testing Checklist

- [ ] Setup script works on clean system
- [ ] Setup script works with `--tier high`
- [ ] Stats script shows correct counts
- [ ] Export creates valid ZIP
- [ ] Import restores correctly
- [ ] Heartbeat handles missing files
- [ ] Windows batch files work

#### Test Environments

| Environment | Status |
|-------------|--------|
| macOS (latest) | Test before PR |
| Linux (Ubuntu 22.04) | Test before PR |
| Windows 11 (Git Bash) | Test before PR |
| Windows CMD | Test before PR |
| Claude Code | Test before PR |
| Codex | Test before PR |

### Pull Request Process

1. **Keep PRs focused**: One feature or fix per PR
2. **Update documentation**: All behavioral changes must be documented
3. **Add tests**: If adding functionality, add basic tests
4. **Follow naming conventions**:
   - Files: `kebab-case.md`, `snake_case.sh`
   - Functions: `snake_case()`
   - Variables: `SCREAMING_SNAKE_CASE` for constants

### SkillHub Compatibility

When contributing, ensure:

- [ ] `SKILL.md` has valid frontmatter (name, version, description, tags, icon, author, license)
- [ ] `_meta.json` has all required fields
- [ ] `metadata.json` exists with complete info
- [ ] No hardcoded absolute paths
- [ ] Cross-platform compatible (Linux, macOS, Windows)

### File Organization

```
self-improving/
├── SKILL.md              # Main documentation
├── _meta.json           # Agent contract (don't modify unless adding features)
├── metadata.json        # SkillHub metadata
├── scripts/             # Executable scripts
│   ├── *.sh            # Unix shell scripts
│   └── *.bat           # Windows batch files
└── templates/           # File templates
```

## Development Workflow

### Adding a New Script

1. Create `scripts/new-script.sh` with:
   - Shebang: `#!/bin/bash`
   - Version comment
   - Usage documentation
   - Dependency checks
   - Error handling

2. Create Windows equivalent in `scripts/new-script.bat`

3. Update `SKILL.md` Quick Reference

4. Update `setup.md` if new files need to be created

5. Add entry to `CHANGELOG.md`

### Adding a New Template

1. Create `templates/new-template.md`

2. Document in `SKILL.md` if it changes workflow

3. Add entry to `CHANGELOG.md`

## Questions?

- Open an issue for bugs
- Check existing issues before creating new ones
- Follow the code style guidelines above

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
