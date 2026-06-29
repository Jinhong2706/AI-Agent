---
name: bilibili-channel-analyst
description: Extract and analyze Bilibili channel video data to provide deep insights, traffic funnel analysis, and actionable optimization suggestions. Use this skill when the user provides a Bilibili space URL (e.g., https://space.bilibili.com/18052876) and asks for channel data analysis, performance review, or video optimization advice. It automates multi-page data extraction, funnel modeling, and strategic reporting.
---

# Bilibili Channel Analyst

This skill enables Claude to perform deep, data-driven analysis of Bilibili channels. It moves beyond simple observation to structured traffic funnel modeling and operational reviews.

## Workflow

### 1. Data Extraction (The Foundation)
When a Bilibili space URL is provided:
- Spawn a **browser agent** to extract ALL video data.
- **Task Prompt**: "Go to [URL]/video. Extract all videos across all pages. For each video, get: Title, Views (播放), Comments (评论), Date, and Duration. Save as a JSON array of objects: `[{"title": "...", "views": "...", "comments": "...", "date": "...", "duration": "..."}]` in `channel_data.json`."
- *Note*: If the channel has many pages (>10), suggest using the Bilibili API `https://api.bilibili.com/x/space/arc/search?mid={mid}&ps=50&pn={pn}` for faster extraction.

### 2. Advanced Multi-dimensional Analysis
Run the bundled script `scripts/analyze_bilibili.py` on the extracted JSON data to generate:
- **Topic Clustering**: Categorize videos based on keywords in titles.
- **Performance Correlation**: Average views/comments per category, and correlation between video length and performance.
- **Traffic Funnel Metrics**: Visibility (Exposure proxies) -> Click (Views) -> Interaction (Comments).
- **Keyword Weight Analysis**: Identify which words in titles drive the most views.

### 3. Reporting Structure
Produce a comprehensive report using the following three sections:

#### A. Traffic Funnel Analysis (流量漏斗分析)
- **Exposure**: Analyze reach and visibility.
- **Conversion**: Click-through rate (CTR) proxies.
- **Engagement**: Interaction rate (Comments/Views). Identify bottlenecks (e.g., "High views but low interaction").

#### B. Operational Review (运营复盘)
- **Wins**: Identify top-performing categories and "hot-topic hijacking" successes.
- **Losses**: Identify underperforming content (e.g., conceptual vs. practical content) and traffic cannibalization issues (e.g., high-frequency posting).
- **Diagnostics**: Why certain videos failed (e.g., "Anxious Developer" persona mismatch).

#### C. Actionable Optimization Plan (整改建议)
- **Title Templates**: Provide specific, data-verified formulas (e.g., `[Model] + [Hardware] + Data实测 + Result`).
- **Thumbnail Strategy**: Visualization of performance metrics (Tokens/s, GPU usage).
- **Content Roadmap**: Shift from "Broad News" to "Deep Tutorials" or "Practical Case Studies."
- **Engagement Hacks**: CTA (Call to Action) strategies for the first 60 seconds of video.

## Output Format
Always provide a concise summary in chat, followed by the full Markdown report as a file.

---
*Created by Ecommerce Mind (TL) for Bilibili Content Strategy.*
