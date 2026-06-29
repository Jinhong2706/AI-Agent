# 阶段 3：回放周期

> 进入时宣告：「**【阶段 3：回放周期】** 准备执行流量回放...」

## 目标

根据用户意图选择路径：
- **方式 A**：将录制的流量回放到目标服务，验证服务行为一致性。
- **方式 B**：将录制的流量**转化为 Testone/优测 测试场景用例**（仅生成用例，不执行回放）。

## 路径选择

用户提到「Testone/优测 测试用例」「流量转用例」「生成测试场景」→ **方式 B**；否则默认 **方式 A**。

---

## 方式 A：LogReplay 直接回放

适用于快速回归验证。

### 可用工具

| 工具 | 功能 |
|------|------|
| **ExecuteReplay** | 执行流量回放 |
| **GetReplayTaskInfo** | 查询回放任务状态和统计 |
| **DiffConfig** | 查询指定接口的 diff 配置 |
| **SetDiffConfig** | 设置指定接口的 diff 策略配置（白名单、黑名单、自定义策略、预处理策略、自定义脚本等） |
| **QueryEditRuleList** | 查询流量编辑规则列表 |
| **CreateEditRule** | 为指定接口创建流量编辑规则 |
| **UpdateEditRule** | 更新流量编辑规则组的启用开关 |
| **DeleteEditRule** | 删除指定的流量编辑规则组 |
| **EditRuleCheck** | 预览校验流量编辑规则（不落库） |

> 业务默认值：`rate` 默认 100，`number` 默认 100，`replay_type` 默认 0（1=只发不比）。
> GetReplayTaskInfo 状态枚举：0=DEFAULT, 1=INIT, 2=SUCCESS, 3=RUNNING, 4=PROCESSING, 5=FAILED, 6=ABORT

### 步骤

#### 1. 收集回放参数

复用录制阶段的服务名，但回放目标地址【必须】由用户显式指定：

- `addr`：**【不可复用录制阶段的容器地址】**，必须由用户显式提供。若用户未指定，**必须主动询问用户**要回放到哪个地址，【绝不】自动拉取容器列表代替询问。组装 `addr` 参数前，**【必须】先阅读 `references/replay.md`**，根据回放场景（普通回放/双环境回放、直接指定地址/北极星寻址）选择正确的 key 和 value 格式
- `start_time` / `end_time`：不指定则使用今天 `00:00:00` 到 `23:59:59` 的时间范围
- `api_list`：可从阶段 2 接口列表选择
- 其余参数（`rate`、`number`、`replay_type` 等）参见工具 schema 及业务默认值

#### 2. 配置流量处理规则（按需）

用户希望在回放前调整流量处理规则时，可使用以下工具。

> **diff 策略 vs 流量编辑规则：**
> - **diff 策略**：作用于**响应对比阶段**。配置回放得到的响应与原始录制响应之间的比对规则（如白名单、黑名单、忽略字段、自定义对比脚本等），用于决定回放报告中哪些差异会被判定为真正的 diff。**不会修改请求/响应数据本身**。
> - **流量编辑规则**：作用于**请求发送前阶段**。在回放前对请求数据做字段级修改（新增、修改、删除），使回放阶段向目标服务发送的是"被编辑过的流量"。典型场景：替换时间戳、脱敏 userId、删除调试标志等。

**diff 策略配置：**

- `DiffConfig`：查看指定接口当前的 diff 配置
- `SetDiffConfig`：修改 diff 策略（先查后改）

> diff 策略规则（白名单、黑名单、预处理策略、自定义对比策略、自定义脚本、字段匹配等）详见 `references/diffrule.md`。

**流量编辑规则工具：**

| 工具 | 功能 |
|------|------|
| **QueryEditRuleList** | 查询已有规则列表（仅用于查看与取规则组 `id`） |
| **EditRuleCheck** | 预览校验规则效果（不落库） |
| **CreateEditRule** | 为指定接口创建一组流量编辑规则 |
| **UpdateEditRule** | 启用 / 禁用已有规则组（需先 `QueryEditRuleList` 取 `id`） |
| **DeleteEditRule** | 删除指定规则组（需先 `QueryEditRuleList` 取 `id`） |

> 规则语法（`action` / `type` / `key` 路径 / 普通替换 / 正则替换 / 动态占位符）、以及 `server_name` / `msg_name` / `protocol` / `proto_version` 的**字段来源与默认值规则**，详见 [`references/editrule.md`](references/editrule.md)。

#### 新增流量编辑规则步骤

用户表达「新增 / 添加 / 配置流量编辑规则」「编辑请求或响应字段」「替换 / 脱敏 / 删除字段」等意图时走此流程。

##### 1. 发现目标接口

若用户未指定 `api_name`，调用 `RecordAgg` 取当前服务的接口流量聚合列表，以表格展示请求量 Top N，供用户选择目标接口。

##### 2. 观察字段结构

调用 `RecordSearch` 取所选接口的一条实际流量，向用户展示其 `requestBody` / `responseBody` 的 JSON 结构，并从该流量中读取 `protocol` 与 `proto_version` 缓存备用。

> `QueryEditRuleList` 不返回字段结构，不可替代本步骤。

##### 3. 收集编辑意图

基于步骤 2 展示的 JSON 结构，与用户交互收集每条 `ItemRule`：

- `key`：目标字段路径（见 `references/editrule.md` §key 路径规则）
- `action`：`add` / `update` / `delete`
- `value` / `type`：按 `action` 与 `references/editrule.md` §value 的数据类型 填写

需要多条规则时逐条收集。

##### 4. 参数摘要

以表格形式展示完整参数，等待用户确认：

| 参数 | 值 |
|------|-----|
| 接口 | `api_name` |
| protocol / proto_version | 来自步骤 2 读取值（或用户显式指定） |
| msg_name | 用户显式指定；未填写则由工具层从 `api_name` 末尾自动截取 |
| rules | 步骤 3 收集的每条 `key` / `action` / `value` / `type` |

> `server_name` 由工具层内部用 `app_server_name` 自动填入，不在摘要中展示。

##### 5. 预览校验（EditRuleCheck）

用户确认后，先调用 `EditRuleCheck` 做非落库校验。若返回错误（key 路径不匹配、value 格式不合法、pb 未定义字段等），回到步骤 3 或 4 修正参数后重新 Check，直到通过。

##### 6. 创建规则（CreateEditRule）

`EditRuleCheck` 通过后，在正式回复中声明「Check 已通过，正在为您创建流量编辑规则...」→ 再调用 `CreateEditRule` 落库。

#### 修改 / 删除已有规则

1. 调用 `QueryEditRuleList` 取规则组 `id`。
2. 启停规则组用 `UpdateEditRule`；删除整组用 `DeleteEditRule`；需修改规则条目内容则「删除 + 重建」（重建走上述新增流程）。

#### 3. 确认回放目标地址

若用户未提供回放目标地址，**必须直接询问用户**要回放到哪个目标地址（IP:Port），【绝不】自动拉取容器列表。

仅当用户**主动要求**查看可用节点列表时，才调用 `GetGoReplayNodeList` 获取节点列表，以表格展示供用户选择：

| 序号 | 来源 | 节点名 | IP:Port | 协议 |
|------|------|--------|---------|------|
| 1 | 服务容器 | xxx | x.x.x.x:xxxx | trpc |
| 2 | Agent | agent-node-1 | x.x.x.x:8080 | http |

用户选择后，取所选节点的 IP:Port 组装为 `addr` 参数。组装前**【必须】先阅读 `references/replay.md`**，根据实际回放场景选择正确的参数格式（不同场景下 key 和 value 的含义不同）。

> ⚠️ 即使录制阶段已选择过容器，回放目标地址仍【必须】由用户在本阶段显式提供，【绝不】自动复用或自动获取。

#### 4. 参数确认

所有回放参数准备完成后，展示完整参数摘要（【必须】醒目展示回放目标地址）→ 等待用户明确确认。确认前【绝不】调用 `ExecuteReplay`。

#### 5. 启动回放

用户确认后，先在正式回复中声明「正在为您启动回放...」→ 再调用 `ExecuteReplay` → 获取 task_id。

#### 6. 查询进度

调用 `GetReplayTaskInfo` 执行**一次**状态查询：

```
回放进度：已回放 {success}/{total}，成功率 {success_rate}%
```

- status=2（SUCCESS）→ 「✅ 回放已完成」，提示是否查看结果。用户确认后进入阶段 4。【绝不】自动进入
- status=5（FAILED）→ 提取 fail_detail 解析原因
- status=6（ABORT）→ 告知回放已中止
- 仍在运行 → 展示进度，提示用户可稍后查询。【绝不】自动轮询

---

## 方式 B：Testone/优测 流量转用例

适用于持续化回归接口测试。本阶段仅负责将录制流量**转化为 Testone/优测 测试场景用例**，用例生成完成即结束。

### 可用工具

| 工具 | 功能 |
|------|------|
| **GenerateTestPlanByTrafficData** | 从录制流量生成测试场景用例（返回任务 uuid） |
| **GetFlow2SceneTaskList** | 通过任务 uuid 查询生成状态并获取 scene_id |

### 核心路径

`RecordSearch → GenerateTestPlanByTrafficData → GetFlow2SceneTaskList（获取 scene_id）`

### 步骤

#### 1. 确认流量数据

调用 `RecordSearch` 确认目标接口存在可用的录制流量。

#### 2. 生成测试场景

调用 `GenerateTestPlanByTrafficData`，传入：
- `app_server_name`（复用录制阶段的服务名）
- `api_name`（从阶段 2 接口列表选择）
- `scene_name`（用户未指定时默认「{api_name} 测试用例」）
- `start_time` / `end_time`（不指定则使用今天 `00:00:00` 到 `23:59:59` 的时间范围）
- `max_count`（用户未指定时默认 `10`）

> ⚠️ 返回的是任务 uuid，【必须】调用 `GetFlow2SceneTaskList` 查询任务状态，完成后获取 scene_id。

#### 3. 展示生成结果

调用 `GetFlow2SceneTaskList` 获取生成结果后，向用户展示测试场景概要（用例数量、接口覆盖、scene_id）。

> 用例生成完成即为本流程终点，Skill 不再介入后续操作。
