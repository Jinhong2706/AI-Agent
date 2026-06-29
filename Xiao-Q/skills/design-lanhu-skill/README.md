<div align="center">

# 🎯 DesignLanhu Skill | 蓝湖像素还原 Agent Skill

**以 Schema 为唯一真相，将蓝湖设计稿交付为可维护、可验收的生产级 UI 代码**

**design-lanhu | 蓝湖 Skill | Lanhu Agent Skill | 设计稿转代码 | Claude Code | Cursor Skills | 像素级还原 | Design Tokens | 蓝湖 Schema | DESIGN.md | 设计系统继承**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Agent Skill](https://img.shields.io/badge/Agent%20Skill-Claude%20%2F%20Compatible-663399.svg)](https://github.com/tiandashu/design-lanhu-skill)
[![HTTPX](https://img.shields.io/badge/HTTPX-Async%20HTTP-009688.svg)](https://www.python-httpx.org/)
[![Lanhu](https://img.shields.io/badge/平台-蓝湖%20Lanhu-FF6A00.svg)](https://lanhuapp.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/tiandashu/design-lanhu-skill/pulls)
[![GitHub Stars](https://img.shields.io/github/stars/tiandashu/design-lanhu-skill?style=social)](https://github.com/tiandashu/design-lanhu-skill/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/tiandashu/design-lanhu-skill)](https://github.com/tiandashu/design-lanhu-skill/issues)
[![GitHub Release](https://img.shields.io/github/v/release/tiandashu/design-lanhu-skill?label=release)](https://github.com/tiandashu/design-lanhu-skill/releases)

[English](README_EN.md) | 简体中文

[项目亮点](#-项目亮点) • [核心特性](#-核心特性) • [快速开始](#-快速开始) • [使用指南](#-使用指南) • [DESIGN.md](#-designmd-设计系统继承) • [产出物说明](#-产出物说明) • [安全与合规](#-安全与合规) • [常见问题](#-常见问题)

</div>

---

## 🌟 项目亮点

**DesignLanhu Skill** 是一套面向 **AI 编程工作流** 的正式交付规范：将蓝湖（Lanhu）设计链路中的 **结构化 Schema**、**高风险视觉 Tokens** 与 **切图资源** 一次性拉取到本地，并由 Agent 按既定工程准则生成目标框架代码。与「凭感觉写界面」不同，本项目强调 **可度量、可对照、可回归** 的还原路径。

🔥 **核心创新**

- 📐 **Schema 单一真相源（SSOT）**：所有尺寸、颜色、定位、字体与布局数值以 `.schema.json` 为准；可选官方 HTML/CSS 仅作结构与漏项对照，杜绝「抄 class 名、改数值」的反模式。
- 🧩 **六阶段闭环工作流**：列表选图 → 拉取数据 → 探测工程栈与移动端适配 → 解析 Schema 生成代码 → Tokens 补缺 → **强制还原度自检清单**，显著降低 AI 产出漂移。
- 🎨 **复杂样式专项规约**：多段渐变、非均匀圆角、叠加阴影、opacity 与填充叠加、`flexGap`、flex 与 padding 冲突等均有明确条文，保证与设计稿语义一致。
- 🏗️ **工程化默认最佳实践**：语义化 **BEM**、克制的组件拆分策略、本地资源路径（禁止蓝湖 CDN 直连进业务代码），便于 Code Review 与长期维护。
- 📘 **DESIGN.md 设计系统继承（可选）**：若目标仓库根目录存在 `DESIGN.md`（或团队约定的同等职责文档），Agent 在解析 Schema 与落盘代码前**必须先读**，在**视觉等价**前提下将实现映射到设计令牌、主题、排版刻度、复用组件与目录/命名规范，避免「单页还原却与全站设计体系脱节」。
- 🔌 **Skill 原生集成、零 MCP 依赖**：一条蓝湖 URL 即可驱动；可与社区 [**Lanhu MCP Server**](https://github.com/dsphper/lanhu-mcp) 并存——MCP 负责平台级协作与上下文，本 Skill 负责 **把一页 UI 落到你的仓库**。

🎯 **适用场景**

- ✅ **Claude Code / Cursor** 等支持 Agent Skills 的客户端，需在真实仓库中落地蓝湖页面级还原。
- ✅ 团队使用 **React / Vue / Nuxt / Flutter / Android / iOS**，希望 AI 输出与现有样式体系（CSS Modules、Tailwind、SCSS 等）对齐。
- ✅ 对 **还原度与可维护性** 有验收标准，需要「对照 Schema 能说清楚为什么这样写」。
- ✅ 仓库中已有 **`DESIGN.md` 设计系统说明**，希望蓝湖落地页与令牌、主题、组件库约定保持一致。

🎯 **解决的痛点**

- ❌ **旧路径**：只看截图或泛型导出代码，数值被四舍五入、渐被简化、远程图链残留，难以维护。
- ✅ **新路径**：Schema 驱动 + Tokens 兜底 + PNG 帧对齐可见图层 + 自检清单，交付 **可审计** 的前端实现。

---

## 📑 目录

- [项目亮点](#-项目亮点)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [使用指南](#-使用指南)
- [DESIGN.md 设计系统继承](#-designmd-设计系统继承)
- [产出物说明](#-产出物说明)
- [与 Lanhu MCP 协同](#-与-lanhu-mcp-协同)
- [安全与合规](#-安全与合规)
- [常见问题](#-常见问题)
- [免责声明](#-免责声明)
- [关键词索引](#-关键词索引)

---

## ✨ 核心特性

### 🎨 设计数据获取

| 能力               | 说明                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| 设计图枚举         | 基于蓝湖项目/画板 URL，输出 `designs` 列表（序号 + 完整名称），便于确认还原范围                        |
| Schema 拉取        | 下载图层树与样式 JSON，作为代码生成的 **唯一数值权威**                                                 |
| Design Tokens 摘要 | 输出 `.tokens.txt`，聚焦渐变、阴影、描边、圆角、透明度等高风险属性                                     |
| 资源本地化         | 支持切图与设计图 PNG 下载，并生成本地路径与远程 URL 的映射表                                           |
| 官方代码（可选）   | `--download-code` 获取蓝湖导出的 HTML/CSS，**仅作对照**；默认不建议主动开启（耗时、且不可替代 Schema） |

### 🤖 Agent 工作流（见 `SKILL.md`）

- **框架探测**：依据 `package.json`、`pubspec.yaml`、原生工程文件等识别技术栈；无法识别时回退为单文件 HTML 策略。
- **移动端适配对齐**：结合 Schema 中 `designType`、画板宽高与项目内 rem/vw/PostCSS 配置，统一输出单位策略。
- **可见性裁剪**：以设计图 PNG 当前帧为准，跳过不可见或被完全遮挡的图层（除非用户明确要求多状态/蒙层）。
- **还原度核查**：生成后逐项对照 Schema，区分「平台有意差异」与「实现偏差」，偏差必须修正；若存在 `DESIGN.md`，自检清单包含是否已继承设计系统（见下节）。

### 📘 DESIGN.md 设计系统继承

当**目标项目**（你要写入代码的仓库）根目录存在 **`DESIGN.md`**，或文档中明确指定了承担同一职责的设计说明文件时，Agent 在解析 Schema、拆分组件与写入文件前**必须先读取**，并在全流程遵守其中约定。适用范围包括但不限于：

| 类别       | 示例                                               |
| ---------- | -------------------------------------------------- |
| 令牌与主题 | 色板、语义色、暗色模式、CSS 变量命名               |
| 排版与刻度 | 字阶、行高、间距与圆角阶梯                         |
| 组件与复用 | 基础组件、变体、何时封装子组件                     |
| 工程约定   | 目录结构、文件命名、BEM/框架惯例、无障碍与交互规范 |

**与 Schema 的分工（必读）**

- **图层级的具体数值**（尺寸、颜色、定位、字体大小等）仍以拉取得到的 **`.schema.json` 为唯一权威来源**。
- **`DESIGN.md`** 负责在**视觉等价**前提下，将实现**映射**到系统 token、既有基础组件与共享样式，并落实 Schema 无法单独表达的全局规则。

**冲突时如何处理**

1. 若 `DESIGN.md` 中已写明冲突处理策略 → **按文档执行**。
2. 若无说明 → **以 Schema 数值优先保证当前屏还原度**，并在回复中简要说明取舍。

完整条文与自检第 13 项见根目录 **`SKILL.md`**（STEP 3 / STEP 6）。

---

## 🚀 快速开始

### 环境要求

- **Python 3.10+**
- 有效的 **蓝湖网页端登录 Cookie**（与账号权限一致）

### 安装依赖

```bash
git clone https://github.com/tiandashu/design-lanhu-skill.git
cd design-lanhu-skill
pip install -r requirements.txt
```

### 配置凭证（任选其一）

```bash
export LANHU_COOKIE="your_lanhu_cookie_here"
```

或复制 `.env.example` 为 `.env` 并填写 `LANHU_COOKIE=`；亦可在命令行使用 `--cookie`。

> ⚠️ **重要**：建议使用具备 **视觉理解能力** 的模型配合本 Skill（对照 PNG 与复杂布局时更稳）。纯文本弱模型可能遗漏视觉层面的裁剪与验收要点。

### 方式一：作为 Claude Code / 兼容客户端的 Skill（推荐）

1. 将本仓库安装为 Skill，确保根目录存在 `SKILL.md`。
2. 在对话中提供蓝湖设计稿 URL，例如：
   `https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx`
3. Agent 将注入 **`${CLAUDE_SKILL_DIR}`**，并调用
   `${CLAUDE_SKILL_DIR}/scripts/fetch_lanhu.py`
   按 **STEP 1 → STEP 6** 执行完整流水线。

完整约束、变量表与禁止项以 **`SKILL.md`** 为唯一规范。

### 方式二：命令行直接使用

**列出设计图：**

```bash
python scripts/fetch_lanhu.py --url "https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx"
```

**拉取指定设计（含图片资源）：**

```bash
python scripts/fetch_lanhu.py \
  --url "https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx" \
  --design "1" \
  --download-images \
  --output-dir ./lanhu_output
```

`--design` 支持 **序号** 或设计图 **完整名称**。仅在用户明确要求时追加 `--download-code`。

---

## 📖 使用指南

### 推荐对话示例（Skill）

```
请按 design-lanhu Skill 还原这一页，蓝湖链接是：
https://lanhuapp.com/web/#/item/project/stage?tid=xxx&pid=xxx
目标框架与样式方案请自动读取我当前仓库。
```

### 与蓝湖「设计稿转代码」的关系

建议在蓝湖侧开启 **设计稿转代码** 能力，以便在需要时使用官方导出作对照；**数值仍以 Schema 为准**。若转换异常，可协调设计同学升级插件后重新上传（与 [Lanhu MCP 文档](https://github.com/dsphper/lanhu-mcp/blob/main/README.md) 中建议一致）。

### 启用 DESIGN.md（推荐有设计系统的团队）

在**业务仓库根目录**维护 `DESIGN.md`，集中描述设计令牌、主题、排版、复用组件与工程约定。使用本 Skill 还原蓝湖页面时，Agent 会自动识别并优先对齐该文档，使新页面与存量 UI 体系一致。

**推荐对话示例：**

```
请按 design-lanhu Skill 还原这一页。蓝湖链接：…
请先阅读我仓库根目录的 DESIGN.md，再生成代码，令牌与组件请尽量复用文档中的约定。
```

---

## 📦 产出物说明

默认输出目录为 `--output-dir`（缺省 `./lanhu_output`）。

| 文件                                     | 职责                                                 |
| ---------------------------------------- | ---------------------------------------------------- |
| `<名称>.schema.json`                     | **权威数据源**：代码中所有度量与样式数值的最终依据   |
| `<名称>.tokens.txt`                      | 高风险视觉属性摘要；仅在 Schema 明显缺失时补充       |
| `<名称>.png`                             | 整图预览；用于对齐「当前帧可见内容」                 |
| `assets/slices/img_N.png`                | 切图等资源文件                                       |
| `<名称>.image_mapping.json`              | 本地路径 ↔ 远程 URL 映射                             |
| `<名称>.official.html` / `.official.css` | 仅当使用 `--download-code` 时生成，**结构/漏项参考** |

> **说明**：上表为 `fetch_lanhu.py` 拉取蓝湖后的**本地产物**。**`DESIGN.md`** 不属于脚本输出，而是由你在目标仓库中维护的**项目设计系统文档**；Skill 仅读取并遵守其约定。

---

## 🔒 安全与合规

- ⚠️ **Cookie 等同于账号凭证**：禁止将 `.env`、含 Cookie 的配置提交至公开仓库。
- 🔐 **最小权限原则**：使用具备项目访问权限的账号；定期轮换 Cookie。
- 📝 **数据本地优先**：拉取内容默认落在本地输出目录，请按公司规范管理备份与清理。

---

## ❓ 常见问题

<details>
<summary><b>Q：Cookie 失效怎么办？</b></summary>

在浏览器重新登录蓝湖，从开发者工具复制最新 `Cookie`，更新环境变量或 `.env`。

</details>

<details>
<summary><b>Q：还原效果与设计稿不一致？</b></summary>

请按优先级排查：① 是否以 `.schema.json` 为数值来源；② `.png` 可见图层是否与生成范围一致；③ 复杂样式是否对照 `.tokens.txt` 与 `SKILL.md` 自检清单。

</details>

<details>
<summary><b>Q：没有 React / Vue 时会怎样？</b></summary>

Skill 将尝试探测工程类型；无法识别时采用 **单文件 HTML** 策略，详见 `SKILL.md`。

</details>

<details>
<summary><b>Q：有 DESIGN.md 时，颜色和间距以谁为准？</b></summary>

**图层上的具体数值**仍以 `.schema.json` 为准，以保证该屏与蓝湖一致；`DESIGN.md` 用于在视觉等价前提下映射到设计令牌、主题变量与既有组件。二者冲突时按 `DESIGN.md` 中的冲突说明处理；无说明则以 Schema 保还原度为主，并在答复中说明取舍（详见 `SKILL.md`）。

</details>

---

## ⚠️ 免责声明

本项目为 **第三方开源技能与工具脚本**，**并非蓝湖官方产品**，与蓝湖公司无隶属或合作关系。使用需遵守 [蓝湖](https://lanhuapp.com/) 服务条款；您应自行确保对目标项目拥有合法访问权限。作者不对因使用本项目导致的账号风险、数据丢失或合规问题承担责任。详见仓库内许可证（如有）。

---

## 🏷️ 关键词索引

**中文**：蓝湖 Skill | 蓝湖 Agent Skill | 设计稿转代码 | 像素级还原 | Schema 还原 | Claude Code 蓝湖 | Cursor 蓝湖 | design-lanhu | 蓝湖切图 | Design Tokens | DESIGN.md | 设计系统文档 | 设计令牌继承 | 前端还原规范 | BEM 自动化 | 多框架 UI 生成

**English**：Lanhu skill | Lanhu design to code | Agent Skill | Claude Code | pixel-perfect UI | design schema | design tokens | frontend codegen | Cursor skills

---

<p align="center">
  若本项目对你的团队有帮助，欢迎点亮 ⭐️ 并分享给更多开发者
</p>

<p align="center">
  <b>DesignLanhu Skill</b> — Schema-first，工程级蓝湖还原
</p>
