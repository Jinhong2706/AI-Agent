---
name: newapi-image
description: 使用 NewAPI 图像生成接口进行文生图。适用于 OpenAI 与 Gemini 渠道生图，且需要将图片保存为本地文件返回的场景。
---

# NewAPI Image

本 Skill 封装了 NewAPI 的多种图像生成调用方式，支持通过提示词直接生成图片。

## 前置条件

优先检查本 Skill 本地目录的 `.env` 文件（`{baseDir}/.env`）中是否已存在以下信息，如果环境文件不存在请新建：

- `NEWAPI_API_KEY`
- `NEWAPI_BASE_URL`

若缺少任一项，再向用户询问并补写到 `.env`：

```bash
cat > {baseDir}/.env <<'EOF'
NEWAPI_API_KEY=你的key
NEWAPI_BASE_URL=https://your-newapi-server-address
EOF
```

执行规则：

1. 每次执行前先检查 `{baseDir}/.env` 是否同时包含 `NEWAPI_API_KEY` 与 `NEWAPI_BASE_URL`。
2. 若本地已存在且非空，直接执行生成脚本，不再询问用户。
3. 若本地缺失或为空，再向用户询问缺失项并写入 `{baseDir}/.env`。
4. 后续优先使用 `.env` 中的配置；命令行参数可覆盖 `.env`。

## 使用方法

### OpenAI 方式（默认）
```bash
uv run {baseDir}/scripts/generate_image.py \
  --mode openai \
  --prompt "一只赛博朋克风格的猫"
```

### OpenAI 方式（指定模型）
```bash
uv run {baseDir}/scripts/generate_image.py \
  --mode openai \
  --prompt "中国风插画，青山与云海" \
  --model "doubao-seedream-4-5"
```

### Gemini 方式
```bash
uv run {baseDir}/scripts/generate_image.py \
  --mode gemini \
  --prompt "生成一张未来城市科幻风格海报" \
  --model "gemini-3.1-flash-image-preview"
```

### 阿里云渠道（当前不支持）
```bash
uv run {baseDir}/scripts/generate_image.py \
  --mode aliyun \
  --prompt "这条会返回不支持错误"
```

### 查看当前可用模型
```bash
uv run {baseDir}/scripts/generate_image.py --list-models
```

### OpenAI 方式返回 Base64
```bash
uv run {baseDir}/scripts/generate_image.py \
  --mode openai \
  --prompt "未来城市夜景" \
  --response-format "b64_json"
```

## 配置方式

可通过命令行参数或环境变量传递配置：

- API Key：
  - `--api-key`
  - `NEWAPI_API_KEY`
- 服务地址：
  - `--base-url`
  - `NEWAPI_BASE_URL`

脚本会自动读取 `{baseDir}/.env` 中的 `NEWAPI_API_KEY` 和 `NEWAPI_BASE_URL`。

## 参数说明

- `--prompt`: 必填，图像生成提示词。
- `--list-models`: 可选，输出当前支持的渠道与模型并退出。
- `--mode`: 可选，`openai` / `gemini` / `aliyun`，默认 `openai`。
- `--model`: 可选。不同模式默认模型不同：
  - `openai`: `doubao-seedream-5-lite`
  - `gemini`: `gemini-3.1-flash-image-preview`
  - `aliyun`: 暂不支持
- `--n`: 可选，生成图片数量，默认 `1`（仅 OpenAI 方式有效）。
- `--size`: 可选，默认 `2048x2048`（Gemini 下用于推导宽高比）。
  - 格式必须是 `宽x高`，例如 `2048x2048`
  - 像素总数下限为 `3686400`
- `--quality`: 可选，例如 `standard` / `hd`（仅 OpenAI 方式）。
- `--style`: 可选，例如 `vivid` / `natural`（仅 OpenAI 方式）。
- `--response-format`: 可选，`url` 或 `b64_json`，默认 `url`（仅 OpenAI 方式）。
- `--user`: 可选，终端用户标识。
- `--timeout`: 可选，请求超时秒数，默认 `60`。
- `--output-dir`: 可选，本地输出目录。默认 `{baseDir}/outputs`。

## 模型配置

默认模型与渠道支持矩阵定义在 `{baseDir}/scripts/model_config.py`：

- OpenAI 支持：
  - `doubao-seedream-5-lite`
  - `doubao-seedream-4-5`
- Gemini 支持：
  - `gemini-3.1-flash-image-preview`
- 阿里云渠道：
  - 当前不支持，调用会返回错误。

## 中文别名

为方便技能理解用户口语化表达，使用以下备注映射：

- `豆包seedream5` -> `doubao-seedream-5-lite`
- `豆包seedream4-5` -> `doubao-seedream-4-5`
- `香蕉模型` -> `gemini-3.1-flash-image-preview`

当用户在需求中提到这些叫法时，应在生成脚本参数时转换为右侧真实模型名。
脚本参数 `--model` 仅接受真实模型名，不接受中文别名。

## 工作流

1. 调用 `generate_image.py`。
2. 根据 `--mode` 自动选择接口：
   - `openai`：`{base_url}/v1/images/generations`（Bearer 鉴权）
   - `gemini`：`{base_url}/v1beta/models/{model}:generateContent?key=API_KEY`
   - `aliyun`：直接返回不支持错误
3. 无论响应是 URL 还是 Base64，脚本都会先保存为本地图片文件。
4. 每张图片输出 `MEDIA_FILE: <absolute_path>`，以本地文件路径形式返回。
5. 若需要自定义保存目录，使用 `--output-dir`。
6. 生成完成后不要读取图片文件内容，以避免消耗大量上下文；仅检查文件存在，并返回图片文件路径。
