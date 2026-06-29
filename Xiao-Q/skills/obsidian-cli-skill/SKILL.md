---
name: obsidian-para-workflow
description: Use when the user wants to initialize, operate, or standardize an Obsidian vault with a PARA structure plus Diary and Share directories. Trigger for requests about setting up PARA folders, writing daily or weekly diary notes, managing active projects, distilling knowledge into areas/resources, archiving old material, preparing share-ready copies, or using Obsidian CLI automation for this workflow.
metadata:
  short-description: Generic PARA + Diary + Share workflow
---

# PARA + Diary + Share Obsidian Workflow

Use this skill to help set up and operate an Obsidian vault organized around PARA, with an active diary area and a share-ready publishing area.

This is generic. Do not assume a specific vault name, local path, language, project name, or existing folder set.

## Usage Guide

Use this skill when the user wants a practical Obsidian knowledge-management workflow rather than a generic note-taking explanation.

Typical user requests:

- "Initialize my Obsidian vault with PARA + Diary + Share."
- "Help me decide where this note should go."
- "Create a project workspace for `<project>`."
- "Write today's diary entry."
- "Turn this project note into reusable knowledge."
- "Prepare this note for sharing."
- "Review my active projects and unfinished tasks."
- "Archive old diary files."

Recommended operating flow:

1. Find the target vault with `obsidian vaults verbose`.
2. Initialize the folder structure if the vault is new.
3. Use `900 - Diary` for the latest month's journal entries.
4. Use `100-Projects` for active outcomes and project logs.
5. Distill reusable knowledge into `200-Area` or `300-Resources`.
6. Copy polished, audience-ready material into `Share`.
7. Move inactive material into `400-Archives`.

Placeholder convention:

- Replace `<vault>` with the Obsidian vault name.
- Replace `<project>` with the project name.
- Replace `<area>` with an ongoing responsibility or domain.
- Replace `<topic>` with a reusable knowledge topic.
- Replace `<title>` with a share-note title.
- Replace `YYYY-MM-DD`, `YYYY`, and `YYYY-MM-Week-N` with real dates.

When responding to the user:

- Start with the chosen target folder and why it fits.
- Then provide concrete Obsidian CLI commands.
- Include a Markdown template when creating a new note.
- Warn clearly before move, overwrite, restore, delete, or bulk operations.
- Keep canonical notes in PARA folders; use `Share` only for share-ready copies.

## First Checks

Inspect the local Obsidian CLI environment before producing vault-specific commands:

```powershell
obsidian version
obsidian vaults verbose
obsidian help
```

Once the target vault is known, route commands explicitly:

```powershell
obsidian vault="<vault>" ...
```

Avoid reading note bodies unless the user asks for content analysis or migration. Before write operations, say whether the command creates, appends, moves, copies, overwrites, or deletes.

## Initialize The Folder Structure

Recommended top-level folders:

```text
000-Sketch/
100-Projects/
200-Area/
300-Resources/
400-Archives/
900 - Diary/
Share/
```

Folder meanings:

- `000-Sketch`: raw capture, rough ideas, inbox notes, unclear material.
- `100-Projects`: active work with a goal, deadline, deliverable, or temporary outcome.
- `200-Area`: ongoing responsibilities, domains, skills, roles, and long-lived operating areas.
- `300-Resources`: reusable references that are not bound to an active project or responsibility.
- `400-Archives`: completed, inactive, abandoned, or historical material.
- `900 - Diary`: daily/weekly journal and personal timeline.
- `Share`: polished copies prepared for other people; not the canonical home of knowledge.

Create folders by creating useful index notes:

```powershell
obsidian vault="<vault>" create path="000-Sketch/_index.md" content="# Sketch\n\nRaw capture and unclear ideas.\n"
obsidian vault="<vault>" create path="100-Projects/_index.md" content="# Projects\n\nActive outcomes and deliverables.\n"
obsidian vault="<vault>" create path="200-Area/_index.md" content="# Area\n\nOngoing responsibilities and domains.\n"
obsidian vault="<vault>" create path="300-Resources/_index.md" content="# Resources\n\nReusable references.\n"
obsidian vault="<vault>" create path="400-Archives/_index.md" content="# Archives\n\nInactive or completed material.\n"
obsidian vault="<vault>" create path="900 - Diary/_index.md" content="# Diary\n\nDaily and weekly logs.\n"
obsidian vault="<vault>" create path="Share/_index.md" content="# Share\n\nPolished copies for sharing.\n"
```

## Routing Rules

Use purpose, not topic alone, to choose a folder:

- Still messy or not yet classified -> `000-Sketch`.
- Has an outcome and will end -> `100-Projects/<project>/`.
- Needs ongoing attention and does not really end -> `200-Area/<area>/`.
- Useful as reference outside the original context -> `300-Resources/<topic>/`.
- No longer active but worth keeping -> `400-Archives/...`.
- Records what happened today/this week -> `900 - Diary/`.
- Prepared for another person or audience -> `Share/`.

Do not move a note from Project to Area/Resource just because it contains knowledge. Move or copy only after its purpose changes.

## Diary Workflow

Default diary behavior:

1. Keep the latest month directly under `900 - Diary/`.
2. Move entries older than one month into `900 - Diary/<year>/`.
3. Use weekly files by default, named `YYYY-MM-Week-N.md` or a localized equivalent.
4. Append dated sections inside weekly files.
5. Use daily files only if the user explicitly prefers them.

Diary section template:

```markdown
## YYYY-MM-DD

### Progress

- 

### Project Log

- 

### Learned

- 

### Next

- [ ] 
```

Append a diary section:

```powershell
obsidian vault="<vault>" append path="900 - Diary/YYYY-MM-Week-N.md" content="\n## YYYY-MM-DD\n\n### Progress\n\n- \n\n### Project Log\n\n- \n\n### Learned\n\n- \n\n### Next\n\n- [ ] \n" open
```

Archive old diary files after checking names and dates:

```powershell
obsidian vault="<vault>" files folder="900 - Diary"
obsidian vault="<vault>" move path="900 - Diary/YYYY-MM-Week-N.md" to="900 - Diary/YYYY/YYYY-MM-Week-N.md"
```

## Project Workflow

For each active project:

```text
100-Projects/<project>/
  <project>.md
  Logs/
  Decisions/
  Knowledge/
  Tasks.md
```

Project entry template:

```markdown
# <project>

status:: active
type:: project

## Goal

## Current Focus

- [ ] 

## Risks

## Decisions

## Knowledge To Distill
```

Create a project:

```powershell
obsidian vault="<vault>" create path="100-Projects/<project>/<project>.md" content="# <project>\n\nstatus:: active\ntype:: project\n\n## Goal\n\n\n## Current Focus\n\n- [ ] \n\n## Risks\n\n\n## Decisions\n\n\n## Knowledge To Distill\n" open
obsidian vault="<vault>" create path="100-Projects/<project>/Tasks.md" content="# <project> Tasks\n\n- [ ] Define the next concrete outcome\n"
```

Track project work:

```powershell
obsidian vault="<vault>" tasks path="100-Projects/<project>" todo verbose
obsidian vault="<vault>" search:context query="risk" path="100-Projects/<project>"
obsidian vault="<vault>" search:context query="decision" path="100-Projects/<project>"
```

## Knowledge Distillation

Use this pipeline:

1. Diary records the day.
2. Project notes capture project-specific context.
3. Area or Resource notes preserve reusable knowledge.
4. Share notes are audience-ready copies.

Choose destination:

- `200-Area/<area>/...`: ongoing responsibility, skill, role, or domain.
- `300-Resources/<topic>/...`: reusable reference independent of current work.
- `Share/<title>.md`: polished copy for someone else.

Knowledge note template:

```markdown
# <topic>

type:: knowledge
source-project:: [[<project>]]
share-ready:: false

## Context

## Conclusion

## When To Use

## Steps / Examples

## Links
```

Create a knowledge note:

```powershell
obsidian vault="<vault>" create path="300-Resources/<topic>/<note>.md" content="# <note>\n\ntype:: knowledge\nshare-ready:: false\n\n## Context\n\n\n## Conclusion\n\n\n## When To Use\n\n\n## Steps / Examples\n\n\n## Links\n" open
```

## Share Workflow

`Share` is an outward-facing copy area. It should not replace the canonical note in Projects, Areas, or Resources.

When preparing a share note:

1. Identify the canonical source note.
2. Decide the audience and remove private/internal details as needed.
3. Create `Share/<title>.md`.
4. Keep links or a source reference back to the canonical note when useful.
5. Avoid overwriting existing share notes unless explicitly requested.

Create a share note:

```powershell
obsidian vault="<vault>" create path="Share/<title>.md" content="# <title>\n\n## Summary\n\n\n## Main Content\n\n\n## Examples\n\n\n## References\n" open
```

For exact copy operations, verify the source and destination first. Use filesystem copy only when needed and avoid overwriting without confirmation.

## Review And Maintenance

Daily review:

```powershell
obsidian vault="<vault>" tasks todo verbose
obsidian vault="<vault>" search:context query="blocked" path="100-Projects"
obsidian vault="<vault>" search:context query="risk" path="100-Projects"
```

Weekly review:

```powershell
obsidian vault="<vault>" files folder="900 - Diary"
obsidian vault="<vault>" tasks path="100-Projects" todo verbose
obsidian vault="<vault>" search:context query="Knowledge To Distill" path="100-Projects"
obsidian vault="<vault>" search query="share-ready:: true"
```

Vault cleanup:

```powershell
obsidian vault="<vault>" unresolved counts verbose
obsidian vault="<vault>" orphans total
obsidian vault="<vault>" deadends total
obsidian vault="<vault>" tags counts sort=count
```

## Response Style

When this skill is active:

- Ask for the vault name only if it cannot be inferred from context or CLI output.
- Provide concrete Obsidian CLI commands.
- Explain the target folder and why that folder fits.
- Use templates for new notes.
- Warn before any command that moves, overwrites, restores, permanently deletes, or bulk edits notes.
