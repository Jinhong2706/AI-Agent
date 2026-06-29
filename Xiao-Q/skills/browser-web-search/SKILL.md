---
name: browser-web-search
description: 一行命令搜遍全网 — 55 个平台 91+ 个命令，头条、知乎、豆瓣、YouTube、GitHub、Reddit、Hacker News 等。专为 OpenClaw 设计，复用浏览器登录态，返回结构化 JSON，天然适配 AI Agent 工具调用。
version: 0.4.3
author: Ping Si <sipingme@gmail.com>
type: cli
requires:
  runtime:
    - name: node
      version: ">=18.0.0"
      description: Node.js 运行时
    - name: npm
      description: Node.js 包管理器（随 Node.js 安装）
  packages:
    - npm: browser-web-search
      global: false
  binaries:
    - name: openclaw
      description: OpenClaw CLI，用于浏览器自动化
install:
  command: npm install -g browser-web-search@0.4.3
  riskLevel: medium
  riskReason: 通过 npm 全局安装第三方包，该包会在浏览器页面上下文中执行 JavaScript。安装前请审计源码。
  requiresApproval: true
  source:
    registry: npmjs.com
    package: browser-web-search
    repository: https://github.com/sipingme/browser-web-search
    npm: https://www.npmjs.com/package/browser-web-search
  verification:
    - 安装前请审查 GitHub 仓库代码
    - 检查 npm 包的下载量和维护状态
    - 对比 npm 发布版本与 GitHub 源码是否一致
  note: 用户需先通过 npm install -g 全局安装 browser-web-search，运行时调用本地已安装的 bws 命令
capabilities:
  sensitive:
    - type: browser-session-access
      riskLevel: high
      description: 通过 OpenClaw 在已认证的浏览器标签页中执行 JavaScript
      scope: 按 adapter 域名隔离（如 zhihu.com, xiaohongshu.com）
      access:
        - 当前页面 DOM
        - 当前页面 Session（继承，非提取）
        - 站点认证数据（登录态下的 API 响应）
        - 账户保护页面内容（如私信、收藏、个人资料）
      noAccess:
        - 浏览器 Cookie 文件（不直接读取）
        - 其他域名数据
        - 用户配置目录
      risks:
        - 第三方 npm 包（browser-web-search）在页面上下文中执行，可访问站点认证数据
        - 恶意代码可能窃取 cookies 或页面内容
        - 包代码不包含在此 Skill 中，需独立审计
      mitigations:
        - adapter 脚本开源可审计
        - 按域名隔离，无法跨站访问
        - 不持久化存储任何凭证
  privacyNotice:
    summary: 此 Skill 自动复用浏览器登录态，可读取您已登录站点的任何可见数据
    details:
      - 零配置意味着 CLI 自动获得您在 OpenClaw 浏览器中的登录会话访问权
      - 可读取账户保护的页面（私信、收藏、个人资料、订单等）
      - 访问范围取决于您在目标站点的登录权限
      - 建议仅在信任 browser-web-search 包代码后使用
metadata:
  openclaw:
    primaryEnv:
      - name: BWS_ALLOW_SENSITIVE
        values: ["0", "1"]
        default: "0"
        purpose: Session-level opt-in for adapters that touch authenticated browser sessions
      - name: BWS_PUBLIC_ONLY
        values: ["0", "1"]
        default: "0"
        purpose: Hard-isolation mode that denies all sensitive adapters (overrides BWS_ALLOW_SENSITIVE)
    primaryCredentialUsage: none
    networkUsage: indirect-via-bws
    auditLog:
      path: ~/.bws/audit.log
      content: metadata-only (no payloads, no responses, args hashed via SHA-256)
      rotation: 1 MiB → audit.log.1
    subprocessUsage: none
    moduleLoad:
      - file: scripts/run.js
        function: safeRunBws
        method: dynamic-esm-import
        loader: "await import(file://...)"
        target: pinned npm package "browser-web-search"
        targetResolution: platform-standard global node_modules roots only (no PATH lookup, no shell)
        argSource: allow-listed-cli-args
        argValidation:
          - length-bounded (<= 1024 bytes per arg)
          - control-char rejection (NUL + ASCII control)
          - long-flag allow-list (--json/--jq/--count/--sort/--id/--limit/--page)
          - adapter-name regex ([a-zA-Z0-9_-]{1,64}/[a-zA-Z0-9_-]{1,64})
          - "--" delimiter between subcommand and positional args
        purpose: Invoke the pinned 'browser-web-search' npm package in-process, with a validated argv injected via process.argv mutation
configPaths:
  - path: ~/.bws/
    required: false
tags:
  - browser
  - web-search
  - scraping
  - automation
  - ai-agent
repository: https://github.com/sipingme/browser-web-search-skill
package: https://github.com/sipingme/browser-web-search
npm: https://www.npmjs.com/package/browser-web-search
---

# Browser Web Search (BWS) Skill

> **一行命令，搜遍全网** — 为 AI Agent 而生的多平台内容搜索工具

把 **55 个主流平台**的搜索接口封装成统一命令行 API，让 AI Agent 直接拿到结构化 JSON，无需 API Key，无需额外配置。

## 🏗️ 架构说明

```
OpenClaw/AI Agent
    ↓ (读取 Skill 配置)
browser-web-search-skill
    ↓ (调用 CLI)
bws 命令
    ↓ (OpenClaw Browser)
目标网站（55 个平台）
```

## 🎯 核心特点

- 🔍 **跨平台搜索** — 今日头条、知乎、豆瓣、YouTube、GitHub、Reddit、Hacker News… 一套语法搞定
- 🔑 **无需 API Key** — 复用浏览器登录态，开箱即用
- 🤖 **AI Agent 友好** — 结构化 JSON 输出，支持 `--jq` 过滤，天然适配 LLM 工具调用
- ⚡ **零配置** — 无需 Chrome Extension，无需后台 Daemon

## 📋 安装

```bash
npm install -g browser-web-search@0.4.3
```

### 验证安装

```bash
bws --version
bws site list
```

## 🚀 快速开始

```bash
# 搜索今日头条关于 "ai search" 的最新文章
bws site toutiao/search "ai search"

# 搜索知乎，返回 5 条
bws site zhihu/search "ai agent" --count 5

# Hacker News 最新讨论（按时间）
bws site hn/search "llm" --sort date

# GitHub 热门仓库（按 Star 数）
bws site github/search "ai search" --sort stars

# Reddit 最新帖子
bws site reddit/search "ai search" --sort new

# YouTube 视频搜索
bws site youtube/search "ai agent tutorial"

# 查看所有可用命令
bws site list
```

## 📊 内置平台（55 个）

> 🔓 无需登录 · 🔐 需登录该站账号 · 🔀 依具体命令而定

### 🇨🇳 国内平台（30 个）

| 平台 | 说明 | 登录 | 命令 |
|-----|------|:----:|-----|
| **今日头条** | 新闻资讯 | 🔀 | `toutiao/search`, `toutiao/hot`, `toutiao/feed` |
| **澎湃新闻** | 权威新闻 | 🔓 | `thepaper/search`, `thepaper/hot` |
| **腾讯新闻** | 热点新闻 | 🔓 | `qqnews/search`, `qqnews/hot` |
| **网易新闻** | 热点新闻 | 🔓 | `netease/search`, `netease/hot` |
| **新浪新闻** | 门户新闻 | 🔓 | `sina/search`, `sina/hot` |
| **36kr** | 科技创投 | 🔓 | `36kr/search`, `36kr/newsflash`, `36kr/article` |
| **虎嗅** | 科技商业媒体 | 🔓 | `huxiu/search` |
| **华尔街见闻** | 财经资讯 | 🔓 | `wallstreetcn/search` |
| **东方财富** | 股票行情 & 财经新闻 | 🔓 | `eastmoney/stock`, `eastmoney/news` |
| **掘金** | 技术社区 | 🔓 | `juejin/search` |
| **CSDN** | 开发者社区 | 🔓 | `csdn/search` |
| **博客园** | 技术博客 | 🔓 | `cnblogs/search` |
| **V2EX** | 技术社区 | 🔓 | `v2ex/search` |
| **Baidu** | 百度搜索 | 🔓 | `baidu/search` |
| **虎扑** | 体育社区 | 🔓 | `hupu/search` |
| **有道翻译** | 中英词典/翻译 | 🔓 | `youdao/translate` |
| **什么值得买** | 好价/优惠聚合 | 🔓 | `smzdm/search` |
| **InfoQ** | 技术媒体 | 🔓 | `infoq/search` |
| **微信公众号** | 公众号文章 | 🔐 | `weixin/search`, `weixin/article` |
| **小红书** | 生活分享 | 🔐 | `xiaohongshu/search`, `xiaohongshu/note`, `xiaohongshu/comments`, `xiaohongshu/user_posts`, `xiaohongshu/me`, `xiaohongshu/feed` |
| **知乎** | 问答社区 | 🔀 | `zhihu/search`, `zhihu/hot`, `zhihu/question`, `zhihu/me` |
| **微博** | 社交热搜 | 🔐 | `weibo/search`, `weibo/hot` |
| **Bilibili** | 视频弹幕 | 🔀 | `bilibili/search`, `bilibili/popular`, `bilibili/trending`, `bilibili/ranking`, `bilibili/video`, `bilibili/comments`, `bilibili/history`, `bilibili/me`, `bilibili/feed` |
| **雪球** | 股票社区 | 🔐 | `xueqiu/search` |
| **BOSS直聘** | 招聘平台 | 🔀 | `boss/search`, `boss/detail` |
| **即刻** | 兴趣社区 | 🔐 | `jike/search` |
| **豆瓣** | 影视/书籍评分社区 | 🔐 | `douban/search`, `douban/movie`, `douban/movie-hot`, `douban/top250`, `douban/comments` |
| **起点中文网** | 网络小说 | 🔐 | `qidian/search` |
| **携程** | 旅行/酒店/景点 | 🔐 | `ctrip/search` |

### 🌏 国际平台（25 个）

| 平台 | 说明 | 登录 | 命令 |
|-----|------|:----:|-----|
| **Google** | 谷歌搜索 | 🔓 | `google/search` |
| **Bing** | 必应搜索 | 🔓 | `bing/search` |
| **DuckDuckGo** | 隐私优先搜索 | 🔓 | `duckduckgo/search` |
| **GitHub** | 代码托管 | 🔓 | `github/search` |
| **Hacker News** | 科技社区 (YC) | 🔓 | `hn/search` |
| **Reddit** | 英文社区 | 🔓 | `reddit/search` |
| **BBC** | 国际新闻 | 🔓 | `bbc/news` |
| **Reuters** | 路透社新闻 | 🔓 | `reuters/search` |
| **The Verge** | 科技媒体 | 🔓 | `verge/search` |
| **Ars Technica** | 深度科技媒体 | 🔓 | `ars/search` |
| **Engadget** | 科技消费媒体 | 🔓 | `engadget/search` |
| **Stack Overflow** | 开发者问答 | 🔓 | `stackoverflow/search` |
| **Dev.to** | 开发者社区 | 🔓 | `devto/search` |
| **npm** | Node.js 包 | 🔓 | `npm/search` |
| **PyPI** | Python 包 | 🔓 | `pypi/search` |
| **arXiv** | 学术论文 | 🔓 | `arxiv/search` |
| **IMDb** | 全球最大影视数据库 | 🔓 | `imdb/search`, `imdb/movie`, `imdb/top250` |
| **Genius** | 歌词/歌曲数据库 | 🔓 | `genius/search` |
| **Wikipedia** | 百科全书 | 🔓 | `wikipedia/search`, `wikipedia/summary` |
| **Open Library** | 图书数据库 | 🔓 | `openlibrary/search` |
| **Yahoo Finance** | 美股/港股行情 | 🔓 | `yahoo-finance/quote` |
| **GSMArena** | 手机规格数据库 | 🔓 | `gsmarena/search` |
| **Product Hunt** | 科技产品发现 | 🔓 | `producthunt/today` |
| **X (Twitter)** | 社交媒体 | 🔐 | `x/search` |
| **LinkedIn** | 职业社交 | 🔐 | `linkedin/search` |
| **YouTube** | 视频 & 字幕 & 评论 | 🔀 | `youtube/search`, `youtube/video`, `youtube/transcript`, `youtube/transcript-by-id`, `youtube/comments`, `youtube/channel`, `youtube/feed` |

## 🔧 命令参考

```bash
bws site list                        # 列出所有 adapter
bws site info <name>                 # 查看 adapter 参数说明
bws site <name> [args...]            # 运行 adapter
bws site <name> --count 5           # 限制返回数量
bws site <name> --json               # 输出原始 JSON
bws site <name> --jq '.items[].url' # jq 过滤提取字段
```

## 📋 标准操作流程 (SOP)

### 操作 1：跨平台搜索

**场景**：用户想搜索多个平台关于某话题的最新内容

```bash
# 国内平台
bws site toutiao/search "ai agent" --count 5
bws site zhihu/search "ai agent" --count 5
bws site huxiu/search "ai agent" --count 5

# 国际平台
bws site hn/search "ai agent" --sort date --count 5
bws site reddit/search "ai agent" --sort new --count 5
bws site github/search "ai agent" --sort stars --count 5
```

---

### 操作 2：获取热点资讯

```bash
bws site zhihu/hot        # 知乎热榜
bws site weibo/hot        # 微博热搜
bws site toutiao/hot      # 今日头条热榜
bws site thepaper/hot     # 澎湃新闻热点
bws site bilibili/trending  # B 站热搜词
bws site bilibili/popular   # B 站全站热门
```

---

### 操作 3：使用 jq 过滤数据

```bash
# 只提取标题
bws site zhihu/search "大模型" --jq '[.items[].title]'

# 只提取 URL 列表
bws site hn/search "llm" --jq '[.items[].url]'

# 提取标题+日期
bws site toutiao/search "ai" --jq '[.items[] | {title, date}]'
```

---

### 操作 4：影视 / 娱乐内容

```bash
# 豆瓣搜索影视
bws site douban/search "三体"
bws site douban/movie-hot

# IMDb 搜索
bws site imdb/search "Inception"
bws site imdb/top250 --count 10

# YouTube 视频与字幕
bws site youtube/search "ai tutorial"
bws site youtube/transcript-by-id --id dQw4w9WgXcQ
```

---

### 操作 5：开发者资源搜索

```bash
# 搜索 npm 包
bws site npm/search "langchain"

# 搜索 PyPI 包
bws site pypi/search "openai"

# arXiv 论文
bws site arxiv/search "retrieval augmented generation" --count 5

# Stack Overflow
bws site stackoverflow/search "python async await"
```

---

### 操作 6：登录态管理

需要登录的站点（微信公众号、小红书、微博、X、豆瓣等）：

```bash
# 在 OpenClaw 浏览器中登录
openclaw browser open https://weixin.qq.com
openclaw browser open https://x.com
openclaw browser open https://www.xiaohongshu.com
openclaw browser open https://www.douban.com

# 登录完成后重试
bws site weixin/search "ai"
bws site douban/search "三体"
```

---

## 🔧 技术架构：如何访问登录态

```
bws 命令
    ↓ 调用
openclaw browser evaluate <script>
    ↓ 在已打开的标签页中执行 JavaScript
目标网站（使用该标签页的登录态）
```

| 访问内容 | 是否访问 | 说明 |
|---------|---------|------|
| 浏览器 Cookie 文件 | ❌ 否 | 不直接读取 `~/.config/chromium/Cookies` 等文件 |
| 用户配置目录 | ❌ 否 | 不访问 `~/.bws/` 以外的配置 |
| 其他网站数据 | ❌ 否 | 只能访问 adapter 指定的域名 |
| 当前页面 DOM | ✅ 是 | adapter 脚本在页面中执行 |
| 当前页面 Session | ✅ 是 | 继承页面的登录状态 |

## 🛡️ 运行安全与最小权限（必读）

> 本 Skill 的核心工作由第三方 npm 包 `browser-web-search` 完成；该包会在已认证的浏览器标签页上下文中执行 JavaScript，因此**理论上可以读取你已登录站点的任何可见数据（私信、收藏、个人资料、订单等）**。Launcher 只能控制传给 `bws` 的参数，无法约束包内代码行为。请务必按以下原则使用。

### 1) 安装前审计与版本固定

```bash
# 审计源码 (与 SKILL.md 中声明的版本严格一致)
npm view browser-web-search@0.4.3 dist.integrity dist.shasum
# 阅读源码: https://github.com/sipingme/browser-web-search/blob/v0.4.3/src/index.ts

# 安装时跳过 install/postinstall 脚本，降低供应链注入面
npm install -g browser-web-search@0.4.3 --ignore-scripts
```

不要使用 `latest` tag、不要使用 `^0.4.3` 之类的范围版本。每次升级前重新审计。

### 2) 浏览器配置隔离

**强烈建议**为 OpenClaw 创建一个独立的 Chrome/Chromium profile，仅在该 profile 中登录会被本 Skill 访问的站点。**不要**让 OpenClaw 复用你日常的浏览器 profile，避免银行、邮箱、企业 SSO 等无关账号被 adapter 触达。

### 3) 默认拒绝 + 显式 opt-in（敏感 adapter）

Launcher 把 adapter 划分为 `public` / `sensitive` 两类。`sensitive` 即默认拒绝；触发条件之一即视为敏感：

- 站点位于 `ALWAYS_SENSITIVE_SITES`：`weixin / xiaohongshu / weibo / xueqiu / jike / douban / qidian / ctrip / x / linkedin`
- 命令后缀匹配 `/(me|feed|history|comments|user_posts|article)$`，例如 `zhihu/me`、`bilibili/feed`、`youtube/history`
- 未在白名单中的未知站点（防御未来 `bws` 新增 adapter）

授权方式（任选其一）：

| 方式 | 适用场景 | 命令 |
|------|---------|------|
| 会话级 env | AI Agent 长期运行 | `export BWS_ALLOW_SENSITIVE=1` |
| per-call flag | 一次性临时使用 | `bws site weixin/search "ai" --i-understand-sensitive` |
| 硬隔离模式 | 不可信环境 / 沙箱 agent | `export BWS_PUBLIC_ONLY=1` （即使设置了上面两个也会被拒绝） |

未 opt-in 时，敏感 adapter 会返回结构化拒绝并在 stderr 提示如何继续。

### 4) 审计日志

Launcher 会在 `~/.bws/audit.log` 追加 JSON Lines 记录，**仅包含元数据**（adapter 名、决策、原因、参数 SHA-256 截断哈希），**不记录任何参数原文、cookie 或响应数据**。日志超过 1 MiB 自动轮转为 `audit.log.1`。

定期 review：

```bash
tail -n 50 ~/.bws/audit.log | jq -c
# 仅查看 sensitive 决策
jq -c 'select(.classification=="sensitive")' ~/.bws/audit.log
```

### 5) 数据最小化

- 优先使用公开 adapter（`hn/search`、`github/search`、`arxiv/search` 等）—— 这些不需要登录态，即使 `bws` 被恶意替换也无敏感数据可窃。
- 用 `--jq` / `--count` 在源头减少返回字段。**不要**把整段 JSON 喂给下游 LLM 或外发到第三方服务。
- 涉及账户保护页面时，使用一次性查询 + 立即关闭 OpenClaw 标签。

### 6) 残留风险（无法在本 Skill 层面消解）

- 一旦 `bws` 被调用（无论是否 sensitive 类别），它都拥有当前 OpenClaw session 的完整执行权限。Launcher 无法阻止包内代码越界访问其他已打开的标签。**唯一的硬隔离手段**是上文 (2) 的浏览器 profile 隔离 + (3) 的 `BWS_PUBLIC_ONLY=1`。
- 若 npm 注册表上的 `browser-web-search@0.4.3` 在你审计后被重新发布（不可变性被破坏），本地已安装版本不受影响，但下次 `npm install -g` 会拉到新版本。建议把审计过的 tarball 缓存到内部 registry 或私有 mirror。

## 🔒 安全模型摘要（机器可读字段已在 `config.json` 中声明）

| 维度 | 状态 |
|-----|------|
| 子进程命令注入 | ✅ launcher 显式 `shell:false` + allow-list 校验 |
| Option injection 到 bws | ✅ flag allow-list + `--` 分隔 |
| 敏感 adapter 默认拒绝 | ✅ deny-by-default，需 env / flag opt-in |
| 公共 adapter 直通 | ✅ 无需 opt-in（如 `hn/search`） |
| 审计日志 | ✅ `~/.bws/audit.log`（仅元数据） |
| 浏览器 session 越权（包内 JS） | ⚠️ 无法在 launcher 层消解，依赖 (2) profile 隔离 |
| 第三方包供应链 | ⚠️ 依赖用户安装前审计 + 版本固定 |
| 跨站访问 | ⚠️ adapter 域名隔离仅约束开源 adapter 的设计意图，不是运行时强制 |
| 上传到第三方服务器 | ⚠️ 当前开源版本未观察到，但每次升级需重新审计 |

## 🎓 示例对话

**用户**：搜索头条最新 3 篇关于 AI Agent 的文章

```bash
bws site toutiao/search "AI Agent" --count 3
```

---

**用户**：看看 Hacker News 上关于 LLM 的最新讨论

```bash
bws site hn/search "llm" --sort date --count 5
```

---

**用户**：GitHub 上 ai search 相关的热门项目

```bash
bws site github/search "ai search" --sort stars --count 5
```

---

**用户**：豆瓣电影 Top 10

```bash
bws site douban/top250 --count 10
```

---

**用户**：YouTube 搜索 AI 教程

```bash
bws site youtube/search "ai agent tutorial" --count 10
```

---

## 📚 参考资料

- [项目 GitHub](https://github.com/sipingme/browser-web-search-skill)
- [browser-web-search 核心库](https://github.com/sipingme/browser-web-search)
- [npm 包](https://www.npmjs.com/package/browser-web-search)

---

## 📝 维护说明

- **版本**: 0.4.3
- **最后更新**: 2026-04-29
- **维护者**: Ping Si <sipingme@gmail.com>
- **许可证**: MIT

---

## ✅ 首次成功检查清单

- [ ] 安装工具：`npm install -g browser-web-search@0.4.3`
- [ ] 验证版本：`bws --version`
- [ ] 查看命令：`bws site list`
- [ ] 测试搜索：`bws site zhihu/search "ai" --count 3`
- [ ] 看到 JSON 输出
