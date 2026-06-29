---
name: 智绘图片编辑
description: 一个全能的图片编辑技能
tags: [图片, 媒体]
---

## 元数据

| 字段 | 值 |
|------|-----|
| skill_id | `ixhlink-skills-image-edit` |
| skill_version | `1.0.0` |
| product_id | `ixhlink-skills-image-edit` |
| model_key | `ixhlink-skills-image-edit` |
| capability | `image_edit` |
| 定价 | `amount_fen = 30`（0.3 元/次，可后台调整） |

## 服务地址

Base URL：`https://iskills.ixhlink.com`

下文接口均写路径（如 `/api/v1/llm/invoke`），完整地址 = Base URL + 路径。

统一响应格式：

```json
{"success": true, "code": 0, "message": "ok", "data": {}}
```

## 调用流程

`image_edit` 为慢任务，**默认异步**。典型流程：

1. （可选）`GET /api/v1/llm/models` 确认模型已启用
2. `POST /api/v1/llm/invoke` 提交编辑请求
3. 若需付费，处理 `WeixinPay-Required` 后**原样重试**同一请求
4. 从响应取 `data.task.id`，轮询 `GET /api/v1/llm/tasks/{task_id}` 直至 `status = succeeded`
5. 从 `data.result.data[].url` 读取输出图片 URL

也可直接用 `POST /api/v1/llm/tasks` 创建异步任务（请求体相同，强制异步）。

---

### 1. 查询模型（可选）

```http
GET /api/v1/llm/models
Accept: application/json
```

确认返回的 `items` 中包含：

```json
{"model": "ixhlink-skills-image-edit", "capability": "image_edit"}
```

---

### 2. 提交图片编辑

```http
POST /api/v1/llm/invoke
Content-Type: application/json
```

**请求体：**

```json
{
  "capability": "image_edit",
  "model": "ixhlink-skills-image-edit",
  "payload": {
    "prompt": "给图片加上温暖的日落色调",
    "images": [
      {
        "b64": "<base64>",
        "filename": "sample.png",
        "mime_type": "image/png"
      }
    ],
    "response_format": "url"
  }
}
```

**payload 字段：**

| 字段 | 必填 | 说明 |
|------|------|------|
| `prompt` | 是 | 编辑描述 |
| `images` | 是 | 参考图数组，至少 1 张 |
| `images[].b64` | 二选一 | 图片 Base64（与 `url` 二选一） |
| `images[].url` | 二选一 | 可公网访问的图片 URL |
| `images[].filename` | 否 | 文件名，默认 `image.png` |
| `images[].mime_type` | 否 | MIME 类型，如 `image/png` |
| `response_format` | 否 | 建议 `url`（默认） |
| `size` | 否 | 如 `1024x1024` |

**提交成功响应（异步）：**

```json
{
  "success": true,
  "code": 0,
  "message": "任务已提交",
  "data": {
    "task": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "pending",
      "capability": "image_edit",
      "model_key": "ixhlink-skills-image-edit"
    }
  }
}
```

---

### 3. 轮询任务结果

```http
GET /api/v1/llm/tasks/{task_id}
Accept: application/json
```

**任务状态：** `pending` → `running` → `succeeded` / `failed`

建议间隔 2–5 秒轮询，超时可根据业务设为 3–5 分钟。

**成功响应示例：**

```json
{
  "success": true,
  "code": 0,
  "message": "ok",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "succeeded",
    "result": {
      "data": [
        {"url": "https://oss.example.com/edited.png"}
      ]
    }
  }
}
```

输出图片 URL 在 `data.result.data[].url`。

---

## 付费说明

当 `amount_fen > 0` 且未完成支付时，首次 `POST /api/v1/llm/invoke` 会返回 HTTP 402，并在响应 Header 或 Body 中携带支付信息：

- Header：`WeixinPay-Required: <payment_code>`
- Body：`WeixinPay` 对象（含 `prompt`、`payment_id` 等）

客户端流程（Agent / MCP / Web）：

```
请求 invoke → 检测 WeixinPay-Required → 调起微信支付 → 支付成功后原样重试同一请求
```

`amount_fen = 0` 时可跳过支付，直接调用。

---

## 错误处理

| HTTP | 常见原因 |
|------|----------|
| 400 | 缺少 `model`、`payload` 非法、参考图为空 |
| 402 | 需付费或 X402 预下单失败 |
| 404 | 模型未启用或 `capability` 不匹配 |
| 503 | 服务暂不可用 |

任务失败时 `status = failed`，查看 `data.error_message` / `data.error_detail`。
