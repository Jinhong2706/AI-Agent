# Skill 诊断报告

## 基本信息

| 项目 | 值 |
|------|-----|
| **Skill Name** | {{SKILL_NAME}} |
| **Skill Type** | {{SKILL_TYPE}}（置信度 {{TYPE_CONFIDENCE}}） |
| **效能分** | {{SCORE}}/100 ({{GRADE}}) |
| **诊断日期** | {{DATE}} |

### 评分构成

| 维度 | 评级 | 得分 | 权重 | 加权分 |
|------|------|------|------|--------|
| 指令 (Directive) | {{DIRECTIVE_RATING}} | {{DIRECTIVE_SCORE}} | 40% | {{DIRECTIVE_WEIGHTED}} |
| 约束 (Constraint) | {{CONSTRAINT_RATING}} | {{CONSTRAINT_SCORE}} | 30% | {{CONSTRAINT_WEIGHTED}} |
| 冗余 (Redundancy) | {{REDUNDANCY_RATING}} | {{REDUNDANCY_SCORE}} | 30% | {{REDUNDANCY_WEIGHTED}} |

---

## 类型识别

{{TYPE_ANALYSIS}}

---

## 逐维分析

### 1. 指令 (Directive) — {{DIRECTIVE_RATING}}

指令是驱动 LLM 做对事的 Token——告诉 LLM「该做什么、怎么做」。

**检测信号：**
{{DIRECTIVE_SIGNALS}}

**评估：**
{{DIRECTIVE_ASSESSMENT}}

### 2. 约束 (Constraint) — {{CONSTRAINT_RATING}}

约束是防止 LLM 犯错的 Token——告诉 LLM「不该做什么」。

**检测信号：**
{{CONSTRAINT_SIGNALS}}

**评估：**
{{CONSTRAINT_ASSESSMENT}}

### 3. 冗余 (Redundancy) — {{REDUNDANCY_RATING}}

冗余是对任务无贡献的 Token（类似死代码），稀释指令和约束的效果。

**检测信号：**
{{REDUNDANCY_SIGNALS}}

**评估（结合 Skill 类型判定）：**
{{REDUNDANCY_ASSESSMENT}}

---

## 补充检查

### 参数语义
{{CLARITY_ISSUES}}

### I/O 确定性
{{IO_CONSTRAINT_ISSUES}}

---

## 优化建议（按优先级排序）

### 优先级 1: 增强指令
{{DIRECTIVE_RECOMMENDATIONS}}

### 优先级 2: 补充约束
{{CONSTRAINT_RECOMMENDATIONS}}

### 优先级 3: 消减冗余
{{REDUNDANCY_RECOMMENDATIONS}}

---

> 请确认上述诊断报告后，进入 Step 2: 逻辑蓝图设计。
