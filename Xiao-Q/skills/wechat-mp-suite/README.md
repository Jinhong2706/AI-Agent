# 微信公众号终极工作台 (wechat-mp-suite)

> OpenClaw Skill — 微信公众号一站式工作台，集成搜索、爬虫、下载、写作、洗稿、AI配图、专业排版、发布八大模块

## 功能模块

| 模块 | 功能 | 说明 |
|------|------|------|
| 🔍 **搜索** | 关键词搜索公众号文章 | 基于搜狗微信搜索，支持批量抓取正文 |
| 📥 **爬虫** | 轻量级文章爬取 | Python 实现，URL → Markdown + 本地图片 |
| 💾 **下载** | 完整文章下载 | 基于 Puppeteer，支持懒加载图片、视频嗅探 |
| ✍️ **写作** | 多风格文章撰写 | 刘润商业风格/爆款推文/真人写作/财经夜报 |
| 🔄 **洗稿** | AI去痕迹+原创改写 | 结构重组、语言改写、SEO优化 |
| 🖼️ **AI配图** | 封面图设计、配图建议 | 根据文章类型推荐配图策略 |
| 🎨 **排版** | Markdown → 公众号富文本 | AI结构化版 + 预设主题版，双版预览 |
| 📤 **发布** | 发布到公众号草稿箱 | 本地 wenyan-cli / 远程 MCP 发布 |

## 快速开始

### 环境要求

- **Node.js** >= 18
- **Python 3**
- **Google Chrome**（下载模块需要）
- [OpenClaw](https://github.com/anthropics/openclaw) 运行环境

### 安装依赖

```bash
# 1. Node.js 依赖
npm install -g cheerio @wenyan-md/cli

# 2. 下载模块依赖
cd {baseDir}/scripts/downloader && npm install

# 3. 爬虫模块依赖
cd {baseDir}/scripts/spider
pip install -r requirements.txt
```

## 使用方法

### 🔍 搜索文章

```bash
# 基础搜索
node {baseDir}/scripts/search/search_wechat.js "关键词"

# 指定数量 + 抓取正文
node {baseDir}/scripts/search/search_wechat.js "关键词" -n 5 -c

# 保存结果
node {baseDir}/scripts/search/search_wechat.js "关键词" -n 20 -o result.json
```

### 📥 爬虫（轻量版）

```bash
python3 {baseDir}/scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx
python3 {baseDir}/scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx ./my-articles
```

### 💾 下载（完整版）

```bash
node {baseDir}/scripts/downloader/download.js https://mp.weixin.qq.com/s/xxxxx
```

> 完整版基于 Puppeteer，支持懒加载图片、视频链接嗅探，适合需要完整内容的场景。

### ✍️ 写作

通过 OpenClaw 自然语言指令触发：
- "帮我写篇公众号文章"
- "用刘润风格写一篇关于AI创业的深度文章"
- "写一篇爆款推文"
- "用老韭菜视角写财经夜报"

### 🔄 洗稿改写

通过 OpenClaw 自然语言指令触发：
- "帮我洗稿这篇文章"
- "改写成原创"
- "去掉 AI 味"

### 🎨 排版

```bash
# 一步完成（推荐）
node {baseDir}/scripts/typeset/wechat-dual-copy.js article.md

# 分别生成
node {baseDir}/scripts/typeset/html-to-wechat-copy.js article.ai.html
```

> 排版功能依赖外部服务 `edit.shiker.tech`，需要联网访问。

### 📤 发布到公众号

**本地发布：**

```bash
# 配置环境变量
export WECHAT_APP_ID=your_app_id
export WECHAT_APP_SECRET=your_app_secret

# 发布
node {baseDir}/scripts/publisher/publish.js /path/to/article.md
wenyan publish -f article.md -t lapis -h solarized-light
```

> IP 必须添加到微信公众号后台白名单！

**远程 MCP 发布：**

```bash
{baseDir}/scripts/publisher/publish-remote.sh ./my-post.md
```

## 项目结构

```
wechat-mp-suite/
├── SKILL.md                        # OpenClaw Skill 定义
├── README.md                       # 本文件
├── CHANGELOG.md                    # 版本变更记录
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
    │   └── wechat.env.example
    └── typeset/                    # 排版模块
        ├── wechat-dual-copy.js
        └── html-to-wechat-copy.js
```

## 注意事项

- 所有工具仅供**个人学习**使用，请遵守相关版权法规
- 搜索功能内置防封禁机制，请勿高频使用
- 微信公众号发布需确保内容合规，遵守平台规则
- IP 白名单：本地发布需添加本机 IP，远程 MCP 发布需添加服务器 IP

## License

MIT
