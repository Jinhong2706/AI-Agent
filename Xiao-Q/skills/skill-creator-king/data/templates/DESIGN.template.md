# DESIGN.md — {{SKILL_NAME}}

> 架构总览 + 代表性决策。逐条设计决策的完整记录见项目 `2-design/` 目录（project-harness 管理）。
> 版本：{{VERSION}}（与 SKILL.md frontmatter 同步）

## 架构总览

{{ARCHITECTURE_OVERVIEW}}
<!-- 一句话 + 流程图/阶段图。说明 skill 的顶层结构（几阶段/几引擎/几入口），读者 30 秒看清全貌。 -->

## 候选方案对比

| 决策点 | 方案 A | 方案 B | 选定 | 理由 |
|--------|--------|--------|:----:|------|
| {{DECISION_1}} | {{OPTION_A}} | {{OPTION_B}} | {{CHOSEN}} | {{RATIONALE}} |

<!-- 至少填一条核心架构取舍。对比表让 audit tool 可检测。 -->

## 决策记录

### ADR-001: {{ADR_001_TITLE}}
- **背景**：{{ADR_001_BG}}
- **决定**：{{ADR_001_DECISION}}
- **备选方案**：{{ADR_001_ALTERNATIVES}}
- **理由**：{{ADR_001_REASON}}
- **影响**：{{ADR_001_CONSEQUENCE}}

<!-- 代表性决策至少一条。后续决策按日期归档到项目 2-design/YYYY-MM-DD*.md，不堆在 skill DESIGN.md 里。 -->

## 核心需求

### REQ-001: {{REQ_001_NAME}}
**描述**：{{REQ_001_DESC}}
**优先级**：P0
**验证标准**：{{REQ_001_VERIFY}}

---

## 非功能需求

| 需求 | 说明 |
|------|------|
| NFR-001 Token预算 | L0:{{L0}} L1:{{L1}} L2:{{L2}} hard_cap:{{HARD_CAP}} |
| NFR-002 风格 | {{STYLE}} |
| NFR-003 安全 | {{SAFETY}} |

---

## Token 实测

| 组件 | 文件 | Token | 占比 |
|------|------|-------|------|
{{TOKEN_TABLE}}

## 模块关系图
{{MODULE_DIAGRAM}}

## 数据流图
{{DATAFLOW_DIAGRAM}}
