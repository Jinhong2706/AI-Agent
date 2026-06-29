# Wiki Architecture

## Three Layers

The LLM Wiki architecture consists of three distinct layers, each with specific responsibilities and constraints.

### Layer 1: Raw Sources

**Purpose**: Immutable source of truth for all knowledge in the wiki.

**Characteristics**:
- **Immutable**: LLM reads from here but NEVER modifies
- **Curated**: You control what enters this collection
- **Organized**: Structured by type (articles/, papers/, assets/)
- **Versioned**: Part of git repository

**Directory Structure**:
```
raw/
├── articles/          # Web articles, blog posts
├── papers/            # Academic papers, reports
├── transcripts/       # Meeting transcripts, interviews
├── notes/             # Personal notes, journal entries
├── data/              # Datasets, spreadsheets
└── assets/            # Images, diagrams, videos
```

**Naming Convention**:
```
raw/articles/2026-04-01-article-slug.md
raw/papers/2025-12-author-title.pdf
raw/transcripts/2026-04-07-meeting-name.md
```

**Processing Rules**:
1. Never modify files in raw/
2. Always preserve original format when possible
3. Convert to markdown for LLM processing if needed (keep original)
4. Use Obsidian Web Clipper for web articles
5. Download images locally to raw/assets/

### Layer 2: Wiki

**Purpose**: LLM-maintained knowledge base with structured, interlinked pages.

**Characteristics**:
- **Mutable**: LLM creates, updates, and maintains these pages
- **Structured**: Organized by page type
- **Interlinked**: Heavy use of `[[wiki-links]]`
- **Synthesized**: Represents cumulative knowledge, not just copies

**Directory Structure**:
```
wiki/
├── index.md           # Content catalog
├── overview.md        # Synthesis of entire wiki
├── entities/          # People, organizations, products, places
│   ├── people/
│   ├── organizations/
│   ├── products/
│   └── places/
├── concepts/          # Ideas, theories, methods, frameworks
│   ├── theories/
│   ├── methods/
│   └── frameworks/
├── sources/           # Summaries of raw sources
│   ├── articles/
│   ├── papers/
│   └── transcripts/
├── comparisons/       # Comparative analyses
├── analyses/          # Deep-dive analyses
└── questions/         # Questions explored (from query results)
```

**Page Types**:

| Type | Purpose | Example |
|------|---------|---------|
| Entity | Real-world things with identity | Person, company, product |
| Concept | Abstract ideas, theories | "Network effects", "First principles" |
| Source | Summary of a raw document | Article summary with key points |
| Comparison | Side-by-side analysis | "iOS vs Android" |
| Analysis | Deep dive on a topic | "Market analysis Q1 2026" |
| Question | Answer to a user query | "What is X?" |

**Evolution**:
- Pages start small and grow as new sources mention them
- Cross-references are added incrementally
- Contradictions are flagged and tracked
- Overview.md is the highest-level synthesis

### Layer 3: Schema

**Purpose**: Configuration file that defines domain-specific conventions and workflows.

**File**: `WIKI.md` at project root

**Characteristics**:
- **Configuration**: Tells LLM how to handle this wiki
- **Domain-specific**: Different for research vs business vs personal
- **Evolving**: You and LLM co-evolve this over time

**Schema Contents**:
```yaml
# Project metadata
project:
  name: "My Knowledge Base"
  domain: "business"  # research, personal, business
  description: "Internal knowledge base for [purpose]"

# Entity types to track
entities:
  types: [person, organization, product, technology, event]
  important_attributes:
    person: [role, affiliation, expertise]
    organization: [industry, size, products]

# Concept categories
concepts:
  categories: [theory, method, framework, metric]
  
# Workflow preferences
workflow:
  default_mode: interactive  # or batch
  interactive_keywords: [important, key, critical]
  batch_threshold: 3
  
# Lint rules
lint:
  check_frequency: weekly
  rules:
    - check_contradictions
    - check_orphans
    - check_stale_claims
    - check_missing_pages

# Output preferences
output:
  default_format: markdown
  enable_marp: true
  enable_charts: true
```

## Data Flow

```
Raw Source → Ingest → Wiki Pages → Query → Answer
                ↓                      ↓
            log.md ←─────────────────┘
                            ↓
                    (Optional) New Wiki Page
```

**Ingest Flow**:
```
1. User adds source to raw/
2. User triggers ingest: "Ingest raw/articles/new-article.md"
3. LLM reads source
4. LLM extracts:
   - Entities (mentioned people, orgs, products)
   - Concepts (key ideas, theories, methods)
   - Key claims and data points
5. LLM creates/updates:
   - Source summary (wiki/sources/)
   - Entity pages (wiki/entities/)
   - Concept pages (wiki/concepts/)
   - Cross-references between pages
6. LLM updates index.md
7. LLM appends to log.md
```

**Query Flow**:
```
1. User asks question
2. LLM reads index.md to find relevant pages
3. LLM reads relevant wiki pages
4. LLM synthesizes answer with citations
5. (Optional) LLM writes answer to wiki/questions/
6. LLM appends to log.md
```

## Consistency Rules

1. **Single Source of Truth**: Raw sources are never modified
2. **Wiki Links**: All internal references use `[[page-name]]` syntax
3. **Metadata Required**: Every wiki page has YAML frontmatter
4. **Citation Trail**: Every claim traces back to sources
5. **Conflict Tracking**: Contradictions are explicitly noted, not hidden

## Version Control

The entire wiki is a git repository:

```bash
# After each ingest
git add raw/ wiki/ log.md
git commit -m "Ingest: [source-name]"

# After queries that create pages
git add wiki/
git commit -m "Query: [question-summary]"

# After lint fixes
git add wiki/
git commit -m "Lint: fix [issues]"
```

Benefits:
- Full history of knowledge evolution
- Easy to revert bad ingests
- Branch for experimental analyses
- Collaborate with team members

## Scale Considerations

### Small Wiki (< 100 sources)
- index.md is sufficient for navigation
- No search infrastructure needed
- All pages in single directories

### Medium Wiki (100-500 sources)
- Consider qmd search engine
- Organize entities/concepts into subdirectories
- Regular lint checks important

### Large Wiki (500+ sources)
- qmd search essential
- May need automated lint scheduling
- Consider splitting into multiple wikis by domain
- Heavy use of tags and Dataview queries

## Comparison to RAG

| Aspect | RAG | LLM Wiki |
|--------|-----|----------|
| Knowledge retrieval | Re-derive every query | Pre-compiled in wiki |
| Cross-references | None | Explicit `[[links]]` |
| Contradictions | Hidden | Flagged and tracked |
| Query cost | High (search every time) | Low (read wiki pages) |
| Accumulation | None | Every source adds value |
| Maintenance | None needed | LLM handles automatically |

The key insight: **RAG retrieves, LLM Wiki compiles.**
