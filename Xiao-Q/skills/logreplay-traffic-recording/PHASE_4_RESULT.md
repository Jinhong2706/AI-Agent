# 阶段 4：结果查询周期

> 进入时宣告：「**【阶段 4：结果查询周期】** 正在查询回放结果...」

仅用于查询**方式 A（LogReplay 直接回放）**的回放结果。

> 方式 B（Testone/优测 流量转用例）在阶段 3 生成测试场景用例后即结束，本阶段不涉及。

---

## 可用工具

| 工具 | 功能 |
|------|------|
| **TaskList** | 分页查询回放任务列表 |
| **GetReplayTaskInfo** | 查询回放任务汇总 |
| **SearchReport** | 查询回放报告详情（result: 1=成功, 2=错误, 3=失败） |
| **ReportAgg** | 回放报告聚合查询（type: 0=Default, 1=APIName, 2=ErrorField, 3=Reason, 4=TraceID, 5=ReplayTag） |
| **SearchResponse** | 查询【普通回放】单条流量 diff 详情（录制 vs 回放） |
| **TwoEnvReplayResultSearch** | 查询【双环境回放】单条流量在两个目标环境上的回放响应 |

> `SearchResponse` 与 `TwoEnvReplayResultSearch` 的接口选择规则、`replay_show_type` 判定逻辑见 [references/replay.md](references/replay.md)。

## 步骤

### 1. 任务列表（按需）

当用户需要先查看历史回放任务列表、筛选目标任务或确认 `task_id` 时，先调用 `TaskList` 展示任务列表。

### 2. 汇总报告

在用户已明确目标任务后，调用 `GetReplayTaskInfo` 展示：


| 指标 | 值 |
|------|-----|
| 回放总量 | {total} |
| 成功数 | {success} |
| 失败数 | {fail} |
| 成功率 | {success_rate}% |
| 回放耗时 | {duration} |
| 目标地址 | {addr} |

### 3. 失败分析（如有失败）


- 调用 `ReportAgg`（type=1）按接口聚合失败分布
- 调用 `SearchReport`（result=2）查询失败详情

| 接口名 | 失败数 | 失败原因 |
|--------|--------|----------|
| {api_name} | {count} | {error_type} |

### 4. Diff 详情

用户指定 trace_id 后查询单条流量 diff 比对结果。

> **接口选择**：普通回放走 `SearchResponse`，双环境回放走 `TwoEnvReplayResultSearch`，二者**不可混用**。具体判定规则（`replay_show_type` / `replay_env_tag` 取值、判断流程、展示模板）见 [references/replay.md](references/replay.md) 中 `SearchResponse` 与 `TwoEnvReplayResultSearch` 章节。

普通回放展示：

| 字段 | 录制响应 | 回放响应 | 差异 |
|------|----------|----------|------|
| {field} | {record_value} | {replay_value} | {diff} |

双环境回放展示：

| 目标环境 | 响应内容 | 备注（reason 等） |
|---------|----------|------------------|
| {target_A} | {response_A} | {reason_A} |
| {target_B} | {response_B} | {reason_B} |

### 5. 回放报告链接

`ExecuteReplay` 和 `GetReplayTaskInfo` 的响应中已包含 `report_url` 字段，直接展示给用户即可。

**展示格式：** 使用 Markdown 链接：`[📊 点击查看回放报告]({report_url})`

---

## 后续操作引导

- 查看更多 diff 详情 → 调用 SearchResponse
- 重新回放 → 返回阶段 3
- 结束流程
