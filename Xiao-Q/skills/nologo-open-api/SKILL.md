---
name: nologo-open-api
description: 抖音、小红书、豆包、千问等平台的图片/视频去水印解析。当用户需要去除视频/图片水印、获取无水印直链、调用解析API、查询价格时使用此skill。
---

# nologo 无水印解析 API 使用指南

此skill提供nologo去水印API的完整调用文档，支持抖音、小红书、豆包、千问等平台的图片和视频去除水印，包括API端点、请求参数、响应格式、错误处理等。

## API 概览

- **API地址**: `https://nologo.code24.top/api/open/parse`
- **认证方式**: Authorization 请求头传递 Token
- **Token获取**: 请添加微信 linglan008 获取
- **频率限制**: 每分钟最多20次请求

## 价格

| 数量 | 单价(元/次) | 合计(元) |
|------|-------------|----------|
| 100次 | 0.02 | 2.00(免费使用) |
| 2,500次 | 0.01 | 25.00 |
| 5,000次 | 0.008 | 42.50 |
| 7,500次 | 0.007 | 56.25 |
| 10,000次 | 0.006 | 65.00 |

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 视频、图片分享链接 |

**核心注意**: url参数必须URL编码
链接获取方式：https://zwf4g5rfwiy.feishu.cn/wiki/JGjpwZ1Feiw8Zxks4Hoc8vI9nle (包含抖音/小红书/豆包/千问等平台链接获取教程)

## AI 对话案例

以下案例展示 AI 助手如何与用户互动，帮助用户完成无水印解析。

### 对话案例一：用户想下载抖音无水印视频

**用户**：帮我下载这个抖音视频，去掉水印 https://v.douyin.com/iKQFm1pR/

**AI 思考过程**：
1. 用户提供了一个抖音分享链接，需要调用 nologo API 解析
2. 链接需要先 URL 编码
3. 将编码后的链接传给 API，加上 Token 认证
4. 从响应中提取无水印视频直链返回给用户

**AI 回复示例**：
```
好的，我帮你解析这个抖音视频，去掉水印。

正在调用解析服务... ✅ 解析成功！

🎬 **视频标题**：这是一段有趣的抖音视频
📝 **描述**：今天发现了一个好玩的地方~ #旅行 #探店
📥 **无水印视频直链**：[点击下载](https://v3-default.douyinvod.com/xxx/xxxyyyy.mp4?xx)

你可以直接点击链接下载，或者在浏览器中打开观看。
当前套餐剩余：4977/5000 次
```

---

### 对话案例二：用户想保存小红书图片原图

**用户**：帮我保存这个小红书笔记里的所有图片 https://www.xiaohongshu.com/explore/67ffa2d3000000000a00abcd

**AI 思考过程**：
1. 用户提供的是小红书笔记链接，type 应为 `img`
2. 解析成功后 `data.urls` 会返回所有图片直链
3. 如果有多个链接，逐一展示给用户

**AI 回复示例**：
```
收到，我来解析这篇小红书笔记的图片。

正在解析... ✅ 解析成功！

📄 **笔记标题**：周末探店分享
📝 **描述**：这家咖啡店真的绝了！附上几张美图~

共获取到 **3 张无水印原图**：

🖼️ 图片 1：[点击下载](https://sns-webpic-qc.xhscdn.com/xxx/0101abcd.jpg)
🖼️ 图片 2：[点击下载](https://sns-webpic-qc.xhscdn.com/xxx/0101efgh.jpg)
🖼️ 图片 3：[点击下载](https://sns-webpic-qc.xhscdn.com/xxx/0101ijkl.jpg)

当前套餐剩余：4976/5000 次
```

---

### 对话案例三：用户询问价格和购买方式

**用户**：这个解析服务怎么收费？我想买一些次数

**AI 回复示例**：
```
nologo 无水印解析 API 的套餐价格如下：

| 数量 | 单价 | 合计 |
|------|------|------|
| 100 次 | 0.02 元/次 | 2.00 元（免费体验）|
| 2,500 次 | 0.01 元/次 | 25.00 元 |
| 5,000 次 | 0.008 元/次 | 42.50 元 |
| 7,500 次 | 0.007 元/次 | 56.25 元 |
| 10,000 次 | 0.006 元/次 | 65.00 元 |

购买方式：请添加微信 **linglan008** 获取 API Token。
建议新手先试用 100 次免费套餐体验效果。
```

---

## 响应格式

### 成功响应 - 图片
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "type": "img",
    "urls": ["xx", "xx"],
    "title": "xx",
    "desc": "xx",
    "usage": {
      "totalLimit": "xxx",
      "usedCount": "xxx",
      "remainingCount": "xxx"
    }
  }
}
```

### 成功响应 - 视频
```json
{
  "code": 200,
  "message": "请求成功",
  "data": {
    "type": "video",
    "url": "xx",
    "title": "xx",
    "desc": "xx",
    "usage": {
      "totalLimit": "xxx",
      "usedCount": "xxx",
      "remainingCount": "xxx"
    }
  }
}
```

## 错误响应

| 错误码 | 错误信息 |
|--------|----------|
| 400 | URL参数不能为空或URL格式不正确 |
| 401 | 缺少API Token，请在Authorization请求头中传递Token |
| 403 | 无效的API Token / API Token已被禁用 / API Token调用次数已耗尽 |
| 404 | 未找到资源或获取失败 |
| 500 | 服务器内部错误 |

## 错误码速查

- `code === 200`: 成功
- `code === 400`: URL参数错误
- `code === 401`: Token未传递
- `code === 403`: Token无效/禁用/次数用尽
- `code === 404`: 资源未找到
- `code === 500`: 服务器错误

## Token缓存脚本

项目提供了Node.js脚本用于缓存Token（默认为空），set-token命令会自动保存到config.json：

### 使用方法

```bash
cd skills/nologo-open-api/references

# 设置Token (token会自动保存到config.json)
node api-client.js set-token your-token-here

# 解析链接
node api-client.js parse "https://v.douyin.com/xxxxx"
```

## 快速开始

```bash
cd skills/nologo-open-api/references

# 设置Token (token会自动保存到config.json)
node api-client.js set-token your-token-here

# 解析链接
node api-client.js parse "https://v.douyin.com/xxxxx"
```

## 文件结构

```
nologo-open-api/
├── SKILL.md          # 文档
├── README.md        # 快速指南
└── references/
    ├── api-client.js    # nologo无水印解析
    └── config.json      # 配置
```
