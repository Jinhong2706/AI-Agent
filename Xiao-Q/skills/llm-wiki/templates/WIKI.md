---
project: [Project Name]
domain: business | research | personal
created: YYYY-MM-DD
---

# Wiki Configuration

## Project Info

- **Name**: [Project Name]
- **Domain**: business
- **Description**: [What this wiki covers and its purpose]
- **Created**: YYYY-MM-DD
- **Owner**: [Your name or team]

## Entity Types

Define what types of entities this wiki tracks:

```yaml
entities:
  # Standard entity types
  types:
    - person          # People, key individuals
    - organization    # Companies, teams, institutions
    - product         # Products, services, offerings
    - technology      # Technologies, tools, platforms
    - event           # Events, milestones, dates
  
  # Custom entity types (add as needed)
  custom_types:
    # - project
    # - market
    # - competitor
  
  # Required attributes for each type
  required_attributes:
    person: [role, affiliation, expertise]
    organization: [industry, size, location]
    product: [category, company, status]
    technology: [category, maturity, adopters]
    event: [date, type, significance]
```

## Concept Categories

Define concept taxonomy for your domain:

```yaml
concepts:
  # Standard concept categories
  categories:
    - theory          # Theoretical frameworks
    - method          # Methodologies, approaches
    - framework       # Conceptual frameworks
    - metric          # Key performance indicators, measurements
    - principle       # Guiding principles, rules
  
  # Domain-specific concepts (customize for your wiki)
  domain_concepts:
    # - strategy
    # - business-model
    # - competitive-advantage
```

## Workflow Configuration

```yaml
workflow:
  # Default ingest mode
  # interactive: Pause after reading source, discuss with user
  # batch: Process autonomously without user interaction
  default_mode: interactive
  
  # Keywords in source name/description that trigger interactive mode
  interactive_keywords:
    - important
    - key
    - critical
    - flagship
    - strategic
    - confidential
    - board
    - executive
  
  # Number of sources to process at once in batch mode
  batch_threshold: 3
  
  # Auto-save query results to wiki
  auto_save_queries: false
  
  # Ask before saving query results
  ask_before_save: true
  
  # Confirm before creating new entity/concept pages
  confirm_new_pages: true
```

## Lint Rules

```yaml
lint:
  # How often to suggest lint checks
  check_frequency: weekly  # daily, weekly, monthly
  
  # Rules to check (all enabled by default)
  rules:
    - check_contradictions      # Find conflicting claims
    - check_orphans             # Pages with no inbound links
    - check_stale_claims        # Claims superseded by newer sources
    - check_missing_pages       # Referenced pages that don't exist
    - check_incomplete_metadata # Pages missing required frontmatter
    - check_data_gaps           # Areas with insufficient source coverage
  
  # Severity thresholds
  severity:
    contradiction: critical
    stale_claim: critical
    orphan_page: warning
    missing_page: warning
    incomplete_metadata: warning
    data_gap: suggestion
```

## Output Preferences

```yaml
output:
  # Default format for query results
  default_format: markdown  # markdown, table, marp
  
  # Enable Marp slide generation for presentations
  enable_marp: true
  
  # Enable chart generation for data visualization
  enable_charts: true
  
  # Chart library preference
  chart_library: matplotlib  # matplotlib, plotly
  
  # Include citations by default
  include_citations: true
```

## Tag Taxonomy

Define consistent tags for Dataview queries:

```yaml
tags:
  # Priority tags (use these consistently)
  priority:
    - p1-critical    # Must address immediately
    - p2-important   # Important but not urgent
    - p3-normal      # Standard priority
    - p4-low         # Low priority / nice to have
  
  # Status tags
  status:
    - draft          # Work in progress
    - reviewed       # Has been reviewed
    - verified       # Facts have been verified
    - deprecated     # No longer current/relevant
  
  # Domain-specific tags (customize for your wiki)
  domain:
    - strategy
    - operations
    - finance
    - product
    - market
    - competitor
    - customer
    - technology
  
  # Confidence tags (for claims and predictions)
  confidence:
    - high-confidence
    - medium-confidence
    - low-confidence
    - speculative
```

## Integration Settings

```yaml
integrations:
  # qmd search engine (for large wikis)
  qmd:
    enabled: false          # Set to true for wikis > 100 sources
    index_path: .qmd-index
    rerank_by_default: true
  
  # Obsidian settings
  obsidian:
    dataview: true          # Enable Dataview queries
    graph_view: true        # Use graph view for navigation
    canvas: true            # Enable canvas for visual organization
    templates: true         # Use page templates
```

## Naming Conventions

```yaml
naming:
  # File naming patterns
  source_files: "{date}-{slug}.{ext}"
  entity_pages: "{entity_type}/{slug}.md"
  concept_pages: "concepts/{slug}.md"
  source_summaries: "sources/{date}-{slug}.md"
  
  # ID generation for cross-references
  id_format: "{type}-{slug}"
  
  # Slug generation rules
  slug_rules:
    lowercase: true
    replace_spaces: "-"
    remove_special_chars: true
```

## Source Organization

```yaml
sources:
  # Directories in raw/
  directories:
    - articles/      # Web articles, blog posts
    - papers/        # Academic papers, research
    - reports/       # Industry reports, analyses
    - transcripts/   # Meeting transcripts, interviews
    - notes/         # Personal notes, observations
    - data/          # Datasets, spreadsheets
    - assets/        # Images, diagrams
  
  # Default source type for each directory
  default_types:
    articles/: article
    papers/: paper
    reports/: report
    transcripts/: transcript
    notes/: note
```

## Quality Standards

```yaml
quality:
  # Minimum required metadata for each page type
  required_metadata:
    entity: [title, type, entity_type, created, updated]
    concept: [title, type, concept_type, created, updated]
    source: [title, type, source_type, created, raw_path]
    comparison: [title, type, created, compares]
  
  # Source credibility thresholds
  source_credibility:
    minimum_level: medium  # low, medium, high
  
  # Claim verification requirements
  claims:
    require_source: true
    require_confidence_level: true
```

## Custom Instructions

Additional instructions for the LLM when working with this wiki:

```
[Add any specific instructions for your domain or workflow]

Examples:
- Always include quantified metrics and numbers when available
- Prefer primary sources (original documents) over secondary sources
- Flag all speculation or predictions explicitly
- Use consistent date format: YYYY-MM-DD
- When extracting company data, always capture revenue, employees, and funding
- For competitive analysis, focus on market share and differentiation
- Highlight action items and decisions in meeting transcripts
- Cross-reference all mentioned entities and concepts
```

## Example Prompts

Common prompts to use with this wiki:

```yaml
prompts:
  ingest: "Ingest raw/[filename]"
  batch_ingest: "Batch ingest all files in raw/articles/"
  query: "What do we know about [topic]?"
  compare: "Compare [entity A] and [entity B]"
  lint: "Run a health check on the wiki"
  update: "Update [entity] with latest information"
  overview: "Generate an overview of [topic]"
```

## Backup and Version Control

```yaml
version_control:
  # Git settings
  auto_commit: true
  commit_message_format: "{operation}: {summary}"
  
  # Backup settings
  backup_frequency: daily
  backup_location: [backup path]
```

---
*Configuration version: 1.0*
*Last updated: YYYY-MM-DD*
