# 流量编辑规则配置指南

LogReplay 支持配置流量编辑规则，在回放前对请求/响应数据进行字段级编辑（新增、修改、删除字段），使回放测试更加灵活。

## 流量编辑规则概述

流量编辑规则用于在回放前对流量数据执行字段级编辑操作，支持对请求体、响应体等 JSON 字段进行 `add`、`update`、`delete`。规则以**接口**为粒度进行配置，一个接口（`api_name`）对应一组编辑规则（`EditRule`），规则组下包含若干条具体规则（`ItemRule`）。

## 编辑操作类型

每条编辑规则（`ItemRule`）必须指定 `action`，共三种：

| action | 说明 | 是否需要 `value` |
|--------|------|------------------|
| `add` | 新增字段 | 需要 |
| `update` | 修改字段值（包含普通替换更新、正则替换更新两种） | 需要 |
| `delete` | 删除字段 | 不需要（填空串即可） |

## value 的数据类型（`type` 字段）

`type` 描述 `value` 的数据类型，共五种取值：

| type | 说明 |
|------|------|
| `string` | 字符串类型 |
| `number` | 数值类型（整型/浮点型） |
| `boolean` | 布尔类型 |
| `null` | 空值 |
| `undefined` | 未定义（通常用于配合正则替换等场景） |

`action` 为 `delete` 时，`value` 不生效，`type` 可填写原字段类型或任意占位值。

## key 路径规则

`key` 是目标字段的 JSON 路径，支持嵌套访问：

- 请求体字段：以 `requestBody.` 开头，例如 `requestBody.user.name`
- 响应体字段：以 `responseBody.` 开头，例如 `responseBody.data.list`
- 请求头/响应头等其他位置按实际协议结构填写

新增字段（`action=add`）时，`key` 同样使用上述路径写法，表示"在该路径下新增一个字段"。例如：

- `requestBody.user.name`：在 `requestBody.user` 下新增 `name` 字段
- `requestBody.custom_field`：在 `requestBody` 顶层新增 `custom_field` 字段

### 新增字段的协议限制

**如果接口绑定了 protobuf 协议文件**：新增 pb 中不存在的字段时，编包阶段会失败，规则不会生效。此场景下 `add` 只能用于 pb 中已定义、但原流量中未赋值（缺省）的字段。

**如果接口没有协议文件**（例如纯 JSON/HTTP 流量）：对新增字段无此限制，可以任意新增。

### 数组批量编辑

对于数组内元素的同名字段，可使用 `*` 作为通配符批量编辑数组下的每一项：

| 场景 | key 写法 | 含义 |
|------|----------|------|
| 编辑单个字段 | `requestBody.key` | 编辑 `requestBody` 下的 `key` 字段 |
| 编辑数组内每一项的同名字段 | `requestBody.list.*.key` | 批量编辑 `requestBody.list` 数组下每个元素的 `key` 字段 |

> `*` 代表数组下所有元素，可用于 `add` / `update` / `delete` 任一 `action`。

## 更新模式：普通替换 vs 正则替换

`action=update` 时支持两种更新模式，通过 `value` 的写法区分：

### 1. 普通替换更新

直接将字段值替换为 `value`，配合 `type` 指定新值的数据类型。

- `type=string` 时，`value` 为新字符串
- `type=number` 时，`value` 为数值字面量（以字符串形式传入，如 `"100"`）
- `type=boolean` 时，`value` 为 `"true"` / `"false"`
- `type=null` 时，字段值会被置为 `null`

### 2. 正则替换更新

`value` 使用 `${regexp_replace("正则表达式", "替换值")}` 模板，对原字段值执行正则匹配后替换：

- 第一个参数：正则表达式。填空串 `""` 时表示整体替换。
- 第二个参数：替换值（可以是字面量，也可以是动态表达式）。

### 3. 动态表达式占位符

`value` 中支持内置动态表达式，在回放执行时动态求值。占位符可单独使用，也可作为 `regexp_replace` 第二个参数（替换值）使用。

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `${random_string(3,"abc")}` | 生成随机字符串。参数 1：长度；参数 2：字符集 | `${random_string(8,"abcdef0123456789")}` |
| `${random_int(0,10)}` | 生成指定范围内的随机整数（闭区间） | `${random_int(100,999)}` |
| `${timestamp()}` | 当前时间戳 | `${timestamp()}` |
| `${uuid()}` | 生成一个 UUID | `${uuid()}` |
| `${base64("abc")}` | 对指定字符串做 Base64 编码 | `${base64("hello")}` |
| `${regexp_replace("<regex>", "<replacement>")}` | 正则替换，用于 `update` 的正则替换模式 | `${regexp_replace("\\d+", "${timestamp()}")}` |

> 上述函数中填写的参数均为示例默认值，实际使用时按需调整。`${...}` 占位符只能出现在 `value` 中，`type` 按占位符求值后的目标类型填写（例如 `${random_string(...)}` 对应 `string`，`${random_int(...)}` / `${timestamp()}` 对应 `number` 或 `string` 视实际服务端接收类型而定）。

## 规则启用开关

每个规则组（`EditRule`）有独立的 `edit_enabled` 开关：

- `true`：该接口的编辑规则组在回放时生效
- `false`：该接口的编辑规则组整体被忽略（即使规则组存在也不执行）

## 规则结构

### ItemRule（单条编辑规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| `key` | string | JSON key 路径 |
| `value` | string | 修改后的 JSON value（`delete` 时不生效） |
| `type` | string | value 的数据类型：`string` / `number` / `boolean` / `null` / `undefined` |
| `action` | string | 编辑行为：`add`（新增）、`update`（修改）、`delete`（删除） |
| `id` | integer | 规则 ID（服务端生成，创建时无需填写） |

### EditRule（编辑规则组）

一个 `EditRule` 对应一个接口的编辑规则集合：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | integer | 规则组 ID（服务端生成，创建时无需填写） |
| `module_id` | string | 模块 ID |
| `api_name` | string | 接口名（以接口为粒度配置规则，必填） |
| `server_name` | string | 服务名 |
| `proto_version` | string | proto 版本号 |
| `msg_name` | string | message name |
| `protocol` | string | 协议名（如 `trpc`、`http`） |
| `edit_enabled` | boolean | 规则组是否启用 |
| `rules` | ItemRule[] | 具体的编辑规则列表 |

### 接口元信息的获取方式

`EditRule` 中除 `api_name`、`edit_enabled`、`rules` 之外的字段，获取方式如下：

- **`server_name`**：工具层不对外暴露，内部会自动使用 `app_server_name`（格式 `app.server`）的原值填入，调用方无需关心。
- **`msg_name`**：即接口的方法名（如 `Count`、`QueryUser`），**不是**带路径的 `api_name`。**可选**，不填时**工具层会自动从 `api_name` 末尾截取方法名**（按 `/` 分隔取最后一段）作为默认值；用户也可显式指定。**注意：后端不会对该字段做兜底，默认值由 Python 工具层填入。`RecordSearch` 返回的流量中不包含该字段**，不要试图从录制流量中读取。
- **`protocol` / `proto_version`**：**必传**。值来源只有两种：① 从该接口的一条录制流量中读取同名字段（通过 `RecordSearch` 获取），② 由用户显式指定。二者取其一，但工具调用时必须传入。
