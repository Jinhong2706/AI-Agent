---
name: obsidian-project-sync
description: Use when the user asks to sync, store, update, or persist real local project content, project information, durable project memory, Obsidian notes, markdown wiki notes, or LLM Wiki notes.
---

# Obsidian Project Sync

## Purpose

Sync durable facts from real project files into an Obsidian-compatible Markdown wiki. Record project knowledge, not the agent's conversation or work narration.

## Resolve the Wiki

Use the first available source:

1. Path explicitly provided by the user.
2. Existing project/vault instruction file such as `SCHEMA.md`, `AGENTS.md`, `CLAUDE.md`, or a handoff note.
3. Environment variables such as `OBSIDIAN_VAULT_PATH` or `WIKI_PATH`.
4. A clearly existing local Obsidian/Markdown wiki folder.

If the wiki path is still ambiguous, ask for it. If the wiki is inaccessible, include a compact `Obsidian Memory Update` block in the final response.

## Scope Gate

Sync only project-type work tied to a real local project folder or repository. Do not store:

- ordinary agent chat content
- assistant status updates or process narration
- skill-installation discussions
- tool-operation history
- "what the agent did" logs
- secrets, tokens, passwords, API keys, private keys, full `.env` contents, credentials, or noisy logs

## Language

Honor the user's requested language. If none is specified, match the existing wiki's language. Keep project names, product names, framework/library names, programming language names, commands, paths, file names, API names, code identifiers, config keys, URLs, and error messages in their original form.

## Workflow

1. Orient first: read existing `SCHEMA.md`, `index.md`, and recent `log.md` when present; search existing notes before creating new ones.
2. Inspect real project files, repo state, docs, source code, tests, configs, and verification commands.
3. Follow the wiki's existing schema. If no schema exists, use the default layout below.
4. Write a sanitized raw project snapshot before or alongside compiled notes.
5. Update the compiled project entity page with durable content: overview, architecture, tech stack, important paths, key files, current status, verification commands, open issues, and related projects.
6. Append a project change log entry with modification time and modification content; when useful, include changed files, commands, verification results, and source notes.
7. Update `index.md`, `log.md`, `wikilinks.md`, and relevant index pages if they exist.
8. Use Obsidian `[[wikilinks]]` to connect projects, change logs, related projects, technologies, decisions, PRDs/specs, and reusable project/domain concepts.
9. Keep `concepts/`, `comparisons/`, and `queries/` sparse; create pages there only for reusable project/domain knowledge, comparisons, or valuable query results.

## Default Layout

Use this only when the target wiki has no stronger local convention:

```text
raw/projects/<project-slug>/<YYYY-MM-DD>-<task-slug>.md
entities/<project-name>/<project-name>.md
entities/<project-name>/<project-name> <change-log-label>.md
```

Choose `<change-log-label>` in the user's/wiki's language, such as `Change Log` for English or `修改记录` for Chinese.

## Source Project Docs

Read existing project guidance when present: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `docs/HANDOFF.md`, `HANDOFF.md`, or equivalent local files. Do not create or modify agent-specific project docs solely for wiki sync unless the user asks.

## Verification

Before claiming completion, verify:

- expected notes exist in the wiki
- wikilinks are not broken
- sensitive-value scans do not reveal credentials

In the final response, briefly report which notes were created or updated.
