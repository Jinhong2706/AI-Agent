# Safety Notes

Memory files, prompt templates, token records, and exported archives may contain private user data.

## Operation Classes

Read-only commands:

- `analyze`
- `search`
- `load`
- `rank`
- `summarize`
- `report`
- `cache-reminder`
- `token-check`
- `token-trends`
- `scan`
- `doctor`
- `prompt-list`
- `prompt-get`
- `prompt-search`

Preview-first commands:

- `cache-clean`
- `clean`
- `auto-clean`
- `dedup`
- `backup`

Write commands requiring explicit confirmation:

- `cache-clean --execute`
- `clean --execute`
- `auto-clean --execute`
- `dedup --execute`
- `backup --execute`
- `import --confirm`
- `prompt-save`

## Boundaries

- Work only inside the user-provided `<workspace>`.
- Do not clean unrelated system folders.
- Do not delete, archive, import, restore, or overwrite memory data without explicit confirmation.
- Prefer preview output before write operations.
- Treat exported ZIP files as sensitive.
- Do not promise perfect safety, permanent memory, automatic sync, or compliance.

## Import Checks

The importer includes ZIP path and size checks, including:

- rejecting absolute paths and parent traversal entries;
- limiting imported file types to `.md` and `.summary`;
- limiting entry count and total uncompressed size;
- writing only under the selected workspace.

These checks reduce risk but do not replace user review of archive contents.
