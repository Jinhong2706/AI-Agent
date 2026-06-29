# 知识回顾自动化配置指南

## 快速创建流程

### 步骤 1：询问用户偏好

```
📅 创建回顾自动化

请告诉我：
1. **回顾周期**：每天 / 每周 / 每月 / 自定义？
2. **回顾时间**：具体几点？（如：每天 21:00 / 每周五 18:00）
3. **回顾维度**：基础版 / 职业适配版 / 自定义组合？
4. **提醒方式**：微信推送 / 无需提醒？

输入示例："每周五18点，基础版，微信推送"
```

### 步骤 2：解析用户输入

将用户输入映射为 rrule 规则：

| 用户选择 | rrule |
|---------|-------|
| 每天 9:00 | `FREQ=DAILY;BYHOUR=9;BYMINUTE=0` |
| 每天 21:00 | `FREQ=DAILY;BYHOUR=21;BYMINUTE=0` |
| 每周五 18:00 | `FREQ=WEEKLY;BYDAY=FR;BYHOUR=18;BYMINUTE=0` |
| 每周一 9:00 | `FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0` |
| 每月最后一天 20:00 | `FREQ=MONTHLY;BYMONTHDAY=-1;BYHOUR=20;BYMINUTE=0` |
| 每两周周五 17:00 | `FREQ=WEEKLY;INTERVAL=2;BYDAY=FR;BYHOUR=17;BYMINUTE=0` |

### 步骤 3：创建自动化

使用 automation_update 工具创建：

```python
automation_update(
    mode="suggested create",
    name="[用户自定义名称]",
    prompt=f"""执行知识回顾任务：

1. 读取工作区的记忆文件：
   - .workbuddy/memory/MEMORY.md（长期记忆）
   - .workbuddy/memory/YYYY-MM-DD.md（近期日记）

2. 分析并生成回顾清单：
   - 本周期内新增的信息
   - 待确认或可能过时的信息
   - 建议清理的临时内容

3. 推送提醒用户确认

4. 根据用户回复更新记忆文件

只沉淀稳定且长期有价值的信息，不记录临时上下文。""",
    cwds='["{工作区路径}"]',
    rrule="[用户选择的规则]",
    status="ACTIVE"
)
```

### 步骤 4：记录到 MEMORY

将配置追加到工作区的 MEMORY.md：

```markdown
## 自动化配置

- 知识回顾：[自动化名称]
  - 周期: [周期描述]
  - 时间: [具体时间]
  - 维度: [回顾深度]
  - 创建日期: [YYYY-MM-DD]
```

## 自动化 Prompt 模板

### 简略版
```
执行快速回顾：读取记忆文件，列出 3-5 条关键变化，询问是否需要详细回顾。
```

### 标准版（推荐）
```
执行标准回顾：读取记忆文件，生成包含分类的回顾清单，推送用户确认，根据回复更新。
```

### 详细版
```
执行深度回顾：分析所有记忆文件，生成全面报告（画像变化、偏好演变、知识更新、经验总结），推送深度报告给用户。
```

## 常见配置示例

| 人群 | 周期 | 时间 | 深度 | rrule |
|------|------|------|------|-------|
| 职场人士 | 每周 | 周五 18:00 | 标准 | FREQ=WEEKLY;BYDAY=FR;BYHOUR=18;BYMINUTE=0 |
| 学生 | 每天 | 21:00 | 简略 | FREQ=DAILY;BYHOUR=21;BYMINUTE=0 |
| 自由职业者 | 每月 | 最后一天 20:00 | 详细 | FREQ=MONTHLY;BYMONTHDAY=-1;BYHOUR=20;BYMINUTE=0 |
| 管理者 | 双周 | 周五 17:00 | 详细 | FREQ=WEEKLY;INTERVAL=2;BYDAY=FR;BYHOUR=17;BYMINUTE=0 |
