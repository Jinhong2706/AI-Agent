---
name: skill-installer
description: Install skills from GitHub repositories into the local skills directory. Use when a user asks to install a skill, add a skill from a repo, list installable skills, or references a GitHub URL containing skills.
---

# Skill Installer

Install skills from GitHub repositories into `.grok/skills/`, persisted across sessions.

## Scripts

All scripts require network access. Use the bash tool to run them.

### List available skills from a GitHub repo

```bash
bash <this-skill-path>/scripts/list-skills.sh [--repo owner/repo] [--path skills-dir] [--ref branch]
```

Defaults: `--repo xai-org/skills --path skills/.curated --ref main`

### Install a skill from GitHub

```bash
bash <this-skill-path>/scripts/install-skill.sh --repo owner/repo --path path/to/skill [--ref branch]
```

Or from a full GitHub URL:

```bash
bash <this-skill-path>/scripts/install-skill.sh --url https://github.com/owner/repo/tree/main/path/to/skill
```

## Behavior

- Downloads the skill directory from GitHub via zip archive (public repos) or falls back to `git sparse-checkout` (private repos).
- Validates that the downloaded directory contains a `SKILL.md`.
- Aborts if the destination skill directory already exists.
- Installs to `.grok/skills/<skill-name>` (persisted across sessions).
- Supports `GITHUB_TOKEN` or `GH_TOKEN` environment variables for private repo access.

## Communication

When listing skills, output the list and ask which ones to install:

```
Available skills from owner/repo:
1. skill-one
2. skill-two (already installed)
Which ones would you like installed?
```

After installing, tell the user to start a new session to pick up the new skill.
