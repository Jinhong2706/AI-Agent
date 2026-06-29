# 微信公众号终极工作台 (wechat-mp-suite) 完整使用文档

> 版本：1.0.0
> 整合自：wechat-toolkit + wechat-mp-writer + wechat-article-spider + wechat-article-pro + wechat-mp-publisher + wechat-article-typeset + wechat-article-crayon + gongzhonghao-xieshou

## 技能信息

- **名称**: wechat-mp-suite
- **版本**: 1.0.0
- **描述**: 微信公众号终极工作台，集成搜索、爬虫、写作、洗稿、AI配图、专业排版、发布八大模块

## 功能模块总览

| 模块 | 功能 | 脚本/方式 | 说明 |
|------|------|----------|------|
| 🔍 **搜索** | 关键词搜索公众号文章 | Node.js 脚本 | 基于搜狗微信搜索 |
| 📥 **爬虫** | URL → Markdown+图片 | Python 脚本 | 自动下载文章 |
| ✍️ **写作** | 4种写作风格 | OpenClaw 自然语言 | 刘润/爆款/真人/财经 |
| 🔄 **洗稿** | AI去痕迹+原创改写 | OpenClaw 自然语言 | 去除AI写作痕迹 |
| 🖼️ **AI配图** | 封面图生成+配图prompt | OpenClaw 自然语言 | AI生成封面 |
| 🎨 **排版** | 两个预览链接 | Node.js 脚本 | AI结构化+预设主题 |
| 📤 **发布** | 本地wenyan / 远程MCP | Node.js + Shell | 两种发布方式 |

## 环境要求

- **Node.js** ≥ 18
- **Python 3**
- **Google Chrome**（下载模块需要）
- **curl**、**jq**（远程发布需要）
- [OpenClaw](https://github.com/anthropics/openclaw) 运行环境

## 安装依赖

```bash
# 1. Node.js 全局依赖
npm install -g cheerio @wenyan-md/cli

# 2. 下载模块依赖
cd /root/skills/wechat-mp-suite/scripts/downloader && npm install

# 3. 爬虫模块依赖
cd /root/skills/wechat-mp-suite/scripts/spider && pip install -r requirements.txt

# 4. 排版模块依赖
cd /root/skills/wechat-mp-suite/scripts/typeset && npm install
```

---

## 🔍 模块一：文章搜索

### 功能说明
通过搜狗微信搜索获取公众号文章列表，支持抓取正文。

### 使用方法

```bash
# 基础搜索
node /root/skills/wechat-mp-suite/scripts/search/search_wechat.js "关键词"

# 指定数量 + 抓取正文
node /root/skills/wechat-mp-suite/scripts/search/search_wechat.js "关键词" -n 5 -c

# 保存结果到 JSON
node /root/skills/wechat-mp-suite/scripts/search/search_wechat.js "关键词" -n 20 -o result.json
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `关键词` | 搜索关键词（必填） | - |
| `-n, --num` | 返回数量 | 10（最大50）|
| `-o, --output` | 输出 JSON 文件路径 | 控制台输出 |
| `-r, --resolve-url` | 解析微信文章真实链接 | 关闭 |
| `-c, --fetch-content` | 抓取文章正文 | 关闭 |

---

## 📥 模块二：文章爬虫

### 功能说明
输入公众号文章 URL，自动下载为 Markdown + 本地图片。

### 使用方法

```bash
# 基础用法
python3 /root/skills/wechat-mp-suite/scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx

# 指定输出目录
python3 /root/skills/wechat-mp-suite/scripts/spider/main.py https://mp.weixin.qq.com/s/xxxxx ./my-articles
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

## ✍️ 模块三：文章写作

### 触发方式
通过 OpenClaw 自然语言指令触发：
- "帮我写篇公众号文章"
- "用刘润风格写一篇商业分析"
- "写一篇爆款推文"
- "用真人写作风格改写"
- "写一篇财经夜报"

### 风格一：刘润商业风格

**适用场景**：商业评论、深度分析、行业洞察

**特点**：
1. 从具体商业案例/故事切入
2. 引出独特商业观点
3. 用2-3个真实商业案例论证
4. 适当引用数据
5. 给出明确结论和行动建议

**结构**：
```
# 大标题（核心观点）
## 小标题1：案例/故事 → 分析 → 结论
## 小标题2：案例/故事 → 分析 → 结论
## 总结：核心观点回顾 + 行动建议
```

**禁止**：
- ❌ 末尾加话题标签
- ❌ 大量emoji
- ❌ "欢迎在评论区分享"结尾

---

### 风格二：爆款推文

**适用场景**：追求高阅读量、传播性强的内容

**爆款五步法**：
1. 爆款标题（5维矩阵）
2. 内容排版（碎片化适配）
3. 智能配图（3-5张）
4. 封面设计（3种风格）
5. 最终输出（Markdown）

**爆款开头五法**：
- 提问式、场景式、数据式、故事式、反差式

---

### 风格三：真人写作

**适用场景**：需要"像真人写的"内容

**核心原则**：随意感 > 口语化

**硬规则**：
- 开头3段内必须有冲突/反差/损失感
- 每4-6段有"划重点小标题"
- 至少1组if/then判断
- 结尾必须有CTA

**禁用词**：
- 空泛词："赋能、抓手、闭环、矩阵化"
- 学术套话："综上所述、毋庸置疑"

---

### 风格四：财经夜报

**适用场景**：财经新闻点评、市场分析

**角色**：市场摸爬滚打十几年的老韭菜

**语气**：大白话说真相，像朋友聊天

---

## 🔄 模块四：文章洗稿

### 触发方式
- "帮我洗稿这篇文章"
- "改写成原创"
- "降低查重率"
- "去掉 AI 味"

### 洗稿策略

**A. 结构重组**
- 段落重排、拆合
- 叙事角度转换
- 论据重组

**B. 语言改写**
- 删除意义膨胀句 → 具体事实
- 去虚假权威 → 写明来源
- 去 AI 高频词：赋能、闭环、生态

**C. 添加真实感**
- 使用第一人称
- 承认复杂性
- 长短句交错
- 加入具体细节

---

## 🖼️ 模块五：AI 配图

### 封面图 Prompt 模板

```
文章封面：{标题}。风格：简洁、现代、公众号头图、强对比、高可读中文标题排版、16:9、2K。主视觉：{核心意象}。颜色：{主色+强调色}。避免：复杂背景、过多文字、水印。
```

### 配图建议

| 文章类型 | 配图建议 |
|---------|---------|
| 技术教程 | 代码截图、架构图、流程图 |
| 产品测评 | 产品实拍、对比图 |
| 行业观点 | 数据图表、趋势图 |
| 个人故事 | 场景照片、聊天截图 |
| 工具推荐 | 软件界面、功能截图 |

---

## 🎨 模块六：专业排版

### 功能说明
用户提供 Markdown，返回**两个预览链接**：
- **AI 结构化版**：Markdown → AI生成HTML → 预览链接
- **预设主题版**：Markdown → 预设主题渲染 → 预览链接

### 使用方法

```bash
# 一步完成模式（推荐）
node /root/skills/wechat-mp-suite/scripts/typeset/wechat-dual-copy.js article.md

# 单独生成 AI 结构化版
node /root/skills/wechat-mp-suite/scripts/typeset/html-to-wechat-copy.js article.ai.html
```

### 输出

两个预览链接：
- `AI:` AI结构化版
- `PRESET:` 预设主题版

用户操作：
1. 打开链接
2. 点击"复制到剪贴板"
3. 粘贴到公众号后台

### 详细规范

见 `/root/skills/wechat-mp-suite/references/SPEC.md`

---

## 📤 模块七：文章发布

### 方式一：本地发布（wenyan-cli）

**配置环境变量**：
```bash
export WECHAT_APP_ID=your_app_id
export WECHAT_APP_SECRET=your_app_secret
```

> ⚠️ IP 必须添加到微信公众号后台白名单！

**发布命令**：
```bash
# 基础发布
node /root/skills/wechat-mp-suite/scripts/publisher/publish.js article.md

# wenyan-cli 直接发布
wenyan publish -f article.md -t lapis -h solarized-light

# 含视频文章
node /root/skills/wechat-mp-suite/scripts/publisher/publish_with_video.js article.md
```

---

### 方式二：远程 MCP 发布（推荐家庭宽带）

**解决痛点**：家庭宽带 IP 频繁变动，无法固定添加到白名单。

**配置步骤**：

**1. 准备 wechat.env**

```bash
cp /root/skills/wechat-mp-suite/scripts/publisher/wechat.env.example /root/skills/wechat-mp-suite/scripts/publisher/wechat.env
nano /root/skills/wechat-mp-suite/scripts/publisher/wechat.env
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

**3. 运行 setup.sh（首次）**

```bash
bash /root/skills/wechat-mp-suite/scripts/publisher/setup.sh
```

**4. 发布**

```bash
# 赋予执行权限
chmod +x /root/skills/wechat-mp-suite/scripts/publisher/publish-remote.sh

# 发布
/root/skills/wechat-mp-suite/scripts/publisher/publish-remote.sh article.md

# 指定主题
/root/skills/wechat-mp-suite/scripts/publisher/publish-remote.sh article.md lapis
```

---

## Markdown 格式要求

所有发布文件必须包含 frontmatter：

```markdown
---
title: 文章标题（必填）
cover: /absolute/path/to/cover.jpg（必填，绝对路径）
---

# 正文...
```

**关键要求**：
- `title` 和 `cover` **缺一不可**
- 所有图片路径必须使用**绝对路径**

---

## 完整工作流

### 工作流 1：搜索 → 洗稿 → 排版 → 发布

```bash
# 1. 搜索文章
node /root/skills/wechat-mp-suite/scripts/search/search_wechat.js "AI教程" -n 5 -c

# 2. 使用 OpenClaw 洗稿（自然语言指令）
# "帮我洗稿这篇文章"

# 3. 排版
node /root/skills/wechat-mp-suite/scripts/typeset/wechat-dual-copy.js article.md

# 4. 发布
node /root/skills/wechat-mp-suite/scripts/publisher/publish.js article.md
```

### 工作流 2：爬虫 → 写作 → 排版 → 远程发布

```bash
# 1. 爬虫下载
python3 /root/skills/wechat-mp-suite/scripts/spider/main.py https://mp.weixin.qq.com/s/xxx ./output

# 2. 使用 OpenClaw 写作（自然语言指令）
# "用刘润风格改写这篇文章"

# 3. 排版
node /root/skills/wechat-mp-suite/scripts/typeset/wechat-dual-copy.js article.md

# 4. 远程发布
/root/skills/wechat-mp-suite/scripts/publisher/publish-remote.sh article.md
```

---

## 项目结构

```
wechat-mp-suite/
├── SKILL.md                        # OpenClaw Skill 定义
├── README.md                       # 使用手册
├── references/
│   ├── USAGE.md                    # 本文件
│   ├── SPEC.md                     # 排版规范
│   ├── typeset-guide.md            # 排版详细指南
│   └── remote-publisher-guide.md   # 远程发布指南
└── scripts/
    ├── search/                     # 搜索模块
    │   └── search_wechat.js
    ├── downloader/                 # 下载模块
    │   └── download.js
    ├── spider/                     # 爬虫模块
    │   ├── main.py
    │   └── requirements.txt
    ├── publisher/                  # 发布模块
    │   ├── publish.js              # 本地发布
    │   ├── publish_with_video.js   # 含视频发布
    │   ├── publish-remote.sh       # 远程MCP发布
    │   └── setup.sh                # 远程发布配置
    └── typeset/                    # 排版模块
        ├── wechat-dual-copy.js     # 一键双版本排版
        ├── html-to-wechat-copy.js  # 单版本排版
        ├── SPEC.md                 # 排版规范
        └── lib/                    # 依赖库
```

---

## 故障排查

| 问题 | 解决方法 |
|------|---------|
| IP 不在白名单 | `curl ifconfig.me` → 添加到公众号后台 |
| wenyan 未安装 | `npm install -g @wenyan-md/cli` |
| 环境变量未设置 | `export WECHAT_APP_ID=xxx` |
| 缺少 frontmatter | 添加 `title` + `cover` 字段 |
| 40001 token 失效 | 使用 `publish_with_video.js` |
| 爬虫抓取失败 | 稍后重试，可能被反爬 |
| 远程发布失败 | 检查 MCP 服务器是否运行 |

---

## 注意事项

- 所有工具仅供**个人学习**使用，请遵守相关版权法规
- 搜索功能内置防封禁机制（随机 UA、请求延迟），请勿高频使用
- 微信公众号发布需确保内容合规，遵守平台规则
- 本地发布需添加本机IP到白名单
- 远程MCP发布需添加服务器IP到白名单
