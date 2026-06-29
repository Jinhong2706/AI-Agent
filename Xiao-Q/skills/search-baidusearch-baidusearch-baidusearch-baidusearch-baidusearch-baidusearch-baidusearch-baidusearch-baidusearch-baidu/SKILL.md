---
name: adp-multimodal-generation
description: 通过腾讯 ADP 平台的多模态插件能力，根据文本或图文组合输入生成图片、视频和 3D 模型，统一以 submit + 轮询 query 完成任务并返回成品 URL。覆盖文生图、图生图、文生视频、图生视频、文生 3D、图生 3D 全场景，并按用户意图自动路由到混元 image.hy、GI 版 image.gi（提到 nano banana / Gemini 时切换）、可灵 video.kling、VIDU video.vidu、混元 3D 3d.hy。只要用户提到"画一张/生成图片/出图/配图/封面图/AI 绘图/换风格""生成视频/做个短视频/图生视频/让图片动起来""做个 3D 模型/3D 建模/glb/obj/glTF"，或点名 nano banana / Gemini / 可灵 / Kling / VIDU / 混元 3D 等模型，即使没明确说"用 ADP"，也应优先使用本 Skill。本 Skill 需要 ADP_API_KEY，且不会跨类别静默降级（视频不会偷偷换成图片）。
---

# ADP 多模态生成

> **ADP 多模态生成 Skill** | 本 Skill 提供 **图片生成、视频生成、3D 模型生成** 三类能力，统一按异步任务方式完成提交与结果查询。

## 概述

本技能用于在中文场景下，按用户意图为图片、视频和 3D 生成请求选择合适的 ADP 能力模块，并以 submit/query 成对方式执行异步任务。

| 特性 | 说明 |
|---|---|
| 支持能力 | 图片生成、视频生成、3D 模型生成 |
| 执行模式 | 异步模式，先提交任务，再轮询查询 |

### 模块划分

| 模块 | 可选模型 | 说明 |
|---|---|---|
| `image` | `hy`、`gi` | 图片生成模块 |
| `video` | `kling`、`vidu` | 视频生成模块 |
| `3d` | `hy` | 3D 模型生成模块 |

调用前先读 [references/ability-catalog.md](references/ability-catalog.md)。里面记录了当前已核实的模块别名、能力页地址、底层工具名、关键参数以及当前可调用状态。

## 重要说明

1. 运行前请先安装依赖：`pip install -r requirements.txt`，并确保环境变量中提供了 `ADP_API_KEY`。详见 [步骤 3 的"运行依赖"](#运行依赖) 小节。
2. 本 Skill 面向中文业务场景，默认用中文向用户解释模块选择、参数和阻塞原因。
3. 本 Skill 调用的是 ADP 平台的多模态能力，不是腾讯云开放 API。
4. 只有在 [references/ability-catalog.md](references/ability-catalog.md) 中被明确核实过的字段，才能当成已确认事实使用。
5. 如果某个能力当前不能执行，直接汇报阻塞，不要猜内部接口，也不要私自换到别的模型。

## 模块与别名

不要直接让用户或调用方记能力 ID。统一按下面的模块别名使用：

| 别名 | 模块 | 对应能力 |
|---|---|---|
| `image.hy` | 图片生成 | `图片生成（3.0）` |
| `image.gi` | 图片生成 | `图片生成GI版` |
| `video.kling` | 视频生成 | `可灵视频生成` |
| `video.vidu` | 视频生成 | `VIDU视频生成` |
| `3d.hy` | 3D 生成 | `混元生3D（专业版）` |

执行时只接受这些模块别名，不接受直接传底层标识。

## 路由规则

按以下规则路由：

| 用户意图 | 默认能力 | 切换条件 | 切换后能力 |
|---|---|---|---|
| 图片生成 | `图片生成（3.0）` | 提到 `Gemini`、`nano banana`，或明确要求换一个生图模型 | `图片生成GI版` |
| 视频生成 | `可灵视频生成` | 提到 `VIDU`，或明确要求换一个生视频模型 | `VIDU视频生成` |
| 3D 生成 | `混元生3D（专业版）` | 无 | 不切换 |

不要跨类别静默降级。比如用户明确要视频生成，而当前目标能力不能外呼时，不能偷偷改成图片或 3D 能力。

## 执行流程

### 步骤 1：选择能力

按上面的路由规则选择能力，再到 [references/ability-catalog.md](references/ability-catalog.md) 核对已验证事实。

### 步骤 2：选择模式

按能力类型选择模式：

| 别名 | 支持模式 | 说明 |
|---|---|---|
| `image.hy` | `text2image`、`image2image` | 文生图或图生图 |
| `image.gi` | `text2image`、`image2image` | 文生图或图生图 |
| `video.kling` | `text2video`、`image2video` | 文生视频或图生视频 |
| `video.vidu` | `text2video`、`image2video` | 文生视频或图生视频 |
| `3d.hy` | `text23d`、`image23d` | 文生 3D 或图生 3D |

补充规则：

- `image.hy` 的 `text2image` 只需要 `Prompt`
- `image.hy` 的 `image2image` 需要 `Prompt + Images`
- `image.gi` 的 `text2image` 只需要 `Prompt`
- `image.gi` 的 `image2image` 需要 `Prompt + Images`

### 步骤 3：脚本用法

#### 运行依赖

执行脚本前请先安装依赖：

```bash
pip install -r requirements.txt
```

依赖清单见 [requirements.txt](requirements.txt)，目前仅需要 `requests`。脚本同时要求环境中提供 `ADP_API_KEY`（环境变量优先），未设置时会汇报阻塞。

#### 调用方式

统一格式：

```bash
python3 scripts/adp_mcp.py <alias> run [--mode <mode>] [--step <submit|query>] (<json> | -f <json-file>)
```

参数提供方式二选一：

- 直接传 JSON 字符串（参数体积小或不含 base64 时使用）。
- 通过 `-f/--arguments-file` 指定 JSON 文件路径，或传 `-f -` 从 stdin 读取（推荐用于图生图、图生视频等含 base64 的大请求体）。

常见示例：

```bash
python3 scripts/adp_mcp.py image.hy run '{"Prompt":"一只白色小猫坐在木桌上，写实风格","Resolution":"1024:1024"}'
python3 scripts/adp_mcp.py image.hy run --mode image2image '{"Prompt":"保留主体，改成宫崎骏风格","Images":["https://example.com/input.png"]}'
python3 scripts/adp_mcp.py image.gi run --mode image2image -f /tmp/gi_args.json
python3 scripts/adp_mcp.py video.kling run --mode text2video '{"Prompt":"海边日落延时摄影","Duration":"5"}'
python3 scripts/adp_mcp.py video.vidu run --mode image2video '{"Images":["https://example.com/input.png"],"Duration":5}'
python3 scripts/adp_mcp.py 3d.hy run '{"Prompt":"一辆未来感概念跑车"}'
```

分步执行示例：

```bash
python3 scripts/adp_mcp.py image.hy run --step submit '{"Prompt":"一只白色小猫坐在木桌上，写实风格","Resolution":"1024:1024"}'
python3 scripts/adp_mcp.py image.hy run --step query '{"JobId":"123"}'
```

### 步骤 4：汇报结果

汇报时必须说明：

- 最终使用了哪个能力
- 这是默认命中还是关键词触发的模型切换
- 如果失败，是 submit 失败还是 query 结果失败
- 如果是外部调用受限，要明确标注为平台限制

## 参考资料

- 逐能力事实看 [references/ability-catalog.md](references/ability-catalog.md)。
