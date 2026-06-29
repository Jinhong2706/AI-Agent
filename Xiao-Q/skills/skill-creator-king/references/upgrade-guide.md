# 升级指南：轻量 → 完整

## 触发词
升级到完整版 / 帮我升级 / 补全 skill

## 升级流程

### Step 1：读取现状
1. 找到现有 skill 目录
2. 读取 SKILL.md frontmatter + body
3. 列出已有文件清单

### Step 2：识别 Gap
用 lightweight.yaml 检查清单对比现状：
- Phase 1：有 SKILL.md 完整的 frontmatter 吗？
- Phase 2：有 DESIGN.md（含 REQ）或 SPEC.md + data/sources.yaml 吗？
- Phase 3：有 DESIGN.md 吗？
- Phase 4：有 scripts + tests 吗？
- Phase 5：有 README.md + CHANGELOG.md 完整版吗？README 有「这是什么」介绍板块（是什么/适合谁/不适合谁）吗？

### Step 3：逐 Gap 补充
⚠️ 核心原则：**保留已有产出，只补缺失**
- 不重写用户已经写好的 SKILL.md
- 不替换用户已有的 L2 文件
- 每个 gap 引导用户补充：

例：
"你的 SKILL.md 很好，不需要重写。现在只缺 DESIGN.md——我们聊聊：你这个 skill 的核心需求和架构决策是什么？"

### Step 4：完整版交付
用完整通道 Phase 5 标准过自检（含 Ralph Loop 自反思） + 交付报告
升级后的 skill 必须重新跑 quality-audit.py 确认分数。
