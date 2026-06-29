---
name: news-crawler-engineering
description: Design, implement, review, and harden news/information crawlers as production data pipelines. Use when the user asks to build, analyze, debug, or refactor news website crawlers, market news crawlers, public opinion/news scraping, article list/detail extraction, pagination, incremental backfill, anti-bot analysis, or crawler database schemas.
---

# News Crawler Engineering

Use this skill whenever working on news/information crawlers. Treat each site as one source in a long-running news collection system, not as a one-off page parser.

## Workflow

1. Recon first:
   - Find the real list API, pagination params, column/channel IDs, detail URL rule.
   - Check whether list API returns title, timestamp, real source, images, summary, and full content.
   - Inspect page source and JS for `ajax`, `fetch`, `page`, `pageNum`, `columnId`, `channel`.
   - Use browser Network and `user-js-reverse` MCP when JS/signature/cookie logic is involved.
   - Do not implement before confirming pagination and the real data entry point.

2. Pick collection mode:
   - API includes full content: use API as primary source; fetch detail only to enrich missing fields.
   - API is list-only: use API for list/pagination, detail page for content.
   - Static HTML only: parse paginated HTML + details.
   - Strong CSR/anti-bot: reverse API/signature first, then replay.

3. Design data model before coding:
   - Use `get_market_news_info` as the lightweight main table.
   - Use `get_market_news_content` for `content`, `content_html`, `images`, and `raw_data`.
   - Both tables use the business unique key:
     ```sql
     UNIQUE KEY `uk_source_unique_id` (`source`,`source_unique_id`)
     ```
   - `news_id` is only a relation/index, not the content table unique key.
   - Keep large fields out of the main table.

## Field Rules

- `media_name`: collection site name.
- `original_source`: true source displayed by the article, empty string if unavailable.
- `summary`: article-specific summary only; never store fixed site description, column intro, or template text.
- `author`: do not use `editor` as a fake author.
- `stock_list`: 文章关联的个股代码列表，格式为纯字符串数组 `["AAPL", "INTC"]`。页面或接口有就提取，没有就存空数组 `[]`。不要存对象数组，不要附带URL等额外信息。
- `crawl_error`: short error only; do not store full HTML/response bodies.
- Site-specific lightweight fields go to `extra_data`; large/raw fields go to the content table.
- Content success rule:
  - Text content exists: success.
  - No text but `images` is non-empty: success; keep `content` empty and store `content_html` if available.
  - No text and no images: `crawl_status = 4` / body empty.

## Content Extraction

Prefer structured API data over HTML parsing for content extraction.

**Data source priority:**

1. API blocks/paragraphs/segments (most reliable, exact paragraph boundaries).
2. HTML detail page with known content container selector (fallback).
3. Full-page `get_text()` split by newline (last resort).

**Paragraph rules:**

- Separate paragraphs with `\n\n` (double newline), not single `\n`.
- When using API blocks, each text block = one paragraph; concatenate inline tokens within a block.
- If the API blocks omit the article intro/teaser (common pattern), prepend `description` as the first paragraph.
- When falling back to HTML: prefer `<p>` tags; also consider `<h2>`–`<h4>`, `<blockquote>`, `<li>` as paragraph-level elements. Skip non-content areas (disclaimers, author bios, related articles) by scoping to the correct content container first.
- If no `<p>` tags exist, fall back to splitting `get_text("\n")` and filtering empty lines.

**Image position in content:**

- When the source provides block-structured data with interleaved text and image blocks, insert a placeholder `[图片：caption]` in `content` at the image's position to preserve the spatial relationship between text and images.
- `images` field stores the full URL list (ordered by appearance).
- `content_html` preserves the original HTML structure for re-rendering if needed.

**Why this matters:**

- Modern sites (React/Next.js SSR) often return incomplete HTML (images rendered by JS, content behind hydration). The API is the source of truth.
- HTTP headers cannot contain non-ASCII characters. When the detail page URL or Referer contains Chinese/Unicode, URL-encode it (`urllib.parse.quote`).

## Incremental and Backfill

News crawlers must support first-time backfill, daily incremental collection, failed retry, batched dedupe, and resumability.

Standard strategy:

1. Query `MAX(publish_time)` per `source + column_name`.
2. If no history exists, threshold is `now - backfill_days` (default 90 days).
3. If history exists, threshold is `max_publish_time - overlap_hours` (default 6 hours).
4. Iterate by column and page.
5. For each page, batch-dedupe candidates with `IN (...)`.
6. Fetch/parse details for that page.
7. Immediately upsert that page into DB.
8. Stop paging when the whole page is older than threshold.

Never collect all columns/all historical pages into memory and only insert at the end.

## Storage and Status

- Write main and content tables in the same transaction.
- Use `INSERT ... ON DUPLICATE KEY UPDATE`.
- Failed records should also be stored for retry and diagnosis.

`crawl_status`:

- `1`: success
- `2`: detail request failed
- `3`: page structure abnormal
- `4`: body empty
- `5`: parse exception

## Code Comments

**File header**: every crawler script must include a module docstring with `@Desc` followed by a `来源url：` line pointing to the target page URL. This makes it easy to locate the crawl target when debugging.

```python
"""
@Author: you name
@File  : 香港01财经快讯.py  python3
@Desc  : 香港01（www.hk01.com 繁体站）財經快訊抓取
来源url：https://www.hk01.com/channel/396/%E8%B2%A1%E7%B6%93%E5%BF%AB%E8%A8%8A
"""
```

Add concise comments to non-obvious logic. Do not narrate what code does line-by-line. Focus on:

- **Method docstrings**: one-line summary of purpose and return value. Example: `"""获取增量抓取的时间阈值：表里有数据则取最新时间-overlap_hours，无数据则回溯backfill_days天"""`
- **Branch intent**: explain *why* a branch exists when the condition alone isn't self-explanatory. Example: `if not self.db_pool:  # 本地调试无DB时直接走全量回溯`
- **Business logic**: threshold calculation, stop conditions, dedup strategy. Example: `should_stop = (not page_has_newer)  # 本页全部早于阈值则停止翻页`
- **Non-obvious fallbacks**: when code has multiple data source priorities or fallback paths, annotate the intent. Example: `if not content_text:  # blocks为空时兜底用HTML提取`

Do NOT comment:
- Imports, variable assignments, obvious operations.
- What a function call does (the function name should be self-documenting).

## Monitoring & Alerting

每个爬虫必须内置监控报警，不能依赖外部监控平台单独配置。

**三层报警（必须全部实现）：**

1. **程序崩溃**：未捕获异常 → 飞书/通知 "程序报错"。
2. **零数据入库**：`total_success == 0` → 飞书/通知 "0条数据入库，请检查网站或API是否异常"。
3. **详情失败率过高**：`total_fail / (total_success + total_fail) > 0.5` → 飞书/通知 "失败率过高，可能触发反爬"。

```python
# main() 示例结构
def main():
    crawler = XxxCrawler(max_workers=3)
    total_success, total_fail = crawler.run()

    if total_success == 0:
        notify("本次执行0条数据入库，请检查网站或API是否异常")
    elif total_fail > 0 and total_fail / (total_success + total_fail) > 0.5:
        notify("详情抓取失败率过高，可能触发反爬")

if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        notify(f"程序报错: {err}")
        raise
```

**连续空页中断：**

- 列表API连续 N 页（建议3页）返回空结果时，主动中断并打印警告。
- 防止API挂了但程序还在傻翻页浪费时间。

## Pagination Stop Logic

翻页停止条件需要区分两种情况，不能混为一谈：

| 情况 | `should_stop` | `consecutive_empty` | 动作 |
|------|:---:|:---:|------|
| 本页所有文章早于阈值 | `True` | 不累加 | 正常结束（翻到底了） |
| API请求失败/返回空 | `False` | +1 | 交给连续空页计数处理 |

**关键原则：**

- API 失败时返回 `([], False)` 而非 `([], True)`。
- `should_stop=True` 仅当确认页面有数据但全部早于阈值时才设置。
- `consecutive_empty` 的判断必须在 `seen` 去重之前，用 `raw_tasks`（原始列表结果）判断，而非去重后的 tasks。

```python
for page in range(max_pages):
    raw_tasks, should_stop = self.parse_list_page(end_index, threshold)

    if not raw_tasks:
        consecutive_empty += 1
        if consecutive_empty >= 3:
            print(f"警告：连续{consecutive_empty}页为空，可能API异常")
            break
    else:
        consecutive_empty = 0

    tasks = [t for t in raw_tasks if t["id"] not in seen]
    seen.update(t["id"] for t in tasks)
    tasks = self.filter_not_exists(tasks)
    # ... process tasks ...

    if should_stop:
        break
```

## Proxy & Network

- 不是所有网站都需要代理。海外网站（如 CNBC、Reuters）从香港/海外服务器直连即可，国内代理反而会被拦截（如 `449 Foreign Host Forbidden`）。
- 当环境变量配置了默认代理时，对不需要代理的站点必须显式传 `proxies={}` 绕过。
- 在实现前先测试目标站点是否需要代理、是否有 TLS 指纹检测，不要假设。

```python
# 需要绕过默认代理的请求
new_request("GET", url, "json", proxies={}, headers=headers)
```

## Memory Management

- task 列表中只存入库和详情解析所需的字段，不要把 API 原始完整 JSON 塞进 task dict。
- `raw_data` 字段入库时从 `item` 构建即可，不需要提前存储完整 API 响应。
- 大批量场景下（单次数百条 task），避免在内存中积累所有页的 tasks 后才开始处理，应逐页处理+入库。

## Verification Checklist

Do not stop at syntax/lint checks. Verify:

- Table structures and unique keys match the model.
- One sample writes to both main and content tables.
- JSON fields are valid.
- Chinese/Unicode encoding is correct.
- `summary` is a real article summary.
- `original_source` is the true article source.
- Re-running skips successful rows.
- Failed rows can be retried.
- **Run the script** end-to-end (list → detail → parse) before delivering. Syntax checks alone are insufficient.
- **Alerting works**: 确认零数据/高失败率/崩溃三种场景都能触发通知。
- **Proxy correctness**: 确认目标站点请求不被代理拦截（海外站传 `proxies={}`）。

## Recommended Class Responsibilities

Prefer a class-based crawler with these responsibilities:

- column configuration
- list/API request
- list field mapping
- per-column threshold calculation
- batched dedupe
- detail parsing
- failed item construction
- transactional main/content upsert
- page-by-page column runner
