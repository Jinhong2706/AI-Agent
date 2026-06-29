---
name: llm-wiki
description: |
  LLM-powered personal knowledge base management. Build and maintain a structured wiki incrementally.
  Use when: building knowledge base, managing wiki, ingesting sources, knowledge management, 
  个人知识库, 知识管理, 摄入来源, 维护 wiki, 增量构建, 交叉引用, 实体页面, 概念页面,
  ingest, query wiki, lint wiki, cross-reference, entity extraction, concept mapping,
  使用wiki技能处理, wiki技能处理一下, 用wiki处理, wiki处理一下.
version: 1.0.0
author: user
triggers:
  - ingest
  - wiki
  - knowledge base
  - 知识库
  - 来源
  - 摄入
  - entity
  - concept
  - cross-reference
  - 交叉引用
  - 实体
  - 概念
  - 使用wiki技能处理
  - wiki技能处理一下
  - 用wiki处理
  - wiki处理一下
---

# LLM Wiki Skill

Transform your LLM into a knowledge base maintainer. Instead of just retrieving from raw documents, the LLM **incrementally builds and maintains a persistent wiki** — a structured, interlinked collection of markdown files.

## Core Philosophy

**The wiki is a persistent, compounding artifact.** The cross-references are already there. The contradictions have already been flagged. The synthesis already reflects everything you've read. The wiki keeps getting richer with every source you add and every question you ask.

## Three-Layer Architecture

```
wiki-project/
├── raw/                        # Layer 1: Source documents (immutable)
│   ├── articles/
│   ├── papers/
│   └── assets/
├── wiki/                       # Layer 2: LLM-maintained knowledge base
│   ├── index.md                # Content index
│   ├── overview.md             # Synthesis overview
│   ├── entities/               # Entity pages (people, orgs, products)
│   ├── concepts/               # Concept pages (ideas, theories, methods)
│   ├── sources/                # Source summaries
│   └── comparisons/            # Comparison analyses
├── log.md                      # Chronological activity log
└── WIKI.md                     # Layer 3: Schema configuration
```

## Core Operations

### 1. Ingest Operation

**When to use**: User adds a new source document and wants it integrated into the wiki.

**Workflow**:
```
1. Read the source document from raw/
2. Discuss key takeaways with user (if interactive mode)
3. Create/update source summary in wiki/sources/
4. Extract and update entity pages in wiki/entities/
5. Extract and update concept pages in wiki/concepts/
6. Update wiki/index.md with new entries
7. Append entry to log.md
```

**Interactive vs Batch Mode**:
- **Interactive** (important sources): Pause after reading source, discuss with user, get guidance on emphasis
- **Batch** (secondary sources): Process autonomously without user interaction

Configure mode in `WIKI.md`:
```yaml
workflow:
  default_mode: interactive  # or batch
  batch_threshold: 3  # Process N sources at once when batch mode
```

**Ingest Checklist**:
- [ ] Source summary created/updated
- [ ] Entities extracted and pages updated
- [ ] Concepts extracted and pages updated
- [ ] Cross-references added (`[[page-name]]` syntax)
- [ ] Frontmatter metadata added
- [ ] index.md updated
- [ ] log.md appended

### 2. Query Operation

**When to use**: User asks a question against the wiki.

**Workflow**:
```
1. Read wiki/index.md to locate relevant pages
2. Read relevant wiki pages
3. Synthesize answer with citations
4. (Optional) Write answer back to wiki as new page
```

**Key Insight**: Good answers can be filed back into the wiki as new pages. A comparison you asked for, an analysis, a connection you discovered — these are valuable and shouldn't disappear into chat history.

**Output Formats**:
- Markdown page (default)
- Comparison table
- Marp slide deck (if requested)
- Chart/visualization (if appropriate)

**Write-back Decision**:
Ask user: "Should I save this analysis to the wiki?" If yes, file under appropriate directory.

### 3. Lint Operation

**When to use**: Periodic health checks, or when user asks to check wiki health.

**Workflow**:
```
1. Iterate through all wiki pages
2. Check for issues:
   - Contradictions between pages
   - Stale claims (newer sources supersede older ones)
   - Orphan pages (no inbound links)
   - Missing pages (referenced but don't exist)
   - Incomplete cross-references
   - Data gaps
3. Generate health report
4. Suggest fixes and new sources to seek
```

**Lint Report Format**:
```markdown
# Wiki Health Report - [DATE]

## Issues Found

### Contradictions
- [[entities/org-a]] claims X, but [[sources/report-b]] says Y

### Orphan Pages
- [[concepts/isolated-idea]] has no inbound links

### Missing Pages
- [[entities/referenced-person]] referenced but doesn't exist

### Data Gaps
- No sources on [topic] since [date]

## Recommendations
1. Resolve contradiction in org-a by...
2. Add cross-references to isolated-idea from...
3. Create page for referenced-person using...
4. Search for recent sources on [topic]
```

## File Conventions

### Page Metadata (YAML Frontmatter)

```yaml
---
title: Page Title
type: entity|concept|source|comparison
created: 2026-04-07
updated: 2026-04-07
sources: [source-id-1, source-id-2]
tags: [tag1, tag2]
related: [[related-page-1]], [[related-page-2]]
---
```

### Index Format (wiki/index.md)

```markdown
# Wiki Index

## Overview
- [[overview]] - Synthesis of all knowledge

## Entities
- [[entities/person-a]] - Brief description
- [[entities/org-b]] - Brief description

## Concepts
- [[concepts/key-idea]] - Brief description

## Sources
- [[sources/article-1]] (2026-04-01) - Brief description

## Comparisons
- [[comparisons/x-vs-y]] - Brief description
```

### Log Format (log.md)

```markdown
## [2026-04-07 10:30] ingest | Article Title
- Added source: [[sources/article-title]]
- Updated entities: [[entities/person-a]], [[entities/org-b]]
- Created concept: [[concepts/key-idea]]
- Cross-references: 5 added

## [2026-04-07 11:00] query | What is X?
- Created comparison: [[comparisons/x-comparison]]

## [2026-04-07 14:00] lint | Health check
- Issues: 1 contradiction, 2 orphans
- Fixed: 1 orphan (added cross-references)
```

**Parsing Tip**: Each entry starts with `## [DATE TIME] operation | Title`, making it grep-friendly.

## Tool Integration

### qmd Search Engine

For large wikis (>100 sources), use qmd for search instead of index.md.

```bash
# Search wiki pages
qmd search "query text" --path wiki/

# With re-ranking
qmd search "query text" --path wiki/ --rerank
```

Read `references/qmd-integration.md` for setup instructions.

### Obsidian Integration

**Dataview Queries**: Use YAML frontmatter for dynamic queries.

```dataview
TABLE type, created, sources
FROM "wiki/entities"
WHERE contains(tags, "important")
SORT created DESC
```

**Graph View**: Visualize wiki connections in Obsidian.

Read `references/obsidian-workflow.md` for detailed setup.

### Marp Slide Decks

Generate presentations from wiki content:

```markdown
---
marp: true
---

# Title Slide

Content from wiki...

---

# Next Slide

More content...
```

## Workflow Modes

### Interactive Mode (Important Sources)

```
User: "Here's an important report, ingest it"
Agent: 
1. Reads source
2. "Key findings: [summary]. Should I emphasize anything specific?"
3. [User guidance]
4. Creates/updates wiki pages
5. Shows summary of changes
```

### Batch Mode (Secondary Sources)

```
User: "Ingest these 5 articles"
Agent:
1. Reads all sources
2. Processes autonomously
3. Reports: "Ingested 5 sources. Created 3 entity pages, updated 7 concept pages."
```

### Mixed Mode (Default)

Configure in `WIKI.md`:
```yaml
workflow:
  mode: mixed
  interactive_keywords: [important, key, critical, flagship]
  # Sources with these keywords trigger interactive mode
```

## References

- `references/wiki-architecture.md` - Detailed architecture explanation
- `references/page-templates.md` - Page structure templates
- `references/lint-rules.md` - Health check rules
- `references/qmd-integration.md` - Search engine setup
- `references/obsidian-workflow.md` - Obsidian setup guide

## Templates

- `templates/entity-page.md` - Entity page template
- `templates/concept-page.md` - Concept page template
- `templates/source-summary.md` - Source summary template
- `templates/comparison-table.md` - Comparison page template
- `templates/WIKI.md` - Schema configuration example

## Scripts

- `scripts/wiki-init.py` - Initialize a new wiki project

## Quick Start

1. **Initialize wiki project**:
   ```
   python scripts/wiki-init.py /path/to/project
   ```

2. **Configure WIKI.md** for your domain

3. **Add sources to raw/** directory

4. **Ingest first source**:
   ```
   "Ingest raw/articles/first-article.md"
   ```

5. **Query wiki**:
   ```
   "What do we know about [topic]?"
   ```

6. **Check health**:
   ```
   "Run a lint check on the wiki"
   ```

## Best Practices

1. **One source at a time** for important content (interactive mode)
2. **Batch similar sources** for efficiency (news updates, routine reports)
3. **Write back good queries** — don't let insights disappear
4. **Lint weekly** — catch issues before they compound
5. **Use tags consistently** — enables Dataview queries
6. **Keep sources in raw/** immutable — wiki is the mutable layer
7. **Git commit after each ingest** — version history is free

## The Key Difference

Most RAG systems retrieve from raw documents on every query. Nothing accumulates.

LLM Wiki compiles knowledge once and keeps it current. Every source and every query makes the wiki richer.

**The human's job**: Curate sources, direct analysis, ask good questions.

**The LLM's job**: Everything else — summarizing, cross-referencing, filing, bookkeeping.
