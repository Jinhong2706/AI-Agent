# Obsidian Workflow Guide

Obsidian is the recommended IDE for viewing and navigating the LLM Wiki. This guide covers setup, plugins, and best practices.

## Why Obsidian?

- **Native wiki-link support**: `[[page-name]]` syntax works out of the box
- **Graph view**: Visualize connections between pages
- **Backlinks**: See which pages link to current page
- **Plugins**: Dataview, Marp, Canvas, etc.
- **Local files**: Works directly with markdown files
- **Fast**: Instant search and navigation

## Initial Setup

### 1. Create Vault

```bash
# Your wiki project is the vault
# Just open the wiki-project/ folder in Obsidian
```

1. Open Obsidian
2. "Open folder as vault"
3. Select your wiki-project directory

### 2. Configure Settings

**Files & Links**:
- Attachment folder path: `raw/assets`
- Default location for new notes: In the folder that contains the current file
- Use [[Wikilinks]]: ON
- Automatically update internal links: ON

**Editor**:
- Spell check: ON (optional)
- Line numbers: ON (optional)
- Readable line length: ON

### 3. Hotkey Setup

**Essential hotkeys**:
- `Ctrl/Cmd + O`: Quick switcher (find pages)
- `Ctrl/Cmd + P`: Command palette
- `Ctrl/Cmd + G`: Graph view
- `Ctrl/Cmd + Shift + D`: Download attachments (see below)

**Download attachments hotkey**:
1. Settings → Hotkeys
2. Search "Download"
3. Find "Download attachments for current file"
4. Set to `Ctrl/Cmd + Shift + D`

## Essential Plugins

### Core Plugins (Built-in)

Enable these in Settings → Core plugins:

- **Backlinks**: Show pages that link to current page
- **Graph view**: Visualize wiki connections
- **Outgoing links**: Show pages current page links to
- **Quick switcher**: Fast page navigation
- **Search**: Full-text search
- **Templates**: Insert page templates
- **Canvas**: Visual whiteboard

### Community Plugins

Install from Settings → Community plugins:

#### 1. Dataview (Essential)

Query your wiki with SQL-like syntax.

```dataview
TABLE type, created, sources
FROM "wiki/entities"
WHERE contains(tags, "important")
SORT created DESC
```

```dataview
LIST
FROM "wiki/sources"
WHERE publication_date >= date(2026-01-01)
```

**Setup**:
1. Install Dataview plugin
2. Enable in Community plugins
3. Settings → Dataview → Enable JavaScript queries

#### 2. Marp (Optional)

Create presentations from wiki pages.

```markdown
---
marp: true
---

# Presentation Title

## Slide 1
Content...

---

## Slide 2
More content...
```

**Setup**:
1. Install Marp plugin
2. Open markdown file with `marp: true` in frontmatter
3. Click Marp icon to preview slides

#### 3. Canvas (Built-in)

Visual whiteboard for organizing ideas.

**Usage**:
- Drag wiki pages onto canvas
- Create visual maps of concepts
- Link ideas spatially

#### 4. Excalidraw (Optional)

Hand-drawn diagrams and sketches.

**Use for**:
- Concept diagrams
- Flowcharts
- Visual explanations

## Web Clipping

### Obsidian Web Clipper

Browser extension to save web articles as markdown.

**Setup**:
1. Install Obsidian Web Clipper (Chrome/Firefox/Edge)
2. Configure to save to `raw/articles/`
3. Set template for clipped content

**Template example**:
```markdown
---
title: {{title}}
source: {{url}}
date: {{date}}
---

{{content}}
```

### Clipping Workflow

1. Find article in browser
2. Click Web Clipper extension
3. Save to `raw/articles/`
4. In Obsidian, open the saved file
5. Press `Ctrl/Cmd + Shift + D` to download images locally
6. Trigger ingest: "Ingest raw/articles/[filename].md"

## Daily Workflow

### Viewing Changes

After LLM makes edits:

1. **Graph view**: See new connections
2. **Backlinks panel**: See what's linking to current page
3. **Outgoing links**: See what current page links to
4. **Git diff**: Review changes in detail

### Navigation

1. **Quick switcher** (`Ctrl/Cmd + O`): Find any page
2. **Graph view** (`Ctrl/Cmd + G`): Explore connections
3. **Backlinks**: Discover related content
4. **Tags**: Click tag to find all pages with that tag

### Querying with Dataview

Create a "Dashboard" page:

```markdown
# Wiki Dashboard

## Recent Sources
```dataview
TABLE title as "Title", publication_date as "Date"
FROM "wiki/sources"
SORT publication_date DESC
LIMIT 10
```

## Important Entities
```dataview
TABLE type as "Type", updated as "Last Updated"
FROM "wiki/entities"
WHERE contains(tags, "important")
SORT updated DESC
```

## Orphan Pages
```dataview
LIST
FROM "wiki"
WHERE length(file.inlinks) = 0
```
```

## Graph View

### Understanding the Graph

- **Nodes**: Wiki pages
- **Edges**: Links between pages
- **Node size**: Number of connections
- **Colors**: Can be set by tag or folder

### Graph Settings

**Groups** (color by type):
```
entities: #color1
concepts: #color2
sources: #color3
comparisons: #color4
```

### Local Graph

View connections from current page:
1. Open any page
2. Click "Open local graph" (top right)
3. See immediate connections

### Using Graph for Lint

1. Open global graph
2. Look for isolated nodes (orphans)
3. Look for dense clusters (highly connected topics)
4. Identify gaps (areas with few connections)

## Canvas Workflow

Canvas is useful for:

1. **Planning**: Map out what sources to ingest
2. **Synthesis**: Visually organize related concepts
3. **Presentation**: Create visual narratives
4. **Analysis**: See relationships spatially

**Example Canvas**:
- Drag entity pages as cards
- Draw arrows between related entities
- Add notes and annotations
- Export as image or PDF

## Templates Integration

### Setting Up Templates

1. Create `templates/` folder in vault root
2. Settings → Core plugins → Templates
3. Set template folder location

### Using Templates

1. Create template file (e.g., `templates/entity.md`)
2. When creating new page, use "Insert template" command
3. Template content is inserted

**Note**: The LLM Wiki skill has templates in `~/.workbuddy/skills/llm-wiki/templates/`. Copy these to your vault's templates folder.

## Git Integration

### Obsidian Git Plugin

Track changes with git.

**Setup**:
1. Install Obsidian Git plugin
2. Configure auto-commit interval (e.g., every 5 minutes)
3. Set commit message format

**Workflow**:
- Plugin auto-commits changes
- Review git history for wiki evolution
- Revert if needed

### Manual Git

```bash
# After LLM makes changes
git status
git add wiki/
git commit -m "Ingest: [source-name]"
```

## Mobile Sync

### Obsidian Sync (Paid)

Official sync service with end-to-end encryption.

### Git-based (Free)

Use mobile git client to sync:
- iOS: Working Copy
- Android: Termux + git

## Best Practices

### Folder Organization

Let LLM handle folder structure, but understand it:
- `raw/`: Don't edit directly
- `wiki/`: Where knowledge lives
- `templates/`: Page templates

### Naming Conventions

Use consistent naming:
- Entity pages: `entity-slug.md`
- Concept pages: `concept-slug.md`
- Source summaries: `source-slug.md`

### Tagging Strategy

Define consistent tags in WIKI.md:
```yaml
tags:
  priority: [p1-critical, p2-important, p3-normal]
  status: [draft, reviewed, verified]
```

Use tags in frontmatter:
```yaml
---
tags: [p1-critical, reviewed, technology]
---
```

### Regular Maintenance

1. **Weekly**: Run lint check
2. **After ingest**: Check graph view
3. **Monthly**: Review orphan pages
4. **As needed**: Consolidate duplicates

## Troubleshooting

### Links Not Working

- Ensure page names match exactly
- Check for special characters
- Use slug format (lowercase, hyphens)

### Graph View Empty

- Check if pages have `[[links]]`
- Verify link syntax
- Refresh graph

### Dataview Not Working

- Enable JavaScript in Dataview settings
- Check query syntax
- Verify file paths match

### Slow Performance

- Reduce graph view nodes
- Disable unused plugins
- Check vault size (large files?)

## Summary

- Obsidian is the IDE, LLM is the programmer
- Use Dataview for dynamic queries
- Use Graph view to see wiki structure
- Use Web Clipper to add sources
- Let LLM handle wiki maintenance
- You focus on curation and exploration
