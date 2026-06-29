# 推荐模块

泛化推荐请求（"推荐适合我的 skill"、"有什么好用的 skill"）时启用。已安装的 Skill 和收藏列表是用户画像的核心信号。

---

## R1：多信号环境扫描（并行执行）

```
Tool call 1: ls -1 ~/.cursor/skills/ 2>/dev/null; echo "---"; ls -1 .cursor/skills/ 2>/dev/null; echo "---"; ls -1 ~/.agents/skills/ 2>/dev/null
Tool call 2: list_dir 工作区根目录（depth=2）
Tool call 3: 读取已安装 skill 的 SKILL.md frontmatter（head -5）
Tool call 4: read_file README.md（limit=30）
Tool call 5（代码项目时）: 读取依赖文件前 20 行
Tool call 6: cat ~/.cursor/skills/.starred.json 2>/dev/null（读收藏列表）
Tool call 7: cat MEMORY.md 2>/dev/null; cat .cursor/rules/*.md 2>/dev/null | head -30（读 AI 记忆和规则）
```

### 信号优先级

| 优先级 | 信号源 | 推断维度 | 说明 |
|--------|--------|---------|------|
| 1 | README.md | 业务领域 | **最高优先级**，必须优先于目录名和依赖文件 |
| 2 | 已安装 Skill 列表 | 能力覆盖 | 已有什么、缺什么 |
| 3 | MEMORY.md / Rules | 工作习惯 | AI 记忆中的常见任务模式、用户偏好、历史纠正 |
| 4 | 项目结构 + 依赖 | 技术栈 + 角色 | 框架、语言、工具链 |
| 5 | 收藏列表 | 兴趣方向 | 用户主动标记的关注领域 |

> **AI 记忆信号**：MEMORY.md 和 `.cursor/rules/` 中记录了用户的历史行为模式、常用工作流和偏好。例如用户频繁做"竞品分析"但没装相关 Skill，这是强缺口信号。

## R2：构建用户画像

1. **采集信号**：已安装 skill → 能力覆盖；收藏列表 → 兴趣方向；工作区 → 场景；README → 业务领域；MEMORY.md → 工作习惯与高频任务
2. **推断角色**：综合信号匹配角色快查表
3. **推断业务领域**：README 定位 > 目录名 > 依赖文件 > MEMORY.md 高频任务
4. **识别缺口**：该角色通常需要但用户未覆盖的能力。检验："这个角色会日常用 AI 工具做这件事吗？"
5. **业务价值排序**：优先推荐能**直接为业务创造价值**的 Skill（如竞品分析、数据报告、客户沟通），而非只推荐研发基建类 Skill（如 CI/CD、lint、测试框架）。研发基建在角色缺口中已覆盖时降低优先级。

### 角色快查表

信号不明确时，以此表快速定位角色：

| 角色 | 典型信号 | 推荐方向 |
|------|---------|---------|
| 前端开发 | React/Vue/CSS/Tailwind 依赖 | 组件、测试、设计系统 |
| 后端开发 | Express/Django/FastAPI/DB 配置 | API、数据库、部署、安全 |
| 全栈开发 | 前后端依赖混合 | 脚手架、CI/CD、代码审查 |
| 数据工程 | pandas/SQL/Jupyter/dbt | 数据分析、可视化、ETL |
| DevOps | Dockerfile/K8s/Terraform | 基础设施、监控、日志 |
| 设计师 | Figma/Sketch/设计稿文件 | 设计规范、切图、原型 |
| 产品经理 | PRD/需求文档/Jira | 文档、竞品分析、数据报告 |
| 内容创作 | 文章/博客/Markdown 为主 | 写作、SEO、图片生成 |
| 学生/初学者 | 简单结构、学习项目 | 教程、代码解释、skill 创建入门 |
| Azure 工程师 | bicep/ARM/Azure SDK | Azure 部署、环境构建 |

详细角色映射见 [references/recommend-templates.md](../references/recommend-templates.md)。

## R3：基于画像搜索（多路并行）

```bash
Tool call 1: npx skills find "{角色词A}"
Tool call 2: npx skills find "{领域词}"
Tool call 3: skillhub search "{缺口词}"
Tool call 4: gh search code "{角色词B}" --filename SKILL.md --limit 10
```

搜索词构造详见 [references/recommend-templates.md](../references/recommend-templates.md)。

## R4：输出推荐

```markdown
## 🎯 为你智能推荐的 Skill

### 你的环境概览
- **工作场景**：{识别到的场景}
- **业务领域**：{推断的领域}
- **推断角色**：{角色}
- **已安装 {N} 个 skill**：{列表}
- **推荐依据**：{一句话}

### 推荐列表

| # | Skill | 推荐理由 | 与已有 Skill 的关系 | 来源 | 信任 |
|---|-------|---------|-------------------|------|------|
| 1 | [{名称}](链接) | {基于画像的理由} | 互补/增强/延伸 {已有 Skill} 的 {能力} | skills.sh | 🏢/📋/👥 |

### 💡 最佳推荐

**#{编号} {名称}** — {推荐理由}。你已有 {X}，这个 Skill 可以 {互补/增强/延伸} 你的 {具体能力}。

---
**下一步？**
1. 📦 安装？（告诉我编号）
2. 🔍 查看详情？
3. ⭐ 收藏到喜爱列表？
4. 🔄 换个方向推荐？
```

**推荐排序**：业务价值 > 业务领域匹配 > 角色缺口 > 互补关系 > 收藏相关 > 场景驱动 > 热门补充

**互补关系说明**：每条推荐必须说明与已安装 Skill 的关系：

| 关系类型 | 说明 | 示例 |
|---------|------|------|
| **互补** | 已有 Skill 不覆盖的新能力 | 已有 code-review，推荐 testing（review → test 自然衔接） |
| **增强** | 加强已有 Skill 的某个维度 | 已有 skill-assistant，推荐 skill-vetter（增强安全审查深度） |
| **延伸** | 同领域的上下游能力 | 已有 data-analysis，推荐 data-visualization（分析→展示） |

推荐理由必须包含：「你已有 {X}，{推荐 Skill} 可以 {互补/增强/延伸} 你的 {具体能力}」。

**约束**：
- 2-5 条推荐，每条有画像理由 + 互补关系
- 不含已安装 skill
- 不推荐 skill-assistant 自身
- 不预设用户是开发者（可能是办公、创作、学习场景）
- 不用技术栈推断覆盖 README 的业务定位
- 业务价值类推荐优先于研发基建类推荐

---

## 收藏系统

用户说"收藏 / star / 喜欢这个 skill"时，将 Skill 信息追加到收藏文件：

**存储位置**：`~/.cursor/skills/.starred.json`

```json
[
  {"name": "skill-name", "source": "skills.sh", "url": "https://...", "starred_at": "2026-03-31"}
]
```

**操作**：
- **收藏**：追加条目（去重）
- **查看收藏**：`cat ~/.cursor/skills/.starred.json`
- **取消收藏**：从数组中移除对应条目

收藏的 Skill 在推荐时作为"兴趣信号"提升相关领域的推荐权重。
