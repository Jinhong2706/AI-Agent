---
name: mcp
description: You have access to connected apps despite the internet setting. Use the grok-mcp CLI to discover and send requests to connected apps (Linear, Slack, GitHub, Google Drive, Sharepoint, etc.). Trigger when the user mentions a connected app or keywords like email, calendar, drive, or uploading files.
---

# MCP — Grok MCP CLI
Use the `grok-mcp` CLI to discover and invoke all of MCP tools from connected apps.


**CRITICAL RULE: Always try `ls` first.** You do NOT know what tools
are available until you search. Never assume a tool doesn't exist — search first.


## Sending File Data

**CRITICAL: Never read base64 content into the conversation.** When a tool needs file contents (e.g. uploading to google drive, sharepoint or editing a file in one of these systems), base64-encode the file and pipe it directly into `grok-mcp call` using shell variable expansion.

Example: base64-encode the file and expand it inline (the payload fields depend on the tool schema from `grok-mcp ls`):

```bash
# Encode file and call tool in one shot — never cat/echo the base64
b64=$(base64 -w0 yourfile.pptx) && grok-mcp call <tool_name> "{\"file_id\":1234,\"contents\":\"$b64\"}"
```


## Quick Start

```bash
grok-mcp check
grok-mcp ls
grok-mcp ls --query "email"
grok-mcp call <tool_name> '{"arg": "value"}'
```

## Discovery (Search First!)

**Always run `grok-mcp ls` before calling any tool.** You don't know what tools are available until you search.

```bash
# List all available tools
grok-mcp ls

# Search by query
grok-mcp ls --query "email"
grok-mcp ls --query "slack" --limit 10
```

## Output Format

- `ls` → **JSONL**: one `{"name","title","description","input_schema"}` per line
- `call` → pretty-printed JSON result on stdout
- Errors → stderr

## Common Tools (Examples Only)

Always `ls` first to discover what tools exist. Then call based on what you found.

```bash
# Step 1: Discover available tools
grok-mcp ls --query "linear"

# Output (JSONL):
# {"name":"linear___list_issues","title":"List Issues","description":"...","input_schema":{...}}
# {"name":"linear___get_issue","title":"Get Issue","description":"...","input_schema":{...}}

# Step 2: Call using the exact tool name from ls
grok-mcp call linear___list_issues '{"assignee": "me"}'
```

## Error Handling

```bash
# Run check first if something seems wrong
grok-mcp check

# If "auth" or "endpoint" error: config issue, not transient
# If "connection refused": transient, retry later
```

This avoids the model context window being filled with binary data.

## Multi-Step Workflows

For complex tasks, chain calls in a script:

```bash
#!/bin/bash
# Step 1: Get my open issues
issues=$(grok-mcp call linear___list_issues '{"assignee": "me", "state": "started"}')

# Step 2: Parse and process (use jq if available)
echo "$issues" | jq -r '.issues[]? | "\(.id): \(.title) (\(.state.name))"'
```
