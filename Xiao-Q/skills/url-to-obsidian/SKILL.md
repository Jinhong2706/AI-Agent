---
name: url-to-obsidian
description: >
  将任意网址的内容通过浏览器抓取、AI 总结后，以 Markdown 笔记存入 Obsidian Vault。
  当用户发送网址（URL）并要求总结、保存、记录时使用此 skill。
  适用于普通网页、视频页面、搜索引擎结果页（如小红书搜索）。
  即使用户只是简单地发了一个链接没有说明，也应该触发此 skill。
  支持批量处理多个网址。
---

# URL to Obsidian

将网址内容总结为结构化 Markdown 笔记，存入 Obsidian Vault。

## 流程概览

```
用户发送网址 → 健康检查 → 浏览器打开 → 获取内容 → AI 总结 → 保存笔记 → 关闭会话
```

## 步骤详解

### 1. 健康检查

每次执行前必须先检查 kimi-webbridge 状态：

```bash
~/.kimi-webbridge/bin/kimi-webbridge status
```

- `running: true` + `extension_connected: true` → 正常，继续
- 其他状态 → 读取 `references/operations.md`（位于 kimi-webbridge skill 目录）排查

### 2. 打开网址

使用 kimi-webbridge 的 `navigate` 工具，首次调用必须用 `newTab:true`：

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"<用户提供的网址>","newTab":true},"session":"url-summarize"}'
```

使用固定 session 名 `url-summarize`，避免与其他任务冲突。

### 3. 获取页面内容

根据页面类型选择不同策略：

#### 普通网页
用 `snapshot` 获取无障碍树，提取页面文字内容：

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"snapshot","args":{},"session":"url-summarize"}'
```

从返回的 tree 中提取所有 `StaticText` 节点的 `name` 字段，拼接为完整文本。

#### 搜索引擎结果页（如小红书搜索）

当 URL 是搜索结果页时，需要额外处理：

1. **提取搜索结果列表**：用 `evaluate` 获取所有帖子链接和标题
2. **按热度排序**：根据点赞数排序，取前 3-5 名
3. **逐个打开详情页**：用 `navigate` 打开每个帖子，用 `snapshot` 获取内容
4. **合并总结**：将所有帖子内容合并后进行综合总结

提取帖子链接的 JS 模板（以小红书为例）：
```javascript
(() => {
  const links = document.querySelectorAll("a");
  const results = [];
  links.forEach(l => {
    const href = l.href || "";
    const text = l.textContent.trim().substring(0, 60);
    if (text.length > 10 && href.includes("xhs"))
      results.push({text, href});
  });
  return JSON.stringify(results.slice(0, 15));
})()
```

注意：小红书的搜索结果链接格式为 `/search_result/xxx`，点击后会跳转到 `/explore/xxx`。

#### 视频页面（B 站等）
获取视频标题、描述、标签等文字信息。**必须尝试提取字幕**，字幕是视频内容总结的核心来源。**同时必须获取视频简介**，简介通常包含相关链接和补充说明。

**B 站视频信息提取流程：**

1. 从页面状态获取视频元数据和简介：
```javascript
(() => {
  const s = window.__INITIAL_STATE__;
  const v = s.videoData || {};
  return JSON.stringify({aid: v.aid, bvid: v.bvid, cid: v.cid, title: v.title, desc: v.desc});
})()
```

`desc` 字段即为 B 站视频简介，包含作者描述、相关链接等信息，需完整保存到笔记的「B 站简介」章节。

2. 通过 B 站 API 获取字幕 URL（需带 cookies）：
```javascript
(() => {
  const url = "https://api.bilibili.com/x/player/wbi/v2?aid=<aid>&cid=<cid>&bvid=<bvid>";
  return fetch(url, {credentials: "include"})
    .then(r => r.json())
    .then(d => JSON.stringify(d.data.subtitle.subtitles.map(s => ({
      lan: s.lan, lan_doc: s.lan_doc, url: s.subtitle_url
    }))));
})()
```

3. 获取完整字幕内容：
```javascript
(() => {
  const url = "<subtitle_url>";
  return fetch(url)
    .then(r => r.json())
    .then(d => d.body.map(b => b.content).join(""));
})()
```

4. 将字幕全文交给 AI 进行结构化总结。

**注意：** B 站 AI 生成字幕的 `subtitle_url` 可能为空，需通过步骤 2 的 API 获取带 `auth_key` 的完整 URL。字幕 URL 的域名通常是 `aisubtitle.hdslb.com`。

**其他视频平台：** 如果无法提取字幕，则基于标题、描述、标签、评论等文字信息进行总结。

### 4. AI 总结

对获取的内容进行结构化总结，包含：
- **标题**：从页面 `<title>` 或内容首行提取
- **总结**：200-500 字的内容摘要
- **关键要点**：3-7 个核心要点，用列表形式

### 5. 生成并保存笔记

笔记保存到 `D:\ObsidianVault\网址总结\`，文件名格式：`YYYY-MM-DD-标题.md`

笔记模板：
```markdown
---
date: YYYY-MM-DD
source: 原始网址
type: url-summary
---

# [页面标题]

## B 站简介
（仅 B 站视频：完整粘贴 desc 字段内容，保留其中的链接和格式）

## 总结
（200-500 字内容摘要）

## 关键要点
- 要点1
- 要点2
- 要点3

## 原文链接
[页面标题](原始网址)
```

说明：「B 站简介」章节仅在来源为 B 站视频时添加，普通网页和其他平台不需要此章节。

文件名中的标题应简洁，去除特殊字符，保留中文和英文。

### 6. 关闭浏览器会话

任务完成后必须关闭会话，释放资源：

```bash
curl -s -X POST http://127.0.0.1:10086/command \
  -H 'Content-Type: application/json' \
  -d '{"action":"close_session","args":{},"session":"url-summarize"}'
```

## 批量处理

当用户提供多个网址时：
1. 为每个网址独立执行步骤 2-3（可复用同一 session）
2. 分别总结每个网址的内容
3. 每个网址生成独立的笔记文件
4. 最后统一关闭会话

## Obsidian Vault 配置

- Vault 路径：`D:\ObsidianVault`
- 笔记存放目录：`D:\ObsidianVault\网址总结\`
- 如果目录不存在，自动创建

## 注意事项

- 截图必须用 `scripts/screenshot.sh`，不要直接调用 screenshot API（会返回大量 base64 数据撑爆上下文）
- `evaluate` 中的 JS 代码不要用模板字符串或特殊引号，避免 JSON 转义问题
- 每次 `evaluate` 调用后如果要再调用，用 IIFE 包裹避免变量重声明报错
- 如果页面内容过长（超过 snapshot 返回限制），优先提取正文区域，忽略导航栏、侧边栏等
