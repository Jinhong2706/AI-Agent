# 阶段 1：录制周期

> 进入时宣告：「**【阶段 1：录制周期】** 正在收集录制参数...」

## 目标

启动流量录制并监控状态。支持两种录制方式：
- **GoReplay 录制方式**（默认）：通过 GoReplay 抓包录制
- **tRPC 插件录制方式**：通过 tRPC 插件节点录制

## 录制方式选择

用户提到「tRPC 插件」「插件录制」「tRPC 插件录制」→ **tRPC 插件录制方式**；否则默认 **GoReplay 录制方式**。

## 可用工具

### GoReplay 录制方式工具

| 工具 | 功能 |
|------|------|
| **GetGoReplayNodeList** | 获取节点列表，返回 `service_list`（123服务容器节点）和 `agent_list`（Agent 注册节点） |
| **StartGoReplay** | 启动 GoReplay 录制 |
| **StopGoReplayTask** | 停止正在执行的录制任务 |
| **MultiGetTaskStatus** | 批量查询录制任务状态 |
| **GetGoReplayStatus** | 通过 IP:Port 或 Agent ID 查询录制状态 |
| **GetGoReplayExecTask** | 获取 GoReplay 录制任务列表 |
| **GetProtoInfoList** | 获取协议信息列表（协议版本号 `commit_id`） |
| **GetProtocolName** | 获取具体的协议类型名称 |

### tRPC 插件录制方式工具

| 工具 | 功能 |
|------|------|
| **GetTrpcPluginInstanceList** | 获取 tRPC 插件录制方式的节点实例列表，返回 `list`（Instance 列表） |
| **UpdateTrpcPluginConfig** | 更新 tRPC 插件节点配置（开启/关闭录制或回放、修改录制参数等） |


## GoReplay 录制方式步骤

### 1. 收集基础参数

只收集不确认，先从用户消息中提取已有参数，仅询问缺失项：

- `服务名`（即 `app_server_name`，格式 `app.server`，如 `myapp.myserver`）

> 若用户已提供 module_id、env 等非当前阶段必需参数，直接缓存供后续使用，【不主动询问】。
> `env` 为可选参数，用户主动指定时使用，【不主动询问】。

### 2. 获取节点列表

调用 `GetGoReplayNodeList`，统一以表格展示 `service_list` 和 `agent_list`：

| 序号 | 来源 | 节点名 | IP:Port | 协议 |
|------|------|--------|---------|------|
| 1 | 服务容器 | xxx | x.x.x.x:xxxx | trpc |
| 2 | Agent | agent-node-1 | x.x.x.x:8080 | http |

> Agent 节点的 IP:Port 由 `ip` + `port_protocol[].port` 拼接，协议取 `port_protocol[].protocol`。一个 Agent 节点可能包含多个端口协议组合，每个组合作为独立行展示。

### 3. 用户选择节点

选择后自动填充 `container_name_params`，Agent 节点需将 `is_agent` 设为 true。

> **重要**：`container_name_params` 的 key 必须使用**完整容器名**（即 GetGoReplayNodeList 返回的 `docker_name` / `name` 原始值），不可截断或简写。

### 4. 一次性确认并启动

所有参数（基础参数 + 容器选择 + 录制时长等）准备完成后，展示完整参数摘要 → 用户确认 → 调用 `StartGoReplay`。

### 5. 解析启动结果

逐容器展示执行状态，失败容器（error_code != 0）展示错误并询问是否重试。

### 6. 查询状态

调用 `MultiGetTaskStatus` 执行**一次**状态查询：

- 已完成 → 展示录制结果，提示：「录制已完成，是否需要进入数据观察阶段？」等待用户确认。【绝不】自动进入阶段 2
- 仍在运行 → 展示当前状态，提示：「录制任务正在进行中（预计 {record_time} 小时），您可以随时告诉我查询录制状态。」
- 【绝不】自动持续轮询。保留 task_id 供后续查询

### 7. 结束录制

定时到期自动停止，或用户主动要求停止时调用 `StopGoReplayTask`（传入 `app_server_name` 和 `task_id`）。

## StartGoReplay 的 container_name_params 组装规则

key 为**完整容器名**（直接取 GetGoReplayNodeList 返回的 `docker_name` 或 `name` 字段原始值，禁止截断或简写），value 包含 `go_replay_params` 数组，每项字段值来源：

| 字段 | 来源 |
|------|------|
| `ip_port` | service_list 取 `address` 字段；agent_list 由 `ip` + `port_protocol[].port` 拼接（如 `10.0.0.1:8080`） |
| `protocol` | 取自 GetProtocolName 返回的 `protocol_name`。若 GetGoReplayNodeList 返回节点列表为空，默认 `"http"`，无需调用 GetProtocolName |
| `protocol_service_version` | 取自 GetProtoInfoList 返回的 `commit_id`（列表为空时默认 `"0.0.0"`） |
| `extend` | 扩展参数数组，仅在用户明确指定时传入。可用值：`--output-logreplay-record-limit`（录制条数上限）。例如用户说"最多录 10000 条"，则传 `["--output-logreplay-record-limit", "10000"]` |
| `record_time` | 默认 6 小时 |
| `is_agent` | Agent 节点设为 true，默认 false |

## tRPC 插件录制方式步骤

### 1. 收集基础参数

只收集不确认，先从用户消息中提取已有参数，仅询问缺失项：

- `服务名`（即 `app_server_name`，格式 `app.server`，如 `myapp.myserver`）

### 2. 获取节点实例列表

调用 `GetTrpcPluginInstanceList`，以表格展示返回的 `list`（Instance 列表）：

| 序号 | 容器名 | IP:Port | 服务名 | SDK版本 | 录制状态 | 更新时间 |
|------|--------|---------|--------|---------|---------|---------|
| 1 | container-1 | x.x.x.x:xxxx | trpc.demo.hello | v1.0.0 | 录制中 | 2026-04-16 |

> 每个 Instance 包含 `info`（节点基础信息）、`config`（节点配置）、`status`（节点状态）。
> - `info.docker_name`：容器名
> - `info.ip` + `info.port`：IP:Port
> - `info.service_name`：服务名
> - `info.sdk_version`：SDK 版本
> - `info.update_time`：更新时间
> - `config.enable`：录制回放总开关
> - `config.type`：节点类型（空/录制/回放）
> - `status.logreplay_status`：logreplay 状态

### 3. 展示节点信息

将获取到的节点列表以表格形式展示给用户，供用户查看当前 tRPC 插件录制节点的状态。

> 展示时需标明每个节点的当前模式和开关状态：
> - `config.is_replay_server=false` + `config.enable=true` → 录制中
> - `config.is_replay_server=true` + `config.enable=true` → 回放中
> - `config.enable=false` → 已关闭

### 4. 用户选择节点并确认操作

用户选择要操作的节点后，展示操作摘要并获得确认：

```
| 参数 | 值 |
|------|-----| 
| 应用/服务 | xxx.xxx |
| 目标节点 | container-1 (x.x.x.x:xxxx) |
| 操作 | 开启录制 |

确认无误请回复"确认"，需修改请告知具体参数。
```

### 5. 更新节点配置启动录制

根据用户选择的操作（开启/关闭录制），调用 `UpdateTrpcPluginConfig`。具体的参数组装规则、默认值与字段约束详见 `UpdateTrpcPluginConfig` 工具定义和 `references/record.md`，【不在本流程中展开】。

### 6. 解析更新结果

展示更新结果中的 `updated` 字段（成功更新的节点数），失败时展示 `base_rsp.msg` 错误信息并询问是否重试。
