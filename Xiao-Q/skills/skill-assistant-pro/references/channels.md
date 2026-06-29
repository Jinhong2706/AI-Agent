# Skills 搜索源完整参考

> 当搜索某源无结果时，切换到下一个源尝试。

## 源分类

源分为两大类 + 通用搜索兜底：

| 类别 | 定位 | 代表 | 独有价值 |
|------|------|------|---------|
| **平台型技能市场** | 收录第三方来源的 Skill，提供独有质量信号 | skills.sh、SkillsMP、ClawHub、SkillHub | 安装量/评分/认证/语义搜索 |
| **GitHub 优质仓库** | 高质量 Skill 源码或策展索引 | anthropics/skills、awesome-openclaw、awesome-claude-skills、obra/superpowers | Stars/作者声誉/社区策展 |
| **通用搜索** | 兜底覆盖 | GitHub code search | 全量覆盖 |

**三层架构**：

| 层级 | 定义 | 示例 |
|------|------|------|
| **搜索入口** | 在哪里发现/检索 Skill | 平台 API、GitHub 搜索、awesome-list |
| **存放源** | Skill 文件实际存储在哪里 | GitHub（绝大多数）、ClawHub registry |
| **获取方式** | 用什么手段拿到文件 | `install_skill.sh`（推荐，含 `_skill_meta.json`）、`git clone`、平台 CLI |

> 平台型市场和 GitHub 仓库搜索到同一个 Skill 是正常的——多源交叉验证是质量信号。

## 版本管理

每个已安装 Skill 目录下生成 `_skill_meta.json`（而非 `_meta.json`，避免与 SkillHub/ClawHub 自带的 `_meta.json` 冲突），
记录来源、版本、commit hash、安全扫描结果。支持按 Skill 粒度追踪和更新检测。

## 一、官方渠道

### Cursor Marketplace

- **定位**：Cursor 官方市场，人工审核，质量最高
- **规模**：含 Datadog、Slack、Figma、Linear 等大厂合作插件
- **安全等级**：✅ 高
- **官网**：[cursor.com/marketplace](https://cursor.com/marketplace)

### Anthropic 官方技能仓库

- **定位**：SKILL.md 规范的参考实现
- **规模**：106K+ stars，覆盖 PDF/DOCX/PPTX/XLSX 处理、Claude API、MCP 构建、前端设计
- **安全等级**：✅ 高
- **GitHub**：[anthropics/skills](https://github.com/anthropics/skills)

### Cursor 官方文档

- **定位**：SKILL.md 规范的权威说明
- **官网**：[cursor.com/docs/skills](https://cursor.com/docs/skills)

### prompts.chat 注册表

- **定位**：独立的 Skill 注册表，通过 MCP 工具访问
- **特点**：支持分类、标签过滤，结构化 API 返回（含文件列表）
- **安全等级**：⚠️ 中
- **MCP 工具**：`search_skills`（搜索）、`get_skill`（获取详情和文件）

---

## 二、主流市场平台（2026 年格局）

> 2026 年 MCP (Model Context Protocol) 已成主流协议。ClawHub 和 skills.sh 已全面支持 MCP，技能不仅是 Prompt，还可能包含自动运行的轻量服务器。

### skills.sh — 追求精品首选

- **运营方**：Vercel 官方（2026.01 推出）
- **规模**：91,000+ Skills
- **核心优势**：经团队审核，技能质量极高；沙盒执行环境，推理与执行分离；适合集成 CI/CD
- **特点**：热度排行榜、18+ AI Agent 支持、类"应用商店"体验、全面支持 MCP
- **安全等级**：⚠️ 中偏高（Vercel 审核机制）
- **搜索 CLI**：`npx skills find <关键词>`
- **安装**（推荐 `install_skill.sh`，含安全扫描 + telemetry 通知 skills.sh）：
  ```bash
  bash scripts/install_skill.sh https://github.com/<owner>/<repo> <skill-name>
  # 降级：git clone --depth 1 https://github.com/<owner>/<repo>.git && 手动复制
  ```
- **降级链路**（CLI → curl API，仅两级）：

  | 降级层级 | 方式 | 命令 | 说明 |
  |:--------:|------|------|------|
  | 优先级 1 | CLI | `npx skills find "<关键词>"` | 自带后处理（`limit=10` + `installs` 降序 + Top 6） |
  | 优先级 2 | curl API | `curl -s "…/api/search?q=<关键词>&limit=10" \| python3 排序脚本` | 需手动复现 CLI 后处理 |
- **生命周期**：唯一支持完整 check/update/remove 的安装渠道（通过 `.skill-lock.json` + GitHub Trees API）
- **官网**：[skills.sh](https://skills.sh)
- **适合**：追求极简、安全、高性能的开发者

### ClawHub — 数量最全首选

- **定位**：OpenClaw 官方 registry，事实上的行业标准（类比 npm/apt）
- **规模**：13,000+ Skills（清理恢复后）
- **核心优势**：向量搜索 + 自然语言描述匹配，版本管理成熟，全面支持 MCP
- **安全等级**：⚠️ 中 — 2026.02 **ClawHavoc 安全事件**后已加强审核，但仍允许任何人发布
- **安全建议**：优先选择带 **Verified** 标识或下载量 TOP 100 的技能。近期 Silverfort 指出恶意技能可能通过篡改排名进行钓鱼
- **CLI**：
  ```bash
  clawhub search "<关键词>"
  clawhub inspect <skill-name>    # 安装前查看详情
  clawhub install <skill-name>
  ```
- **官网**：[claw-hub.net](https://claw-hub.net/)
- **适合**：使用 OpenClaw / Claude Code 的重度用户

### SkillsMP — 跨领域灵感首选

- **定位**：全能型技能市场，兼容性最广
- **规模**：66,500+ Skills
- **核心优势**：不仅有 Code 技能，还有办公自动化技能；分类、热度排行和趋势查看
- **特点**：自然语言搜索、model-invoked skills、多 Skills 并行执行、Trending 榜单
- **安全等级**：⚠️ 中（最低 2-star GitHub 过滤）
- **搜索**：网站 [skillsmp.com](https://skillsmp.com)
- **适合**：需要跨平台、跨领域寻找灵感的用户

---

## 三、社区与开源渠道

### awesome-openclaw-skills 精选合集

- **定位**：社区精选的 OpenClaw Skills 合集
- **规模**：5,400+ Skills
- **GitHub**：[VoltAgent/awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills)
- **安全等级**：⚠️ 中（需看具体 Skill）

### Awesome Claude Skills (Composio) — 第三方服务连接首选

- **定位**：500+ 应用连接能力合集，4.7K+ Stars
- **核心优势**：Composio 工具层支持 1000+ 预建工具，处理 OAuth 鉴权极为专业
- **适合**：需要 Agent 操作 Slack、Notion、Gmail、GitHub 等第三方服务的用户
- **GitHub**：[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)

### 其他社区目录

| 名称 | 定位 | 地址 |
|------|------|------|
| cursor.directory | Cursor 插件 / MCP 目录 | [cursor.directory](https://cursor.directory/) |
| CursorList | .cursorrules 按技术栈分类 | [cursorlist.com](https://cursorlist.com/) |
| Awesome CursorRules | 精选 .cursorrules 合集 | [mdskills.ai](https://www.mdskills.ai/rules/awesome-cursorrules) |

### 高质量 GitHub 仓库

| 仓库 | Stars | 核心价值 | 安全评估 |
|------|-------|---------|---------|
| [anthropics/skills](https://github.com/anthropics/skills) | 106K+ | SKILL.md 规范参考 | ✅ 高 |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 100K+ | 完整 Agent 优化系统 | ✅ 高 |
| [PatrickJS/awesome-cursorrules](https://github.com/PatrickJS/awesome-cursorrules) | 38K+ | 最流行 Rules 合集 | ✅ 高 |
| [shanraisshan/claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) | 27K+ | 84 条最佳实践 | ✅ 高 |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 10K+ | TypeScript 专家出品 | ✅ 高 |

---

## 四、国内渠道

### 腾讯 SkillHub

- **定位**：面向中国用户的本地化镜像站
- **规模**：整合 13,000+ OpenClaw 生态 Skills
- **特点**：中文搜索、国内镜像分发

---

## 五、安全与防护工具

| 工具 | 用途 | 地址 |
|------|------|------|
| Chainguard Agent Skills | 企业级供应链安全加固 | [chainguard.dev](https://www.chainguard.dev/) |
| dwarvesf/claude-guardrails | Shell 安全防护 | [GitHub](https://github.com/dwarvesf/claude-guardrails) |
| GoPlusSecurity/agentguard | 三层实时安全防护 | [GitHub](https://github.com/GoPlusSecurity/agentguard) |

---

## 六、Skills 本地存放路径

| 层级 | 路径 | 适用 IDE |
|------|------|----------|
| 项目级 | `.cursor/skills/` | Cursor |
| 项目级 | `.agents/skills/` | 通用 |
| 用户全局级 | `~/.cursor/skills/` | Cursor |
| Claude 兼容 | `.claude/skills/` | Claude Code |

---

## 七、按需求选择源

| 需求 | 推荐源 | 类别 | 理由 |
|------|--------|------|------|
| 找最精、最稳的 | skills.sh | 平台 | Vercel 审核，91K+，质量极高 |
| 找最多、最全的 | SkillsMP | 平台 | 700K+ 聚合，按 Stars 排序 |
| 连接第三方服务 | awesome-claude-skills | 仓库 | 500+ App OAuth 集成 |
| 官方高质量 | Anthropic 官方 | 仓库 | SKILL.md 规范标杆，108K Stars |
| 安全验证 | Cursor Marketplace > skills.sh | 平台 | 经审查 |
| 国内加速 | 腾讯 SkillHub | 平台 | OpenClaw 镜像 |
| OpenClaw 精选 | awesome-openclaw | 仓库 | 5.4K+ 策展，43.5K Stars |

### 按角色推荐

| 角色 | 首选渠道 |
|------|---------|
| 开发者 | ClawHub 或 skills.sh |
| 普通用户/办公族 | SkillsMP |
| 需要连接外部服务 | Awesome Claude Skills (Composio) |
| 追求安全 | Cursor Marketplace > skills.sh |
