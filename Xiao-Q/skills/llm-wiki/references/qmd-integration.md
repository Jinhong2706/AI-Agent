# qmd Integration Guide

qmd is a local search engine for markdown files with hybrid BM25/vector search and LLM re-ranking. Use it for large wikis where index.md navigation becomes inefficient.

## Installation

```bash
# Using Homebrew (macOS)
brew install qmd

# Using cargo (Rust)
cargo install qmd

# Using npm
npm install -g qmd
```

## Basic Usage

### Index Wiki Pages

```bash
# Index the wiki directory
qmd index wiki/

# Check index status
qmd status
```

### Search

```bash
# Basic search
qmd search "machine learning"

# Search with re-ranking (better results, slower)
qmd search "machine learning" --rerank

# Limit results
qmd search "query" --limit 10

# Search specific directory
qmd search "query" --path wiki/entities/
```

### Advanced Options

```bash
# BM25 only (faster, no vectors)
qmd search "query" --bm25-only

# Vector only (semantic search)
qmd search "query" --vector-only

# Hybrid search (default, combines both)
qmd search "query" --hybrid

# Output as JSON
qmd search "query" --format json

# Include context (surrounding lines)
qmd search "query" --context 3
```

## Integration with LLM Wiki

### When to Use qmd

| Wiki Size | Search Method |
|-----------|---------------|
| < 100 sources | index.md is sufficient |
| 100-500 sources | Use qmd for complex queries |
| 500+ sources | Always use qmd |

### Configuration

Add to WIKI.md:

```yaml
integrations:
  qmd:
    enabled: true
    index_path: .qmd-index
    rerank_by_default: true
    default_limit: 10
```

### LLM Workflow

When qmd is enabled, the query workflow becomes:

```
1. User asks question
2. LLM runs: qmd search "[query]" --rerank --limit 10
3. LLM reads top matching pages
4. LLM synthesizes answer with citations
5. (Optional) Write answer to wiki
```

### Example LLM Commands

The LLM should shell out to qmd:

```bash
# Find pages about a topic
qmd search "revenue growth strategy" --path wiki/ --rerank

# Find entities mentioned with a concept
qmd search "network effects" --path wiki/entities/

# Find recent content
qmd search "2026" --path wiki/sources/
```

## Search Strategies

### 1. Entity Search

Find all mentions of an entity:
```bash
qmd search "[Entity Name]" --path wiki/
```

### 2. Concept Exploration

Deep dive on a concept:
```bash
qmd search "[concept]" --rerank --limit 20
```

### 3. Cross-Reference Discovery

Find connections between concepts:
```bash
qmd search "[concept A] [concept B]" --rerank
```

### 4. Source Finding

Find sources on a topic:
```bash
qmd search "[topic]" --path wiki/sources/
```

### 5. Contradiction Detection

Search for conflicting claims:
```bash
# Search for entity and manually check for conflicts
qmd search "[entity] revenue" --rerank
qmd search "[entity] growth" --rerank
```

## Performance Tips

1. **Re-index after batch ingests**:
   ```bash
   qmd index wiki/ --force
   ```

2. **Use --bm25-only for quick searches**:
   ```bash
   qmd search "term" --bm25-only --limit 5
   ```

3. **Use --rerank for important queries**:
   ```bash
   qmd search "complex query" --rerank
   ```

4. **Limit results to avoid token overflow**:
   ```bash
   qmd search "query" --limit 10
   ```

## MCP Server Mode

qmd also supports MCP (Model Context Protocol) server mode, allowing LLMs to use it as a native tool.

### Start MCP Server

```bash
qmd serve --path wiki/
```

### MCP Configuration

Add to MCP config (for Claude Code, etc.):

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["serve", "--path", "/path/to/wiki"]
    }
  }
}
```

### Benefits

- LLM can search without shelling out
- Better error handling
- Structured responses
- Streaming results

## Troubleshooting

### Index Not Updating

```bash
# Force rebuild index
qmd index wiki/ --force
```

### Slow Searches

```bash
# Use BM25 only for speed
qmd search "query" --bm25-only

# Or reduce limit
qmd search "query" --limit 5
```

### No Results

1. Check if index exists: `qmd status`
2. Check path is correct
3. Re-index: `qmd index wiki/ --force`
4. Try simpler query

## Alternatives

If qmd is not available:

1. **grep/ripgrep**:
   ```bash
   rg "query" wiki/ -l
   ```

2. **Simple search script**:
   ```python
   import os
   import re
   
   def search_wiki(query, path="wiki/"):
       results = []
       for root, dirs, files in os.walk(path):
           for file in files:
               if file.endswith('.md'):
                   filepath = os.path.join(root, file)
                   with open(filepath, 'r') as f:
                       content = f.read()
                       if query.lower() in content.lower():
                           results.append(filepath)
       return results
   ```

3. **Obsidian's built-in search** (when using Obsidian)

## Summary

- Use qmd for wikis > 100 sources
- Configure in WIKI.md
- LLM shells out to qmd search
- Use --rerank for important queries
- Re-index after batch updates
- Consider MCP mode for better integration
