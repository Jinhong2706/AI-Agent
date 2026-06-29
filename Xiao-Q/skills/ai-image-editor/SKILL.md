---
name: ai-image-editor
description: AI修图技能，支持基础调色（亮度/对比度/饱和度/裁剪/旋转）、智能处理（去水印/去路人/换背景/AI扩图）、风格化滤镜（复古/黑白/暖色/冷色等）。当用户发来图片并要求修图、调色、加滤镜、去水印、换背景、消除物体等操作时触发此技能。
---

# AI Image Editor

## 概述

接收用户图片 + 修图指令，调用 Python 脚本完成处理，返回修好后的图片。

## 支持的修图操作

### 基础调整
- **亮度**：调亮 / 调暗
- **对比度**：增强 / 降低
- **饱和度**：增强 / 降低 / 黑白
- **裁剪**：按指定比例或尺寸裁剪
- **旋转**：顺时针/逆时针 90°、180°、任意角度
- **翻转**：水平翻转 / 垂直翻转

### 智能处理
- **去水印**：去除图片中指定区域的水印文字
- **去路人**：消除图片中指定物体或人物
- **换背景**：将前景主体抠出，替换为纯色或指定背景
- **AI扩图**：按指定方向扩展画布并填充内容

### 风格化滤镜
- 复古、黑白、暖色、冷色、胶片、鲜艳

## 使用流程

1. **确认需求**：从用户消息中提取修图指令和参数
2. **保存图片**：将用户图片下载到 `/workspace/ai-image-editor/assets/input.jpg`
3. **调用脚本**：根据需求执行对应脚本（见下方脚本映射）
4. **返回结果**：将处理后的图片路径通过 `getfile` 返回给用户

## 脚本映射

| 用户需求 | 调用脚本 |
|---------|---------|
| 调亮度/对比度/饱和度 | `scripts/adjust_basic.py` |
| 裁剪/旋转/翻转 | `scripts/transform.py` |
| 去水印/去物体 | `scripts/inpaint.py` |
| 换背景 | `scripts/change_bg.py` |
| 加滤镜 | `scripts/filter.py` |
| AI扩图 | `scripts/outpaint.py` |

## 脚本调用示例

```bash
# 基础调色：亮度+30，对比度+20，饱和度+10
python scripts/adjust_basic.py \
  --input assets/input.jpg \
  --output assets/output.jpg \
  --brightness 30 --contrast 20 --saturation 10

# 旋转90度
python scripts/transform.py \
  --input assets/input.jpg \
  --output assets/output.jpg \
  --rotate 90

# 裁剪：从(x,y)开始裁剪w*h区域
python scripts/transform.py \
  --input assets/input.jpg \
  --output assets/output.jpg \
  --crop 100 50 400 300

# 黑白滤镜
python scripts/filter.py \
  --input assets/input.jpg \
  --output assets/output.jpg \
  --filter grayscale

# 复古滤镜
python scripts/filter.py \
  --input assets/input.jpg \
  --output assets/output.jpg \
  --filter vintage
```

## 参数说明

### adjust_basic.py
- `--brightness`：亮度调整，-100 ~ 100，默认0
- `--contrast`：对比度调整，-100 ~ 100，默认0
- `--saturation`：饱和度调整，-100 ~ 100，默认0

### transform.py
- `--rotate`：旋转角度（度），支持任意角度
- `--crop x y w h`：裁剪区域，x y为左上角坐标，w h为宽高
- `--flip`：`horizontal` 或 `vertical`

### filter.py
- `--filter`：滤镜名称，可选 `grayscale` / `vintage` / `warm` / `cool` / `film` / `vivid`

### inpaint.py（去水印/去物体）
- `--mask`：蒙版图片路径，白色区域为要去除的区域
- 或使用 `--auto` 自动检测水印区域

### change_bg.py（换背景）
- `--bg-color`：背景颜色，如 `white` / `#FF0000` / `transparent`
- 或使用 `--bg-image` 指定背景图片

## 注意事项

- 输入图片优先使用用户提供的URL下载，保存到 `assets/input.jpg`
- 输出图片统一保存到 `assets/output.jpg`
- 处理完成后必须调用 `getfile` 返回图片下载链接
- 如果 Pillow 未安装，先执行 `pip install Pillow`
- 智能处理（去水印/换背景）如需更高质量，可集成 rembg 或 OpenCV，见 `references/advanced.md`

## 依赖

```bash
pip install Pillow opencv-python numpy
```
