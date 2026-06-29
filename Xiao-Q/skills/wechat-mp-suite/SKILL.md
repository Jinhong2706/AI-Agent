---
name: wechat-mp-suite
version: 1.0.1
description: "微信公众号终极工作台 — 集成搜索、爬虫、写作（刘润风格/爆款推文/真人写作）、洗稿、AI配图、专业排版、发布（本地/远程MCP）八大模块。当用户需要公众号全流程创作时使用。"
metadata:
  openclaw:
    emoji: "📱"
    requires: { "bins": ["node", "python3", "curl", "jq"] }
    platforms: ["macos", "linux"]
    install:
      - id: node-brew
        kind: brew
        formula: node
        bins: ["node"]
        label: Install Node.js (brew)
      - id: python3
        kind: pip
        formula: requests beautifulsoup4 lxml
        bins: ["python3"]
        label: Install Python dependencies
---

# 📱 微信公众号终极工作台 (wechat-mp-suite)

集 **搜索 → 爬虫 → 写作 → 洗稿 → AI配图 → 专业排版 → 发布** 全流程于一体，覆盖公众号内容创作全生命周期。

---

## Quick Start（直接说这些就能用）

| 想做什么 | 直接说 |
|---------|--------|
| 搜索文章 | "搜索最近公众号关于AI的文章" |
| 下载文章 | "下载这篇公众号文章 https://mp.weixin.qq.com/s/xxx" |
| 写新文章 | "用刘润风格帮我写一篇关于AI创业的公众号" |
| 洗稿改写 | "帮我把这篇文章洗稿成原创风格" |
| AI配图 | "给这篇文章生成封面图prompt" |
| 排版 | "帮我排版 article.md 这篇文章" |
| 发布 | "发布 article.md 到公众号" |

---

## 模块一览

| 模块 | 功能 | 触发词示例 |
|------|------|-----------|
| 🔍 搜索 | 关键词搜索公众号文章（搜狗微信） | "搜XX的公众号文章" |
| 📥 爬虫 | URL → Markdown + 本地图片（轻量版） | "爬取这篇公众号文章" |
| 💾 下载 | URL → Markdown + 图片/视频（完整版，含懒加载） | "下载这篇公众号文章" |
| ✍️ 写作 | 刘润风格/爆款推文/真人写作/财经深度 | "帮我写篇公众号" |
| 🔄 洗稿 | AI去痕迹+原创改写 | "帮我洗稿/改写这篇文章" |
| 🖼️ AI配图 | AI生成封面图+配图prompt | "给文章配张图" |
| 🎨 排版 | AI结构化版+预设主题版预览链接 | "公众号排版" |
| 📤 发布 | 本地wenyan / 远程MCP发布 | "发布到公众号" |

---

# 🔍 模块一：文章搜索

通过搜狗微信搜索获取公众号文章列表，支持抓取正文。

## 使用方法

```bash
node {baseDir}/scripts/search/search_wechat.js "关键词"
node {baseDir}/scripts/search/search_wechat.js "关键词" -n 15 -c
node {baseDir}/scripts/search/search_wechat.js "关键词" -n 20 -o result.json
```

### 参数说明
- `query`：搜索关键词（必填）
- `-n, --num`：返回数量（默认 10，最大 50）
- `-o, --output`：输出 JSON 文件路径
- `-r, --resolve-url`：解析微信文章真实链接
- `-c, --fetch-content`：抓取文章正文（自动启用 `-r`）

---

# 📥 模块二：文章爬虫

输入公众号文章 URL，自动下载为 Markdown + 本地图片。

## 安装依赖

```bash
cd {baseDir}/scripts/spider
pip install -r requirements.txt
```

## 使用方法

```bash
# 基础用法
python3 {baseDir}/scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx

# 指定输出目录
python3 {baseDir}/scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx ./my-articles
```

### 输出结构
```
output/
├── 文章标题.md
└── images/
    ├── img_001.jpg
    └── img_002.png
```

---

# ✍️ 模块三：文章写作（多风格支持）

## 风格一：刘润商业风格（深度文章）

适合商业评论、深度分析，3000-5000字。

### 写作特点
1. **开篇切入**：从具体商业案例/故事/现象切入
2. **引入洞察**：引出独特商业观点
3. **案例论证**：用2-3个真实商业案例论证
4. **数据支撑**：适当引用数据和事实
5. **结论建议**：给出明确结论和行动建议

### 结构建议
```
# 大标题（核心观点）

## 小标题1：第一个分论点
- 案例/故事 → 分析 → 结论

## 小标题2：第二个分论点
- 案例/故事 → 分析 → 结论

## 总结
- 核心观点回顾 + 行动建议
```

### 禁止事项
- ❌ 末尾加话题标签（#xxx）
- ❌ 大量emoji
- ❌ "欢迎在评论区分享"结尾

---

## 风格二：爆款推文（传播学驱动）

适合追求高阅读量、传播性强的内容。

### 爆款五步法
1. **爆款标题**：5维标题矩阵（悬念型/痛点型/反直觉型/利益相关型/强情绪型）
2. **内容排版**：H2/H3分层，每段≤4行，碎片化阅读适配
3. **智能配图**：3-5张配图，关键位置（开头/转折/总结）
4. **封面设计**：3种风格方案（扁平插画/写实摄影/抽象艺术）
5. **最终输出**：Markdown格式，可直接复制

### 爆款开头五法
- 提问式："你有没有想过……"
- 场景式："想象一下……"
- 数据式："据统计……"
- 故事式："那天，我遇到了……"
- 反差式："大多数人都做错了……"

### 爆款结构四模式
- 总分总结构（干货类）
- 清单式结构（教程类）
- 叙事线结构（故事类）
- 对比式结构（观点类）

---

## 风格三：真人写作（口语化/去AI味）

适合需要"像真人写的"内容，强口语化。

### 核心原则
随意感 > 口语化。真人说话的关键是自然随意，不是刻意。

### 硬规则
- 开头3段内必须出现"冲突/反差/损失感"至少1个钩子
- 每4-6段插入"划重点小标题"
- 至少给1组if/then判断
- 结尾必须有CTA（关注/进群/评论提问）

### 禁用表达
- 空泛词："赋能、抓手、闭环、矩阵化、全方位"
- 学术套话："综上所述、毋庸置疑、不难发现"
- 连续三段同构句式

### 标题生成规则
每次至少3类标题：
- 悬念型：留下信息缺口
- 利益型：明确读者收获
- 观点型：态度鲜明、可讨论

---

## 风格四：财经夜报（老韭菜视角）

适合财经新闻点评、市场分析。

### 角色设定
- 市场摸爬滚打十几年的老韭菜
- 大白话说真相，不说官话
- 像朋友聊天一样自然
- 可吐槽、调侃、自嘲

---

# 🔄 模块四：文章洗稿

将文章改写为自然、原创风格，去除 AI 写作痕迹。

## 触发词
- "帮我洗稿这篇文章"
- "改写成原创"
- "降低查重率"
- "去掉 AI 味"

## 洗稿策略

### A. 结构重组
- 段落重排、拆合
- 叙事角度转换
- 论据重组

### B. 语言改写
- 删除意义膨胀句 → 替换为具体事实
- 去虚假权威 → 写明来源或删除
- 去广告语气 → 客观描述
- 去 AI 高频词：赋能、闭环、生态、抓手、底层逻辑

### C. 添加真实感
- 使用第一人称（当合适时）
- 承认复杂性和不确定性
- 变化句子节奏（长短句交错）
- 加入具体细节

---

# 🖼️ 模块五：AI 配图

## 封面图 prompt 生成

```
文章封面：{标题}。风格：简洁、现代、公众号头图、强对比、高可读中文标题排版、16:9、2K。主视觉：{核心意象}。颜色：{主色+强调色}。避免：复杂背景、过多文字、水印。
```

## 配图策略

| 文章类型 | 配图建议 |
|---------|---------|
| 技术教程 | 代码截图、架构图、流程图、效果演示 |
| 产品测评 | 产品实拍、对比图、细节特写 |
| 行业观点 | 数据图表、趋势图、相关新闻截图 |
| 个人故事 | 场景照片、聊天截图、相关物品 |
| 工具推荐 | 软件界面、功能截图、前后对比 |

---

# 🎨 模块六：专业排版

> ⚠️ 排版功能依赖外部服务 `edit.shiker.tech`，需要联网访问。如服务不可用，请手动打开生成的 HTML 文件复制内容。

用户提供 Markdown，返回**两个预览链接**：
- **AI 结构化版**：Markdown → AI生成HTML → 按SPEC改写 → 预览链接
- **预设主题版**：Markdown → 预设主题渲染 → 预览链接

## 使用方法

```bash
# 一步完成模式（推荐）
node {baseDir}/scripts/typeset/wechat-dual-copy.js article.md

# 分别生成
node {baseDir}/scripts/typeset/html-to-wechat-copy.js article.ai.html
```

## 输出

两个预览链接（`https://edit.shiker.tech/copy.html?id=xxx`）：
- `AI:` AI结构化版
- `PRESET:` 预设主题版

用户打开链接 → 点击"复制到剪贴板" → 粘贴到公众号后台。

---

# 📤 模块七：文章发布

## 方式一：本地发布（wenyan-cli）

### 配置

```bash
export WECHAT_APP_ID=your_app_id
export WECHAT_APP_SECRET=your_app_secret
```

> ⚠️ IP 必须添加到微信公众号后台白名单！

### 发布

```bash
# 基础发布
node {baseDir}/scripts/publisher/publish.js /path/to/article.md

# wenyan-cli 直接发布
wenyan publish -f article.md -t lapis -h solarized-light

# 含视频文章
node {baseDir}/scripts/publisher/publish_with_video.js /path/to/article.md
```

---

## 方式二：远程 MCP 发布（推荐家庭宽带用户）

解决家庭宽带 IP 频繁变动问题，通过远程 wenyan-mcp 服务中转。

### 配置

**1. 准备 wechat.env**

```bash
cp {baseDir}/scripts/publisher/wechat.env.example {baseDir}/scripts/publisher/wechat.env
nano {baseDir}/scripts/publisher/wechat.env
```

内容：
```bash
export WECHAT_APP_ID="wx..."
export WECHAT_APP_SECRET="cx..."
```

**2. 配置 mcp.json**

```json
{
  "mcpServers": {
    "wenyan-mcp": {
      "name": "公众号远程助手",
      "transport": "sse",
      "url": "http://<your-remote-server-ip>:3000/sse"
    }
  }
}
```

### 发布

```bash
# 使用脚本发布
chmod +x {baseDir}/scripts/publisher/publish-remote.sh
{baseDir}/scripts/publisher/publish-remote.sh ./my-post.md

# 指定主题
{baseDir}/scripts/publisher/publish-remote.sh ./my-post.md lapis
```

---

## Markdown 格式要求

文件顶部**必须**包含完整 frontmatter：

```markdown
---
title: 文章标题（必填）
cover: /absolute/path/to/cover.jpg（必填，绝对路径）
---

# 正文...
```

⚠️ `title` 和 `cover` **缺一不可**，所有图片路径必须使用**绝对路径**。

---

# 📁 项目结构

```
wechat-mp-suite/
├── SKILL.md                        # OpenClaw Skill 定义
├── README.md                       # 使用手册
├── references/
│   └── USAGE.md                    # 完整使用文档
└── scripts/
    ├── search/                     # 搜索模块
    │   └── search_wechat.js
    ├── downloader/                 # 下载模块
    │   └── download.js
    ├── spider/                     # 爬虫模块
    │   ├── main.py
    │   └── requirements.txt
    ├── publisher/                  # 发布模块
    │   ├── publish.js
    │   ├── publish_with_video.js
    │   ├── publish-remote.sh
    │   └── wechat.env
    └── typeset/                    # 排版模块
        ├── wechat-dual-copy.js
        └── html-to-wechat-copy.js
```

---

# 完整工作流示例

## 工作流 1：搜索 → 洗稿 → 排版 → 发布

```
1. 搜索：node {baseDir}/scripts/search/search_wechat.js "AI教程" -n 5 -c
2. 洗稿：使用 OpenClaw 自然语言指令（"帮我洗稿"）
3. 排版：node {baseDir}/scripts/typeset/wechat-dual-copy.js article.md
4. 发布：node {baseDir}/scripts/publisher/publish.js article.md
```

## 工作流 2：爬虫 → 写作 → 排版 → 远程发布

```
1. 爬虫：python3 {baseDir}/scripts/spider/main.py https://mp.weixin.qq.com/s/xxx ./output
2. 写作：使用 OpenClaw 写作指令（"用刘润风格改写"）
3. 排版：node {baseDir}/scripts/typeset/wechat-dual-copy.js article.md
4. 远程发布：{baseDir}/scripts/publisher/publish-remote.sh article.md
```

---

## 注意事项

- 搜索功能内置防封禁机制（随机 UA、请求延迟），请勿高频使用
- 微信公众号发布需确保内容合规，遵守平台规则
- IP 白名单：本地发布需添加本机IP，远程MCP发布需添加服务器IP
