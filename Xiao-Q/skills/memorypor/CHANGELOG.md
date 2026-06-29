# Changelog — Self-Improving Skill

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.1.0] — 2026-05-25

### Added
- **One-command workspace integration**: Auto-integrates CLAUDE.md, AGENTS.md, and HEARTBEAT.md snippets during setup
- **verify.sh**: Installation verification script for quick health checks
- **TRACE score**: Improved to 95/100 (Effectiveness: 4.5 → 4.75)

### Changed
- **setup.sh**: Enhanced with workspace integration and verification script generation
- **All scripts**: Version bumped to 2.1.0 for consistency

---

## [2.0.0] — 2026-05-25

### Added
- **Universal Adaptation**: Now supports all AI agents (Claude Code, Codex, Copilot, universal)
- **metadata.json**: Complete metadata file for SkillHub compatibility
- **glossary.md**: Unified terminology with Chinese-English mapping
- **corrections-pending.md**: Full overflow handling manual with 14-day observation period
- **Automated Setup Scripts**:
  - `scripts/setup.sh` — One-command installation with tier selection
  - `scripts/heartbeat.sh` — Automated memory maintenance
  - `scripts/stats.sh` — Enhanced statistics with health monitoring
  - `scripts/export.sh` — Full memory export with manifest
  - `scripts/import.sh` — Memory import with backup
- **Windows Support**:
  - `scripts/setup.bat` — Windows batch setup
  - `scripts/stats.bat` — Windows statistics
  - `scripts/heartbeat.bat` — Windows heartbeat
  - `scripts/export.bat` — Windows export
  - `scripts/import.bat` — Windows import
- **templates/**: Separated template directory
  - `templates/memory.md`
  - `templates/corrections.md`
  - `templates/index.md`
  - `templates/heartbeat-state.md`
  - `templates/project.md`
  - `templates/domain.md`
  - `templates/archive.md`
- **Enhanced HEARTBEAT.md**: Executable code snippets for integration
- **Dependency Checks**: All scripts now check for required commands before execution
- **Error Handling**: Improved error messages with recovery suggestions
- **Capacity Config Interface**: `config.json` with tier-based limits

### Changed
- **_meta.json**: Complete restructure to meet SkillHub standards
  - Added: schema_version, input_schema, output_schema, compatibility, tags, license, changelog, trace
  - Updated version to 2.0.0
- **SKILL.md frontmatter**: Standardized to SkillHub format
  - Added: icon, author, license, schema_version
  - Removed: slug, homepage, changelog, metadata (now in respective files)
- **SKILL.md Architecture**: Updated diagram to reflect new file structure
- **Memory Stats**: Enhanced output with progress bars and health status
- **Correction Overflow**: Clarified overflow strategy with corrections-pending.md
- **Promotion Flow**: Unified to "3 occurrences → confirmation → promote"
- **setup.md**: Updated to reference automated scripts

### Fixed
- **Version Inconsistency**: _meta.json now matches SKILL.md version (2.0.0)
- **Corrections Template**: Fixed "high-frequency default" contradiction
- **Script Dependencies**: Added jq and zip dependency checks
- **Error Messages**: Improved friendliness and actionable guidance

### Removed
- **memory-template.md**: Moved to templates/memory.md
- **Hardcoded Paths**: Scripts now use environment variables

---

## [1.2.16] — 2026-01-01

### Added
- Initial release with basic correction tracking
- Three-tier storage (HOT/WARM/COLD)
- Project and domain namespaces
- Basic heartbeat maintenance
- Security boundaries

### Known Issues
- Version management was inconsistent
- No automated setup scripts
- No export/import functionality
- Limited Windows support
- Missing metadata.json for SkillHub
