## replay 相关基础说明

本文仅收录 **LogReplay 直接回放** 与 **回放结果查询** 相关工具说明，作为 skill 前置描述文档使用。

不包含以下内容：
- Testone/优测 流量转用例（见 `replay_utest.md`）

## 直接回放工具

### `ExecuteReplay`

#### 功能说明
本工具用于执行流量回放任务。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExecuteReplayInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "commit_id": {"type": "string", "description": "录制流量的协议版本号"},
    "number": {"type": "integer", "description": "回放请求个数，默认值100"},
    "rate": {"type": "integer", "description": "回放速率，默认值100"},
    "api_list": {"type": "array", "items": {"type": "string"}, "description": "回放接口列表"},
    "addr": {
      "type": "object",
      "description": "目标地址映射，key 为完整服务名（如 trpc.app.server.service）或 default_target",
      "additionalProperties": {
        "type": "object",
        "description": "目标地址信息",
        "properties": {
          "addr": {
            "type": "array",
            "description": "目标地址列表",
            "items": {"type": "string"}
          }
        }
      }
    },
    "trace_id_list": {"type": "array", "items": {"type": "string"}, "description": "trace_id列表，传入后忽略number/api_list"},
    "start_time": {"type": "number", "description": "开始时间戳（纳秒），默认30天前当天开始时间（00:00:00）"},
    "end_time": {"type": "number", "description": "结束时间戳（纳秒），默认当天结束时间（23:59:59）"},
    "replay_type": {"type": "integer", "description": "回放类型，默认0；1表示只发不比"},
    "service_name": {"type": "string", "description": "服务名"},
    "instance_name": {"type": "string", "description": "实例名"},
    "env": {"type": "string", "description": "回放流量的环境"},
    "select_target_by_commit_id": {"type": "boolean", "description": "是否按commit_id强制选目标，默认不填"},
    "diffy_dockers": {"type": "array", "items": {"type": "string"}, "description": "diffy对照容器，默认不填"},
    "disable_white": {"type": "boolean", "description": "是否允许白名单流量，默认false"},
    "all_filters": {"type": "array", "items": {"type": "string"}, "description": "统一过滤条件，默认不填"},
    "replay_env_tag": {"type": "boolean", "description": "双环境回放标记，默认false"},
    "is_devnet": {"type": "boolean", "description": "是否devnet，默认false"},
    "rules": {
      "type": "object",
      "description": "流量编辑规则，key/value 都是字符串",
      "additionalProperties": {"type": "string"}
    },
    "process_timeout": {"type": "integer", "description": "数据处理超时秒数，默认30s"},
    "is_async_report": {"type": "boolean", "description": "是否异步上报，默认false"},
    "polaris_name": {"type": "string", "description": "北极星寻址名"},
    "flow_type": {"type": "integer", "description": "流量类型，默认0流量，1用例"},
    "req_rewrite": {"type": "array", "items": {"type": "string"}, "description": "临时编辑规则，默认不填"},
    "is_async_replay": {"type": "boolean", "description": "是否异步回放，默认false"},
    "frequency": {"type": "integer", "description": "回放频率，单位100ms，默认不填"},
    "get_target_type": {"type": "integer", "description": "目标选择类型，默认值不填"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `start_time` / `end_time` 未传时默认使用最近 30 天范围：`start_time` 为 30 天前当天 `00:00:00` 的纳秒时间戳，`end_time` 为当天 `23:59:59` 的纳秒时间戳。
- 其余字段按需填写；大量字段具备后端默认值，可按业务场景逐步补充。
- 大模型不要随意传入，除非用户明确指定。

##### `addr` 参数详细说明

`addr` 是回放目标地址映射，**必填**，类型为 `map<string, Address>`，其中 key 为完整服务名（如 `trpc.app.server.service`）或 `"default_target"`，value 为地址列表对象（包含 `addr` 字符串数组）。

**填写场景总览：**

| 场景 | `replay_env_tag` | `polaris_name` | key 的含义 | value（`addr`）的含义 |
|------|:-:|:-:|---|---|
| 双环境回放 + 直接指定地址 | `true` | 空 | 固定为 `"default_target"` | `IP:Port` 列表 |
| 双环境回放 + 北极星寻址 | `true` | 非空 | 固定为 `"default_target"` | **环境名**列表（非 IP） |
| 普通回放 + 直接指定地址 | `false` | 空 | 完整服务名 或 `"default_target"` | `IP:Port` 列表 |
| 普通回放 + 北极星寻址 | `false` | 非空 | 完整服务名 | **namespace** 列表 |

**场景示例：**

1. **普通回放 + 直接指定地址**（最常用）：

   单服务：
   ```json
   {
       "addr": {
           "default_target": {
               "addr": ["11.181.210.90:12317"]
           }
       }
   }
   ```

   多服务（key 必须为完整服务名）：
   ```json
   {
       "addr": {
           "trpc.app.server1.service": { "addr": ["127.0.0.1:2020"] },
           "trpc.app.server2.service": { "addr": ["127.0.0.2:3030"] }
       }
   }
   ```

2. **双环境回放 + 直接指定地址**：
   ```json
   {
       "replay_env_tag": true,
       "addr": {
           "default_target": {
               "addr": ["127.0.0.1:2025", "127.0.0.2:2020"]
           }
       }
   }
   ```

3. **双环境回放 + 北极星寻址**（value 为环境名，非 IP）：
   ```json
   {
       "replay_env_tag": true,
       "polaris_name": "trpc.app.server.service",
       "addr": {
           "default_target": {
               "addr": ["Development", "Production"]
           }
       }
   }
   ```

4. **普通回放 + 北极星寻址**（value 为 namespace，非 IP；key 必须为完整服务名）：
   ```json
   {
       "polaris_name": "trpc.app.server.service",
       "addr": {
           "trpc.app.server.service": {
               "addr": ["Development", "Production"]
           }
       }
   }
   ```

**地址格式要求：** 直接指定地址时，必须为 `IP:Port` 格式（如 `11.181.210.90:12317`），IP 必须合法，端口必须为数字。域名（如 `localhost:8080`）或缺少端口（如 `127.0.0.1`）均不合法。

**注意事项：**
- `addr` 为**必填**参数，必须明确指定回放目标地址
- `target_dockers` 优先级高于 `addr`：非双环境模式下，同时指定两者时优先使用 `target_dockers`
- 双环境回放时 key **必须**为 `"default_target"`
- 北极星模式下 value 含义不同：不是 `IP:Port`，而是环境名或 namespace
- 多服务场景中 key 必须为完整的服务名称（如 `trpc.app.server.service`），系统按 `recordMap` 中的 service 进行匹配过滤，确保每个录制服务都有对应的回放目标

#### 输出
调用成功时返回 `Success executeReplay, data: ...`，其中 `data` 对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ExecuteReplayRsp",
  "description": "执行流量回放任务响应体",
  "type": "object",
  "properties": {
    "base_rsp": {
      "type": "object",
      "description": "基础响应结构",
      "properties": {
        "code": {"type": "integer", "description": "响应状态码"},
        "msg": {"type": "string", "description": "响应消息"}
      }
    },
    "task_id": {"type": "integer", "description": "任务ID"},
    "report_url": {"type": "string", "description": "回放报告链接，可直接跳转到 Testone/优测 平台查看详细报告"}

  }
}
```

### `GetReplayTaskInfo`

#### 功能说明
本工具用于查询回放任务状态和统计信息。

> **判断双环境回放**：响应 `data.replay_show_type` 字段值为 `"0_1"` 时表示该任务为**双环境回放**任务（与 `ExecuteReplay` 入参 `replay_env_tag=true` 等价）。后续查询单条流量响应时必须改用 `TwoEnvReplayResultSearch`，**禁止**使用 `SearchResponse`。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetReplayTaskInfoInput",
  "type": "object",
  "properties": {
    "app_server_name": {
      "type": "string",
      "description": "服务名称，格式为app.server"
    },
    "task_id": {
      "type": "integer",
      "description": "任务ID"
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。服务名称格式为 `app.server`。
- `task_id`：**必填**。回放任务 ID。

#### 输出
调用成功时返回 `Success getReplayTaskInfo, data: ...`，其中 `data` 对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TaskInfoRsp",
  "description": "查询回放任务状态响应体",
  "type": "object",
  "properties": {
    "base_rsp": {
      "type": "object",
      "description": "基础响应结构",
      "properties": {
        "code": {"type": "integer", "description": "响应状态码"},
        "msg": {"type": "string", "description": "响应消息"}
      }
    },
    "report_url": {"type": "string", "description": "回放报告链接，可直接跳转到 Testone/优测 平台查看详细报告"}
,
    "data": {
      "type": "object",
      "description": "任务信息",
      "properties": {
        "id": {"type": "integer", "description": "任务ID"},
        "module_id": {"type": "string", "description": "模块ID"},
        "operator": {"type": "string", "description": "任务启动人"},
        "status": {"type": "integer", "description": "任务状态 0默认 1初始化 2成功 3进行中 4数据处理中 5失败 6中止"},
        "total": {"type": "integer", "description": "回放总数"},
        "success": {"type": "integer", "description": "成功数"},
        "fail": {"type": "integer", "description": "失败数"},
        "rate": {"type": "integer", "description": "回放速率"},
        "create_time": {"type": "string", "description": "任务创建时间"},
        "duration": {"type": "integer", "description": "任务持续时间"},
        "record_commit_id": {"type": "string", "description": "录制数据协议版本id"},
        "comment": {"type": "string", "description": "任务备注"},
        "fail_reason_mark": {"type": "string", "description": "失败原因"},
        "addrs": {"type": "string", "description": "回放目标地址"},
        "fail_detail": {"type": "string", "description": "失败原因统计"},
        "replay_type": {"type": "integer", "description": "回放类型，0正常回放，1只发不比"},
        "replay_commit_id": {"type": "string", "description": "回放节点代码git版本"},
        "rbc_used": {"type": "boolean", "description": "是否使用rbc filter"},
        "trace_id": {"type": "string", "description": "回放调用链ID"},
        "target_module_id": {"type": "string", "description": "目标服务模块ID"},
        "replay_show_type": {"type": "string", "description": "页面默认流量对比标识。**值为 `0_1` 时代表双环境回放（等价于 replay_env_tag=true）**，否则为普通回放。该字段是阶段 4 选择 diff 详情接口（SearchResponse vs TwoEnvReplayResultSearch）的判定依据"},
        "success_rate": {"type": "number", "description": "用例执行成功率"},
        "rules": {"type": "string", "description": "回放编辑规则"},
        "flow_type": {"type": "integer", "description": "流量类型，0流量 1用例"},
        "origin_req": {"type": "string", "description": "回放任务原始信息"},
        "fail_detail_obj": {
          "type": "object",
          "description": "失败详情对象",
          "properties": {
            "diff_failed": {"type": "integer", "description": "diff失败数"},
            "send_failed": {"type": "integer", "description": "发送失败数"},
            "report_failed": {"type": "integer", "description": "上报失败数"},
            "dial_failed": {"type": "integer", "description": "连接失败数"},
            "write_failed": {"type": "integer", "description": "写入失败数"},
            "read_failed": {"type": "integer", "description": "读取失败数"},
            "mock_aspect_failed": {"type": "integer", "description": "mock切面失败数"},
            "diff_fail_mock_aspect_failed": {"type": "integer", "description": "diff失败且mock切面失败数"}
          }
        },
        "tag_detail": {
          "type": "object",
          "description": "回放tag统计信息",
          "properties": {
            "replay_mark": {
              "type": "object",
              "description": "回放标记统计",
              "additionalProperties": {"type": "integer"}
            }
          }
        }
      }
    }
  }
}
```

### `TaskList`

#### 功能说明
本工具用于分页查询回放任务列表。

> **判断双环境回放**：返回的 `data[].replay_show_type` 字段值为 `"0_1"` 时，表示该任务为**双环境回放**任务（与 `ExecuteReplay` 入参 `replay_env_tag=true` 等价）。在阶段 4 决定调用哪个 diff 详情接口时，应优先依据该字段。

#### 输入参数
```json
{"app_server_name":"", "page":1, "page_size":20, "operator":"", "status":[], "comment":"", "start_time":"", "end_time":"", "task_id":""}
```

#### 参数说明
1. `app_server_name`（字符串，必填）：服务名称，格式 `app.server`。
2. `page`（整数，可选）：页码，默认值 `1`。
3. `page_size`（整数，可选）：每页数量，默认值 `20`。
4. `operator`（字符串，可选）：任务启动人。
5. `status`（数组，可选）：任务状态过滤，取值：`0` 默认、`1` 初始化、`2` 成功、`3` 进行中、`4` 数据处理中、`5` 失败、`6` 中止。
6. `comment`（字符串，可选）：任务备注过滤。
7. `start_time`（字符串，可选）：开始时间，默认 30 天前当天开始时间。
8. `end_time`（字符串，可选）：结束时间，默认当天结束时间。
9. `task_id`（字符串，可选）：任务 ID 过滤。

#### 输出
调用成功时返回 `Success taskList, data: ...`，其中 `data` 对应结构：

```json
{
  "base_rsp": {"code": 0, "msg": ""},
  "page_rsp": {"page": 1, "page_size": 20, "total": 0},
  "data": [
    {
      "id": 0,
      "module_id": "",
      "operator": "",
      "status": 0,
      "total": 0,
      "success": 0,
      "fail": 0,
      "rate": 0,
      "create_time": "",
      "duration": 0,
      "record_commit_id": "",
      "comment": "",
      "fail_reason_mark": "",
      "addrs": "",
      "fail_detail": "",
      "replay_type": 0,
      "replay_commit_id": "",
      "rbc_used": false,
      "trace_id": "",
      "target_module_id": "",
      "replay_show_type": "",
      "success_rate": 0,
      "rules": "",
      "flow_type": 0,
      "origin_req": "",
      "fail_detail_obj": {
        "diff_failed": 0,
        "send_failed": 0,
        "report_failed": 0,
        "dial_failed": 0,
        "write_failed": 0,
        "read_failed": 0,
        "mock_aspect_failed": 0,
        "diff_fail_mock_aspect_failed": 0
      },
      "tag_detail": {
        "replay_mark": {"key": 0}
      }
    }
  ]
}
```

### `DiffConfig`

#### 功能说明
本工具用于查询指定接口的 diff 配置。

> diff 策略规则（白名单、黑名单、预处理策略、自定义对比策略、自定义脚本、字段匹配等）详见 `references/diffrule.md`。

#### 输入参数
```json
{"app_server_name": "", "api_name": ""}
```

#### 参数说明
1. `app_server_name`（字符串，必填）：服务名称，格式 `app.server`。
2. `api_name`（字符串，必填）：接口名。

#### 输出
调用成功时返回 `Success diffConfig, data: ...`，其中 `data` 对应结构：

```json
{
  "base_rsp": {"code": 0, "msg": ""},
  "white_list": [""],
  "black_list": [""],
  "custom_config": {
    "key": {
      "type": "",
      "args": [""]
    }
  },
  "parse_config": {
    "key": {
      "type": "",
      "args": [""]
    }
  },
  "script": "",
  "enable_script": 1,
  "path_config": [
    {
      "RecordPath": "",
      "ReplayPath": ""
    }
  ]
}
```

> `script`：自定义 diff 脚本内容，当 `enable_script` 开关未开启时忽略此字段。`enable_script`：`1` 表示打开自定义脚本对比，`2` 表示关闭。

### `SetDiffConfig`

#### 功能说明
本工具用于设置指定接口的 diff 策略配置，包括白名单、黑名单、自定义策略、预处理策略、路径策略和自定义 diff 脚本。

> 通常在回放前或回放结果分析后，用户需要调整 diff 规则时使用。可先通过 `DiffConfig` 查询当前配置，再通过本工具进行修改。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SetDiffConfigInput",
  "type": "object",
  "required": ["app_server_name", "api_name"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "api_name": {"type": "string", "description": "接口名"},
    "white_list": {
      "type": "array",
      "items": {"type": "string"},
      "description": "白名单字段列表，仅对比这些字段（与 black_list 互斥使用）"
    },
    "black_list": {
      "type": "array",
      "items": {"type": "string"},
      "description": "黑名单字段列表，忽略这些字段的对比"
    },
    "custom_config": {
      "type": "object",
      "description": "自定义策略配置，key 为字段名，value 为策略对象",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "type": {"type": "string", "description": "策略类型"},
          "args": {"type": "array", "items": {"type": "string"}, "description": "策略参数，第一个参数为对比检查类型（如 default、regexp、floating、remainder、complex、=、<=、>= 等）"}
        }
      }
    },
    "parse_config": {
      "type": "object",
      "description": "预处理策略配置，key 为字段名，value 为策略对象",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "type": {"type": "string", "description": "策略类型"},
          "args": {"type": "array", "items": {"type": "string"}, "description": "策略参数"}
        }
      }
    },
    "script": {"type": "string", "description": "自定义 diff 脚本内容，当 enable_script 开关未开启时忽略此字段"},
    "enable_script": {"type": "integer", "description": "自定义脚本对比开关：1-打开，2-关闭", "enum": [1, 2]},
    "path_config": {
      "type": "array",
      "description": "路径策略配置列表",
      "items": {
        "type": "object",
        "properties": {
          "RecordPath": {"type": "string", "description": "录制路径"},
          "ReplayPath": {"type": "string", "description": "回放路径"}
        }
      }
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。服务名称，格式 `app.server`。
- `api_name`：**必填**。接口名。
- `white_list`：可选。白名单字段列表，设置后仅对比列表中的字段。
- `black_list`：可选。黑名单字段列表，设置后忽略列表中字段的对比。
- `custom_config`：可选。自定义策略，每个 key 为字段名，value 包含 `type`（策略类型）和 `args`（策略参数数组，第一个参数为对比检查类型，如 `default`、`regexp`、`floating`、`remainder`、`complex`、`=`、`<=`、`>=` 等）。
- `parse_config`：可选。预处理策略，结构与 `custom_config` 相同。
- `script`：可选。自定义 diff 脚本内容。当 `enable_script` 开关未开启时，忽略此字段。
- `enable_script`：可选。`1` 表示打开自定义对比，`2` 表示关闭。
- `path_config`：可选。路径策略配置列表，每项包含 `RecordPath`（录制路径）和 `ReplayPath`（回放路径）。

#### 输出
调用成功时返回 `base_rsp`，结构如下：

```json
{
  "base_rsp": {"code": 0, "msg": ""}
}
```

#### 使用场景
- 回放前配置 diff 规则：忽略时间戳、随机 ID 等动态字段（添加到 `black_list`）
- 回放结果分析后调整：发现某些字段变化可忽略，更新 `black_list` 或 `custom_config` 后重新回放
- 通常配合 `DiffConfig`（查询）使用：先查后改

> diff 策略规则（白名单、黑名单、预处理策略、自定义对比策略、自定义脚本、字段匹配等）详见 `references/diffrule.md`。

### `QueryEditRuleList`

#### 功能说明
本工具用于查询流量编辑规则列表。流量编辑规则用于在回放前对请求/响应数据进行字段级编辑（新增、修改、删除字段）。

> 流量编辑规则的详细说明（编辑操作类型、规则结构等）详见 `references/editrule.md`。

#### 输入参数
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "QueryEditRuleListInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "api_name": {"type": "string", "description": "接口名，可选。不传则查询该服务下所有接口的编辑规则"}
  },
  "additionalProperties": false
}
```

#### 参数说明
1. `app_server_name`（字符串，必填）：服务名称，格式 `app.server`。
2. `api_name`（字符串，可选）：接口名。不传则查询该服务下所有接口的编辑规则。

#### 输出
调用成功时返回编辑规则列表，对应结构：

```json
{
  "base_rsp": {"code": 0, "msg": ""},
  "edit_rules": [
    {
      "id": 0,
      "module_id": "",
      "api_name": "",
      "server_name": "",
      "proto_version": "",
      "msg_name": "",
      "protocol": "",
      "edit_enabled": false,
      "rules": [
        {
          "key": "",
          "value": "",
          "type": "",
          "action": "",
          "id": 0
        }
      ]
    }
  ]
}
```

**字段说明：**
- `edit_rules[].edit_enabled`：该规则组是否已启用
- `edit_rules[].rules[].key`：JSON key 路径
- `edit_rules[].rules[].value`：修改后的 JSON value
- `edit_rules[].rules[].type`：value 的数据类型
- `edit_rules[].rules[].action`：编辑行为（`add`=新增、`update`=修改、`delete`=删除）

#### 使用场景
- 回放前查看某个接口当前已配置的流量编辑规则
- 确认编辑规则是否正确（如字段修改、新增、删除）
- 通常与 `DiffConfig` 一起查看完整的流量处理规则配置

### `CreateEditRule`

#### 功能说明
为指定接口创建流量编辑规则。规则以**接口**为粒度配置，一个接口对应一组 `ItemRule`。

> **【强制流程】** 调用本工具前，**必须**先使用 `EditRuleCheck` 对规则进行预览校验；校验通过后才能调用本工具写入。若 `EditRuleCheck` 返回错误，必须先解决问题并重新 Check 通过，再调用本工具，绝不直接 Create。

> 流量编辑规则的详细说明（action 类型、type 取值、key 路径规则、普通替换与正则替换、动态占位符等）详见 `references/editrule.md`。

#### 前置信息获取
调用前需要明确**编辑目标**（接口 + 字段）：

- 若用户未指定要编辑哪个接口（`api_name`），先调用 `RecordAgg`（按接口聚合）列出当前服务已录制的接口名，供用户选择。
- 若用户已指定 `api_name` 但未明确要编辑哪个字段，先调用 `RecordSearch` 拉取该接口的一条实际流量，展示请求头 / 请求体 / 响应体的 JSON 结构，供用户选择目标字段并确认编辑动作（`action`）、值（`value`）与类型（`type`）。

**字段填写说明：**
- `server_name`：**不对外暴露**，工具内部会自动使用 `app_server_name` 原值填入。
- `msg_name`：即接口的方法名（如 `Count`、`QueryUser`），**不是**带路径的 `api_name`。**唯一可选字段**，不填时**工具层会自动从 `api_name` 末尾截取方法名**（按 `/` 分隔取最后一段）作为默认值；用户也可显式指定。**注意：后端不会对该字段做兜底，默认值由 Python 工具层填入。`RecordSearch` 不返回该字段**，不要试图从 `RecordSearch` 中读取。
- `protocol` / `proto_version`：**必传**。值来源两种——① 从 `RecordSearch` 返回流量中读取同名字段，② 由用户显式指定。二者取其一，但调用时必须传入。

#### 输入参数
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CreateEditRuleInput",
  "type": "object",
  "required": ["app_server_name", "api_name", "protocol", "proto_version", "rules"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "api_name": {"type": "string", "description": "接口名（可能带路径），必传"},
    "protocol": {"type": "string", "description": "协议名，如 trpc、http；**必传**，来源：RecordSearch 同名字段或用户显式指定"},
    "proto_version": {"type": "string", "description": "proto 版本号；**必传**，来源：RecordSearch 同名字段或用户显式指定"},
    "msg_name": {"type": "string", "description": "message name，即方法名；可选（唯一可不传字段），不填时工具层会自动从 api_name 末尾截取方法名作为默认值（后端不做兜底）"},
    "edit_enabled": {"type": "boolean", "description": "规则组是否启用，默认 true"},
    "rules": {
      "type": "array",
      "description": "具体的编辑规则列表（ItemRule）",
      "items": {
        "type": "object",
        "required": ["action", "key", "type"],
        "properties": {
          "action": {"type": "string", "enum": ["add", "update", "delete"], "description": "编辑行为"},
          "key": {"type": "string", "description": "JSON key 路径，例如 requestBody.user.name。详细规则见 references/editrule.md"},
          "value": {"type": "string", "description": "字段值；action=delete 时可填空串。支持动态函数占位符，详细规则见 references/editrule.md"},
          "type": {"type": "string", "enum": ["string", "number", "boolean", "null", "undefined"], "description": "value 的数据类型"}
        }
      }
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。用于换取 `module_id`、鉴权 AppId/AppKey，并作为后端 `server_name` 字段的值。
- `api_name`：**必填**。规则以接口为粒度配置。
- `rules`：**必填**。单条规则的 `action` / `key` / `type` 必填，`value` 在 `action=delete` 时可填空串。
- `protocol` / `proto_version`：**必填**。值来源只有两种——从 `RecordSearch` 返回流量读取同名字段，或由用户显式指定；二者取其一，但调用时必须传入。
- `msg_name`：可选（本工具唯一可不传的字段）。不填时**工具层**会自动从 `api_name` 末尾截取方法名作为默认值（后端不做兜底）。
- `edit_enabled`：可选，默认 `true`。

#### 输出
调用成功时返回创建完成的规则组（含服务端生成的 `id`）：

```json
{
  "base_rsp": {"code": 0, "msg": ""},
  "rule": {
    "id": 0,
    "module_id": "",
    "api_name": "",
    "server_name": "",
    "proto_version": "",
    "msg_name": "",
    "protocol": "",
    "edit_enabled": true,
    "rules": [
      {"key": "", "value": "", "type": "", "action": "", "id": 0}
    ]
  }
}
```

#### 使用场景
- 为某个接口新增流量编辑规则（如请求体字段替换、删除调试标志、注入动态时间戳等）
- **必须**先配合 `EditRuleCheck` 验证规则效果，再调用本工具创建落库

### `UpdateEditRule`

#### 功能说明
更新已有流量编辑规则组的**启用开关**（`edit_enabled`）。本工具**不修改规则内容**，仅切换规则组是否生效。

#### 输入参数
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UpdateEditRuleInput",
  "type": "object",
  "required": ["app_server_name", "id", "edit_enabled"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "id": {"type": "integer", "description": "规则组 ID，通过 QueryEditRuleList 获取"},
    "edit_enabled": {"type": "boolean", "description": "是否启用该规则组"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。
- `id`：**必填**。规则组 ID，通过 `QueryEditRuleList` 查询得到。
- `edit_enabled`：**必填**。`true` 启用，`false` 禁用。

#### 输出
```json
{"base_rsp": {"code": 0, "msg": ""}}
```

#### 使用场景
- 临时禁用某接口的编辑规则（回放时不生效），但保留规则配置
- 重新启用已禁用的规则组

### `DeleteEditRule`

#### 功能说明
删除指定的流量编辑规则组（整组删除，不可恢复）。

#### 输入参数
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DeleteEditRuleInput",
  "type": "object",
  "required": ["app_server_name", "id"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "id": {"type": "integer", "description": "规则组 ID，通过 QueryEditRuleList 获取"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。
- `id`：**必填**。规则组 ID，通过 `QueryEditRuleList` 查询得到。

#### 输出
```json
{"base_rsp": {"code": 0, "msg": ""}}
```

#### 使用场景
- 彻底清理某个接口不再需要的流量编辑规则组
- 删除前建议先用 `QueryEditRuleList` 确认目标 `id`

### `EditRuleCheck`

#### 功能说明
对指定接口的流量编辑规则进行**预览校验**：将规则应用到一条样例流量上，返回编辑前/编辑后的 JSON 内容对比。本工具**不会写入规则**，仅用于在正式创建或回放前确认规则效果是否符合预期。

> **【强制流程】** 用户希望创建流量编辑规则时，**必须**先调用本工具做预览校验，校验通过后再调用 `CreateEditRule` 写入。若本工具返回错误（如 key 路径无法匹配、value 格式不合法等），**必须**先解决问题并重新 Check 通过，不得跳过本工具直接 Create。

> 流量编辑规则的详细说明（action 类型、type 取值、key 路径规则、正则替换与动态占位符等）详见 `references/editrule.md`。

#### 前置信息获取
与 `CreateEditRule` 一致：

- **编辑目标（接口 + 字段）**：若用户未指定 `api_name`，先用 `RecordAgg` 列接口供用户选择；若未指定要编辑的字段，先用 `RecordSearch` 拉一条该接口的流量展示 JSON 结构，供用户选定目标字段、`action`、`value`、`type`。

**字段填写说明：**
- `server_name`：**不对外暴露**，工具内部会自动使用 `app_server_name` 原值填入。
- `message_name`：即接口的方法名（等同于 `CreateEditRule` 中的 `msg_name`，仅本接口后端入参字段名不同）。**不是**带路径的 `api_name`。**唯一可选字段**，不填时**工具层会自动从 `api_name` 末尾截取方法名**（按 `/` 分隔取最后一段）作为默认值；用户也可显式指定。**注意：后端不会对该字段做兜底，默认值由 Python 工具层填入。`RecordSearch` 不返回该字段**，不要试图从 `RecordSearch` 中读取。
- `protocol` / `proto_version`：**必传**。值来源两种——① 从 `RecordSearch` 返回流量中读取同名字段，② 由用户显式指定。二者取其一，但调用时必须传入。

#### 输入参数
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "EditRuleCheckInput",
  "type": "object",
  "required": ["app_server_name", "api_name", "protocol", "proto_version", "rules"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "api_name": {"type": "string", "description": "接口名（可能带路径），必传"},
    "protocol": {"type": "string", "description": "协议名；**必传**，来源：RecordSearch 同名字段或用户显式指定"},
    "proto_version": {"type": "string", "description": "proto 版本号；**必传**，来源：RecordSearch 同名字段或用户显式指定"},
    "message_name": {"type": "string", "description": "message name，即方法名；可选（唯一可不传字段），不填时工具层会自动从 api_name 末尾截取方法名作为默认值（后端不做兜底）"},
    "rules": {
      "type": "array",
      "description": "待校验的编辑规则列表（ItemRule），结构与 CreateEditRule 中 rules 相同",
      "items": {
        "type": "object",
        "required": ["action", "key", "type"],
        "properties": {
          "action": {"type": "string", "enum": ["add", "update", "delete"]},
          "key": {"type": "string", "description": "JSON key 路径，例如 requestBody.user.name。详细规则见 references/editrule.md"},
          "value": {"type": "string", "description": "字段值。支持动态函数占位符，详细规则见 references/editrule.md"},
          "type": {"type": "string", "enum": ["string", "number", "boolean", "null", "undefined"]}
        }
      }
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。工具内部会将其作为后端 `server_name` 字段的值填入。
- `api_name`：**必填**。
- `rules`：**必填**。同 `CreateEditRule`。
- `protocol` / `proto_version`：**必填**。值来源只有两种——从 `RecordSearch` 返回流量读取同名字段，或由用户显式指定；二者取其一，但调用时必须传入。
- `message_name`：可选（本工具唯一可不传的字段）。不填时**工具层**会自动从 `api_name` 末尾截取方法名作为默认值（后端不做兜底）。

#### 输出
```json
{
  "base_rsp": {"code": 0, "msg": ""},
  "before_edit": "<bytes>",
  "after_edit": "<bytes>"
}
```

- `before_edit`：编辑前的内容（bytes，通常为 base64 或原始 JSON 字节）。
- `after_edit`：应用规则后的内容，用于与 `before_edit` 对比。

#### 使用场景
- **创建流量编辑规则的强制前置步骤**：在调用 `CreateEditRule` 前必须先用本工具预览规则效果，避免写入错误规则
- 调整规则内容时逐步验证 `regexp_replace` 等正则表达式是否匹配目标字段

## 回放结果查询工具

### `SearchReport`

#### 功能说明
本工具用于查询回放报告详情，支持按 diff 结果、接口名、错误字段等条件筛选。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SearchReportInput",
  "type": "object",
  "required": ["app_server_name", "task_id"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "task_id": {"type": "integer", "description": "回放任务ID，必填"},
    "api_name": {"type": "string", "description": "接口名，可选"},
    "result": {"type": "integer", "description": "diff结果筛选：1=成功，2=错误，3=失败，可选"},
    "error_field": {"type": "string", "description": "错误字段名，可选"},
    "reason": {"type": "string", "description": "错误原因，可选"},
    "trace_id": {"type": "string", "description": "TraceID，可选"},
    "page": {"type": "integer", "description": "页码，默认1"},
    "page_size": {"type": "integer", "description": "每页大小，默认20"},
    "mock_aspect_flag": {"type": "string", "description": "切面mock失败标识，可选"},
    "replay_tag": {"type": "object", "additionalProperties": {"type": "string"}, "description": "回放数据tag，可选"},
    "includes": {"type": "array", "items": {"type": "string"}, "description": "返回字段包含，可选"},
    "excludes": {"type": "array", "items": {"type": "string"}, "description": "返回字段排除，可选"},
    "regexp_fields": {"type": "array", "items": {"type": "string"}, "description": "正则检索字段，支持：api_name、error_field、reason，可选"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。服务名称。
- `task_id`：**必填**。回放任务 ID，来自 `ExecuteReplay` 返回的 `task_id` 或 `TaskList` 中的任务 ID。
- `result`：可选。用于筛选 diff 结果：`1` = 成功，`2` = 错误，`3` = 失败。
- `page` / `page_size`：可选，默认 `1/20`。
- 其余字段可选。

#### 输出
返回回放报告明细列表，每条记录包含接口名、diff 结果、错误字段、trace_id 等信息。

#### 使用场景
- 阶段 4 方式 A 中查看失败详情：`SearchReport(result=2)` 查看错误记录
- 按接口名筛选特定接口的回放结果
- 按 trace_id 定位具体的失败请求

### `ReportAgg`

#### 功能说明
本工具用于按不同维度对回放报告进行聚合查询，支持按接口名、错误字段、失败原因、TraceID、回放标签等维度聚合。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ReportAggInput",
  "type": "object",
  "required": ["app_server_name", "type", "task_id"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "type": {
      "type": "integer",
      "description": "聚合类型：0=Default，1=APIName，2=ErrorField，3=Reason，4=TraceID，5=ReplayTag",
      "enum": [0, 1, 2, 3, 4, 5]
    },
    "task_id": {"type": "integer", "description": "回放任务ID，必填"},
    "api_name": {"type": "string", "description": "接口名，可选"},
    "result": {"type": "integer", "description": "diff结果，可选"},
    "error_field": {"type": "string", "description": "字段名，可选"},
    "trace_id": {"type": "string", "description": "TraceID，可选"},
    "mock_aspect_flag": {"type": "string", "description": "切面mock失败标识，可选"},
    "replay_tag": {"type": "object", "additionalProperties": {"type": "string"}, "description": "回放数据tag，可选"},
    "tag_agg": {"type": "array", "items": {"type": "string"}, "description": "回放tag聚合字段，可选"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。
- `type`：**必填**。聚合维度：
  - `0` = Default
  - `1` = APIName（按接口聚合）
  - `2` = ErrorField（按错误字段聚合）
  - `3` = Reason（按失败原因聚合）
  - `4` = TraceID
  - `5` = ReplayTag
- `task_id`：**必填**。回放任务 ID。
- 其余字段可选，用于进一步筛选聚合范围。

#### 输出
返回按指定维度聚合后的统计数据，每项包含维度 key 和对应的数量。

#### 使用场景
- 阶段 4 方式 A 中按接口聚合失败分布：`ReportAgg(type=1, task_id=xxx)`
- 按失败原因聚合分析根因：`ReportAgg(type=3, task_id=xxx)`
- 按错误字段分析 diff 差异集中点：`ReportAgg(type=2, task_id=xxx)`

### `SearchResponse`

#### 功能说明
本工具用于查询**普通回放（单环境回放）**单条流量的录制与回放响应比对结果（diff 详情），展示具体的字段级差异。

> **【重要 · 接口选择】** 查询单条流量 diff 响应比对结果时，**必须**先确认任务类型，根据任务类型选择不同接口：
> - **普通回放**（`replay_show_type` 不为 `"0_1"` 且 `replay_env_tag != true`）→ 使用本工具 `SearchResponse`（录制响应 vs 回放响应）。
> - **双环境回放**（`replay_show_type == "0_1"` 或 `replay_env_tag == true`）→ **禁止**使用本工具，必须改用 `TwoEnvReplayResultSearch`（环境 A 响应 vs 环境 B 响应）。
>
> 任务类型可通过 `TaskList` 或 `GetReplayTaskInfo` 返回的 `replay_show_type` 字段判断，二者必须先调用其中之一确认任务类型再决定接口。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SearchResponseInput",
  "type": "object",
  "required": ["app_server_name", "trace_id", "task_id"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "trace_id": {"type": "string", "description": "TraceID，必填"},
    "task_id": {"type": "integer", "description": "回放任务ID，必填"},
    "needDiff": {"type": "boolean", "description": "是否需要比对，默认false"},
    "module_id": {"type": "string", "description": "模块ID，可选（不传时自动从 app_server_name 解析）"},
    "flow_type": {"type": "integer", "description": "流量类型，默认0：流量，1：用例"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。
- `trace_id`：**必填**。来自 `SearchReport` 结果中的 `trace_id` 字段。
- `task_id`：**必填**。回放任务 ID。
- `needDiff`：可选，默认 `false`。设为 `true` 时返回详细的字段级 diff 结果。
- `module_id`：可选，不传时自动从 `app_server_name` 解析。
- `flow_type`：可选，默认 `0`（流量）。`1` 表示用例。

#### 输出
返回单条流量的录制响应与回放响应，以及 diff 比对结果（当 `needDiff=true` 时）。

#### 使用场景
- 阶段 4 方式 A 中用户指定 trace_id 后查看详细 diff
- 通常先通过 `SearchReport` 找到关注的 trace_id，再调用本工具查看具体差异
- 建议设置 `needDiff=true` 以获取完整比对信息

### `TwoEnvReplayResultSearch`

#### 功能说明
本工具用于**双环境回放**后，按 `task_id + trace_id` 查询同一条流量在两个目标地址（不同 `IP:Port`）上的回放响应数据。能力上与 `SearchResponse` 近似，但 `SearchResponse` 面向「录制 vs 回放」单环境对比；本工具专用于「双环境回放」场景，返回的是**两个回放目标各自产生的响应**，用于对比两个环境回放结果差异。

> **【重要 · 接口选择】** 查询单条流量 diff 响应比对结果时，**必须**先确认任务类型，根据任务类型选择不同接口：
> - **双环境回放**（`replay_show_type == "0_1"` 或 `replay_env_tag == true`）→ 使用本工具 `TwoEnvReplayResultSearch`（环境 A 响应 vs 环境 B 响应）。
> - **普通回放**（`replay_show_type` 不为 `"0_1"` 且 `replay_env_tag != true`）→ **禁止**使用本工具，必须改用 `SearchResponse`。
>
> 任务类型判断：`TaskList` / `GetReplayTaskInfo` 返回的 `replay_show_type` 字段值为 `"0_1"` 即代表双环境回放。

> 双环境回放：调用 `ExecuteReplay` 时设置 `replay_env_tag=true`，并在 `addr.default_target.addr` 中传入两个目标地址（`IP:Port` 或环境名）。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TwoEnvReplayResultSearchInput",
  "type": "object",
  "required": ["app_server_name", "task_id", "trace_id"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "task_id": {"type": "integer", "description": "回放任务ID，必填"},
    "trace_id": {"type": "string", "description": "流量 Trace ID，必填"},
    "commit_id": {"type": "string", "description": "Git提交ID，可选"},
    "api_name": {"type": "string", "description": "接口名，可选"},
    "status": {"type": "integer", "description": "回放结果（对应 pb 中的 Status 枚举），可选"},
    "reasons": {"type": "array", "items": {"type": "string"}, "description": "响应对比结果，支持批量查询，可选"},
    "start_time": {"type": "number", "description": "起始时间，可选"},
    "end_time": {"type": "number", "description": "结束时间，可选"},
    "includes": {"type": "array", "items": {"type": "string"}, "description": "返回字段包含，默认 [\"target\", \"response\"]"},
    "excludes": {"type": "array", "items": {"type": "string"}, "description": "返回字段排除，可选"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。服务名称，工具内部用于换取 `module_id` 与鉴权头。
- `task_id`：**必填**。双环境回放任务 ID，来自 `ExecuteReplay` 返回的 `task_id`。
- `trace_id`：**必填**。要查询的具体一条流量的 Trace ID。
- `includes`：可选。**默认 `["target", "response"]`**：
  - `target`：本条响应对应的回放目标地址（双环境下两条记录的 `target` 即为两个不同的 `IP:Port`）。
  - `response`：回放响应的结构化数据。
  - 若需要返回原始字节，可在 `includes` 中追加 `response_bytes`。
- `commit_id` / `api_name` / `status` / `reasons` / `start_time` / `end_time` / `excludes`：均为可选过滤条件，按需传入。

> **不暴露给调用方的内部参数**：
> - `username`：自动从鉴权上下文中注入到 `base_req.username`。
> - `module_id`：通过 `app_server_name` 自动解析，无需调用方传入。
> - `page_req`：内置固定为 `page=1`、`page_size=2`（双环境回放每条 trace 通常对应 2 条响应记录）。

#### 输出
返回 `ReplaySearchRsp`（pb 中名为 `ReplaySearchRsp`），结构如下：

```json
{
  "base_rsp": {"code": 0, "msg": ""},
  "page_rsp": {"page": 1, "page_size": 2, "total": 0},
  "data": [
    {
      "commit_id": "",
      "task_id": 0,
      "api_name": "",
      "status": 0,
      "reason": "",
      "trace_id": "",
      "time": 0,
      "response": "<bytes>",
      "response_bytes": "<bytes>",
      "target": ""
    }
  ]
}
```

- `data[].target`：双环境的回放目标地址，两条记录的 `target` 即为不同的 `IP:Port`。
- `data[].response`：回放响应的结构化数据。
- `data[].reason`：当前条记录的响应对比结果（如失败原因等）。

#### 使用场景
- **双环境回放结果对比**：双环境回放完成后，已通过 `SearchReport` 拿到某条关注的 `trace_id`，使用本工具查看该 trace 在两个目标环境上的实际回放响应。
- 排查双环境差异：当双环境回放报告中某条 trace 出现 diff，调用本工具拉取两份响应做人工核对。

> 与 `SearchResponse` 的区别：`SearchResponse` 用于「录制响应 vs 回放响应」对比；`TwoEnvReplayResultSearch` 用于「回放环境 A 的响应 vs 回放环境 B 的响应」对比，仅适用于双环境回放（`replay_env_tag=true`）任务。



