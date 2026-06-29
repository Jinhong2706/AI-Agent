# Page Templates

Standard templates for different wiki page types. Use these as starting points when creating new pages.

## Entity Page Template

**Purpose**: Document a real-world entity (person, organization, product, place).

**Template**: `templates/entity-page.md`

```markdown
---
title: [Entity Name]
type: entity
entity_type: person|organization|product|place
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-id-1, source-id-2]
tags: [tag1, tag2]
related: [[related-page-1]], [[related-page-2]]
---

# [Entity Name]

## Overview
[1-2 sentence description of what this entity is]

## Key Facts
- **Founded/Created**: [Date]
- **Location**: [Place]
- **Industry/Sector**: [Industry]
- **Key People**: [[entities/person-1]], [[entities/person-2]]

## Description
[Detailed description, 2-4 paragraphs]

## History
[Chronological account of important events]

- **[Date]**: [Event]
- **[Date]**: [Event]

## Key Attributes

| Attribute | Value | Source |
|-----------|-------|--------|
| [Metric 1] | [Value] | [[sources/source-1]] |
| [Metric 2] | [Value] | [[sources/source-2]] |

## Relationships

### Related Entities
- [[entities/entity-1]] - [Relationship description]
- [[entities/entity-2]] - [Relationship description]

### Key Concepts
- [[concepts/concept-1]] - [Connection description]
- [[concepts/concept-2]] - [Connection description]

## Sources
- [[sources/source-1]]
- [[sources/source-2]]

## Open Questions
- [ ] [Question about this entity not yet answered]
- [ ] [Another question]

---
*Last updated: [DATE] based on [sources]*
```

## Concept Page Template

**Purpose**: Document an abstract idea, theory, method, or framework.

**Template**: `templates/concept-page.md`

```markdown
---
title: [Concept Name]
type: concept
concept_type: theory|method|framework|metric
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-id-1, source-id-2]
tags: [tag1, tag2]
related: [[related-page-1]], [[related-page-2]]
---

# [Concept Name]

## Definition
[Clear, concise definition in 1-2 sentences]

## Explanation
[Detailed explanation, 2-4 paragraphs]

- What problem does it solve?
- How does it work?
- When is it applicable?

## Key Principles

1. **[Principle 1]**: [Explanation]
2. **[Principle 2]**: [Explanation]
3. **[Principle 3]**: [Explanation]

## Components / Steps

| Component | Description | Example |
|-----------|-------------|---------|
| [Component 1] | [Description] | [Example] |
| [Component 2] | [Description] | [Example] |

## Applications

### Where it applies
- [Use case 1]
- [Use case 2]

### Where it doesn't apply
- [Limitation 1]
- [Limitation 2]

## Related Concepts

### Precursors
- [[concepts/prerequisite-concept]] - [Connection]

### Related
- [[concepts/related-concept-1]] - [How it relates]
- [[concepts/related-concept-2]] - [How it differs]

### Alternatives
- [[concepts/alternative-approach]] - [Trade-offs]

## Real-World Examples

### Example 1: [Name]
[Description of how this concept is applied]
Source: [[sources/example-source]]

### Example 2: [Name]
[Description]
Source: [[sources/example-source-2]]

## Criticism & Limitations
[Known weaknesses, criticisms, or limitations]

## Evolution
[How this concept has evolved over time, if applicable]

- **[Date/Period]**: [Evolution event]

## Sources
- [[sources/source-1]]
- [[sources/source-2]]

---
*Last updated: [DATE] based on [sources]*
```

## Source Summary Template

**Purpose**: Summarize a raw source document for the wiki.

**Template**: `templates/source-summary.md`

```markdown
---
title: [Source Title]
type: source
source_type: article|paper|transcript|note
created: YYYY-MM-DD
updated: YYYY-MM-DD
raw_path: raw/[path/to/source]
publication_date: YYYY-MM-DD
authors: [Author 1, Author 2]
tags: [tag1, tag2]
---

# [Source Title]

## Metadata
- **Type**: [Article/Paper/Transcript]
- **Author(s)**: [Author names]
- **Published**: [Date]
- **Source**: [URL or publication]
- **Raw File**: [Link to raw/ file]

## Summary
[2-3 paragraph summary of the main content]

## Key Points

1. **[Point 1]**: [Explanation]
2. **[Point 2]**: [Explanation]
3. **[Point 3]**: [Explanation]

## Key Claims

| Claim | Evidence | Confidence |
|-------|----------|------------|
| [Claim 1] | [Evidence] | [High/Medium/Low] |
| [Claim 2] | [Evidence] | [High/Medium/Low] |

## Entities Mentioned

| Entity | Type | Context |
|--------|------|---------|
| [[entities/entity-1]] | person | [How mentioned] |
| [[entities/entity-2]] | organization | [How mentioned] |

## Concepts Discussed

| Concept | Context |
|---------|---------|
| [[concepts/concept-1]] | [How discussed] |
| [[concepts/concept-2]] | [How discussed] |

## Data Points

| Metric | Value | Context |
|--------|-------|---------|
| [Metric 1] | [Value] | [Context] |
| [Metric 2] | [Value] | [Context] |

## Notable Quotes
> "[Quote 1]"
> — [Speaker/Author], context

> "[Quote 2]"
> — [Speaker/Author], context

## Relation to Other Sources

### Agrees With
- [[sources/source-1]] - [What they agree on]

### Contradicts
- [[sources/source-2]] - [What they disagree on]

### Extends
- [[sources/source-3]] - [How this extends previous work]

## Open Questions Raised
- [ ] [Question 1]
- [ ] [Question 2]

## Personal Notes
[Optional: Your thoughts, reactions, questions]

---
*Ingested: [DATE]*
```

## Comparison Template

**Purpose**: Compare two or more entities, concepts, or approaches.

**Template**: `templates/comparison-table.md`

```markdown
---
title: [A vs B vs C]
type: comparison
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: [source-id-1, source-id-2]
compares: [[entities/a]], [[entities/b]]
tags: [comparison, tag1]
---

# [A] vs [B] Comparison

## Overview
[Brief intro to what's being compared and why]

## At a Glance

| Aspect | [[entities/a]] | [[entities/b]] |
|--------|----------------|----------------|
| [Aspect 1] | [Value] | [Value] |
| [Aspect 2] | [Value] | [Value] |
| [Aspect 3] | [Value] | [Value] |

## Detailed Comparison

### [Category 1]

| Criterion | [[entities/a]] | [[entities/b]] | Winner |
|-----------|----------------|----------------|--------|
| [Criterion 1] | [Details] | [Details] | [A/B/Tie] |
| [Criterion 2] | [Details] | [Details] | [A/B/Tie] |

**Analysis**: [Text analysis of this category]

### [Category 2]

| Criterion | [[entities/a]] | [[entities/b]] | Winner |
|-----------|----------------|----------------|--------|
| [Criterion 1] | [Details] | [Details] | [A/B/Tie] |
| [Criterion 2] | [Details] | [Details] | [A/B/Tie] |

**Analysis**: [Text analysis of this category]

## Strengths & Weaknesses

### [[entities/a]]

**Strengths**:
- [Strength 1]
- [Strength 2]

**Weaknesses**:
- [Weakness 1]
- [Weakness 2]

### [[entities/b]]

**Strengths**:
- [Strength 1]
- [Strength 2]

**Weaknesses**:
- [Weakness 1]
- [Weakness 2]

## Use Cases

### When to choose [[entities/a]]
- [Use case 1]
- [Use case 2]

### When to choose [[entities/b]]
- [Use case 1]
- [Use case 2]

## Key Differences

1. **[Difference 1]**: [Explanation]
2. **[Difference 2]**: [Explanation]

## Common Ground
[What they share or agree on]

## Conclusion
[Summary recommendation or synthesis]

## Sources
- [[sources/source-1]]
- [[sources/source-2]]

---
*Created: [DATE]*
```

## WIKI.md Schema Template

**Purpose**: Configure a new wiki project.

**Template**: `templates/WIKI.md`

```markdown
---
project: [Project Name]
---

# Wiki Configuration

## Project Info

- **Name**: [Project Name]
- **Domain**: business | research | personal
- **Description**: [What this wiki covers]
- **Created**: YYYY-MM-DD

## Entity Types

Define what types of entities this wiki tracks:

```yaml
entities:
  types:
    - person
    - organization
    - product
    - technology
    - event
  
  # Custom entity types (optional)
  custom_types:
    - [custom_type_1]
    - [custom_type_2]
  
  # Required attributes for each type
  required_attributes:
    person: [role, affiliation]
    organization: [industry, location]
```

## Concept Categories

Define concept taxonomy:

```yaml
concepts:
  categories:
    - theory
    - method
    - framework
    - metric
    - principle
  
  # Domain-specific concepts
  domain_concepts:
    - [concept_1]
    - [concept_2]
```

## Workflow Configuration

```yaml
workflow:
  # Default ingest mode
  default_mode: interactive  # or batch
  
  # Keywords that trigger interactive mode
  interactive_keywords:
    - important
    - key
    - critical
    - flagship
    - strategic
  
  # Number of sources to process at once in batch mode
  batch_threshold: 3
  
  # Auto-save query results to wiki
  auto_save_queries: false
  
  # Ask before saving query results
  ask_before_save: true
```

## Lint Rules

```yaml
lint:
  # How often to suggest lint checks
  check_frequency: weekly
  
  # Rules to check
  rules:
    - check_contradictions      # Find conflicting claims
    - check_orphans             # Pages with no inbound links
    - check_stale_claims        # Claims superseded by newer sources
    - check_missing_pages       # Referenced pages that don't exist
    - check_incomplete_metadata # Pages missing required frontmatter
  
  # Custom rules (optional)
  custom_rules:
    - [custom_rule_1]
```

## Output Preferences

```yaml
output:
  # Default format for query results
  default_format: markdown  # markdown, table, marp
  
  # Enable Marp slide generation
  enable_marp: true
  
  # Enable chart generation
  enable_charts: true
  
  # Chart library preference
  chart_library: matplotlib  # matplotlib, plotly
```

## Tag Taxonomy

Define consistent tags for Dataview queries:

```yaml
tags:
  # Priority tags
  priority:
    - p1-critical
    - p2-important
    - p3-normal
  
  # Status tags
  status:
    - draft
    - reviewed
    - verified
    - deprecated
  
  # Domain tags (customize for your wiki)
  domain:
    - [tag1]
    - [tag2]
```

## Integration Settings

```yaml
integrations:
  # qmd search (for large wikis)
  qmd:
    enabled: false
    index_path: .qmd-index
  
  # Obsidian settings
  obsidian:
    dataview: true
    graph_view: true
    canvas: true
```

## Naming Conventions

```yaml
naming:
  # File naming pattern
  source_files: "{date}-{slug}.{ext}"
  entity_pages: "{type}/{slug}.md"
  concept_pages: "concepts/{slug}.md"
  
  # ID generation
  id_format: "{type}-{slug}"
```

## Custom Instructions

Any additional instructions for the LLM when working with this wiki:

```
[Your custom instructions here]

Example:
- Always include quantified metrics when available
- Prefer primary sources over secondary
- Flag speculation explicitly
- Use consistent date format: YYYY-MM-DD
```

---
*Configuration version: 1.0*
```

## Usage Tips

1. **Copy templates** to create new pages, don't start from scratch
2. **Customize for domain** — add/remove sections as needed
3. **Stay consistent** — use the same structure across similar pages
4. **Metadata matters** — fill out all frontmatter fields for Dataview
5. **Cross-reference heavily** — link to related entities and concepts
6. **Update timestamps** — always update the `updated` field
7. **Cite sources** — every claim should trace to a source
