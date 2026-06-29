# 进度日程管理助手 (Progress Assistant)

> 版本：v2.1 | 完善版：含模板、脚本、定时任务配置、战略静默（休息关怀）

---

## 概述

这是一个智能进度与日程管理助手 skill，通过多维度感知执行人状态，智能管理日程安排，并一键生成各类工作报告。

**核心特色**：
- 支持定时任务 + 微信 Claw 推送联动
- 自动收集进度并保存为 MD 文件
- 内置完整模板，开箱即用
- 战略静默：连续工作检测 + 休息关怀，休息记录独立于工作数据

---

## 触发条件

当用户提到以下意图时触发：
- "进度"、"日程"、"任务"、"计划"、"安排"相关的请求
- "生成日报"、"生成周报"、"生成月报"、"写报告"
- "感知状态"、"了解进展"、"任务卡住"
- "帮我规划"、"帮我安排"、"时间冲突"
- 定时获取进度、定时提醒
- 与文档交互（读取任务文件、项目文档）
- "休息"、"战略静默"、"放松"、"劳逸结合"相关的请求

---

## 核心能力

### 1. 状态感知

通过以下方式主动感知执行人状态：

- **文档交互**：读取并分析任务文档、进度报告、项目文件
- **问答交互**：通过对话主动询问任务进展、遇到的问题
- **定时感知**：在关键时间点自动收集进度信息（支持微信推送）
- **微信联动**：通过 ClawBot 接收用户回答并记录

感知维度：
- 当前任务进展（完成度、里程碑）
- 遇到的问题和阻碍
- 情绪状态和工作负荷
- 优先级变化

### 2. 日程管理

- 创建、修改、删除日程安排
- 检测日程冲突并提供解决方案
- 根据任务紧急程度智能推荐时间分配
- 支持临时任务插入和重新规划
- 与用户确认后执行日程调整

### 3. 报告生成

支持一键生成以下报告：

| 报告类型 | 内容要点 | 触发关键词 |
|----------|----------|------------|
| 日报 | 今日完成、明日计划、问题阻塞 | "日报"、"今天总结" |
| 周报 | 本周进展、下周安排、风险预警 | "周报"、"周总结" |
| 月报 | 月度成果、整体进度、资源评估 | "月报"、"月总结" |
| 分析报告 | 效率分析、趋势洞察、改进建议 | "分析"、"统计" |

### 4. 定时任务 + 微信推送

#### 预配置定时任务

| 任务名称 | 触发时间 | rrule 配置 | 内容 |
|----------|----------|------------|------|
| 📅 每日早间计划提醒 | 每天 9:00 | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` | 询问今日任务、优先级 |
| 📝 每日晚间日报收集 | 每天 17:30 | `FREQ=DAILY;BYHOUR=17;BYMINUTE=30` | 收集完成情况、问题、明日计划 |
| 📊 周一收集周报数据 | 每周一 9:00 | `FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0` | 上周总结 + 本周目标 |
| 📋 周五生成完整周报 | 每周五 17:00 | `FREQ=WEEKLY;BYDAY=FR;BYHOUR=17;BYMINUTE=0` | 汇总日报生成正式周报 |
| ☕ 连续工作2小时提醒 | 每2小时 | `FREQ=HOURLY;INTERVAL=2` | 温和提醒起身活动、补充水分 |
| 🧘 连续工作4小时关怀 | 每4小时 | `FREQ=HOURLY;INTERVAL=4` | 强制休息建议（15分钟以上） |

#### 微信 Claw 配置步骤

1. **安装微信 ClawBot 插件**
   - 打开微信 → 设置 → 插件 → 搜索 "ClawBot" → 安装启用

2. **在 WorkBuddy 中绑定微信**
   - 打开 WorkBuddy 桌面端（4.6.4+）
   - 点击左下角头像 → 「Claw 设置」
   - 选择「微信通道」→ 扫码绑定

3. **定时任务自动推送**
   - 绑定后，定时任务执行时会自动推送通知到微信
   - 用户在微信回复 → WorkBuddy 接收 → 自动记录到 MD 文件

---

## 工作流程

### 流程1：状态收集（定时 + 微信联动）

```
定时触发（每天9:00/17:30）
    ↓
微信收到提醒
    ↓
用户在微信回复回答
    ↓
WorkBuddy 接收并处理
    ↓
生成带日期的 MD 文件
    ↓
保存到日程文件夹
```

### 流程2：日程规划

1. **收集任务**：列出所有待办任务和截止日期
2. **评估优先级**：根据紧急程度和重要性排序
3. **检查冲突**：检测时间冲突和资源冲突
4. **生成方案**：提供日程安排建议
5. **用户确认**：获得确认后执行变更

### 流程3：报告生成

1. **确定范围**：明确报告的时间范围和主题
2. **收集数据**：汇总相关任务、日程、状态信息
3. **读取模板**：加载对应的报告模板（见下方内嵌模板）
4. **生成内容**：填充模板，生成结构化报告
5. **交付确认**：呈现报告给用户确认

### 流程4：战略静默（休息关怀）

```
定时触发（每2小时/每4小时）
    ↓
微信收到关怀提醒
    ↓
用户回复选择（继续工作 / 进入战略静默）
    ↓
├─ 继续：记录当前连续工作时长，更新状态
└─ 战略静默：
    ↓
    记录静默开始时间
    ↓
    用户回复恢复（或定时15分钟后询问）
    ↓
    记录静默结束时间
    ↓
    保存到 日程/战略静默/YYYY-MM-DD.md
    ↓
    工作时间统计自动扣除静默时段
```

---

## 文件存储规范

### 目录结构

```
workspace/
└── 日程/
    ├── 📝 日报/              ← 每日进度记录
    │   └── YYYY-MM-DD.md    ← 自动按日期命名
    ├── 📊 周报/              ← 每周汇总报告
    │   └── YYYY-WXX.md      ← 自动按周数命名
    ├── 📅 月报/              ← 每月汇总报告
    │   └── YYYY-MM.md
    ├── 📋 任务/              ← 当前任务管理
    │   ├── 当前任务.md       ← 每日更新最新状态
    │   └── 历史任务/         ← 已完成任务归档
    ├── 💡 状态/              ← 状态感知记录
    │   └── 状态记录.md
    └── 🌿 战略静默/          ← 休息/恢复记录（独立于工作记录）
        └── YYYY-MM-DD.md    ← 按日期记录当日休息情况
```

### 文件命名规则

| 类型 | 格式 | 示例 |
|------|------|------|
| 日报 | `YYYY-MM-DD.md` | `2026-04-12.md` |
| 周报 | `YYYY-WXX.md` | `2026-W15.md` |
| 月报 | `YYYY-MM.md` | `2026-04.md` |
| 战略静默 | `YYYY-MM-DD.md` | `2026-04-12.md` |

### 数据管理规则

- **日报**：每日新建，不会覆盖（按日期区分）
- **任务**：每日更新最新状态（会覆盖）
- **周报**：周一收集初稿 → 周五生成正式版本（覆盖更新）
- **备份**：重要任务会自动归档到 `历史任务/` 目录

### 数据隔离规则（战略静默）

战略静默记录与工作数据严格隔离，遵循以下原则：

| 规则 | 说明 |
|------|------|
| 日报/周报/月报排除休息时段 | 报告中的工作时间统计**不包含**战略静默期间 |
| 当前任务计时暂停 | 进入战略静默期间，任务进度计时自动暂停 |
| 战略静默独立存储 | 所有休息记录**只存入** `日程/战略静默/` 目录 |
| 不影响工作效率指标 | 休息时长不纳入效率分析和绩效统计 |

---

## 内置模板

### 模板1：日报模板

```markdown
# 📝 日报 - {{date}}

> 生成时间：{{generated_time}}

## 今日完成

{{completed_items}}

## 明日计划

{{planned_items}}

## 问题与阻塞

{{blockers}}

## 备注

{{notes}}

---
*由 Progress Assistant 自动生成*
```

### 模板2：周报/月报模板

```markdown
# 📊 {{report_type}} - {{period}}

> 生成时间：{{generated_time}}
> 汇报人：{{user_name}}

## 📈 本{{period_type}}回顾

### 完成情况

{{completion_summary}}

### 关键里程碑

{{milestones}}

### 数据指标

| 指标 | 数值 | 环比 |
|------|------|------|
| 完成任务数 | {{completed_count}} | {{completed_change}} |
| 新增任务数 | {{new_count}} | {{new_change}} |
| 阻塞任务数 | {{blocked_count}} | {{blocked_change}} |

## 🎯 下{{period_type}}计划

### 重点任务

{{next_period_tasks}}

### 预期里程碑

{{next_milestones}}

## ⚠️ 风险与问题

{{risks}}

## 💡 改进建议

{{suggestions}}

---
*由 Progress Assistant 自动生成*
```

### 模板3：任务结构模板

```markdown
# 📋 任务列表

> 最后更新：{{updated_time}}

## 🔴 高优先级

{{high_priority_tasks}}

## 🟡 中优先级

{{medium_priority_tasks}}

## 🟢 低优先级

{{low_priority_tasks}}

## ✅ 已完成

{{completed_tasks}}

---

## 任务详情

{{task_details}}
```

### 模板4：状态收集问卷

```markdown
# 💡 状态收集

> 时间：{{collect_time}}

## 任务进展

1. **当前正在做什么？**
   {{current_task}}

2. **完成度如何？**
   {{progress}}

3. **预计何时完成？**
   {{eta}}

## 遇到的问题

{{issues}}

## 需要什么支持？

{{support_needed}}

## 情绪状态

- [ ] 🟢 状态良好
- [ ] 🟡 有点压力
- [ ] 🔴 需要帮助

{{mood_note}}

## 工作节奏

5. **距离上次休息已过多久？**
   {{time_since_last_rest}}

6. **是否需要现在进入战略静默？**
   - [ ] 还可以继续
   - [ ] 稍微静默一下（5-10分钟）
   - [ ] 需要较长时间静默（15分钟以上）
```

### 模板5：战略静默记录模板

```markdown
# 🌿 战略静默 - {{date}}

> 记录时间：{{generated_time}}

## 静默记录

| 序号 | 开始时间 | 结束时间 | 静默时长 | 静默类型 | 恢复状态 |
|------|----------|----------|----------|----------|----------|
| {{index}} | {{start_time}} | {{end_time}} | {{duration}} | {{type}} | {{after_status}} |

### 静默类型说明

| 类型 | 代码 | 说明 |
|------|------|------|
| 短暂休息 | `SHORT` | 5-10 分钟，起身活动、饮水 |
| 标准静默 | `STANDARD` | 15-30 分钟，散步、拉伸、冥想 |
| 深度恢复 | `DEEP` | 30 分钟以上，午休、户外活动 |

## 当日累计

| 指标 | 数值 |
|------|------|
| 静默次数 | {{rest_count}} 次 |
| 累计静默时长 | {{total_rest_time}} |
| 连续工作最长时长 | {{max_continuous_work}} |
| 净工作时长（扣除静默） | {{net_work_time}} |

## 备注

{{notes}}

---
*由 Progress Assistant 自动生成 · 战略静默记录不纳入工作统计*
```

---

## 工作流脚本

### 脚本1：生成日报

```javascript
// scripts/generate_daily_report.js
// 用法：在对话中调用此逻辑，或使用 automation 执行

async function generateDailyReport(context) {
  const { user, date, completedItems, plannedItems, blockers, notes } = context;
  
  const template = loadTemplate('daily_report_template.md');
  const content = template
    .replace('{{date}}', date)
    .replace('{{generated_time}}', new Date().toLocaleString('zh-CN'))
    .replace('{{completed_items}}', completedItems || '（待填写）')
    .replace('{{planned_items}}', plannedItems || '（待填写）')
    .replace('{{blockers}}', blockers || '无')
    .replace('{{notes}}', notes || '');

  const fileName = `日程/日报/${date}.md`;
  await writeFile(fileName, content);
  
  return { success: true, fileName, content };
}
```

### 脚本2：生成周报

```javascript
// scripts/generate_weekly_report.js
// 汇总本周所有日报，生成周报

async function generateWeeklyReport(weekNumber) {
  const { year, week } = parseWeekNumber(weekNumber);
  
  // 1. 收集本周所有日报
  const dailyReports = await collectDailyReports(year, week);
  
  // 2. 汇总数据
  const summary = aggregateReports(dailyReports);
  
  // 3. 生成周报
  const template = loadTemplate('weekly_monthly_report_template.md');
  const content = template
    .replace('{{report_type}}', '周报')
    .replace('{{period}}', `${year}-W${week.toString().padStart(2, '0')}`)
    .replace('{{period_type}}', '周')
    .replace('{{generated_time}}', new Date().toLocaleString('zh-CN'))
    .replace('{{user_name}}', getUserName())
    .replace('{{completion_summary}}', summary.completion)
    .replace('{{milestones}}', summary.milestones)
    .replace('{{completed_count}}', summary.completed)
    .replace('{{completed_change}}', summary.completedChange)
    .replace('{{new_count}}', summary.new)
    .replace('{{new_change}}', summary.newChange)
    .replace('{{blocked_count}}', summary.blocked)
    .replace('{{blocked_change}}', summary.blockedChange)
    .replace('{{next_period_tasks}}', summary.nextTasks)
    .replace('{{next_milestones}}', summary.nextMilestones)
    .replace('{{risks}}', summary.risks)
    .replace('{{suggestions}}', summary.suggestions);

  const fileName = `日程/周报/${year}-W${week.toString().padStart(2, '0')}.md`;
  await writeFile(fileName, content);
  
  return { success: true, fileName, content };
}
```

### 脚本3：检查日程冲突

```javascript
// scripts/check_schedule_conflicts.js

function checkScheduleConflicts(tasks, existingSchedule) {
  const conflicts = [];
  
  for (const task of tasks) {
    const taskStart = new Date(task.startTime);
    const taskEnd = new Date(task.endTime);
    
    for (const existing of existingSchedule) {
      if (existing.id === task.id) continue;
      
      const existingStart = new Date(existing.startTime);
      const existingEnd = new Date(existing.endTime);
      
      // 检测重叠
      if (taskStart < existingEnd && taskEnd > existingStart) {
        conflicts.push({
          task1: task.name,
          task2: existing.name,
          overlap: `与 "${existing.name}" 时间冲突 (${existing.startTime} - ${existing.endTime})`
        });
      }
    }
  }
  
  // 生成解决建议
  const suggestions = conflicts.map(c => ({
    ...c,
    solution: generateRescheduleSuggestion(c)
  }));
  
  return { hasConflicts: conflicts.length > 0, conflicts, suggestions };
}
```

---

## 定时任务配置示例

### 示例1：每日早间提醒（创建）

```yaml
automation:
  name: "每日早间计划提醒"
  prompt: |
    早安！请回复你今天的：
    1. 主要任务（最多3项）
    2. 优先级最高的事项
    3. 预计完成的截止时间
    
    请简短回复，我会帮你记录到今日计划中。
  schedule:
    rrule: "FREQ=DAILY;BYHOUR=9;BYMINUTE=0"
  cwds: "workspace"
  status: "ACTIVE"
```

### 示例2：每日晚间日报收集（创建）

```yaml
automation:
  name: "每日晚间日报收集"
  prompt: |
    今天的工作即将结束，请回复今日：
    1. 完成了哪些任务？
    2. 遇到了什么问题？
    3. 明天计划做什么？
    
    我会将内容整理成日报保存。
  schedule:
    rrule: "FREQ=DAILY;BYHOUR=17;BYMINUTE=30"
  cwds: "workspace"
  status: "ACTIVE"
```

### 示例3：周一收集周报数据（创建）

```yaml
automation:
  name: "周一收集周报数据"
  prompt: |
    新的一周开始了！请回复：
    1. 上周完成了什么？
    2. 本周的主要目标是什么？
    3. 有哪些需要注意的风险？
    
    我会汇总数据生成周报。
  schedule:
    rrule: "FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0"
  cwds: "workspace"
  status: "ACTIVE"
```

### 示例4：周五生成完整周报（创建）

```yaml
automation:
  name: "周五生成周报"
  prompt: |
    正在汇总本周所有日报，生成正式周报...
    请稍候，我会将周报保存到「日程/周报/」目录。
  schedule:
    rrule: "FREQ=WEEKLY;BYDAY=FR;BYHOUR=17;BYMINUTE=0"
  cwds: "workspace"
  status: "ACTIVE"
```

### 示例5：连续工作2小时提醒（创建）

```yaml
automation:
  name: "连续工作2小时提醒"
  prompt: |
    ☕ 你已经连续工作了2个小时啦！

    建议现在：
    1. 站起来活动一下身体
    2. 喝杯水，补充水分
    3. 看看远处，放松眼睛

    回复以下选项：
    - "继续" → 记录并继续工作
    - "静默" → 进入战略静默，我会帮你记录休息时段
    - "跳过" → 本次跳过提醒
  schedule:
    rrule: "FREQ=HOURLY;INTERVAL=2"
  cwds: "workspace"
  status: "ACTIVE"
```

### 示例6：连续工作4小时关怀（创建）

```yaml
automation:
  name: "连续工作4小时关怀"
  prompt: |
    🧘 你已经连续工作了4个小时，是时候进入战略静默了！

    长时间连续工作会降低效率，建议休息15分钟以上：
    1. 出门走走，呼吸新鲜空气
    2. 做几分钟拉伸运动
    3. 闭目养神，让大脑恢复

    回复以下选项：
    - "静默" → 进入战略静默，记录休息时段
    - "5分钟" → 短暂休息5分钟后提醒你
    - "继续" → 了解风险后继续（不推荐）

    你的健康是最高优先级。
  schedule:
    rrule: "FREQ=HOURLY;INTERVAL=4"
  cwds: "workspace"
  status: "ACTIVE"
```

### 示例5：配置定时任务（用户指令示例）

当用户说"设置每日早间提醒"时，你应该：

1. 询问触发时间（默认 9:00）
2. 询问提醒内容偏好
3. 使用 automation_update 工具创建任务：

```javascript
// 调用 automation_update 工具
automation_update({
  mode: "suggested create",
  name: "每日早间计划提醒",
  prompt: "早安！请回复你今天的：\n1. 主要任务（最多3项）\n2. 优先级最高的事项\n3. 预计完成的截止时间\n\n请简短回复，我会帮你记录到今日计划中。",
  rrule: "FREQ=DAILY;BYHOUR=9;BYMINUTE=0",
  cwds: "workspace",
  status: "ACTIVE"
})
```

---

## 使用示例

### 场景1：了解用户当前状态

```
用户：帮我看看我今天都完成了什么
助手：
1. 读取日程/日报/YYYY-MM-DD.md（如存在）
2. 读取日程/任务/当前任务.md
3. 通过问答询问用户今日完成情况
4. 汇总呈现今日进度概览
```

### 场景2：生成日报

```
用户：帮我生成今天的日报
助手：
1. 加载内置日报模板
2. 询问用户今日完成事项
3. 询问遇到的问题
4. 询问明日计划
5. 生成格式化日报并保存到日程/日报/YYYY-MM-DD.md
```

### 场景3：日程规划

```
用户：帮我安排下周的工作
助手：
1. 读取当前任务列表
2. 询问任务优先级和截止日期
3. 检测时间冲突
4. 生成日程安排建议
5. 用户确认后写入日程文件
```

### 场景4：配置定时任务

```
用户：设置定时收集任务
助手：
1. 询问用户希望的触发时间
2. 询问收集内容
3. 创建自动化任务（使用 automation_update 工具）
4. 配置微信推送（如已绑定）
5. 确认创建成功
```

### 场景5：一键创建所有定时任务

```
用户：帮我设置完整的进度管理定时任务
助手：
好的，我将为你创建以下6个定时任务：

1. 📅 每日早间计划提醒（每天 9:00）
2. 📝 每日晚间日报收集（每天 17:30）
3. 📊 周一收集周报数据（每周一 9:00）
4. 📋 周五生成完整周报（每周五 17:00）
5. ☕ 连续工作2小时提醒（每2小时）
6. 🧘 连续工作4小时关怀（每4小时）

确认创建吗？
→ 用户确认后，批量创建所有任务
```

### 场景6：进入战略静默

```
用户：我要休息一下 / 进入战略静默
助手：
1. 记录当前时间作为静默开始时间
2. 询问预计静默时长（短暂5分钟 / 标准15分钟 / 深度30分钟以上）
3. 保存静默记录到 日程/战略静默/YYYY-MM-DD.md
4. 任务进度计时暂停
5. 静默结束后询问恢复状态并更新记录
```

---

## 交互原则

1. **主动感知**：不等用户问，主动了解状态
2. **定时联动**：善用定时任务 + 微信推送，保持持续跟踪
3. **数据持久化**：所有回答自动保存为带日期的 MD 文件
4. **简洁确认**：关键决策前先确认
5. **结构化输出**：报告格式统一，便于阅读
6. **持续学习**：记住用户偏好和习惯
7. **健康优先**：战略静默期间不打扰，休息记录严格隔离于工作数据

---

## 注意事项

- 涉及外部操作（发送邮件、发布消息）需明确告知用户
- 日程变更需获得用户明确确认
- 敏感信息注意保护
- 保持对话自然流畅，避免机械感
- 微信推送需要先在 WorkBuddy 中绑定 Claw 微信通道
- 所有文件保存在 `日程/` 目录下，按类型自动分类
- **战略静默数据隔离**：休息记录不写入日报/周报/月报，工作时间统计自动扣除静默时段
- **任务计时暂停**：进入战略静默后，当前任务进度计时自动暂停，恢复后继续

---

## 附录：快速参考

### 快速创建定时任务

| 用户指令 | 对应任务 | rrule |
|----------|----------|-------|
| "每天早上提醒我" | 每日早间提醒 | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` |
| "傍晚收集日报" | 每日晚间收集 | `FREQ=DAILY;BYHOUR=17;BYMINUTE=30` |
| "周一提醒我写周报" | 周一收集 | `FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0` |
| "周五自动生成周报" | 周五生成 | `FREQ=WEEKLY;BYDAY=FR;BYHOUR=17;BYMINUTE=0` |
| "每2小时提醒休息" | 2小时休息提醒 | `FREQ=HOURLY;INTERVAL=2` |
| "每4小时关怀提醒" | 4小时关怀提醒 | `FREQ=HOURLY;INTERVAL=4` |

### 文件位置速查

| 用途 | 路径 |
|------|------|
| 保存日报 | `日程/日报/YYYY-MM-DD.md` |
| 保存周报 | `日程/周报/YYYY-WXX.md` |
| 保存月报 | `日程/月报/YYYY-MM.md` |
| 任务列表 | `日程/任务/当前任务.md` |
| 状态记录 | `日程/状态/状态记录.md` |
| 战略静默记录 | `日程/战略静默/YYYY-MM-DD.md` |

### 战略静默数据隔离速查

| 数据类型 | 是否包含静默时段 | 说明 |
|----------|------------------|------|
| 日报统计 | ❌ 不包含 | 只统计净工作时间 |
| 周报/月报 | ❌ 不包含 | 效率指标排除休息 |
| 任务进度 | ⏸ 暂停计时 | 静默期间不计时 |
| 战略静默记录 | ✅ 独立记录 | 存入专属目录 |

---

*Progress Assistant v2.1 - 让进度管理更简单，让休息更有质量*
