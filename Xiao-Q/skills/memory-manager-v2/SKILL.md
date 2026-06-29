---
name: memory-manager-v3
description: Manage WorkBuddy .workbuddy/memory files with the bundled Python CLI: analyze, search, load, rank, summarize, report, token-check, cache preview, backup/export/import, and PROMPT_ template management. Use for memory manager, memory analysis, memory search, token budget check, cache cleanup preview, memory backup, prompt templates, 记忆管家, 记忆分析, 记忆搜索, Token检查, 缓存清理预览, 记忆备份, Prompt模板管理.
author: aakook
organization: 叁五（汕尾）科技有限公司
email: 38505053@qq.com
---

# Memory Manager V3

中文摘要：当用户需要管理 WorkBuddy 工作区中的 `.workbuddy/memory/` 记忆文件、Token 预算、缓存预览、备份导出、导入恢复或 `PROMPT_` 模板时使用此 Skill。

Run commands from this skill directory. Use the bundled CLI:

```powershell
python memory_manager.py --help
python memory_manager.py <command> <workspace>
```

`<workspace>` is the folder that contains, or should contain, `.workbuddy/memory/`.

## Use For

- Analyze, search, load, rank, summarize, or report memory files.
- Check estimated Token usage and trends.
- Preview cache cleanup and memory cleanup.
- Export or import memory data with explicit confirmation.
- Manage prompt templates stored as `PROMPT_*.md`.

Do not use this skill for general file cleanup, code review, document conversion, or deleting unrelated files.

## Inputs

Before running a command, identify:

- Workspace path.
- Intended action: read-only, preview, or write.
- Search keyword, date range, tags, output archive, or prompt content when needed.

## Read-Only Commands

These commands inspect data and can run without confirmation:

```powershell
python memory_manager.py analyze <workspace>
python memory_manager.py search <keyword> <workspace>
python memory_manager.py load <workspace> --days 7
python memory_manager.py rank <workspace>
python memory_manager.py summarize <workspace>
python memory_manager.py report <workspace>
python memory_manager.py token-check <workspace>
python memory_manager.py token-trends <workspace> --period week
python memory_manager.py cache-reminder <workspace>
python memory_manager.py scan <workspace>
python memory_manager.py doctor <workspace>
python memory_manager.py prompt-list <workspace>
python memory_manager.py prompt-search <workspace> --keyword <keyword>
```

## Preview Commands

Cleanup and deduplication commands are preview-only unless `--execute` is provided:

```powershell
python memory_manager.py cache-clean <workspace>
python memory_manager.py clean <workspace>
python memory_manager.py auto-clean <workspace>
python memory_manager.py dedup <workspace>
```

Use `--execute` only after showing the preview and receiving explicit user confirmation:

```powershell
python memory_manager.py cache-clean <workspace> --execute
python memory_manager.py clean <workspace> --execute
python memory_manager.py auto-clean <workspace> --execute
python memory_manager.py dedup <workspace> --execute
```

## Export, Import, And Backup

Export writes a ZIP archive:

```powershell
python memory_manager.py export <workspace> <output.zip>
```

Import writes files into the workspace and requires `--confirm`:

```powershell
python memory_manager.py import <workspace> <input.zip> --confirm
```

Backup defaults to preview mode. Use `--execute` only after user confirmation:

```powershell
python memory_manager.py backup <workspace> --path <backup_dir>
python memory_manager.py backup <workspace> --path <backup_dir> --execute
```

## Prompt Templates

Prompt templates are stored under `.workbuddy/memory/` with the `PROMPT_` prefix:

```powershell
python memory_manager.py prompt-list <workspace>
python memory_manager.py prompt-get <name> <workspace>
python memory_manager.py prompt-save <name> <workspace> --content "<prompt text>"
python memory_manager.py prompt-search <workspace> --keyword <keyword>
```

## Language

The CLI supports Chinese and English interface output:

```powershell
python memory_manager.py --lang zh analyze <workspace>
python memory_manager.py --lang en analyze <workspace>
```

## Safety And Privacy

- Treat memory files and exported ZIP files as sensitive user data.
- Do not import, delete, archive, restore, or execute cleanup unless the user explicitly confirms.
- Prefer preview commands before any write operation.
- Do not claim permanent memory, automatic sync, perfect accuracy, or absolute safety.
- Exported archives may contain private information; ask the user where to save them.
- Import checks ZIP paths and size limits, but important memory changes still require user review.

## References

- Read `references/cli-reference.md` when exact command syntax is needed.
- Read `references/security.md` before import, cleanup, backup, restore, or other write operations.
