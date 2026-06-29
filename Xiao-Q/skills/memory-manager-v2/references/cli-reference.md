# CLI Reference

Run commands from the skill root:

```powershell
python memory_manager.py --help
python memory_manager.py --version
```

All workspace commands require a `<workspace>` path.

## Read-Only

```powershell
python memory_manager.py analyze <workspace>
python memory_manager.py analyze <workspace> --json
python memory_manager.py search <keyword> <workspace>
python memory_manager.py search <keyword> <workspace> --tag <tag>
python memory_manager.py search <keyword> <workspace> --folder <folder>
python memory_manager.py load <workspace> --days 7
python memory_manager.py load <workspace> --mode brief
python memory_manager.py rank <workspace>
python memory_manager.py rank <workspace> --days 30
python memory_manager.py summarize <workspace>
python memory_manager.py report <workspace>
python memory_manager.py cache-reminder <workspace>
python memory_manager.py token-check <workspace>
python memory_manager.py token-trends <workspace> --period daily
python memory_manager.py token-trends <workspace> --period week
python memory_manager.py token-trends <workspace> --period month
python memory_manager.py scan <workspace>
python memory_manager.py doctor <workspace>
```

## Preview And Cleanup

These commands preview by default:

```powershell
python memory_manager.py cache-clean <workspace>
python memory_manager.py clean <workspace>
python memory_manager.py auto-clean <workspace>
python memory_manager.py dedup <workspace>
```

Use `--execute` only after explicit user confirmation:

```powershell
python memory_manager.py cache-clean <workspace> --execute
python memory_manager.py clean <workspace> --execute
python memory_manager.py auto-clean <workspace> --execute
python memory_manager.py dedup <workspace> --execute
```

## Export, Import, Backup

```powershell
python memory_manager.py export <workspace> <output.zip>
python memory_manager.py import <workspace> <input.zip> --confirm
python memory_manager.py backup <workspace> --path <backup_dir>
python memory_manager.py backup <workspace> --path <backup_dir> --execute
python memory_manager.py backup <workspace> --path <backup_dir> --restore --execute
```

`import` writes memory files and requires `--confirm`.

## Prompt Templates

```powershell
python memory_manager.py prompt-list <workspace>
python memory_manager.py prompt-list <workspace> --tag <tag>
python memory_manager.py prompt-get <name> <workspace>
python memory_manager.py prompt-save <name> <workspace> --content "<prompt text>"
python memory_manager.py prompt-save <name> <workspace> --content "<prompt text>" --tags "tag1,tag2"
python memory_manager.py prompt-search <workspace> --keyword <keyword>
python memory_manager.py prompt-search <workspace> --tag <tag>
```

Prompt files are stored as `PROMPT_*.md`.

## Language

```powershell
python memory_manager.py --lang zh analyze <workspace>
python memory_manager.py --lang en analyze <workspace>
```

Supported values are `zh` and `en`.

## Common Failures

- Missing workspace argument: rerun with the path containing `.workbuddy/memory/`.
- Missing memory directory: create `<workspace>/.workbuddy/memory/` or choose the correct workspace.
- Import without confirmation: inspect the archive first, then rerun with `--confirm`.
- Console encoding problems: this release configures stdout/stderr with replacement behavior to avoid Unicode crashes on legacy Windows consoles.
