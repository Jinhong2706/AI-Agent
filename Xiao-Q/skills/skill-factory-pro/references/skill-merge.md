# 技能合并方法论

## 合并场景

| 场景 | 示例 | 合并策略 |
|------|------|---------|
| Agent经验→技能 | 赛华佗会话→sai-huatuo优化 | 提取新知识→更新references |
| 多技能→综合技能 | tcm-consultant+sai-huatuo→综合中医 | 去重+补缺+重新组织 |
| 通用技能→领域定制 | skill-factory→chinese-medicine技能 | 模板+领域知识注入 |

---

## 合并流程（5步法）

### Step 1：盘点

扫描所有相关技能，列出：
- 每个技能的 SKILL.md 行数
- references/ 文件列表和大小
- 与目标Agent的关联度

### Step 2：差异分析

对比多个技能，标记：
- ✅ 共有内容（去重）
- ➕ 独有内容（保留）
- ❌ 冲突内容（以Agent实际输出为准）
- ❓ 缺失内容（从Agent会话提取补充）

### Step 3：知识提取

```
sessions_spawn → 目标Agent
提示词："基于你近期所有会话经验，输出以下内容（≤500字）：
1. 你最常被问到的高频场景Top5
2. 你最满意的3个回答模式
3. 你发现通用AI做不好的地方
4. 你认为技能里应该增加但缺少的知识"
```

### Step 4：重新设计

遵循 skill-factory Phase 3-6：
- SKILL.md ≤ 100行
- description ≤ 120字
- 详细内容 → references/
- 命名有辨识度和市场吸引力

### Step 5：验证上线

- 功能验证：spawn子Agent测试
- Token验证：行数+字数检查
- 旧技能：标记deprecated或直接替换

---

## 实战案例：赛华佗综合技能

### 盘点结果

| 技能 | 位置 | 行数 | 状态 |
|------|------|------|------|
| sai-huatuo | ~/.openclaw/workspace/skills/ | 180+ | 内容丰富但超体积 |
| tcm-consultant | ~/.qclaw/skills/ | 待确认 | 中医理论体系 |
| constitution_calculator.py | sai-huatuo/scripts/ | 存在 | 体质计算脚本 |
| 中医体质详解.md | sai-huatuo/knowledge/ | 存在 | 九种体质详解 |

### 差异分析

**sai-huatuo优势：**
- 完整的辨证流程（四步法）
- 九种体质的详细参考（饮食/代茶饮/穴位/禁忌）
- 辨证加减原则（久坐/熬夜/饮食偏好的叠加修正）
- 回答风格示例

**tcm-consultant优势：**
- 七大核心理论体系
- 专业模式/科普模式双轨
- 望闻问切四诊方法论

**合并方向：**
1. 以 sai-huatuo 为主体（更实战、更具体）
2. 补入 tcm-consultant 的理论体系（双轨模式）
3. 精简至 ≤100行（详细知识→references）
4. 统一命名和 description

### 合并后目标结构

```
sai-huatuo/
├── SKILL.md                          ← ≤100行（辨证流程+输出格式）
├── references/
│   ├── constitution-types.md         ← 九种体质详解（从SKILL.md拆出）
│   ├── tcm-theory.md                 ← 七大理论体系（从tcm-consultant合并）
│   ├── food-therapy.md               ← 五行食药参考+辨证加减
│   ├── style-guide.md                ← 回答风格+示例
│   └── knowledge-base.md             ← 从Agent会话提取的新知识
├── scripts/
│   └── constitution_calculator.py    ← 保留
└── knowledge/
    └── 中医体质详解.md                ← 保留
```

---

## 其他合并候选

| 目标技能 | 合并源 | 优先级 |
|---------|--------|--------|
| sai-huatuo | sai-huatuo + tcm-consultant | 🔴 高（重叠严重）|
| chinese-medicine | chinese-medicine + sai-huatuo知识 | 🟡 中 |
| 商业洞察 | 百事通经验 + market-trends | 🟡 中 |
| content-factory | 无不言经验 + 爆款模式库 | 🟢 低 |
