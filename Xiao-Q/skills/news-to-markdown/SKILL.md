---
name: news-to-markdown-skill
description: 输入文章 URL，输出干净的 Markdown 正文。支持17个平台专项优化（头条、微信公众号、知乎、36kr、虎嗅、华尔街见闻、澎湃、InfoQ 等），双引擎提取、图片本地化、三层抓取策略。常与 browser-web-search skill 配合：先用 bws 搜索拿到 url 列表，再逐篇调用本 skill 读取正文。
version: 3.3.1
author: Ping Si <sipingme@gmail.com>
user-invocable: true
requires:
  runtime:
    - name: node
      version: ">=18.0.0"
    - name: npm
      version: ">=8.0.0"
install:
  type: npx
  package: news-to-markdown
  version: "^3.3.1"
  execution: "npx --yes news-to-markdown@^3.3.1"
  riskLevel: moderate
  riskReason: "通过 npx 动态拉取并执行第三方 npm 包，存在供应链风险。使用前请审计源码。"
  source:
    registry: https://registry.npmjs.org
    repository: https://github.com/sipingme/news-to-markdown
    license: MIT
    audit: https://github.com/sipingme/news-to-markdown/blob/main/src/index.ts
tags:
  - news
  - markdown
  - converter
  - extractor
  - web-scraping
  - toutiao
  - wechat
  - 36kr
  - bilibili
  - csdn
repository: https://github.com/sipingme/news-to-markdown-skill
core-library: https://github.com/sipingme/news-to-markdown
---

# news-to-markdown Skill

> 输入文章 URL，输出干净的 Markdown 正文。17 个平台专项优化，为 AI Agent 而生。

## 🎯 核心特点

- 📰 **17 个平台专项适配** — 头条、微信、知乎、36kr、虎嗅、华尔街见闻、澎湃、InfoQ 等
- 🔄 **三层抓取策略** — curl → wget → Playwright 自动回退，静态/动态页面均支持
- 🧠 **双引擎提取** — Mozilla Readability + news-extractor-node 智能取优
- 🖼️ **图片本地化** — 可选将远程图片下载到本地，防止 URL 过期
- 🎨 **无封面自动兜底** — 文章未识别到封面图时，基于标题生成抽象图案占位封面写入 frontmatter `cover:`，避免下游发布链路（如微信公众号）因缺少封面失败
- 📦 **零安装** — 通过 `npx` 按需拉取，无需全局安装

---

## 🚀 快速开始

```bash
# 基本转换，输出到终端
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/123"

# 保存到文件
npx --yes news-to-markdown@^3.3.1 --url "https://mp.weixin.qq.com/s/xxx" --output article.md

# 下载图片到本地（推荐，防止图片 URL 过期）
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/123" \
  --download-images --output-dir ./article

# 只要正文
npx --yes news-to-markdown@^3.3.1 --url "https://www.zhihu.com/p/xxx" --no-metadata
```

---

## 🔗 与 browser-web-search 配合使用

最常见的 AI Agent 编排模式：

```
browser-web-search  →  搜索，产出 URL 列表
news-to-markdown    →  读取正文，产出 Markdown
```

```bash
# Step 1：用 bws 搜索，拿到文章 URL 列表
bws site toutiao/search "ai agent" --count 3

# Step 2：对每个 URL 提取正文
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/111"
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/222"
npx --yes news-to-markdown@^3.3.1 --url "https://www.toutiao.com/article/333"
```

**适用搜索命令**（browser-web-search 0.4.2，30 个平台）：

- 🇨🇳 国内文章类：`toutiao/search`、`weixin/search`、`zhihu/search`、`36kr/search`、`xiaohongshu/search`、`huxiu/search`、`wallstreetcn/search`、`thepaper/search`、`qqnews/search`、`netease/search`、`sina/search`、`juejin/search`、`csdn/search`、`cnblogs/search`、`infoq/search`
- 🌏 国际文章类：`verge/search`、`ars/search`、`engadget/search`、`hn/search`（外链文章）

> **注意**：`github/search`、`reddit/search`、`x/search`、`weibo/search` 等平台的 bws 结果本身是结构化数据，无需再用本工具提取正文。

---

## 📋 支持平台

### 专项优化平台（17 个）

| 平台 | 域名 | 专项说明 |
|-----|------|------|
| **今日头条** | toutiao.com | 标题规范化、`data-src` 图片、列表修复 |
| **微信公众号** | mp.weixin.qq.com | `#js_content` 提取、移动端 UA 回退 |
| **小红书** | xiaohongshu.com | `.note-content` 提取、懒加载图片 |
| **知乎** | zhihu.com | 真实 Chrome 绕过 zse-ck 反爬 |
| **36kr** | 36kr.com | 自动转移动端 URL 绕过反爬 |
| **虎嗅** | huxiu.com | 正文区域提取、懒加载图片修复 |
| **华尔街见闻** | wallstreetcn.com | 财经正文提取、去高亮 `<em>` 标签 |
| **澎湃新闻** | thepaper.cn | `.news_txt` 正文区域提取 |
| **InfoQ** | infoq.cn / infoq.com | 技术文章正文提取 |
| **Bilibili 专栏** | bilibili.com | `/read/` 路径文章提取 |
| **掘金** | juejin.cn | 代码块与正文提取 |
| **CSDN** | csdn.net | 去广告侧边栏、`#content_views` 提取 |
| **博客园** | cnblogs.com | 技术博客正文提取 |
| **简书** | jianshu.com | 文章正文提取 |
| **SegmentFault** | segmentfault.com | 技术问答正文提取 |
| **开源中国** | oschina.net | 资讯正文提取 |
| **人人都是产品经理** | woshipm.com | 产品文章正文提取 |

其余平台（The Verge、Ars Technica、Engadget 等英文站）走通用 Readability 算法。

---

## 🔧 命令参数

```bash
npx --yes news-to-markdown@^3.3.1 --url <URL> [选项]
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--url` | string | 文章 URL（必填） |
| `--output` | string | 输出文件路径（默认输出到终端） |
| `--download-images` | flag | 下载图片到本地（推荐）|
| `--output-dir` | string | 图片输出目录（`--download-images` 时使用） |
| `--no-metadata` | flag | 只要正文，不含标题/作者/时间 |
| `--selector` | string | 自定义内容区域 CSS 选择器 |
| `--noise` | string | 移除元素的选择器，逗号分隔 |
| `--verbose` | flag | 详细日志（调试用） |

---

## 📋 标准操作流程 (SOP)

### 操作 1：基础文章转换

**场景**：用户提供一个文章 URL，要求转换为 Markdown

```bash
npx --yes news-to-markdown@^3.3.1 \
  --url "https://www.toutiao.com/article/123" \
  --output article.md
```

---

### 操作 2：转换并下载图片（推荐）

**场景**：需要保留图片，或后续要发布到微信公众号

```bash
npx --yes news-to-markdown@^3.3.1 \
  --url "https://www.toutiao.com/article/123" \
  --download-images \
  --output-dir ./article
# 输出：./article/article.md + ./article/images/*.jpg
```

> 头条、微信等平台的图片 URL 包含签名，数小时后失效。下载到本地可避免此问题。

---

### 操作 3：只提取正文

**场景**：用户说"只要文章内容，不要标题作者等信息"

```bash
npx --yes news-to-markdown@^3.3.1 \
  --url "https://36kr.com/p/xxx" \
  --no-metadata
```

---

### 操作 4：批量处理多篇文章

**场景**：配合 bws 搜索结果批量提取

```bash
# 先搜索
bws site zhihu/search "大模型" --count 5 --jq '[.items[].url]'

# 再逐篇提取
for url in "${urls[@]}"; do
  npx --yes news-to-markdown@^3.3.1 --url "$url" --output "articles/$(echo $url | md5sum | cut -c1-8).md"
done
```

---

### 操作 5：自定义提取（去噪 / 指定区域）

**场景**：提取结果不准，用户要求去掉广告或指定正文区域

```bash
# 去掉广告和评论
npx --yes news-to-markdown@^3.3.1 \
  --url "https://example.com/article" \
  --noise ".ad,.sidebar,.comments"

# 指定内容区域
npx --yes news-to-markdown@^3.3.1 \
  --url "https://example.com/article" \
  --selector "article.main-content"
```

---

### 操作 6：调试失败页面

**场景**：抓取或提取失败，需要排查

```bash
npx --yes news-to-markdown@^3.3.1 \
  --url "https://example.com/article" \
  --verbose
```

**常见原因与解决方案**：

| 问题 | 原因 | 解决方案 |
|------|------|------|
| 抓取失败 | 需要 JS 渲染 | 自动使用 Playwright（需提前安装） |
| 内容为空 | 选择器不匹配 | 使用 `--selector` 指定内容区域 |
| 图片显示不了 | URL 过期 | 使用 `--download-images` |
| 反爬拦截 | 无头浏览器被检测 | 知乎已内置 Chrome UA，其他平台视情况处理 |

可选安装 Playwright 浏览器（动态页面支持）：

```bash
npx playwright install chromium
```

---

## 🎓 示例对话

**用户**：帮我把这篇虎嗅文章转成 Markdown，图片也要保存

```bash
npx --yes news-to-markdown@^3.3.1 \
  --url "https://www.huxiu.com/article/xxx.html" \
  --download-images \
  --output-dir ./huxiu-article
```

---

**用户**：搜索头条最新 3 篇关于 AI Agent 的文章，并获取每篇正文

```bash
# Step 1: 搜索
bws site toutiao/search "AI Agent" --count 3

# Step 2: 逐篇提取（对每个 url 执行）
npx --yes news-to-markdown@^3.3.1 --url "<url>" --output "<title>.md"
```

---

**用户**：只要这篇知乎文章的正文，不要其他信息

```bash
npx --yes news-to-markdown@^3.3.1 \
  --url "https://www.zhihu.com/p/xxx" \
  --no-metadata
```

---

## ⚠️ 安全与版权

**两条调用路径**：

1. **直接终端调用**（人类 / Agent shell 命令）：保持 `npx --yes news-to-markdown@^3.3.1 …` 习惯用法，无需任何额外安装。
2. **Skill 插件路径**（`scripts/run.js convert …`）：在进程内 `require()` 已固定版本的 npm 包，**不再 fork 子进程、不再调用 `npx`**。该路径需要一次性安装：

   ```bash
   npm install -g news-to-markdown@3.3.1
   ```

   未安装时，启动器会以可操作的 JSON 错误提示退出（不会自动安装、不会回退到子进程）。该选择是为了消除 `^3.3.1` 范围内的运行时版本漂移与 `child_process` 调用面，匹配 `codeguard-0-supply-chain-security` 与 `codeguard-0-input-validation-injection` 的硬化要求。

**供应链风险**：本 Skill 透传到第三方 npm 包，使用前请审计源码：
- 源码：https://github.com/sipingme/news-to-markdown
- 入口：https://github.com/sipingme/news-to-markdown/blob/main/src/index.ts

**入参收紧**：`scripts/run.js` 仅放行 SKILL.md 中文档化的子命令与参数（allow-list），并对每个参数做长度上限与控制字符校验后才注入到 CLI 进程的 `argv`，不会进入 shell。

**版权提示**：本工具默认用于个人学习和内容归档。对外发布时，请保留来源链接和作者信息，并确认来源站点的版权声明与转载政策。

---

## 📝 维护说明

- **版本**: 3.3.1
- **最后更新**: 2026-04-28
- **维护者**: Ping Si <sipingme@gmail.com>
- **许可证**: MIT

---

## 📚 参考资料

- [news-to-markdown GitHub](https://github.com/sipingme/news-to-markdown)
- [npm 包](https://www.npmjs.com/package/news-to-markdown)
- [browser-web-search Skill](https://github.com/sipingme/browser-web-search-skill)
