# Token 优化方法论

> 适用于所有 QClaw 技能的设计与优化指南

---

## 核心目标

功能相同，消耗不同。通过优化，可将 Token 消耗降低 **70-90%**。

---

## 1. description 精简规范

**字数限制：≤ 120 字**

```
前 80 字：技能是做什么的
后 40 字：精确触发场景（3-5 个用户会说/输入的具体话）
```

❌ 超长（200+ 字，影响触发）：
```
玄学大师 · 命理运势专家。触发场景：用户问「今天运势如何」「今日宜忌」
「八字分析」「五行缺什么」「今日吉凶方位」「穿什么颜色」……
基于生辰八字+五行喜忌+玄空飞星，提供趋吉避凶的具体行动建议。
目标用户：对中国传统命理感兴趣、想要可操作日常指引的成年人。
```

✅ 精简（118 字）：
```
玄学大师 · 命理 AI。触发：问「今天运势」「今日宜忌」「八字分析」
「五行缺什么」「穿什么颜色好」「属相配对」「事业/感情/财运」。
基于生辰八字+五行喜忌，给出趋吉避凶的具体行动建议。
```

---

## 2. SKILL.md 分层规范

| 层级 | 文件 | 行数限制 | 内容 |
|------|------|---------|------|
| L1 | SKILL.md 主体 | ≤ 100 行 | 触发条件 + 核心流程 + 引用路径 |
| L2 | references/concepts.md | 50-100 行 | 详细概念、术语表 |
| L3 | references/step-by-step.md | 50-100 行 | 完整操作步骤 |
| L4 | references/templates.md | 50-100 行 | 输出模板完整版 |
| L5 | references/examples.md | 可选 | 完整示例 |

**SKILL.md 主体禁止写入：**
- 大段详细步骤（→ references/step-by-step.md）
- 完整用户数据（→ references/user-profile.md）
- 完整术语表（→ references/glossary.md）
- 完整输出模板（→ references/templates.md）

---

## 3. 动态加载机制

| 任务类型 | 加载内容 |
|---------|---------|
| 快速查询（< 1 分钟）| SKILL.md 主体 |
| 深度分析（报告生成）| SKILL.md + references/concepts.md |
| 完整诊断（多维度）| 加载全部 references |

**references 文件命名规范（便于按需加载）：**
```
references/concepts.md       ← 核心概念，必读
references/step-by-step.md   ← 详细流程，按任务选读
references/templates.md      ← 输出模板，按格式选读
references/examples.md       ← 示例，按需查
```

---

## 4. 函数调用优先级

| 优先级 | 类型 | Token 消耗 | 使用场景 |
|--------|------|-----------|---------|
| ✅ 最高 | 内置工具（web_search/exec/browser）| 无额外开销 | 数据获取、计算、自动化 |
| ✅ 高 | 轻量脚本（scripts/xxx.py，< 50 行）| 低 | 确定性任务 |
| ⚠️ 中 | 外部 API（HTTP 请求）| 视数据量 | 实时数据 |
| ❌ 高 | 子 Agent 推理（sessions_spawn）| 高 | 仅领域深挖时使用 |

---

## 5. 子 Agent 调用优化

- **提示词精简**：只传递当前任务必要的上下文，不重复系统信息
- **输出格式约束**：提示词中明确"输出 ≤ 500 字，结构化"
- **结果复用**：子 Agent 输出同步到 references/，避免重复调用
- **批量处理**：多个相似任务合并为一次调用

---

## 6. 技能自检清单

每个技能 SKILL.md 末尾必须包含：

```
## 自检清单（发布前必查）
- [ ] description ≤ 120 字 ✓
- [ ] SKILL.md 主体 ≤ 100 行 ✓
- [ ] 详细知识已移至 references/ ✓
- [ ] 无冗余重复内容 ✓
- [ ] 脚本实际可用（已测试）✓
```

---

## 7. 赛华佗优化案例

**优化前**（~300 行，冗余严重）：
- SKILL.md 包含完整九种体质定义、详细舌象描述、完整方剂列表
- description 200+ 字

**优化后**（55 行）：
- 核心判断逻辑保留在 SKILL.md 主体
- 九种体质详细定义 → references/constitutions.md
- 方剂/穴位详细列表 → references/prescriptions.md
- 用户数据 → references/user-profile.md
- description 压缩至 118 字

**效果**：主体文件缩小 80%，触发准确率提升，详细知识仍完整保留。
