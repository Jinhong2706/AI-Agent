---
name: browser-skill-creator
description: Use when/适用于：用户提供一个网站 URL 和期望的操作或结果描述，需要通过浏览器录制请求、分析数据，然后沉淀为一个可复用的新 skill（含 SKILL.md 和脚本）。
---

# Browser Skill Creator — 浏览器录制 & Skill 生成工作流

依赖技能: `mtop-devtools-socket`

## 前置依赖

1. 安装全局 CLI：`npm install -g @mtop-devtools/native-host @mtop-devtools/client`

## 适用场景

用户想要创建一个新的 skill，该 skill 的核心逻辑是：访问某个网站 → 获取/分析请求数据。例如：

- "帮我做一个 skill，能从 xxx 平台拉取我的待办列表"
- "我想沉淀一个 skill，自动抓取 xxx 系统的报表数据"
- "帮我录制一下访问 xxx 页面时的接口调用，生成一个可复用的 skill"

## 核心流程

本 skill 不包含脚本，所有能力均来自 `mtop-devtools-socket`。

> ⛔ **全流程工具约束**：本 skill 创建过程中，所有浏览器交互（打开页面、抓请求、点击、执行 JS、获取页面内容等）**只允许**使用 `mtop-devtools` 命令，**严禁**使用 puppeteer、playwright、curl 抓页面、其他 MCP 浏览器工具等任何 `mtop-devtools` 之外的浏览器控制能力。

### 步骤一：收集信息

从用户输入提取：
- **url**（必填）：目标网站地址
- **description**（必填）：期望的操作或结果描述
- **skill-name**（可选）：未提供时从 description 推导（kebab-case）

### 步骤二：打开页面 & 等待用户操作

1. 使用 `mtop-devtools tab_open` 打开目标网站：

```bash
mtop-devtools tab_open --payload '{"url": "https://example.com/dashboard", "active": true, "closeExisting": true}'
```

2. **必须停下来等待用户确认**：提示用户在页面上完成期望录制的操作（点击、搜索、翻页等），操作完成后告诉 Agent 继续。**严禁跳过等待直接抓取请求。**

### 步骤三：抓取请求

用户确认操作完成后，使用 `mtop-devtools get_requests` 抓取请求数据。使用步骤二中 `tab_open` 返回的 `tabId` 指定目标 tab：

```bash
# 抓取 mtop 请求
mtop-devtools get_requests --payload '{"count": 100, "source": "mtop", "tabId": 12345}'

# 抓取普通 HTTP 请求
mtop-devtools get_requests --payload '{"count": 100, "source": "requests", "tabId": 12345}'
```

- **必须同时抓取 mtop 和 HTTP 两种请求**，不要只抓一种，以免遗漏
- 如果请求数量为 0，提示用户检查操作时是否有网络请求发出，或等待几秒后重试
- **如果找不到用户期望的请求数据**，使用 `mtop-devtools tab_list --payload '{}'` 列出所有标签页，让用户确认应该从哪个 tab 获取，再用对应 tabId 重新抓取

### 步骤四：分析请求（⚠️ 关键步骤）

只关注业务接口（忽略 script、stylesheet、image、埋点等），按类型筛选并**根据类型确定唯一调用方式**：

| 类型 | 来源 | 生成 skill 的唯一调用方式 |
|------|------|---------------------------|
| mtop | `source: "mtop"` | `mtop-devtools send_mtop_request` |
| xhr / fetch | `source: "requests"`，`resourceType` 为 `xhr`/`fetch` | `mtop-devtools proxy_request` |
| document（HTML 页面/SSR 数据） | `resourceType: "document"` | `mtop-devtools proxy_request`（直接 GET 该 URL 拿 HTML，再用脚本解析）|

> ⛔ **document 类型的硬约束**：即使原始请求是浏览器导航产生的，生成的 skill **必须**用 `proxy_request` 直接 HTTP 请求拿 HTML/JSON，**严禁**用 `tab_open` + `page_eval` / `page_snapshot` 的方式去打开 tab 抓页面内容。`proxy_request` 会自动携带浏览器 Cookie，登录态不是问题。

**必须输出结构化分析报告**后才能进入下一步，包含：

1. **关键 API 表格**：列出与用户需求相关的接口（类型、API/URL、用途、**确定的调用方式**），相同接口去重
2. **参数分析**：每个 API 区分固定参数和可变参数（可变部分 → skill 输入参数），列出响应关键字段路径
3. **Skill 设计**：**唯一**的实现方案（不要给备选），包含：调用命令、输入参数、输出格式

> mtop 接口可用 `mtop-devtools get_api_schema --payload '{"api": "mtop.xxx.query", "version": "1.0"}'` 获取 schema 辅助分析。

### 步骤五：生成 Skill

基于分析报告生成 skill 文件。

#### ⛔ 硬性约束（必须遵守）

1. **纯 HTTP 调用**：所有数据获取**必须**通过 `mtop-devtools proxy_request`（HTTP/document）或 `mtop-devtools send_mtop_request`（mtop）完成。**严禁**在生成的 skill 中使用 `tab_open`、`page_click`、`page_eval`、`page_snapshot`、`page_navigate` 等任何浏览器操作来获取业务数据
2. **单一方案**：每个数据需求只给出**一套**确定的实现方式，**禁止**在 SKILL.md 中写"方案 A / 方案 B"、"也可以用 xxx"、"或者用 xxx" 等多套备选方案，避免增加用户理解成本
3. **只用 mtop-devtools**：生成的 skill **只允许**依赖 `mtop-devtools-socket`，**严禁**引入 puppeteer、playwright、axios、node-fetch、curl 等其他网络/浏览器依赖
4. **禁止硬编码**：用户给出的具体 URL、ID、关键词等**禁止写死**，必须参数化
5. **描述一类场景**：SKILL.md 的 description / 适用场景**禁止出现具体链接或参数值**，应描述通用操作意图
6. **脚本接受外部输入**：通过 `process.argv` 接收可变值，可选参数提供合理默认值

##### 唯一例外：登录态前置

如果分析时发现接口需要先登录（302 跳 SSO、响应含 `loginUrl` 等），生成的 skill **可以**在「实施步骤」开头加一段前置：用 `mtop-devtools tab_open` 打开登录页，等用户完成登录后再调用业务 API。这是**唯一**允许在生成 skill 中出现 `tab_open` 的场景，且仅用于登录，不得用于抓数据。

#### 生成文件

生成的 skill 目录结构应为：

```
packages/skills/<skill-name>/
├── SKILL.md              # skill 描述文档
└── scripts/              # 可选
    └── <skill-name>.mjs  # 数据抓取脚本
```

#### SKILL.md 必须包含的结构

```markdown
---
name: <skill-name>
description: Use when/适用于：<一句话描述适用场景，不含具体链接>
argument-hint: <参数提示，如：<keyword> [--page <n>]>
---

# <Skill 标题>

依赖技能: `mtop-devtools-socket`

## 前置依赖

1. 安装全局 CLI：`npm install -g @mtop-devtools/native-host @mtop-devtools/client`

## 适用场景
<列出 3+ 种用户输入模式>

## 实施步骤
<具体的命令/脚本调用方式、参数说明、输出格式>

## 错误处理
<常见错误及处理方式>
```

#### 实现方式选择（二选一，不能并存）

根据接口数量决定**唯一**的实现形态：

- **接口 = 1 个，且无需后处理**：不写脚本，直接在 SKILL.md 的「实施步骤」中给出**一条** `mtop-devtools` 命令及参数说明
- **接口 ≥ 2 个，或需要数据合并/解析**：写**一个** `scripts/<skill-name>.mjs`，内部用 `child_process.execSync` 调 `mtop-devtools proxy_request` / `send_mtop_request`，输出结构化 JSON

**禁止**两种方式同时给出，**禁止**在文档中描述"你也可以手动调用 mtop-devtools 命令"等并行方案。

### 步骤六：验证 & 修复

生成 skill 后，**必须使用步骤四中分析到的真实请求参数**进行端到端验证：

1. **运行脚本/命令**：按生成的 SKILL.md 中的实施步骤，用真实参数调用脚本或 `mtop-devtools` 命令
2. **检查输出**：确认返回的数据结构与分析报告中描述的一致，且包含用户关心的字段
3. **修复问题**：如果调用失败或输出不符合预期，分析原因并修复脚本/SKILL.md，然后重新验证，直到通过
4. **向用户展示结果**：将验证通过的输出展示给用户确认

## 常见问题处理

- **需要登录**：提示用户先在浏览器中登录目标网站，再继续流程
- **抓取到 0 个请求**：提示用户检查操作时是否有网络请求发出，或等待几秒后重试
- **请求太多，难以识别**：让用户描述更具体的操作，或按关键词过滤
- **需要域名授权**：生成的 skill 如果使用 `proxy_request`，引导用户在扩展 Options 页「Agent Service > Domain Permissions」添加目标域名
- **跳转登录（SSO/OAuth）**：如果分析请求时发现 302/307 重定向到 login 域名、响应含 `loginUrl`/`authUrl` 字段等，说明需要先获取登录态。生成的 skill 应在实施步骤中增加前置步骤：先用 `mtop-devtools tab_open` 打开登录链接完成认证，再调用业务 API（这是 `tab_open` 在生成 skill 中的唯一合法用途）
- **想抓 HTML 页面内容**：不要用 `tab_open` + `page_snapshot`/`page_eval`，直接 `mtop-devtools proxy_request --payload '{"url":"<page-url>","method":"GET"}'` 拿 HTML 字符串，再在脚本里用正则解析（解析逻辑写进脚本，不要依赖浏览器）
