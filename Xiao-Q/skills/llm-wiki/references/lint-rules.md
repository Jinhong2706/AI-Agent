# Lint Rules

Health check rules for maintaining wiki quality. Run lint checks periodically to catch issues before they compound.

## Overview

Lint checks analyze the wiki for:
- Internal consistency
- Completeness
- Cross-reference health
- Metadata validity
- Content freshness

## Lint Check Categories

### 1. Contradiction Detection

**Rule**: Find claims that contradict across different pages.

**Detection**:
1. Extract claims from each page
2. Compare claims about the same entity/concept
3. Flag when sources disagree

**Example Issues**:
```
⚠️ CONTRADICTION: 
  [[entities/company-a]] says revenue: $100M
  [[sources/report-2025]] says revenue: $85M
  
⚠️ TIMELINE CONFLICT:
  [[entities/product-x]] says launched: 2024-01
  [[sources/announcement]] says launched: 2024-03
```

**Resolution**:
1. Check which source is more recent/authoritative
2. Update entity page with correct value
3. Add note about discrepancy
4. Flag older source as potentially outdated

### 2. Orphan Pages

**Rule**: Find pages with no inbound links.

**Detection**:
1. Scan all `[[wiki-links]]` in wiki
2. Build reverse-link index
3. Find pages with no inbound links

**Example Issues**:
```
⚠️ ORPHAN PAGES:
  - [[concepts/isolated-theory]] - No pages link to this
  - [[entities/obscure-person]] - No inbound links
```

**Resolution**:
1. Check if page is valuable (if not, consider deletion)
2. Find related pages that should link to it
3. Add cross-references from related pages
4. Update index.md if significant

### 3. Missing Pages

**Rule**: Find referenced pages that don't exist.

**Detection**:
1. Extract all `[[wiki-links]]` from pages
2. Check if each referenced page exists
3. List missing pages

**Example Issues**:
```
⚠️ MISSING PAGES:
  - [[entities/referenced-person]] linked from 3 pages but doesn't exist
  - [[concepts/mentioned-idea]] linked from [[sources/article-1]] but no page
```

**Resolution**:
1. Create missing page if entity/concept is important
2. Check for typos in link name
3. Remove link if reference was incorrect

### 4. Stale Claims

**Rule**: Find claims superseded by newer sources.

**Detection**:
1. Identify time-sensitive claims (metrics, status, etc.)
2. Compare with more recent sources
3. Flag outdated information

**Example Issues**:
```
⚠️ STALE CLAIM:
  [[entities/company-a]] says "current CEO: John Smith"
  But [[sources/news-2026-03]] reports CEO changed in March 2026
  
⚠️ OUTDATED METRIC:
  [[overview.md]] says "market size: $10B (2024)"
  More recent data available in [[sources/report-2026]]
```

**Resolution**:
1. Update page with current information
2. Note historical values if relevant
3. Add source citation
4. Update overview if affected

### 5. Incomplete Metadata

**Rule**: Find pages missing required frontmatter fields.

**Detection**:
1. Parse YAML frontmatter from each page
2. Check for required fields based on page type
3. List incomplete pages

**Required Fields by Type**:

| Page Type | Required Fields |
|-----------|-----------------|
| entity | title, type, entity_type, created, updated, sources |
| concept | title, type, concept_type, created, updated, sources |
| source | title, type, source_type, created, raw_path |
| comparison | title, type, created, compares |

**Example Issues**:
```
⚠️ INCOMPLETE METADATA:
  - [[entities/person-x]] missing: entity_type, sources
  - [[concepts/idea-y]] missing: concept_type
```

**Resolution**:
1. Add missing fields
2. Infer values from page content if possible
3. Ask user for missing critical information

### 6. Broken Cross-References

**Rule**: Find cross-references that don't make sense.

**Detection**:
1. Verify link targets exist
2. Check link context is appropriate
3. Detect circular or redundant links

**Example Issues**:
```
⚠️ BROKEN LINKS:
  - [[entities/person-a]] links to [[entities/person-a]] (self-link)
  - [[concepts/x]] links to [[entities/x]] (different type, potential typo)
```

**Resolution**:
1. Remove or fix broken links
2. Clarify confusing references

### 7. Data Gaps

**Rule**: Identify areas with insufficient source coverage.

**Detection**:
1. Analyze source distribution by topic
2. Find entities/concepts with no recent sources
3. Detect important areas with sparse coverage

**Example Issues**:
```
⚠️ DATA GAPS:
  - No sources on [topic] since 2025-06
  - [[entities/key-company]] hasn't been updated in 6 months
  - Category "competitors" has only 2 sources
```

**Resolution**:
1. Note gaps for user awareness
2. Suggest sources to seek
3. Recommend topics to research

### 8. Duplicate Content

**Rule**: Find similar or duplicated information across pages.

**Detection**:
1. Compare page content for similarity
2. Find overlapping entity descriptions
3. Detect redundant concept explanations

**Example Issues**:
```
⚠️ DUPLICATE CONTENT:
  - [[entities/company-a]] and [[sources/article-about-a]] have same description
  - [[concepts/x]] definition repeated in 3 other pages
```

**Resolution**:
1. Consolidate duplicates
2. Keep canonical version in appropriate page type
3. Use links instead of duplication

## Lint Report Format

```markdown
# Wiki Health Report - 2026-04-07

## Summary
- Total pages: 150
- Issues found: 12
- Critical: 2
- Warnings: 7
- Suggestions: 3

## Critical Issues

### Contradictions (1)
- **[[entities/org-x]]** vs **[[sources/report-y]]**
  - Issue: Revenue figures conflict ($100M vs $85M)
  - Action: Verify with most recent source, update org-x

### Stale Claims (1)
- **[[overview.md]]**
  - Issue: Market data from 2024, 2026 data available
  - Action: Update with [[sources/report-2026]]

## Warnings

### Orphan Pages (3)
- [[concepts/isolated-idea]] - Consider adding links from related pages
- [[entities/obscure-person]] - Verify if page is needed
- [[analyses/old-analysis]] - May be outdated

### Missing Pages (2)
- [[entities/referenced-person]] - Create or remove link
- [[concepts/mentioned-framework]] - Create page

### Incomplete Metadata (2)
- [[entities/person-x]] - Add entity_type, sources
- [[concepts/idea-y]] - Add concept_type

## Suggestions

### Data Gaps
- No sources on "emerging markets" since 2025-09
- Recommend searching for recent reports

### Content Opportunities
- [[entities/key-player]] mentioned in 5 sources but has no dedicated page
- Consider creating comparison: [[entities/a]] vs [[entities/b]]

## Recommended Actions

1. **Immediate**: Resolve contradictions in org-x revenue
2. **This week**: Update overview.md with 2026 data
3. **This week**: Add metadata to incomplete pages
4. **Next lint**: Review orphan pages for relevance

## Next Lint Scheduled
2026-04-14 (weekly)
```

## Running Lint Checks

### Manual Trigger

User requests:
```
"Run a lint check on the wiki"
"Check wiki health"
"Find issues in the wiki"
```

### Scheduled Checks

Configure in WIKI.md:
```yaml
lint:
  check_frequency: weekly  # daily, weekly, monthly
  auto_run: true           # LLM should suggest lint periodically
```

LLM should note in log.md when suggesting lint:
```markdown
## [2026-04-07 10:00] system | Lint reminder
- Scheduled weekly lint check due
- User should run: "lint the wiki"
```

## Lint Severity Levels

| Level | Icon | Meaning |
|-------|------|---------|
| Critical | 🚨 | Contradictions, data integrity issues |
| Warning | ⚠️ | Orphans, missing pages, incomplete data |
| Suggestion | 💡 | Optimization opportunities, gaps |

## Best Practices

1. **Run lint weekly** for active wikis
2. **Fix critical issues immediately**
3. **Address warnings within the week**
4. **Review suggestions opportunistically**
5. **Keep lint report** for reference
6. **Git commit after fixes**
7. **Track metrics** (issues over time = wiki health trend)
