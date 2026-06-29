## replay_utest 相关基础说明

本文仅收录 **Testone/优测 流量转用例** 相关工具说明，作为 skill 前置描述文档使用。

使用入口：
- 基于录制流量生成 Testone/优测 测试场景用例：先使用 `GenerateTestPlanByTrafficData` 发起用例生成，再通过 `GetFlow2SceneTaskList` 查询生成结果与 `scene_id`。

本文档**不覆盖**以下内容：
- LogReplay 直接回放
- GoReplay 录制与录制流量查询

## 流量转用例工具

### `GenerateTestPlanByTrafficData`

#### 功能说明
连接优测 Testone 平台，使用流量数据生成测试场景用例。

调用前应先通过 `RecordAgg` / `RecordSearch` 获取流量相关字段（如 `commit_id`、`protocol`、`instance_name` 等），再将这些值作为参数传入本工具。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GenerateTestPlanByTrafficDataInput",
  "type": "object",
  "required": ["app_server_name", "api_name"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "api_name": {"type": "string", "description": "接口名，用于过滤特定流量（必填）"},
    "scene_name": {"type": "string", "description": "测试场景名称（可选，默认自动生成）"},
    "start_time": {"type": "string", "description": "开始时间，格式 YYYY-MM-DD HH:MM:SS（可选）"},
    "end_time": {"type": "string", "description": "结束时间，格式 YYYY-MM-DD HH:MM:SS（可选）"},
    "max_count": {"type": "integer", "description": "最大流量数据条数，默认10"},
    "commit_id": {"type": "string", "description": "流量协议版本号（可选，可从 RecordAgg commitId 维度获取）"},
    "server_name": {"type": "string", "description": "logreplay server name（可选）"},
    "instance_name": {"type": "string", "description": "服务容器名称（可选，可从 RecordAgg instanceName 维度获取）"},
    "protocol": {"type": "string", "description": "协议类型，如 trpc、http（可选，可从 RecordSearch 结果获取）"},
    "traceIds": {"type": "string", "description": "链路ID，多个以 | 分割（可选）"},
    "dir_id": {"type": "integer", "description": "测试场景所在目录ID（可选，默认-1即未分组）"},
    "export_filed_names": {
      "type": "array",
      "items": {"type": "string"},
      "description": "导出字段列表（可选）"
    },
    "label_uuid": {"type": "string", "description": "场景标签（可选，默认 flow2logreplay）"},
    "all_filters": {"type": "array", "items": {"type": "string"}, "description": "流量过滤条件，格式见 record.md「all_filters 流量过滤条件」章节（可选）"}
  },
  "additionalProperties": false
}
```

#### 参数说明

**必填参数：**
1. `app_server_name`（字符串）：服务名称，格式 `app.server`。
2. `api_name`（字符串）：接口名，用于过滤特定流量。对于 HTTP 协议，填写 URI 中问号 `?` 之前的路径部分。

**流量相关参数（建议通过 RecordAgg 获取后传入）：**
3. `commit_id`（字符串，可选）：流量协议版本号。可从 `RecordAgg` 结果中获取（`commitId` 维度）。
4. `protocol`（字符串，可选）：协议类型（如 `trpc`、`http`）。可从 `RecordAgg` 结果中获取（`protocol` 维度）。
5. `instance_name`（字符串，可选）：服务容器名称。可从 `RecordAgg` 结果中获取（`instanceName` 维度）。
6. `server_name`（字符串，可选）：logreplay server name。

**时间范围：**
7. `start_time`（字符串，可选）：开始时间，格式 `YYYY-MM-DD HH:MM:SS`。
8. `end_time`（字符串，可选）：结束时间，格式 `YYYY-MM-DD HH:MM:SS`。

**场景配置：**
9. `scene_name`（字符串，可选）：测试场景名称。未指定时自动生成 `{api_name} 测试用例`。
10. `max_count`（整数，可选）：最大流量数据条数，默认 `10`。
11. `dir_id`（整数，可选）：生成的测试场景所在目录 ID，默认 `-1`（未分组）。
12. `export_filed_names`（字符串数组，可选）：导出字段列表。可选值：
    - `request_header`、`request_body`、`response_header`、`response_body`、`trace_id`
    - `request_binary`、`request_metadata`、`response_metadata`
    - 默认使用前五个。
13. `label_uuid`（字符串，可选）：场景标签。可选值：
    - `flow2logreplay`：流量转回放用例（**默认值**）
    - `flow2api`：流量转接口测试用例
    - `flow2perf`：流量转压测用例
    - `ai2scene`：AI 生成用例
14. `traceIds`（字符串，可选）：链路 ID，多个以 `|` 分割。
15. `all_filters`（字符串数组，可选）：流量过滤条件，格式见 [record.md「all_filters 流量过滤条件」](record.md#all_filters-流量过滤条件) 章节。

**内部自动获取的字段（无需传入）：**
- `userGroupId` / `userProjectId` / `userId`：从鉴权上下文自动获取。
- `business_id`：使用 `userProjectId` 的值。
- `module_id`：通过 `app_server_name` 自动解析。
- `app_name_en` / `module_name_en`：从 `app_server_name` 按 `.` 拆分自动填充。
- `label_group_uuid`：固定值 `system-001`。
- `analysis_type`：固定值 `3`（自定义数据条数）。

#### 推荐调用流程
1. 先调用 `RecordAgg`（默认 `agg_names=["apiName", "commitId", "protocol", "instanceName"]`），返回嵌套树结构，一次获取所有维度数据
2. 将返回结果展开为表格展示给用户，让用户选择目标接口及对应的 `commit_id`、`protocol`、`instance_name`
3. 将用户选择的值作为参数传入 `GenerateTestPlanByTrafficData`

#### 重要提示
- `app_server_name` 和 `api_name` 必须提供，否则无法执行。
- 时间格式为字符串 `YYYY-MM-DD HH:MM:SS`，不是纳秒时间戳。
- `commit_id`、`protocol` 等流量字段不传时后端会使用空值，可能影响生成结果的准确性，建议尽量提供。

#### 输出
调用成功后会返回**流量转用例任务 uuid**，而非用例 ID；后续可通过 `GetFlow2SceneTaskList` 查询任务状态和测试场景用例的 `scene_id`。

### `GetFlow2SceneTaskList`

#### 功能说明
本工具用于获取流量转用例任务列表。

可查询当前团队和项目下的流量转用例任务，返回任务列表信息，包括任务 ID、场景名称、任务状态、创建人、创建时间等；支持通过 `uuid` 筛选指定任务。

#### 输入参数
```json
{"uuid": ""}
```

#### 参数说明
- `uuid`（字符串，可选）：流量转用例任务的 UUID，用于筛选指定任务。不传则返回所有任务。
- 团队 ID 和项目 ID 会从鉴权上下文自动获取，无需手动传入。

#### 输出
调用成功时返回任务列表，每个任务包含以下字段：
- `uuid`：任务 ID
- `scene_name`：场景名称
- `status_num`：任务状态编号
- `status_name`：任务状态说明
- `create_user`：创建人
- `create_time`：创建时间
- `scene_id`：场景 ID
