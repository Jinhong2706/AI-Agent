# 搜索 Refine 规则

搜索模块 Step 7 使用此文件。**首次搜索无需加载此文件**——仅在用户通过输出菜单 7-11 发起 refine 时按需加载。

> **设计理念**：首次搜索结果的诊断头（见 `search-transparency.md`）让用户看见黑盒，Refine 菜单让用户干预黑盒。两者配合形成完整的反馈闭环：**看见 → 诊断 → 调整 → 再看见**。

---

## 一、Refine 入口（交互菜单 7-11）

诊断头输出后，交互菜单在原 1-6（安装/详情/融合/相似/收藏/换词重搜）基础上追加 5 个 refine 分支：

```markdown
**— 或者搜索不对劲？—**
7. 🔧 修改关键词（如"L2-A 改成 ATS resume"）
8. 🔎 深搜某渠道（如"skills.sh 深搜 limit=50"）
9. 📡 升级策略（当前 balanced → thorough，预计多 60% 候选）
10. 🈯 补充关键词（如"加 career builder"或"加中文：求职"）
11. 🗑️ 排除关键词（如"排除 template，我要 AI agent 型的"）
```

> 菜单 6「换关键词重搜」和菜单 7「修改关键词」的区别：
> - **6 换词重搜** = 完全重来，丢弃所有现有诊断数据
> - **7 修改关键词** = 保留诊断状态，只改指定层级，其他保留 → 可以做 diff 对比

---

## 二、5 个 Refine 分支的处理规则

### 分支 7：修改关键词

**触发语气**："L2-A 改成 X"、"宽路换成 Y"、"L3 改为 ATS"、"把精确词改成 tailored resume"

**处理步骤**：
1. 解析用户指定的层级（L1 / L2-A/B/C / L3 / L4 / 中文变体）和新关键词
2. 在现有 `diagnostics.keywords` 基础上替换**只该层级**，其他层级保留
3. 标记本次为 `Refine #{N+1}`，保留上次 `diagnostics` 为 `previous_diagnostics`
4. 重新执行 Step 2（搜索）→ Step 5（漏斗）
5. Step 6 输出时使用**诊断头变化 diff 模板**（见 `search-transparency.md` §五），高亮变化项

**示例**：
```
用户输入："L2-A 改成 ATS resume"
Agent 操作：
  keywords.level_2.a.keyword: "resume builder" → "ATS resume"
  其他 L1/L2-B/L2-C/L3 保持不变
  重新搜索，输出变化 diff
```

**规则约束**：
- 禁止悄悄改动未被用户指定的层级
- 如果用户说"改 L2"没有指定 A/B/C，默认改 L2-A，并在 diff 中说明这个默认行为

### 分支 8：深搜某渠道

**触发语气**："skills.sh 深搜"、"skills.sh 翻页"、"GitHub 搜 50 条"、"深挖 skills.sh limit=50"

**处理步骤**：
1. 解析渠道名 + 目标 `limit`（未指定时默认翻倍：30 → 60，10 → 30）
2. **仅对该渠道**重新发起搜索：
   - 如平台支持翻页（skills.sh 增加 `limit` / SkillsMP `limit`），追加调用
   - 如不支持翻页，直接提升 `limit` 重发
3. 新返回的结果与首次结果**合并去重**
4. 其他渠道保持首次结果不变
5. Step 6 输出时只刷新该渠道的漏斗行 + 命中诊断

**示例**：
```
用户输入："skills.sh 深搜到 50"
Agent 操作：
  仅对 skills.sh 重发：limit=50，按 installs 排序
  合并新旧 skills.sh 结果，去重
  其他渠道 GitHub 保持不变
  漏斗表 skills.sh 行更新为 50 → 合并去重后数 → 重新筛
```

**规则约束**：
- 深搜禁止在其他渠道重发请求（避免浪费 API 配额）
- 深搜结果与首次合并后，相关度评分和推荐指数必须全量重算（因为 Top N 的分母变了）

### 分支 9：升级策略

**触发语气**："升级策略"、"用 thorough"、"深度搜索"、"全搜一遍"

**处理步骤**：
1. 当前策略升一档：`speed → balanced → thorough`（已经是 thorough 则提示无法再升）
2. 按新策略的完整规则重搜（见 `channel-search-commands.md#搜索策略完整定义`）
3. 重要：**这不是 refine，是完整重搜**，因为策略影响关键词层级、渠道范围、Top N 数等底层参数
4. Step 6 输出使用变化 diff 模板，重点对比"策略升级前后的候选量差异"

**策略升级预期效果**：

| 原策略 → 新策略 | 候选量预期变化 | 耗时预期变化 |
|---|:-:|:-:|
| speed → balanced | +40% ~ +70% | 2-3× |
| balanced → thorough | +50% ~ +80% | 2× |
| speed → thorough（跨档） | +100% ~ +200% | 3-4× |

如果实际候选量变化显著低于预期（如 balanced → thorough 只多了 5%），必须在诊断头提示：**"策略升级收益有限，可能关键词本身就是瓶颈，建议改用菜单 7/10"**。

### 分支 10：补充关键词

**触发语气**："加一个 career builder"、"再搜一下 cover letter"、"补个中文：求职"、"加 L2-D"

**处理步骤**：
1. 解析补充的关键词 + 目标层级（未指定时默认追加为 L2-D 扩展组）
2. 在现有 `diagnostics.keywords` 上**追加**（不替换），创建新的 L2-D 组或在 `chinese_variants` 追加
3. 仅对这个新关键词发起搜索（限制 limit=15，避免过度抓取）
4. 新结果与首次结果**合并去重**，全量重算相关度
5. Step 6 输出使用变化 diff，展示"补充关键词新发现的 N 条结果"

**示例**：
```
用户输入："加 L2-D：career builder"
Agent 操作：
  keywords.level_2.d = {keyword: "career builder", hits: 0}
  对所有启用渠道发起搜索（limit=15），仅使用新关键词 "career builder"
  新结果合并去重，重算全量 Top N
  诊断头展示 L2-D 新行
```

**规则约束**：
- L2-D 是"扩展槽位"，不是永久架构——本次 refine 结束后自动回收，除非用户再次补充
- 中文变体追加不占 L2-D 槽位，直接扩充 `chinese_variants[]`

### 分支 11：排除关键词

**触发语气**："排除 template"、"不要 LaTeX 模板"、"过滤掉 awesome 合集"、"别给我模板类的"

**处理步骤**：
1. 解析排除词（可以是关键词、类型、描述特征）
2. **不发起新的 API 调用**——在现有的 Top N 结果集中筛选：
   - 结果 name 含排除词 → 移除
   - 结果 description 含排除词 → 移除
   - 结果 tags 含排除词 → 移除
3. 筛后如果 Top N 不足 3 条，自动从原始候选（漏斗 1 之后的去重集）中补齐
4. Step 6 输出只展示"排除后的新 Top N"，诊断头追加一行：**"已排除含『{排除词}』的 N 条结果"**

**示例**：
```
用户输入："排除 template，我要 AI agent 型的"
Agent 操作：
  排除词 = "template" / "模板"
  在现有候选中过滤：reactive-resume ❌（含 template），Awesome-CV ❌（LaTeX 模板）
  保留：career-ops ✅（AI agent 型），Resume-Matcher ✅
  如 Top N 不足，从候选池补齐
  诊断头追加："已排除 3 条模板类结果"
```

**规则约束**：
- 排除是**客户端过滤**，不是 API 层过滤——避免因为 API 层过滤丢掉好结果
- 排除词可多个（"排除 template + LaTeX + 合集"）
- 排除后 Top N < 2 时提示用户："排除后结果过少，建议菜单 7 修改关键词重搜"

---

## 三、Refine 状态管理

### Refine 计数器

每次 refine 递增 `diagnostics.refine_count`，从 0 开始。第一次 refine 后 = 1，以此类推。

### Refine 上限

单次会话内同一搜索的 refine 次数上限为 **5 次**。超过后：
- 菜单 7-11 依然可用，但会警告："你已 refine 5 次，搜索方向可能已偏离初始需求。建议输入菜单 6 完全重搜。"
- 这个上限是防止用户在一个错误方向上无限深钻

### Refine 历史

每次 refine 后，`previous_diagnostics` 链保留最近 3 次：

```yaml
diagnostics:
  refine_count: 3
  previous_diagnostics:
    - refine_count: 2  # 最近一次
      summary: "分支 10 补充 L2-D career builder"
    - refine_count: 1
      summary: "分支 7 修改 L2-A 为 ATS resume"
    - refine_count: 0
      summary: "初次搜索"
```

用户可以输入 `/search history` 查看 refine 链路，或输入 `/search rollback` 回到上一次 refine 状态。

---

## 四、Refine 和 NEVER 规则的互动

Refine 过程中仍须遵守所有 NEVER 规则：

| NEVER 规则 | Refine 场景中的应用 |
|---|---|
| 单核心词优先（`gh search repos` 第一轮） | 分支 8「深搜 GitHub」时首轮仍必须单核心词 |
| 宽路不可省 | 分支 9 策略升级后，新策略的宽路仍必须执行 |
| 双语平台双语关键词 | 分支 10 追加中文时自动触发 SkillHub 重搜 |

Agent 在执行 refine 时，如果用户的指令与 NEVER 规则冲突（如"SkillHub 只搜英文"而用户原需求是中文），必须提示冲突并给用户确认：

```
⚠️ 你要求 SkillHub 只搜英文，但原需求含中文。
   SkillHub 收录大量中文 Skill，跳过中文关键词可能导致命中率下降。
   是否继续？[y: 按你说的办 / n: 保留中文双语]
```

---

## 五、Refine UX 原则

1. **最小意外原则**：用户说改什么就改什么，不悄悄动其他参数
2. **可视化变化**：每次 refine 后的输出必须展示 diff，让用户看见调整的效果
3. **可回滚**：至少保留最近 3 次 refine 状态，允许 `/search rollback`
4. **收敛提示**：连续 3 次 refine 仍未命中高相关度结果时，提示用户考虑创建 Skill（路由到 create 模块）
5. **禁止无限循环**：5 次 refine 上限 + 超限后引导完全重搜

---

## 六、常见 Refine 组合

| 场景 | 推荐 refine 序列 |
|---|---|
| 关键词方向对但深度不够 | 分支 8（深搜渠道）+ 分支 9（升级策略） |
| 关键词偏离需求 | 分支 7（修改）+ 分支 10（补充） |
| 结果太杂 | 分支 11（排除）+ 分支 7（修改为更精确词） |
| 中文需求英文关键词占主导 | 分支 10（补充中文）+ 分支 8（SkillHub 深搜） |
| 仅 L3 命中过多 | 分支 7（L2-A 改精确）或 分支 10（补 L2-D） |

这些组合可以作为 Agent 在异常检测命中时给出的"推荐 refine 序列"建议。
