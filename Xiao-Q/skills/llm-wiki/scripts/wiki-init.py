#!/usr/bin/env python3
"""
Wiki Project Initializer

Creates a new LLM Wiki project with the standard directory structure
and initial files.

Usage:
    python wiki-init.py /path/to/new/wiki [--name "Project Name"] [--domain business|research|personal]
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def create_wiki_project(base_path: str, name: str, domain: str) -> None:
    """Create a new wiki project with standard structure."""
    
    base = Path(base_path)
    
    # Define directory structure
    directories = [
        "raw/articles",
        "raw/papers", 
        "raw/transcripts",
        "raw/notes",
        "raw/data",
        "raw/assets",
        "wiki/entities/people",
        "wiki/entities/organizations",
        "wiki/entities/products",
        "wiki/entities/places",
        "wiki/entities/technologies",
        "wiki/concepts/theories",
        "wiki/concepts/methods",
        "wiki/concepts/frameworks",
        "wiki/sources/articles",
        "wiki/sources/papers",
        "wiki/sources/transcripts",
        "wiki/comparisons",
        "wiki/analyses",
        "wiki/questions",
    ]
    
    # Create directories
    print(f"Creating wiki project: {name}")
    print(f"Location: {base.absolute()}")
    print()
    
    for dir_path in directories:
        full_path = base / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}/")
    
    # Create initial files
    create_index_md(base, name)
    create_overview_md(base, name)
    create_log_md(base)
    create_wiki_md(base, name, domain)
    create_gitignore(base)
    
    print()
    print("=" * 60)
    print("Wiki project created successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. cd to your project directory")
    print("  2. Open in Obsidian (or your preferred markdown editor)")
    print("  3. Add sources to raw/ directories")
    print("  4. Use the LLM Wiki skill to ingest sources")
    print()
    print("Example ingest command:")
    print('  "Ingest raw/articles/my-first-article.md"')
    print()


def create_index_md(base: Path, name: str) -> None:
    """Create the wiki index file."""
    content = f"""---
title: {name} Wiki Index
created: {datetime.now().strftime('%Y-%m-%d')}
---

# {name} Wiki Index

Welcome to your knowledge base. This index provides a catalog of all wiki content.

## Overview
- [[overview]] - Synthesis of all knowledge in this wiki

## Entities

### People
*No pages yet*

### Organizations
*No pages yet*

### Products
*No pages yet*

### Technologies
*No pages yet*

## Concepts

### Theories
*No pages yet*

### Methods
*No pages yet*

### Frameworks
*No pages yet*

## Sources

### Articles
*No pages yet*

### Papers
*No pages yet*

## Comparisons
*No pages yet*

## Analyses
*No pages yet*

---
*This index is automatically updated when sources are ingested*
"""
    index_path = base / "wiki/index.md"
    index_path.write_text(content, encoding='utf-8')
    print(f"  Created: wiki/index.md")


def create_overview_md(base: Path, name: str) -> None:
    """Create the overview/synthesis file."""
    content = f"""---
title: {name} Overview
type: overview
created: {datetime.now().strftime('%Y-%m-%d')}
updated: {datetime.now().strftime('%Y-%m-%d')}
sources: []
---

# {name} Overview

## Introduction

[This overview will be synthesized from all sources as the wiki grows. The LLM will maintain this page to provide a high-level summary of accumulated knowledge.]

## Key Themes

*Themes and patterns will be identified as sources are ingested.*

## Major Entities

*Key entities will be listed here as they are discovered.*

## Core Concepts

*Main concepts and frameworks will be documented here.*

## Open Questions

*Important unanswered questions will be tracked here.*

## Knowledge Gaps

*Areas requiring more sources will be noted here.*

---
*This overview is maintained by the LLM and updated as new sources are added.*
"""
    overview_path = base / "wiki/overview.md"
    overview_path.write_text(content, encoding='utf-8')
    print(f"  Created: wiki/overview.md")


def create_log_md(base: Path) -> None:
    """Create the activity log file."""
    content = f"""# Wiki Activity Log

This log records all wiki operations (ingests, queries, lint checks).

Format: `## [YYYY-MM-DD HH:MM] operation | Title`

---

## [{datetime.now().strftime('%Y-%m-%d %H:%M')}] init | Wiki Created
- Project initialized with standard structure
- Directories created: raw/, wiki/
- Initial files created: index.md, overview.md, WIKI.md

"""
    log_path = base / "log.md"
    log_path.write_text(content, encoding='utf-8')
    print(f"  Created: log.md")


def create_wiki_md(base: Path, name: str, domain: str) -> None:
    """Create the WIKI.md configuration file."""
    content = f"""---
project: {name}
domain: {domain}
created: {datetime.now().strftime('%Y-%m-%d')}
---

# Wiki Configuration

## Project Info

- **Name**: {name}
- **Domain**: {domain}
- **Description**: [Add description here]
- **Created**: {datetime.now().strftime('%Y-%m-%d')}

## Entity Types

```yaml
entities:
  types:
    - person
    - organization
    - product
    - technology
    - event
  
  required_attributes:
    person: [role, affiliation, expertise]
    organization: [industry, size, location]
    product: [category, company, status]
    technology: [category, maturity, adopters]
    event: [date, type, significance]
```

## Concept Categories

```yaml
concepts:
  categories:
    - theory
    - method
    - framework
    - metric
    - principle
```

## Workflow Configuration

```yaml
workflow:
  default_mode: interactive
  interactive_keywords:
    - important
    - key
    - critical
    - strategic
  batch_threshold: 3
  auto_save_queries: false
  ask_before_save: true
  confirm_new_pages: true
```

## Lint Rules

```yaml
lint:
  check_frequency: weekly
  rules:
    - check_contradictions
    - check_orphans
    - check_stale_claims
    - check_missing_pages
    - check_incomplete_metadata
    - check_data_gaps
```

## Output Preferences

```yaml
output:
  default_format: markdown
  enable_marp: true
  enable_charts: true
  include_citations: true
```

## Tag Taxonomy

```yaml
tags:
  priority:
    - p1-critical
    - p2-important
    - p3-normal
    - p4-low
  
  status:
    - draft
    - reviewed
    - verified
    - deprecated
```

## Integration Settings

```yaml
integrations:
  qmd:
    enabled: false
    index_path: .qmd-index
    rerank_by_default: true
  
  obsidian:
    dataview: true
    graph_view: true
    canvas: true
    templates: true
```

## Custom Instructions

```
[Add domain-specific instructions here]

Examples:
- Always include quantified metrics when available
- Prefer primary sources over secondary
- Flag speculation explicitly
- Use consistent date format: YYYY-MM-DD
```

---
*Configuration version: 1.0*
"""
    wiki_path = base / "WIKI.md"
    wiki_path.write_text(content, encoding='utf-8')
    print(f"  Created: WIKI.md")


def create_gitignore(base: Path) -> None:
    """Create a .gitignore file."""
    content = """# Obsidian
.obsidian/

# qmd index
.qmd-index/

# OS files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.bak
*~

# Python
__pycache__/
*.pyc
.venv/
venv/

# Node
node_modules/
"""
    gitignore_path = base / ".gitignore"
    gitignore_path.write_text(content, encoding='utf-8')
    print(f"  Created: .gitignore")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new LLM Wiki project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wiki-init.py ./my-wiki
  python wiki-init.py ./company-kb --name "Company Knowledge Base" --domain business
  python wiki-init.py ./research-notes --name "Research Notes" --domain research
        """
    )
    
    parser.add_argument(
        "path",
        help="Path where the wiki project will be created"
    )
    
    parser.add_argument(
        "--name",
        default="My Wiki",
        help="Name of the wiki project (default: My Wiki)"
    )
    
    parser.add_argument(
        "--domain",
        choices=["business", "research", "personal"],
        default="business",
        help="Domain type (default: business)"
    )
    
    args = parser.parse_args()
    
    # Check if directory exists
    target_path = Path(args.path)
    if target_path.exists():
        print(f"Error: Directory '{args.path}' already exists")
        print("Please specify a new directory or remove the existing one.")
        sys.exit(1)
    
    # Create the project
    create_wiki_project(args.path, args.name, args.domain)


if __name__ == "__main__":
    main()
