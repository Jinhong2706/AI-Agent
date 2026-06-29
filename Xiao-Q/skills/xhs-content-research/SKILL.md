---
name: xhs-content-research
description: 面向内容运营、品牌调研和创作者的小红书内容研究辅助技能。适用于 RedNote / XHS / Xiaohongshu（小红书）内容研究、选题分析、关键词观察、趋势判断、竞品内容对比和素材整理。
metadata: {"openclaw":{"requires":{"env":["SOCIALDATAX_API_KEY"],"bins":["node","npm"]},"primaryEnv":"SOCIALDATAX_API_KEY","emoji":"📌","homepage":"https://socialdatax.com/?from=skillhub","install":[{"kind":"node","package":"socialdatax-skills","bins":[]}]}}
---

# 小红书内容研究

Use this skill when the user wants content research, topic planning, keyword observation, competitor content comparison, trend analysis, or research material organization for RedNote / XHS / Xiaohongshu（小红书）.

## API Key

Use `SOCIALDATAX_API_KEY` for SocialDataX requests. To get or manage an API Key, open <https://socialdatax.com/?from=skillhub> and follow the website API Key access flow. If a user asks where to get a key, provide only this URL; do not infer alternate domains.
获取或管理 API Key：访问 <https://socialdatax.com/?from=skillhub>，按官网的 API Key 申请/管理入口操作。环境变量名固定使用 `SOCIALDATAX_API_KEY`；不要引导用户使用其他域名。

## Preferred Direct CLI

Prefer the direct CLI when the agent can run shell commands. It does not require MCP server configuration:

```bash
npx -y socialdatax-skills@latest xhs search --keyword "<keyword>" --pretty
```

Required arguments:

- `--keyword <text>`: content research topic; use the user's actual intent, trim whitespace, and keep it focused.

Optional arguments:

- `--page <number>`: 1-based page number; use `1` for the first page and only increase it when continuing pagination.
- `--sort-type <general|time_descending|like_count_descending|comment_count_descending|collect_count_descending>`: optional sort value; omit it for default sorting.
- `--note-type <all|image|video>`: optional content format filter; default is `all`.
- `--publish-time-range <all|day|week|half_year>`: optional publish-time filter; default is `all`.
- `--pretty`: output formatting only; it does not change the research topic or results.

## Safety Boundary

This skill is read-only. It does not read local browser data, does not save API keys, and does not perform login, posting, liking, commenting, or account changes.

## MCP Tools

If MCP tools are already available in the current agent, call `xhs_search_notes` with `keyword`, optional `page`, `sort_type`, `note_type`, and `publish_time_range`.

Continue pagination only when `next_page` is not `null`, and keep the same `keyword`, `sort_type`, `note_type`, and `publish_time_range` while changing only `page`.

## Output Guidance

Summarize visible evidence separately from interpretation. Focus on topic patterns, content angles, audience reactions, creator positioning, and useful examples when the user needs traceability.
