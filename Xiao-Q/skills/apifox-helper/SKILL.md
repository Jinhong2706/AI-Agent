---
name: apifox-helper
description: Use when 用户要求把当前选中的接口上传到 Apifox、同步当前接口到 Apifox，或将某段控制器和路由处理函数导入 Apifox。
---

# Apifox Helper

## 目的

把用户当前选中的接口代码整理成最小可用的 OpenAPI 3 文档，并导入到 Apifox。

## 配置要求

开始前先检查 skill 目录下的 `config.json`：

- `accessToken`
- `projectId`

如果 `config.json` 不存在，先在当前 skill 目录中创建该文件模板，再让用户填写。

如果 `config.json` 已存在但缺少以下任一字段，则必须先让用户补充到文件中后再继续：

- `accessToken`
- `projectId`

不能带着缺失配置往下执行。

配置文件路径：

```text
当前 skill 目录下的 `config.json`
```

配置文件格式：

```json
{
  "accessToken": "",
  "projectId": ""
}
```

命令行参数可覆盖配置文件中的值，但默认优先使用该配置文件。

以下参数不要写入配置文件，只在每次执行时按需传入：

- `moduleId`
- `targetEndpointFolderId`

导入位置规则：

- 如果 `moduleId` 和 `targetEndpointFolderId` 都没有传入，则导入到默认模块
- 如果只传入 `moduleId`，则导入到该模块下；如导入内容包含目录结构，会在该模块下生成对应目录
- 如果传入 `moduleId` 但未传入 `targetEndpointFolderId`，则导入到目标模块的根目录
- `targetEndpointFolderId` 必须和 `moduleId` 一起传入
- 如果只传入 `targetEndpointFolderId`，则不要单独使用该参数

## 使用场景

在以下场景使用：

- 用户要求把当前选中的接口上传到 Apifox
- 用户要求把当前正在看的接口同步到 Apifox
- 用户要求把某段控制器、路由处理函数导入到 Apifox

## 执行流程

1. 确认范围
   - 优先使用当前编辑器选中的代码。
   - 如果没有明确选区，要求用户先选中接口代码，或明确给出符号/文件范围。
   - 只处理选中的接口，不默认扫描整个项目。

2. 从代码中提取接口信息
   - HTTP 方法
   - 路由路径
   - Header 参数（如鉴权、租户、版本、幂等键、自定义业务头）
   - 路径参数、查询参数
   - 请求体（body）
   - 成功响应的大致结构
   - 控制器或模块标签

3. 生成接口名称
   - 优先使用接口上方的注释、文档注释或框架摘要注解作为名称。
   - 可参考 JSDoc、JavaDoc、处理函数上方的行注释、Swagger/框架摘要注解。
   - 如果没有注释，则根据路由语义和方法行为生成一个简洁名称。
   - 项目本身以中文为主时优先用中文名称。

4. 生成最小 OpenAPI 3 文档
   - 把接口名称写入 `summary`。
   - 每个接口生成一个 `paths[path][method]` 条目。
   - 如果接口存在 Header 入参，写入 `parameters`，并标记 `in: header`。
   - 如果接口存在路径参数、查询参数，也分别写入 `parameters`。
   - 如果接口存在请求体，写入 `requestBody`；至少补齐 `required`、`content`、`schema` 的最小结构。
   - 始终包含 `responses`，若响应结构不清晰，至少给出一个最小 `200` 占位响应。
   - 只生成必要结构，不凭空臆造复杂 schema。

5. 导入到 Apifox
   - 开始执行前，先检查当前 skill 目录下是否存在 `config.json`。
   - 如果不存在，先创建模板文件，再提示用户补充配置。
   - 如果文件存在但缺少 `accessToken` 或 `projectId`，提示用户补充到文件中后再继续。
   - 默认不要落地临时文件，优先直接通过标准输入把 OpenAPI JSON 传给脚本。
   - 执行：

```bash
python "当前 skill 目录/scripts/import_openapi.py" --input -
```

   - 如果用户本次希望指定模块或接口目录，可额外传入：

```bash
python "当前 skill 目录/scripts/import_openapi.py" \
  --input - \
  --module-id 123 \
  --target-endpoint-folder-id 456
```

   - 仅当用户显式传入 `moduleId` 或 `targetEndpointFolderId` 时，才把它们带到导入请求中。
   - 如果用户没有传入，则不要写入配置文件；请求中的 `endpointOverwriteBehavior` 和 `schemaOverwriteBehavior` 使用 Apifox 默认值 `OVERWRITE_EXISTING`。
   - 如果只传入 `moduleId`，则导入到目标模块的根目录。
   - 如果同时传入 `moduleId` 和 `targetEndpointFolderId`，则导入到指定模块下的指定目录。
   - 如果只传入 `targetEndpointFolderId`，则忽略该参数，不单独使用。
   - 如果用户描述了重复处理方式，则将描述映射为对应枚举后再传给脚本：`OVERWRITE_EXISTING`、`AUTO_MERGE`、`KEEP_EXISTING`、`CREATE_NEW`。
   - 可识别的常见描述包括：
     `覆盖现有接口/模型` -> `OVERWRITE_EXISTING`
     `自动合并/自动合并更改` -> `AUTO_MERGE`
     `跳过并保留/保留现有` -> `KEEP_EXISTING`
     `创建新的/保留现有并创建新的` -> `CREATE_NEW`

   - 只有在内容过大、需要排查问题、或用户明确要求保留导入产物时，才允许先写入文件。
   - 一旦必须写文件，文件必须输出到当前项目目录，不要写到系统临时目录。
   - 默认可放在项目内类似 `./.cursor/apifox/selected-endpoints.openapitmp.json` 的位置；若项目没有 `.cursor` 目录，可直接放到当前项目根目录下的临时文件名。

6. 正确处理重复路由
   - 用户未指定时，辅助脚本对 `endpointOverwriteBehavior` 和 `schemaOverwriteBehavior` 使用默认值 `OVERWRITE_EXISTING`。
   - 用户指定时，辅助脚本根据用户描述映射到对应枚举。
   - 如果选择 `KEEP_EXISTING`，Apifox 判断该路由已存在时会保留已有接口，不覆盖。
   - 出现 `endpointIgnored` 属于预期行为。

## 命名规则

接口名称按以下优先级生成：

1. 显式注释
2. 框架摘要注解
3. 处理函数名 + 路由语义

示例：

- `/** 查询用户详情 */` -> `查询用户详情`
- 无注释，`GET /users/{id}` -> `获取用户详情`
- 无注释，`POST /orders` -> `创建订单`

## OpenAPI 模板

按这个结构组织：

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "选中接口导入",
    "version": "1.0.0"
  },
  "paths": {
    "/example/path": {
      "get": {
        "summary": "示例接口名",
        "operationId": "getExamplePath",
        "tags": ["Example"],
        "parameters": [
          {
            "name": "Authorization",
            "in": "header",
            "required": false,
            "schema": {
              "type": "string"
            },
            "description": "认证令牌"
          }
        ],
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "OK"
          }
        }
      }
    }
  }
}
```

## 约束

- 如果 `config.json` 中的 `accessToken` 或 `projectId` 缺失，则必须先让用户补齐。
- 如果 `config.json` 不存在，则先创建模板文件，再让用户补充配置。
- `moduleId` 和 `targetEndpointFolderId` 只允许作为本次执行的可选参数传入，不写入配置文件。
- `targetEndpointFolderId` 必须搭配 `moduleId` 使用，不能单独使用。
- 如果接口代码里存在 Header 或 body 入参，必须写入生成的 OpenAPI，不能省略。
- 除了 `config.json` 这类必要配置文件，执行过程中尽量不生成额外文件。
- 如果确实必须生成文件，文件必须放在当前项目目录中。
- 未经用户明确授权，不处理未选中的文件或接口。
- 不覆盖 Apifox 中已存在的接口。
- 不删除 Apifox 中未匹配的资源。
- 如果代码里看不清 HTTP 方法或路由路径，先询问用户，不要猜。

## 辅助脚本

默认使用辅助脚本，不手写 `curl`：

- `scripts/import_openapi.py`

该脚本会请求：

- `POST https://api.apifox.com/v1/projects/{projectId}/import-openapi`

并使用以下策略：

- `X-Apifox-Api-Version: 2024-03-28`
- `Authorization: Bearer <token>`
- `endpointOverwriteBehavior`：未指定时默认 `OVERWRITE_EXISTING`，指定时按用户描述映射
- `schemaOverwriteBehavior`：未指定时默认 `OVERWRITE_EXISTING`，指定时按用户描述映射

## 最终回复

只需要简要说明：

- 本次整理了哪些接口
- 最终使用了哪些接口名称
- 导入结果是新增还是忽略
- 是否存在配置缺失或接口信息不明确的问题
