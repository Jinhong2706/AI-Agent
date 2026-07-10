---
name: skill-creator
description: Guide for creating and updating skills that extend the agent's capabilities. Use when a user wants to create a new skill, update an existing skill, or asks about the skill format. Triggers include "create a skill", "make a skill for", "new skill", "update this skill", "skill format".
---

# Skill Creator

Create and manage skills — modular instruction packages that specialize the agent for specific tasks, domains, or workflows.

## What Skills Are

Skills are directories containing a `SKILL.md` file and optional supporting resources. They provide knowledge the model doesn't inherently have: company-specific workflows, domain procedures, tool integrations, templates.

**Do not create skills for things the model already knows.** Only encode knowledge that is non-obvious, procedural, or organization-specific.

```
skill-name/
├── SKILL.md              # Required: frontmatter + instructions
├── scripts/              # Optional: executable code
├── references/           # Optional: docs loaded on demand
└── assets/               # Optional: templates, images, fonts
```

## SKILL.md Format

### Frontmatter (required)

```yaml
---
name: kebab-case-name
description: What this skill does and WHEN to use it. Include trigger words and scenarios. This is the only thing shown before the skill is loaded — make it count.
---
```

- `name`: lowercase letters (a-z), digits (0-9), and single hyphens (-) only. Must start and end with a letter or digit, no consecutive hyphens. Must be 2-64 characters long and **must equal the parent directory name** (e.g. directory `my-skill/` → `name: my-skill`).
- `description`: the primary trigger mechanism. Include both what and when. All trigger information goes here, not in the body. Maximum 1,024 characters.

**Strict YAML rules for `description` (validator-enforced, no exceptions):**

- Write it as a plain (unquoted) YAML scalar — do not wrap in `"..."` or `'...'`.
- Do not include `: ` (colon-space). It forces quoting, which is banned. Reword instead:
  - ❌ `Use for X: a, b, c.`
  - ✅ `Use for X — a, b, c.` / `Use for X including a, b, c.`
- Do not include `<` or `>`. They get parsed as XML tags by the system-prompt assembler.
- Keep it on a single line (multi-line scalars require quoting).

**Allowed top-level frontmatter keys** (agentskills.io spec): `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Anything else fails CI — put custom fields under `metadata:`:

```yaml
metadata:
  type: workflow
  version: "1.0"
```

### Body (required)

Markdown instructions loaded when the skill is activated. Write in imperative form. Be concise — the context window is shared with everything else.

**Key principle:** Only include what the model doesn't already know. Challenge every paragraph: "Does this justify its token cost?"

## Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (name + description) — always visible in context (~100 tokens)
2. **SKILL.md body** — loaded on demand via `load_skill` (target <5k tokens)
3. **Bundled resources** — read by the model as needed (unlimited)

Keep SKILL.md under 500 lines. When approaching this limit, move content to `references/` files and link to them from SKILL.md.

## Resource Guidelines

### scripts/

Executable code for tasks that need deterministic reliability or are repeatedly rewritten.

- Use when the same code would be rewritten every time
- Scripts can be executed without loading into context (token efficient)
- Test scripts by running them before finalizing

### references/

Documentation loaded into context as needed.

- Use for detailed information too long for SKILL.md
- Organize by domain or variant (e.g., `references/aws.md`, `references/gcp.md`)
- For files >100 lines, include a table of contents
- Keep references one level deep from SKILL.md — no nested references

### assets/

Files used in output, not loaded into context.

- Templates, images, boilerplate code, fonts
- The model copies or modifies these rather than reading them

## Creating a Skill

### 1. Understand the use case

Clarify with concrete examples:
- What tasks should this skill handle?
- What would a user say that should trigger it?
- What does the model NOT already know about this domain?

### 2. Plan resources

For each example task, identify:
- What code is rewritten repeatedly? → `scripts/`
- What reference docs are needed? → `references/`
- What templates or assets are reused? → `assets/`

### 3. Initialize the skill

Run the init script to create the skill in `/home/workdir/.grok/skills/` (skills in this directory persist across sessions):

```bash
bash <this-skill-path>/scripts/init-skill.sh <skill-name> /home/workdir/.grok/skills [--resources scripts,references,assets]
```

### 4. Write SKILL.md

- Start with a clear, concise frontmatter description
- Write instructions in imperative form
- Reference bundled resources with relative paths
- Test by reading it fresh — does it contain everything needed?

### 5. Validate

Run validation to catch structural issues:

```bash
bash <this-skill-path>/scripts/validate-skill.sh <skill-directory>
```

### 6. Iterate

Use the skill on real tasks, notice gaps, update accordingly.

## Skill Location

Always create new skills in `/home/workdir/.grok/skills/<skill-name>/`. This is the only directory that is automatically synced to cloud storage. Skills created elsewhere (e.g. `~/.grok/skills/`) will be lost when the session ends.

Skills are discovered from two sources (highest to lowest priority):

1. **User skills** in `/home/workdir/.grok/skills/` — created, edited, and deleted here. Persisted across sessions.
2. **Bundled skills** — shipped defaults (e.g. pdf, color, docx). Editable in-session but changes do not persist. To permanently customize a bundled skill, create a skill with the same name in `.grok/skills/` — it will override the bundled version.

## Anti-patterns

- **Don't duplicate model knowledge.** No "how to write a for loop" skills.
- **Don't put trigger info in the body.** It's only read after triggering.
- **Don't create README.md, CHANGELOG.md, etc.** Skills are for agents, not humans.
- **Don't nest references.** All reference files link directly from SKILL.md.
- **Don't exceed 500 lines in SKILL.md.** Split into references.
