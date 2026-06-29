---
name: schedule-reminder
description: Provides unified scheduling and management for all types of timed tasks. Supports creating one-time tasks (e.g., "Remind me to take medicine in 15 minutes") and recurring cron tasks (e.g., "Remind me to have a meeting every Friday at 10:00 AM"), and allows listing and deleting existing tasks. All time-based reminders, schedules, and recurring jobs must be created through this skill.
version: 0.0.1
author: qqai
user-invocable: true
disable-model-invocation: false
tags: [timer, schedule, crontab, cron]
trigger-phrases:
  - "{time}提醒我{content}"
  - "取消我的定时任务{job_id}"
  - "查看我的所有定时任务"
  - "每天{hour}提醒我{content}"
  - "每周{weekday} {hour}提醒我{content}"
timeout: 300s
---

## 强制约束（模型必须遵守）
- 解析用户指令时，优先判定任务类型：先判断是一次性（task）还是循环（cron），再生成对应参数，禁止混用参数；
- 生成 start_time 时，必须基于 system prompt 中的「Runtime: agent=main | time= {datetime} 」计算，禁止使用上下文无关时间；
- 生成 cron 表达式时，必须严格匹配下面的映射表，禁止自定义表达式；
- 所有参数值必须用双引号包裹，JSON 格式必须合法（无多余 / 缺失括号）。
- 删除、取消任务时，如果无法从上下文中确定job_id，使用list（列举任务）查询后根据描述得到精确的job_id

## 核心参数规则（必须严格遵守）
### 1. 通用参数（所有操作必填）
| 参数名   | 类型   | 必选 | 取值范围                | 说明                     |
|----------|--------|------|-------------------------|--------------------------|
| method   | string | 是   | create/list/delete      | 操作类型：创建/列举/删除 |

### 2. 「创建一次性任务」参数（method=create 且 非循环任务）
| 参数名         | 类型     | 必选 | 示例值                   | 说明                                                        |
|-------------|--------|----|-----------------------|-----------------------------------------------------------|
| description | string | 是  | "15分钟后提醒我吃药"          | 任务描述，必须和用户原始指令一致                                          |
| job_type    | string | 是  | task                  | 固定值：task（标识一次性任务）                                         |
| start_time  | string | 是  | "2026-03-20 13:00:00" | 任务执行时间，格式：YYYY-MM-DD HH:MM:SS，需基于当前系统时间计算                 |
| time_delta  | string | 是  | "15m"                 | Time interval from now (e.g., "15m" for 15 minutes later) |

### 3. 「创建循环任务」参数（method=create 且 循环任务）
| 参数名        | 类型   | 必选 | 示例值                  | 说明                                  |
|---------------|--------|------|-------------------------|---------------------------------------|
| description   | string | 是   | "每周五早上10点提醒我开周会" | 任务描述，必须和用户原始指令一致    |
| job_type      | string | 是   | cron                    | 固定值：cron（标识循环任务）          |
| cron          | string | 是   | "0 10 * * 5"            | cron表达式，严格按下方映射规则生成    |

### 4. 「删除任务」参数（method=delete）
| 参数名   | 类型   | 必选 | 示例值                  | 说明         |
|----------|--------|------|-------------------------|------------|
| job_id   | string | 是   | "t_ae59b628bd458871"    | 要删除的任务ID,精确取消。从之前 create 返回、list 结果中获取。**推荐先 list 再用 task_id 精确取消** |

### 5. 「列举任务」参数（method=list）
- 无额外参数，仅需 `{"method": "list"}`

## 指令→参数映射规则（模型必须严格执行）
### 规则1：识别一次性任务（生成 task 类型参数）
用户指令包含以下关键词 → 判定为一次性任务，生成 `job_type: task` + `start_time`：
- 时间关键词：X分钟后、X小时后、明天、后天、下周一（具体某天）、几点几分（单次）
- 示例映射：
    - 用户说："15分钟后提醒我吃药" → 计算当前时间+15分钟，生成 `start_time: "2026-03-20 13:15:00"`，`job_type: task`， `time_delta: "15m"`
    - 用户说："明天下午3点提醒我开会" → 生成 `start_time: "2026-03-21 15:00:00"`，`job_type: task`， `time_delta: "1d"`

### 规则2：识别循环任务（生成 cron 类型参数）
用户指令包含以下关键词 → 判定为循环任务，生成 `job_type: cron` + cron表达式：
- 循环关键词：每天、每周、每月、每隔、每逢、每天X点、每周XX点
- 自然语言→cron 精准映射（必须严格按此转换）：
  | 自然语言指令          | 对应cron表达式 | 备注 |
  |-----------------------|----------------|------|
  | 每5分钟提醒我喝水     | */5 * * * *    | 分钟级循环 |
  | 每天早上8点提醒我打卡 | 0 8 * * *      | 每日循环 |
  | 每周五早上10点开周会  | 0 10 * * 5     | 每周循环 |
  | 每周一到周五9点提醒   | 0 9 * * 1-5    | 工作日循环 |
  | 每周六周日中午12点提醒 | 0 12 * * 6,0   | 周末循环 |
  | 每月1号9点提醒        | 0 9 1 * *      | 每月循环 |

## 正确命令示例（参数与规则严格对应）
```bash
# 创建一次性任务：15分钟后提醒吃药（基于当前时间计算start_time）
exec("schedule-reminder --parameters '{
    \"method\": \"create\",
    \"description\": \"15分钟后提醒我吃药\",
    \"job_type\": \"task\",
    \"start_time\": \"2026-03-20 13:15:00\",
    \"time_delta\": \"15m\"    
}'")

# 创建循环任务：每周五10点开周会（cron表达式严格按映射表生成）
exec("schedule-reminder --parameters '{
    \"method\": \"create\", 
    \"description\": \"每周五早上10点提醒我开周会\",
    \"job_type\": \"cron\",
    \"cron\": \"0 10 * * 5\"
}'")

# 列出所有任务
exec("schedule-reminder --parameters '{
    \"method\": \"list\"
}'")

# 删除指定任务
exec("schedule-reminder --parameters '{
    \"method\": \"delete\",
    \"job_id\": \"t_ae59b628bd458871\"
}'")
```

## 输出格式（修正语法错误）
### 成功响应
```json
{
  "success": true,
  "result": {
    "job_id": "t_a00001"
  },
  "status": 0
}
```