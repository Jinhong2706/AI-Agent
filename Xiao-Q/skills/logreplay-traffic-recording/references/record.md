## record 相关基础说明

本文仅收录 **录制流量查询**、**GoReplay 录制**、**tRPC 插件录制** 与 **录制任务状态查询** 相关的工具说明，作为 skill 前置描述文档使用。

不包含以下内容：
- 流量回放任务执行与结果查询
- 流量转测试场景
- 回放报告与报告明细

## 通用字段规范

### `all_filters` 流量过滤条件

`all_filters` 是一个通用的流量复杂查询字段，在 `RecordAgg`、`RecordSearch`、`GenerateTestPlanByTrafficData` 等工具中均可使用，用于对请求/响应字段做精确筛选。

#### 格式

每条规则为一个字符串，格式为：

```
<路径><操作符><值>
```

#### 路径规则

- 路径**必须**以 `request` 或 `response` 开头，分别表示请求侧和响应侧
- 支持请求/响应的头（header）和体（body）字段
- 使用 `.` 分隔嵌套层级

路径结构：
```
request.requestBody.<字段路径>
request.requestHeader.<字段名>
response.responseBody.<字段路径>
response.responseHeader.<字段名>
```

#### 操作符

| 操作符 | 含义 | 示例 |
|--------|------|------|
| `:` | 精确匹配 | `request.requestBody.name:test` |
| `^:` | 前缀匹配 | `request.requestBody.name^:test` |
| `!:` | 不等于 | `response.responseBody.base_rsp.code!:0` |

#### 示例

```json
[
  "response.responseBody.base_rsp.code:100000",
  "request.requestHeader.Content-Type:application/json",
  "response.responseBody.status^:success",
  "response.responseBody.error_code!:0"
]
```

#### 使用场景
- 筛选特定用户的流量：`request.requestBody.base_req.username:xxx`
- 只查看成功的流量：`response.responseBody.base_rsp.code:100000`
- 排除某类错误码：`response.responseBody.error_code!:500`
- 按前缀匹配接口版本：`request.requestBody.version^:v2`

---

## 录制流量查询

### `RecordAgg`

#### 功能说明
本工具用于按条件聚合查询录制流量。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RecordAggInput",
  "type": "object",
  "required": ["app_server_name", "agg_names"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server，必填"},
    "page": {"type": "integer", "description": "页码，默认 1"},
    "page_size": {"type": "integer", "description": "每页数量，默认 20"},
    "commit_id": {"type": "string", "description": "流量协议版本id"},
    "start_time": {"type": "number", "description": "开始时间戳（纳秒），默认30天前当天开始时间（00:00:00）"},
    "end_time": {"type": "number", "description": "结束时间戳（纳秒），默认当天结束时间（23:59:59）"},
    "api_names": {"type": "array", "items": {"type": "string"}, "description": "接口名列表，默认空"},
    "trace_ids": {"type": "array", "items": {"type": "string"}, "description": "TraceID列表，默认空"},
    "service_name": {"type": "string", "description": "服务名，默认空"},
    "instance_name": {"type": "string", "description": "实例名，默认空"},
    "protocol": {"type": "string", "description": "协议，默认空"},
    "p_trace_id": {"type": "string", "description": "父Trace ID，默认空"},
    "agg_names": {"type": "array", "items": {"type": "string"}, "description": "聚合字段列表，可为commitId, instanceName, serviceName, protocol, apiName, traceId，默认填apiName"},
    "env": {"type": "string", "description": "环境名，默认空"},
    "all_filters": {"type": "array", "items": {"type": "string"}, "description": "流量过滤条件，格式见本文「all_filters 流量过滤条件」章节，默认空"},
    "no_need_routing": {"type": "boolean", "description": "是否不需要routing，默认false"},
    "flow_types": {"type": "array", "items": {"type": "integer"}, "description": "流量类型列表，默认空"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。
- `page` / `page_size` 未传时默认使用 `1/20`。
- `start_time` / `end_time` 未传时默认使用最近 30 天范围：`start_time` 为 30 天前当天 `00:00:00` 的纳秒时间戳，`end_time` 为当天 `23:59:59` 的纳秒时间戳。
- `agg_names` 未传时默认填 `["apiName", "commitId", "protocol", "instanceName"]`。
- 其余字段默认空值。

#### 输出

`agg_names` 传入多个字段时，返回结果为**嵌套树结构**：按传入顺序逐层嵌套在 `sub` 字段中。例如默认的 `["apiName", "commitId", "protocol", "instanceName"]` 会产生四层嵌套：

```
apiName（第1层）
  └─ commitId（第2层，在 sub 中）
       └─ protocol（第3层，在 sub.sub 中）
            └─ instanceName（第4层，在 sub.sub.sub 中）
```

展示时应按 `agg_names` 的顺序将嵌套结构**展开为表格**，例如：

| 接口名 | 协议版本 | 协议 | 容器实例 | 数量 |
|--------|---------|------|---------|------|
| /api/xxx | 2.5.8 | trpc | server.gz100036 | 581 |
| /api/yyy | 2.5.8 | trpc | server.gz100036 | 50 |

> 遍历规则：从顶层 `data[]` 开始，每一项的 `type`/`key`/`count` 对应第 1 层维度，`sub[]` 对应第 2 层，`sub[].sub[]` 对应第 3 层，以此类推。叶子节点的 `count` 即为该组合的流量数量。

对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RecordAggRsp",
  "type": "object",
  "properties": {
    "base_rsp": {
      "type": "object",
      "properties": {
        "code": {"type": "integer", "description": "响应状态码"},
        "msg": {"type": "string", "description": "响应消息"}
      }
    },
    "data": {
      "type": "array",
      "description": "聚合项列表",
      "items": {
        "type": "object",
        "properties": {
          "type": {"type": "string", "description": "类型"},
          "key": {"type": "string", "description": "key"},
          "count": {"type": "integer", "description": "数量"},
          "sub": {
            "type": "array",
            "description": "子项",
            "items": {
              "type": "object",
              "properties": {
                "type": {"type": "string"},
                "key": {"type": "string"},
                "count": {"type": "integer"}
              }
            }
          }
        }
      }
    },
    "page_rsp": {
      "type": "object",
      "properties": {
        "page": {"type": "integer", "description": "页码"},
        "page_size": {"type": "integer", "description": "每页数量"},
        "total": {"type": "integer", "description": "总数"}
      }
    }
  }
}
```

### `RecordSearch`

#### 功能说明
本工具用于按条件检索录制流量明细。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RecordSearchInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server，必填"},
    "page": {"type": "integer", "description": "页码，默认 1"},
    "page_size": {"type": "integer", "description": "每页数量，默认 20"},
    "commit_id": {"type": "string", "description": "流量协议版本id，可从RecordAgg聚合结果的commitId维度获取，可列举给用户选择；用户不选择时可不传，默认空"},
    "start_time": {"type": "number", "description": "开始时间戳（纳秒），默认30天前当天开始时间（00:00:00）"},
    "end_time": {"type": "number", "description": "结束时间戳（纳秒），默认当天结束时间（23:59:59）"},
    "api_names": {"type": "array", "items": {"type": "string"}, "description": "接口名列表，可从RecordAgg聚合结果的apiName维度获取，可列举给用户选择；用户不选择时可不传，默认空"},
    "trace_ids": {"type": "array", "items": {"type": "string"}, "description": "TraceID列表，默认空"},
    "includes": {"type": "array", "items": {"type": "string"}, "description": "返回字段包含，默认空"},
    "excludes": {"type": "array", "items": {"type": "string"}, "description": "返回字段排除，默认空"},
    "service_name": {"type": "string", "description": "服务名，可从RecordAgg聚合结果的serviceName维度获取，可列举给用户选择；用户不选择时可不传，默认空"},
    "instance_name": {"type": "string", "description": "实例名，可从RecordAgg聚合结果的instanceName维度获取，可列举给用户选择；用户不选择时可不传，默认空"},
    "protocol": {"type": "string", "description": "协议，默认空"},
    "p_trace_id": {"type": "string", "description": "父Trace ID，默认空"},
    "only_body": {"type": "boolean", "description": "只返回requestBody，默认false"},
    "with_sub_record": {"type": "boolean", "description": "包含下游请求，默认false"},
    "all_filters": {"type": "array", "items": {"type": "string"}, "description": "流量过滤条件，格式见本文「all_filters 流量过滤条件」章节，默认空"},
    "no_need_routing": {"type": "boolean", "description": "是否不需要routing，默认false"},
    "flow_type": {"type": "integer", "description": "流量类型，默认0"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。
- `page` / `page_size` 未传时默认使用 `1/20`。
- `start_time` / `end_time` 未传时默认使用最近 30 天范围：`start_time` 为 30 天前当天 `00:00:00` 的纳秒时间戳，`end_time` 为当天 `23:59:59` 的纳秒时间戳。
- `commit_id`、`api_names`、`service_name`、`instance_name` 均可通过先调用 `RecordAgg` 聚合查询获取可选值；如果用户不选择，可不传这些参数，默认空即可。
- 其余字段默认空值。

#### 输出
对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RecordSearchRsp",
  "type": "object",
  "properties": {
    "base_rsp": {
      "type": "object",
      "properties": {
        "code": {"type": "integer", "description": "响应状态码"},
        "msg": {"type": "string", "description": "响应消息"}
      }
    },
    "page_rsp": {
      "type": "object",
      "properties": {
        "page": {"type": "integer", "description": "页码"},
        "page_size": {"type": "integer", "description": "每页数量"},
        "total": {"type": "integer", "description": "总数"}
      }
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "module_id": {"type": "string", "description": "模块ID"},
          "commit_id": {"type": "string", "description": "流量协议版本id"},
          "p_trace_id": {"type": "string", "description": "父Trace ID"},
          "trace_id": {"type": "string", "description": "Trace ID"},
          "time": {"type": "number", "description": "时间"},
          "service_name": {"type": "string", "description": "服务名"},
          "instance_name": {"type": "string", "description": "实例名"},
          "protocol": {"type": "string", "description": "协议"},
          "api_name": {"type": "string", "description": "接口名"},
          "request": {"type": "string", "description": "请求内容（工具已对原始 base64 解码为 UTF-8 字符串）"},
          "request_bytes": {"type": "string", "description": "请求二进制(base64)"},
          "response": {"type": "string", "description": "响应内容（工具已对原始 base64 解码为 UTF-8 字符串）"},
          "response_bytes": {"type": "string", "description": "响应二进制(base64)"},
          "tag": {"type": "string", "description": "自定义tag分词数据(base64)"},
          "doc_id": {"type": "string", "description": "流量对应文档ID"},
          "dupli_hash": {"type": "string", "description": "流量去重hash(base64)"},
          "sub_records": {
            "type": "array",
            "description": "下游请求",
            "items": {"type": "object"}
          },
          "case_info": {
            "type": "object",
            "description": "用例相关信息"
          }
        }
      }
    }
  }
}
```

#### 字段编码说明
- `data[].request` 和 `data[].response`：后端原始返回为 base64 编码的字节流，**本工具在响应返回前已自动 base64 解码并转为 UTF-8 字符串**，调用方无需再次解码即可直接读取。

## GoReplay 录制辅助信息

### `GetGoReplayNodeList`

#### 功能说明
本工具用于获取指定服务的 GoReplay 节点列表。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetGoReplayNodeListInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {
      "type": "string",
      "description": "服务名称，格式 app.server"
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。

#### 输出
调用成功时返回 `Success getGoReplayNodeList, data: ...`，其中 `data` 对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetGoReplayNodeListRsp",
  "description": "获取GoReplay节点列表响应体",
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
    "service_list": {
      "type": "array",
      "description": "123服务的goreplay节点列表",
      "items": {
        "type": "object",
        "description": "123服务的goreplay节点信息",
        "properties": {
          "name": {"type": "string", "description": "服务名称"},
          "protocol": {"type": "string", "description": "协议"},
          "address": {"type": "string", "description": "地址"},
          "docker_name": {"type": "string", "description": "容器名称"},
          "env": {"type": "string", "description": "环境"},
          "create_time": {"type": "string", "description": "创建时间"},
          "update_time": {"type": "string", "description": "更新时间"}
        }
      }
    },
    "agent_list": {
      "type": "array",
      "description": "Agent注册的goreplay节点列表",
      "items": {
        "type": "object",
        "description": "Agent注册的goreplay节点信息",
        "properties": {
          "agent_id": {"type": "string", "description": "Agent ID"},
          "module_id": {"type": "string", "description": "模块ID"},
          "name": {"type": "string", "description": "名称"},
          "ip": {"type": "string", "description": "IP地址"},
          "env": {"type": "string", "description": "环境"},
          "port_protocol": {
            "type": "array",
            "description": "端口协议列表",
            "items": {
              "type": "object",
              "description": "端口协议",
              "properties": {
                "port": {"type": "integer", "description": "端口号"},
                "protocol": {"type": "string", "description": "协议"}
              }
            }
          },
          "create_time": {"type": "string", "description": "创建时间"},
          "update_time": {"type": "string", "description": "更新时间"}
        }
      }
    }
  }
}
```

### `GetProtoInfoList`

#### 功能说明
本工具用于获取指定服务的协议信息列表，主要用于获取协议版本号（`commit_id`）。

协议版本号（`version_str`）即为 `commit_id`，用于表示协议版本号，格式大概为 `x.y.z`（如 `1.0.0`、`1.0.1`、`1.1.0` 等）。
新版本递增规则：`1.0.0 → 1.0.1 → 1.0.2 → ... → 1.0.9 → 1.1.0`。
如果协议信息列表长度为零，则默认 `commit_id` 为 `0.0.0`。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetProtoInfoListInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {
      "type": "string",
      "description": "服务名称，格式 app.server"
    },
    "get_type": {
      "type": "number",
      "description": "获取类型，0-获取全部信息，1-获取最新信息"
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `get_type`：**用户选填**。默认 `0`。

#### 输出
调用成功时返回 `Success getProtoInfoList, data: ...`，其中 `data` 包含以下字段：
- `commit_id`：协议版本号字符串（如 `1.0.0`），如果列表为空则默认 `0.0.0`
- `protocol_info_list`：协议信息列表，每项包含：
  - `app_server_name`：服务名称
  - `version_str`：版本号（即 `commit_id`）
  - `file_type`：协议文件类型
  - `cmdb_id`：CMDB ID
  - `file_src_name`：文件来源
  - `upload_user_name`：上传人账号
  - `external_platform_info`：外部平台信息
- `total_count`：总数

### `GetProtocolName`

#### 功能说明
本工具用于获取具体的协议类型名称。

#### 说明
- 除了 `app_server_name` 外，其他字段（`docker_name`、`service_name`、`env`）通常来自 `GetGoReplayNodeList` 的返回结果。
- 如果 `GetGoReplayNodeList` 返回的节点列表为空，可按 HTTP 协议处理。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetProtocolNameInput",
  "type": "object",
  "required": ["app_server_name", "docker_name", "service_name", "env"],
  "properties": {
    "app_server_name": {
      "type": "string",
      "description": "服务名称，格式 app.server"
    },
    "docker_name": {
      "type": "string",
      "description": "容器名称，来自 GetGoReplayNodeList 返回的 service_list 或 agent_list 中的容器名/名称"
    },
    "service_name": {
      "type": "string",
      "description": "项目中单一服务名，例如 trpc.demo.hello.**** 这种格式，来自 GetGoReplayNodeList 返回的 service_list 中的 name 字段"
    },
    "env": {
      "type": "string",
      "description": "环境名称，来自 GetGoReplayNodeList 返回的 service_list 或 agent_list 中的 env 字段"
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `docker_name`：**必填**。容器名称，从 `GetGoReplayNodeList` 的返回结果中获取。
- `service_name`：**必填**。协议服务名，从 `GetGoReplayNodeList` 的返回结果中获取。
- `env`：**必填**。环境信息，从 `GetGoReplayNodeList` 的返回结果中获取。

#### 输出
调用成功时返回 `Success getProtocolName, data: ...`，其中 `data` 对应结构如下：

```json
{
  "base_rsp": {
    "code": 0,
    "msg": ""
  },
  "protocol_name": "协议类型名称"
}
```

## tRPC 插件录制

### `GetTrpcPluginInstanceList`

#### 功能说明
本工具用于获取 tRPC 插件录制方式的节点实例列表。与 GoReplay 录制方式不同，tRPC 插件录制通过在服务内部集成 tRPC 插件实现流量录制，无需外部 GoReplay 进程。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetTrpcPluginInstanceListInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {
      "type": "string",
      "description": "服务名称，格式 app.server"
    },
    "onlyReplay": {
      "type": "boolean",
      "description": "是否只返回回放节点，默认false"
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `onlyReplay`：**可选**。默认 `false`。设为 `true` 时只返回回放节点。

#### 输出
调用成功时返回节点实例列表，其中 `list` 包含 Instance 数组，每个 Instance 对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetTrpcPluginInstanceListRsp",
  "description": "获取tRPC插件节点实例列表响应体",
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
    "list": {
      "type": "array",
      "description": "节点实例列表",
      "items": {
        "type": "object",
        "description": "节点实例",
        "properties": {
          "info": {
            "type": "object",
            "description": "节点基础信息",
            "properties": {
              "module_id": {"type": "string", "description": "模块ID"},
              "docker_env": {"type": "string", "description": "容器环境"},
              "docker_name": {"type": "string", "description": "容器名"},
              "ip": {"type": "string", "description": "IP地址"},
              "service_name": {"type": "string", "description": "服务名"},
              "port": {"type": "integer", "description": "端口"},
              "commit_id": {"type": "string", "description": "git commit id"},
              "commit_msg": {"type": "string", "description": "git commit msg"},
              "sdk_version": {"type": "string", "description": "sdk版本"},
              "update_time": {"type": "string", "description": "更新时间"},
              "app_name": {"type": "string", "description": "业务名"},
              "module_name": {"type": "string", "description": "模块名"},
              "repo_url": {"type": "string", "description": "仓库地址"},
              "lang": {"type": "string", "description": "模块语言"},
              "platform": {"type": "string", "description": "发布平台"},
              "protocol": {"type": "string", "description": "服务协议"},
              "filters": {"type": "array", "items": {"type": "string"}, "description": "可用过滤器列表"},
              "sdk_type": {"type": "string", "description": "接入类型"},
              "aspects": {"type": "array", "items": {"type": "string"}, "description": "可用切面配置列表"},
              "full_set_name": {"type": "string", "description": "set名"}
            }
          },
          "config": {
            "type": "object",
            "description": "节点配置",
            "properties": {
              "is_replay_server": {"type": "boolean", "description": "是否为回放服务器，false=录制模式（启动录制），true=回放模式（将节点设置成回放模式）"},
              "type": {"type": "integer", "description": "节点类型（空/录制/回放）"},
              "enable": {"type": "boolean", "description": "录制回放总开关"},
              "write_content_log": {"type": "boolean", "description": "记录请求内容到日志"},
              "log_level": {"type": "integer", "description": "根日志等级"},
              "api_whitelist": {"type": "array", "items": {"type": "string"}, "description": "录制的接口白名单"},
              "cpu_usage_threshold": {"type": "number", "description": "CPU占用阈值百分比"},
              "recordLimitSpeed": {"type": "integer", "description": "录制速度限制(次/秒)"},
              "rise_quickly": {"type": "boolean", "description": "录制速率快速上升开关"},
              "state": {"type": "string", "description": "状态（none|record|replay|bench）"},
              "aspect_attribute": {"type": "object", "additionalProperties": {"type": "string"}, "description": "切面特性"},
              "field_whitelist": {
                "type": "array",
                "items": {"type": "object", "properties": {"path": {"type": "string"}, "value": {"type": "string"}}},
                "description": "字段过滤白名单"
              },
              "filters": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "name": {"type": "string", "description": "过滤器名称"},
                    "enable": {"type": "boolean", "description": "过滤器开关"},
                    "ext": {"type": "object", "additionalProperties": {"type": "string"}, "description": "附加信息"}
                  }
                },
                "description": "过滤器配置"
              },
              "filter_relation": {"type": "integer", "description": "过滤器关系，1全与，2全或"},
              "mem_usage_threshold": {"type": "number", "description": "内存占用阈值百分比"},
              "is_whitelist_must_record": {"type": "boolean", "description": "白名单流量一定录制"},
              "enable_not_whitelist": {"type": "boolean", "description": "是否录制非白名单流量"},
              "net_work_band_with_threshold": {"type": "number", "description": "网络带宽阈值(Mb)"},
              "block_device_write_ps": {"type": "number", "description": "块设备每秒写MB"},
              "block_device_read_ps": {"type": "number", "description": "块设备每秒读MB"},
              "global_aspect": {"type": "boolean", "description": "是否启用全局切面配置"},
              "cron_expression": {"type": "string", "description": "定时开启录制开关"},
              "duration": {"type": "integer", "description": "定时开关开启时间"}
            }
          },
          "pnconfig": {
            "type": "object",
            "description": "perfMetrics 插件节点配置",
            "properties": {
              "log_level": {"type": "integer", "description": "日志级别"},
              "enable_cpu_threshold": {"type": "integer", "description": "触发pprof采集cpu阈值(%)"},
              "enable_mem_threshold": {"type": "integer", "description": "触发pprof采集mem阈值(%)"},
              "disable_cpu_threshold": {"type": "integer", "description": "告警失效cpu阈值"},
              "disable_mem_threshold": {"type": "integer", "description": "告警失效mem阈值"},
              "enable_trace": {"type": "boolean", "description": "是否开启trace profile采集"},
              "rsp_timeout_threshold": {"type": "integer", "description": "接口请求超时时间阈值"},
              "rsp_timeout_rate_threshold": {"type": "integer", "description": "接口请求超时率阈值"}
            }
          },
          "status": {
            "type": "object",
            "description": "节点状态",
            "properties": {
              "logreplay_status": {"type": "string", "description": "logreplay状态"},
              "perfMetrics_status": {"type": "string", "description": "perfMetrics状态"}
            }
          }
        }
      }
    }
  }
}
```

#### 关键字段说明
- `info.docker_name`：容器名称
- `info.ip` + `info.port`：节点的 IP:Port
- `info.service_name`：tRPC 服务名
- `info.sdk_version`：SDK 版本
- `info.protocol`：服务协议
- `info.filters`：该节点可用的过滤器列表
- `info.aspects`：该节点可用的切面配置列表
- `config.enable`：录制回放总开关
- `config.type`：节点类型
- `config.state`：节点状态（none/record/replay/bench）
- `config.api_whitelist`：录制的接口白名单
- `config.recordLimitSpeed`：录制速度限制
- `status.logreplay_status`：logreplay 运行状态

### `UpdateTrpcPluginConfig`

#### 功能说明
本工具用于更新 tRPC 插件节点的配置，包括开启/关闭录制或回放、修改录制参数（白名单、速度限制等）。录制和回放都通过此接口控制。

> **重要前置条件**：调用前【必须】先通过 `GetTrpcPluginInstanceList` 获取节点列表。返回的 `list` 可能包含多个 Instance，且同一 `info.docker_name` 可能重复。组装更新参数时遵循以下规则：
> 1. **`list`**：允许放多个 `info`（多个不同 `docker_name` 并存时），但**同一个 `docker_name` 只能放一个 `info`**（默认取该 `docker_name` 命中的第一条 Instance 的 `info`）。
> 2. **`config`**：直接使用 `GetTrpcPluginInstanceList` 返回的 `list` **第一个元素**的 `config` 作为默认值（`config` 是对象，不是数组），再按需覆盖字段。
> 3. 用户未显式指定修改的字段【必须】保留默认值，【绝不】传空值或零值覆盖已有配置。

#### 隐性默认值规则

以下字段在 `config` 中有隐性默认值，若查询结果中未返回或值为空，使用下列默认值；用户未显式修改时也保持原值：

| 字段 | 含义 | 取值 | 默认值 |
|------|------|------|------|
| `log_level` | 日志等级 | `2`=Error，`3`=Warn，`4`=Info，`5`=Debug | `4`（Info） |
| `recordLimitSpeed` | 录制速度（次/秒） | 整数，`<0` 表示不录制 | `10` |

#### 过滤器（`config.filters`）规则

`config.filters` 是过滤器配置数组，**可选**，由用户明确要求时才添加/修改。规则如下：

1. **过滤器仅支持 4 种**，`name` 只能取以下取值之一，且在 `filters` 数组中**每种过滤器最多只能出现一次**（即数组最多 4 个元素）：

   | `name` | 含义 | 是否常用 | 联动白名单 |
   |--------|------|---------|------------|
   | `APINameFilter` | 接口名过滤 | ✅ 常用 | `config.api_whitelist` |
   | `RequestFieldFilter` | 请求字段过滤 | ✅ 常用 | `config.field_whitelist` |
   | `MessageFieldFilter` | 消息字段过滤 | 少用 | — |
   | `QQliveHeadUnmarshalFilter` | QQLive 头解析过滤 | 少用 | — |

2. **每个过滤器元素结构**：`{"name": <上表 name>, "enable": <true/false>, "ext": {...可选附加信息...}}`。`enable=true` 表示开启，`false` 表示关闭。

3. **白名单联动规则（重要）**：

   - **开启 `APINameFilter`（`enable=true`）时**：【必须】在 `config.api_whitelist` 中填入接口名列表。如果不填，后端将拒绝录制所有请求。
   - **开启 `RequestFieldFilter`（`enable=true`）时**：【必须】在 `config.field_whitelist` 中填入过滤条件，每个元素格式 `{"path": "<请求字段路径>", "value": "<匹配值>"}`。如果不填，后端将拒绝录制所有请求。
   - 关闭这两个过滤器（`enable=false`）或不配置时，对应白名单可不填。

4. **何时使用**：仅当用户明确要求「按接口过滤」「按字段过滤」「开启/关闭某个过滤器」等场景才设置；未提及时【不要】自作主张添加 `filters` 字段。



#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UpdateTrpcPluginConfigInput",
  "type": "object",
  "required": ["app_server_name", "list", "config"],
  "properties": {
    "app_server_name": {
      "type": "string",
      "description": "服务名称，格式 app.server"
    },
    "list": {
      "type": "array",
      "description": "要更新的节点 Info 列表，元素来自 GetTrpcPluginInstanceList 返回的 instance.info。允许包含多个不同 docker_name 的 info，但同一 docker_name 只能保留一个 info（默认取命中的第一条 Instance 的 info）",
      "items": {
        "type": "object",
        "description": "节点 Info，字段同 GetTrpcPluginInstanceList 返回的 info 结构"
      }
    },
    "config": {
      "type": "object",
      "description": "节点配置对象（不是数组）。默认取 GetTrpcPluginInstanceList 返回的 list 第一个元素的 config 作为基础，仅覆盖需要修改的字段。log_level 默认 4(Info)，recordLimitSpeed 默认 10"
    },
    "pnconfig": {
      "type": "object",
      "description": "perfMetrics 插件配置（可选），字段同 GetTrpcPluginInstanceList 返回的 pnconfig 结构"
    },
    "sdk_type": {
      "type": "string",
      "description": "接入类型（可选）"
    },
    "set_name": {
      "type": "array",
      "items": {"type": "string"},
      "description": "set名列表（可选）"
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `list`：**必填**。要更新的节点 Info 列表。允许包含多个不同 `docker_name` 的 `info`，但**同一个 `docker_name` 只能放一个 `info`**，默认取该 `docker_name` 命中的第一条 Instance 的 `info`。
- `config`：**必填**。节点配置对象（不是数组）。默认取 `GetTrpcPluginInstanceList` 返回的 `list` **第一个元素**的 `config` 作为基础，再按需覆盖字段。
  - 开启录制：`enable=true`，`is_replay_server=false`
  - 关闭录制：`enable=false`
  - 开启回放：`enable=true`，`is_replay_server=true`
  - 关闭回放：`enable=false`
  - `log_level`：日志等级。`2`=Error、`3`=Warn、`4`=Info、`5`=Debug。查询结果未返回或为空时默认 `4`（Info）；用户未显式修改时保持原值。
  - `recordLimitSpeed`：录制速度（次/秒）。查询结果未返回或为空时默认 `10`；`<0` 表示不录制；用户未显式修改时保持原值。
  - `filters`：**可选**。过滤器配置，仅支持 `APINameFilter`/`RequestFieldFilter`/`MessageFieldFilter`/`QQliveHeadUnmarshalFilter` 四种，每种最多一个。详见本节「过滤器（`config.filters`）规则」。
  - `api_whitelist`：接口名白名单。开启 `APINameFilter` 时**必须**填入接口名列表，否则后端拒绝录制所有请求。
  - `field_whitelist`：请求字段白名单，元素为 `{"path": "...", "value": "..."}`。开启 `RequestFieldFilter` 时**必须**填入，否则后端拒绝录制所有请求。
- `pnconfig`：**可选**。perfMetrics 配置，不传则不修改。
- `sdk_type`：**可选**。接入类型。
- `set_name`：**可选**。set 名列表。

#### 输出
调用成功时返回更新结果，对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UpdateTrpcPluginConfigRsp",
  "description": "更新tRPC插件节点配置响应体",
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
    "updated": {
      "type": "integer",
      "description": "成功更新的节点数量"
    }
  }
}
```

#### 典型使用场景

**开启录制：**
```json
{
  "app_server_name": "myapp.myserver",
  "list": [{"每个 docker_name 各取第一条 Instance.info"}],
  "config": {"...查询结果 list 第一个元素的 config...", "enable": true, "is_replay_server": false}
}
```

**关闭录制：**
```json
{
  "app_server_name": "myapp.myserver",
  "list": [{"每个 docker_name 各取第一条 Instance.info"}],
  "config": {"...查询结果 list 第一个元素的 config...", "enable": false}
}
```

**修改录制白名单：**
```json
{
  "app_server_name": "myapp.myserver",
  "list": [{"每个 docker_name 各取第一条 Instance.info"}],
  "config": {"...查询结果 list 第一个元素的 config...", "api_whitelist": ["/api/v1/user", "/api/v1/order"]}
}
```

**开启接口名过滤（APINameFilter + api_whitelist 联动）：**
```json
{
  "app_server_name": "myapp.myserver",
  "list": [{"每个 docker_name 各取第一条 Instance.info"}],
  "config": {
    "...查询结果 list 第一个元素的 config...",
    "filters": [{"name": "APINameFilter", "enable": true}],
    "api_whitelist": ["/api/v1/user", "/api/v1/order"]
  }
}
```

**开启请求字段过滤（RequestFieldFilter + field_whitelist 联动）：**
```json
{
  "app_server_name": "myapp.myserver",
  "list": [{"每个 docker_name 各取第一条 Instance.info"}],
  "config": {
    "...查询结果 list 第一个元素的 config...",
    "filters": [{"name": "RequestFieldFilter", "enable": true}],
    "field_whitelist": [{"path": "base_req.username", "value": "testuser"}]
  }
}
```

---

## GoReplay 录制任务

### `StartGoReplay`

#### 功能说明
本工具用于启动 GoReplay 录制任务。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StartGoReplayInput",
  "type": "object",
  "required": ["app_server_name", "container_name_params"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "container_name_params": {
      "type": "object",
      "description": "容器到录制参数的映射，key 为容器名，这里container_name_params至少要有一个容器名和对应的启动录制参数",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "is_without_static_go_replay": {"type": "boolean", "description": "是否非静态goreplay，默认 false"},
          "go_replay_params": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "ip_port": {"type": "string", "description": "抓包地址 ip:port，必填"},
                "protocol": {"type": "string", "description": "协议，必填"},
                "protocol_service_version": {"type": "string", "description": "协议版本，必填"},
                "is_udp": {"type": "boolean", "description": "是否UDP，默认 false"},
                "is_agent": {"type": "boolean", "description": "是否Agent，默认 false"},
                "flux_switch": {"type": "integer", "description": "流量转用例开关，0关1开，默认 0"},
                "verbose": {"type": "integer", "description": "日志等级，默认值1"},
                "extend": {"type": "array", "items": {"type": "string"}, "description": "扩展参数，可选填。可用值：--output-logreplay-record-limit（录制条数上限）"},
                "record_time": {"type": "integer", "description": "定时录制时长（小时），默认 6"},
                "only_one_process": {"type": "boolean", "description": "单容器单进程开关，默认 false"}
              }
            }
          }
        }
      }
    }
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `container_name_params` 中 `go_replay_params` 的以下字段为**必填**，需要由用户主动填写或通过其他工具获取：
  - `ip_port`：**必填**。抓包地址（`ip:port`），来自 `GetGoReplayNodeList` 返回的 `service_list` 中的 `address` 字段或 `agent_list` 中的 `ip + port_protocol` 组合。
  - `protocol`：**必填**。协议类型名，来自 `GetProtocolName` 返回的 `protocol_name` 字段。如果 `GetGoReplayNodeList` 返回的节点列表为空，说明没有容器列表，可直接当作 HTTP 协议（即填 `"http"`），无需调用 `GetProtocolName`。
  - `protocol_service_version`：**必填**。协议版本号（即 `commit_id`），来自 `GetProtoInfoList` 返回的 `commit_id` 字段。版本格式为 `x.y.z`（如 `1.0.0`、`1.0.1`），如果 `GetProtoInfoList` 返回列表为空，默认 `"0.0.0"`。
- `extend`：**可选**。扩展参数数组，每个元素为一个字符串。可用值：
  - `--output-logreplay-record-limit <数量>`：设置录制的条数上限。例如 `["--output-logreplay-record-limit", "10000"]` 表示最多录制 10000 条。
- 其他字段按需传入；未传时由后端按默认值处理。
- 大模型不要随意传入，除非用户明确指定。

#### 输出
调用成功时返回 `Success startGoReplay, data: ...`，其中 `data` 对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "StartGoReplayOutput",
  "description": "启动GoReplay录制任务输出结构",
  "type": "object",
  "properties": {
    "task_result": {
      "type": "array",
      "description": "任务结果列表",
      "items": {
        "type": "object",
        "description": "启动GoReplay结果项",
        "properties": {
          "task_ids": {"type": "array", "items": {"type": "string"}, "description": "goreplay任务ID列表，映射自接口响应中的 goReplayTaskIds"},
          "container_name": {"type": "string", "description": "容器名"},
          "error_code": {"type": "integer", "description": "任务状态码，0：成功"},
          "msg": {"type": "string", "description": "提示信息"}
        }
      }
    }
  }
}
```


### `GetGoReplayExecTask`

#### 功能说明
本工具用于获取 GoReplay 录制任务列表。

#### 输入参数
**参数格式：**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetGoReplayExecTaskInput",
  "type": "object",
  "required": ["app_server_name"],
  "properties": {
    "app_server_name": {"type": "string", "description": "服务名称，格式 app.server"},
    "start_time": {"type": "string", "description": "开始时间 YYYY-MM-DD HH:mm:ss，默认30天前当天开始时间"},
    "end_time": {"type": "string", "description": "结束时间 YYYY-MM-DD HH:mm:ss，默认当天结束时间"},
    "ip_port": {"type": "string", "description": "IP端口过滤"},
    "page": {"type": "integer", "description": "页码，默认值1"},
    "page_size": {"type": "integer", "description": "每页数量，默认值20"},
    "status": {
      "type": "array",
      "items": {"type": "integer"},
      "description": "状态过滤列表"
    },
    "user": {"type": "string", "description": "用户名，不传默认空"}
  },
  "additionalProperties": false
}
```

#### 参数说明
- `app_server_name`：**必填**。为空会直接报错。
- `page` / `page_size` 未传时默认使用 `1/20`。
- `start_time` / `end_time` 未传时默认使用最近 30 天范围：`start_time` 为 30 天前当天开始时间，`end_time` 为当天结束时间。
- `user` 不传时，后端默认取当前登录用户。

#### 输出
调用成功时返回 `Success getGoReplayExecTask, data: ...`，其中 `data` 对应结构如下：

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GetGoReplayExecTaskRsp",
  "description": "获取goreplay录制任务列表响应体",
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
    "page_rsp": {
      "type": "object",
      "description": "分页响应结构",
      "properties": {
        "page": {"type": "integer", "description": "页码"},
        "page_size": {"type": "integer", "description": "每页数量"},
        "total": {"type": "integer", "description": "总数"}
      }
    },
    "execTaskInfo": {
      "type": "array",
      "description": "任务信息列表",
      "items": {
        "type": "object",
        "description": "录制任务信息",
        "properties": {
          "task_id": {"type": "string", "description": "任务ID"},
          "ip_port": {"type": "string", "description": "IP端口"},
          "user": {"type": "string", "description": "用户名"},
          "record_num": {"type": "integer", "description": "录制数量"},
          "start_time": {"type": "string", "description": "开始时间"},
          "status": {"type": "integer", "description": "任务状态 1启动，2停止"},
          "cmd_id": {"type": "integer", "description": "命令ID"},
          "source": {"type": "string", "description": "来源(manual/regular/openApi)"},
          "cmd": {"type": "string", "description": "命令详情"},
          "cmd_task_id": {"type": "string", "description": "123任务ID"},
          "container_name": {"type": "string", "description": "容器名"},
          "error_code": {"type": "integer", "description": "错误码"},
          "msg": {"type": "string", "description": "错误信息，成功是success"}
        }
      }
    }
  }
}
```

### `StopGoReplayTask`

#### 功能说明
本工具用于停止正在执行的 goreplay 任务。

#### 输入参数
```json
{"app_server_name": "", "task_id": ""}
```

#### 参数说明
1. `app_server_name`（字符串，必填）：服务名称，格式为 `app.server`，由 `app` 名称和 `server` 名称用英文句点 `.` 连接。
2. `task_id`（字符串，必填）：任务 ID。

#### 输出
调用成功时返回 `Success stopGoReplayTask, data: ...`，其中 `data` 对应结构：

```json
{
  "base_rsp": {
    "code": 0,
    "msg": ""
  }
}
```

## GoReplay 录制任务状态查询

### `MultiGetTaskStatus`

#### 功能说明
本工具用于批量查询 GoReplay 录制任务状态，传入一组 `task_id`，返回每个任务的当前状态。

#### 输入参数
```json
{
  "app_server_name": "",
  "task_ids": [""]
}
```

#### 参数说明
1. `app_server_name`（字符串，必填）：服务名称，格式为 `app.server`。
2. `task_ids`（字符串数组，必填，至少有一个）：任务 ID 列表，来自 `StartGoReplay` 返回的 `task_ids` 字段。

#### 输出
调用成功时返回各任务的状态信息，包含 `base_rsp` 和任务状态详情。

#### 使用场景
- 录制启动后，通过 `StartGoReplay` 返回的 `task_ids` 查询录制进度
- 配合 PHASE_1 阶段 6 的状态查询步骤使用
- 仅执行**一次**查询，【绝不】自动轮询

### `GetGoReplayStatus`

#### 功能说明
本工具用于通过 IP:Port 或 Agent ID 查询 GoReplay 录制任务的运行状态。与 `MultiGetTaskStatus` 按 task_id 查询不同，本工具按网络地址或 Agent 维度查询。

#### 输入参数
```json
{
  "app_server_name": "",
  "ipAndPorts": [""],
  "agent_ids": [""]
}
```

#### 参数说明
1. `app_server_name`（字符串，必填）：服务名称，格式为 `app.server`。
2. `ipAndPorts`（字符串数组，可选）：IP:Port 地址列表，来自 `GetGoReplayNodeList` 返回的 `service_list[].address` 或 `agent_list` 的 `ip:port` 组合。
3. `agent_ids`（字符串数组，可选）：Agent ID 列表，来自 `GetGoReplayNodeList` 返回的 `agent_list[].agent_id`。

> `ipAndPorts` 和 `agent_ids` 至少传入一个，否则查询结果为空。

#### 输出
调用成功时返回各地址 / Agent 的录制状态信息。

#### 使用场景
- 当不知道 task_id 但知道录制节点地址时，可用此工具查询
- 适合在未保存 task_id 的场景下检查某个节点是否正在录制
