# img2layered-tiff — 图片转分层 TIFF / PSD

> 将 JPG/PNG 格式图片转换为分层信息的 TIFF / PSD 格式文件

## 概述

本 Skill 将常见的位图格式（JPG、PNG、BMP、WebP）转换为多页分层 TIFF 文件或 **Photoshop PSD 文件**。每个图层在输出文件中独立存储。

**输出格式区别：**

| 格式 | 说明 | Photoshop 中查看方式 |
|------|------|---------------------|
| **TIFF** (默认) | 多页 TIFF，每页一个图层 | 「窗口 > 图层」或「导入 > 视频帧到图层」 |
| **PSD** | Photoshop 原生格式 | **图层面板直接可见每个图层** |

> **推荐：** 如果你需要在 Photoshop 中直接看到分层效果，请使用 `--format psd`。

**典型使用场景：**
- 印刷前分色：RGB → CMYK 四色通道分离
- 印刷质量检测：检查各色版网点分布
- 科学图像分析：分离各通道用于独立分析
- 透明通道提取：导出 Alpha 通道用于合成
- 灰度参考：生成灰度版用于对比
- **图形边缘提取：** 提取图片中轮廓清晰的图形/Logo/线条，用于矢量化参考、印刷版检查、形状分析
- **Photoshop 分层交付：** 输出 PSD 文件，直接在 Photoshop 图层面板中查看各通道

## 分层模式

| 模式 | 说明 | 图层 |
|------|------|------|
| `rgb` | RGB 三通道分离 | Red, Green, Blue (灰度) |
| `rgba` | RGBA 四通道分离 | Red, Green, Blue, Alpha (灰度) |
| `cmyk` | CMYK 四通道分离 | Cyan, Magenta, Yellow, Black (灰度) |
| `alpha` | 彩色 + Alpha 通道 | Composite (彩色), Alpha (灰度) |
| `gray+color` | 灰度 + 彩色原图 | Grayscale (灰度), Color (彩色) |
| `hsl` | HSV 三通道分离 | Hue, Saturation, Lightness (灰度) |
| `lab` | CIE Lab 三通道分离 | L*, a*, b* (灰度) |
| `edge-extract` | 边缘清晰图形提取 | Composite (彩色), Canny-Edge (灰度), Gradient-Mag (灰度), Binary-Edge (灰度) |

### edge-extract 模式详解

该模式使用三种经典边缘检测算法，将图片中的清晰轮廓/图形提取为独立图层：

| 图层 | 算法 | 说明 |
|------|------|------|
| **Composite** | — | 原始彩色图，作为参考 |
| **Canny-Edge** | Canny 边缘检测 | 最精准的边缘线（白色=边缘，黑色=背景），适合提取清晰轮廓 |
| **Gradient-Mag** | Sobel 梯度幅值 | 边缘强度热力图，边缘越亮越强，适合观察渐变过渡区域 |
| **Binary-Edge** | 拉普拉斯 + 二值化 | 对锐利轮廓最敏感的算法，适合提取 Logo、文字等硬边缘图形 |

阈值控制 (`--edge-threshold`, 1-255, 默认 30)：
- **低值 (10-20)**：提取更多细节边缘，适合复杂图形
- **中值 (30-60)**：平衡模式，适合大多数场景
- **高值 (80-150)**：只保留最锐利的轮廓，适合简洁图形/Logo

## 依赖安装

```bash
pip install Pillow numpy tifffile imagecodecs

# PSD 输出需要额外安装 pytoshop
pip install pytoshop

# 可选：安装 scipy 可加速边缘提取的高斯平滑
pip install scipy
```

## 触发词

当用户提到以下需求时，自动触发此 Skill：
- "图片转 TIFF"、"JPG 转 TIFF"、"PNG 转 TIFF"
- "分层 TIFF"、"多页 TIFF"
- "图片转 PSD"、"分层 PSD"、"PSD 图层"
- "通道分离"、"RGB 分离"、"CMYK 分色"
- "Alpha 通道提取"、"透明通道导出"
- "图像分色"、"分色 TIFF"
- "边缘提取"、"图形提取"、"轮廓提取"、"边缘检测"、"edge extract"
- "TIFF 不分层"、"PSD 图层看不到"（问题排查场景）

## 核心脚本

```
scripts/img2layered_tiff.py
```

### 单文件转换

```bash
# 基本用法 - RGB 三通道分离 (TIFF 格式)
python scripts/img2layered_tiff.py photo.jpg --mode rgb

# CMYK 四色分色（印刷用）
python scripts/img2layered_tiff.py photo.jpg --mode cmyk --dpi 300 --compression lzw

# 提取 Alpha 透明通道
python scripts/img2layered_tiff.py logo.png --mode alpha

# 灰度 + 彩色双图层
python scripts/img2layered_tiff.py photo.jpg --mode gray+color

# 指定输出路径
python scripts/img2layered_tiff.py photo.jpg --mode rgb -o output/color_split.tif

# 边缘图形提取（默认阈值 30）
python scripts/img2layered_tiff.py logo.png --mode edge-extract

# 边缘提取 + 高阈值（只保留最锐利的轮廓）
python scripts/img2layered_tiff.py logo.png --mode edge-extract --edge-threshold 80

# 边缘提取 + 低阈值（提取更多细节）
python scripts/img2layered_tiff.py photo.jpg --mode edge-extract --edge-threshold 10

# ★ PSD 格式输出（Photoshop 图层面板直接可见）
python scripts/img2layered_tiff.py photo.jpg --mode rgb --format psd
python scripts/img2layered_tiff.py logo.png --mode rgba --format psd
python scripts/img2layered_tiff.py photo.jpg --mode cmyk --format psd
python scripts/img2layered_tiff.py logo.png --mode edge-extract --format psd
```

### 批量转换

```bash
# 批量处理当前目录所有 JPG
python scripts/img2layered_tiff.py *.jpg --mode rgb

# 批量处理并指定输出目录
python scripts/img2layered_tiff.py *.png --mode cmyk --output-dir ./cmyk_output

# 通配符 + 自定义 DPI
python scripts/img2layered_tiff.py images/*.jpg --mode alpha --dpi 300

# 批量输出 PSD 格式
python scripts/img2layered_tiff.py *.jpg --mode rgb --format psd --output-dir ./psd_output
```

### 压缩选项

| 压缩方式 | 参数 | 特点 |
|---------|------|------|
| 无压缩 | `--compression none` | 文件最大，兼容性最好 |
| LZW | `--compression lzw` (默认) | 无损，压缩比中等，兼容性好 |
| Deflate | `--compression deflate` | 无损，压缩比较高 |
| JPEG | `--compression jpeg` | 有损，文件最小，灰度图层推荐 |

### 列出所有模式

```bash
python scripts/img2layered_tiff.py --list-modes
```

## CLI 参数完整说明

```
positional arguments:
  inputs                  输入图片路径 (支持多文件和通配符 *.jpg/*.png)

optional arguments:
  --mode, -m              分层模式: rgb/rgba/cmyk/alpha/gray+color/hsl/lab/edge-extract (默认: rgb)
  --format, -f            输出格式: tiff/psd (默认: tiff; psd 需要安装 pytoshop)
  --output, -o            输出文件路径 (单文件时有效)
  --output-dir            输出目录 (批量处理时有效)
  --compression, -c       压缩方式: none/lzw/deflate/jpeg (默认: lzw，仅 tiff 格式)
  --dpi                   输出 DPI (默认保留原图 DPI，仅 tiff 格式)
  --edge-threshold        边缘提取阈值 1-255 (默认: 30，仅 edge-extract 模式)
  --list-modes            列出所有分层模式
```

## 在 AI Agent 中的使用指南

当用户请求图片转分层 TIFF 时，Agent 应：

1. **确认输入文件**：获取用户提供的图片文件路径
2. **推荐模式**：根据用户场景推荐合适的分层模式
   - 印刷/分色 → `cmyk`
   - 通道分析 → `rgb` 或 `rgba`
   - 透明度处理 → `alpha`
   - 灰度对比 → `gray+color`
   - **边缘/轮廓提取** → `edge-extract`
3. **执行转换**：调用核心脚本
4. **报告结果**：告知输出路径、文件大小、图层数量

### Python API 调用

```python
import sys
sys.path.insert(0, "path/to/skill/scripts")
from img2layered_tiff import convert_single, convert_batch

# 单文件 TIFF 转换
result = convert_single(
    input_path="photo.jpg",
    mode="cmyk",
    compression="lzw",
    dpi=300,
)
print(f"输出: {result}")

# 单文件 PSD 转换（Photoshop 图层面板可见）
result = convert_single(
    input_path="photo.jpg",
    mode="rgb",
    output_format="psd",
)
print(f"输出: {result}")

# 边缘提取（自定义阈值）
result = convert_single(
    input_path="logo.png",
    mode="edge-extract",
    edge_threshold=50,
)
print(f"输出: {result}")

# 批量转换 PSD
results = convert_batch(
    input_paths=["a.jpg", "b.png"],
    mode="rgb",
    output_dir="./output",
    output_format="psd",
)
```

## 技术细节

- **TIFF 格式**：使用 tifffile 库写入标准多页 TIFF，每页对应一个图层
- **CMYK 转换**：优先使用系统 ICC Profile（USWebCoatedSWOP.icc 等）进行精确色彩转换，回退到 PIL 内置转换
- **DPI 处理**：默认保留原图 EXIF 中的 DPI 信息，可通过 `--dpi` 参数覆盖
- **文件命名**：默认输出为 `{原名}_{模式}.tif`，如 `photo_cmyk.tif`
- **压缩**：默认使用 LZW 无损压缩，兼顾文件大小和兼容性

## 输出文件说明

### TIFF 格式
- 多页结构，每页一个图层
- 第一页包含描述元数据（源文件信息、图层数量、尺寸等）
- 每页包含 DocumentName 标签标注图层名称
- 支持 Photoshop、GIMP、ImageJ、Affinity Photo 等软件打开
- 在 Photoshop 中可通过「窗口 > 图层」查看各页面，或使用「文件 > 导入 > 视频帧到图层」

### PSD 格式
- Photoshop 原生格式，**图层面板直接可见每个图层**
- 支持 RGB/RGBA 灰度和彩色图层
- RGBA 图层包含透明通道（channel -1）
- 在 Photoshop 中打开后即可在图层面板中看到所有通道分离结果
- 注意：PSD 输出使用 Raw 无压缩（文件稍大），因为 pytoshop 的 PackBits Cython 扩展在 Windows 上未编译

## 版本历史

- **v1.3.0** (2026-04-28)
  - 新增 PSD 输出格式（`--format psd`），图层在 Photoshop 图层面板中直接可见
  - 使用 pytoshop 库生成标准 PSD 文件，支持 RGB/RGBA 灰度和彩色图层
  - RGBA 图层自动包含透明通道（channel -1）
  - pytoshop 为可选依赖，未安装时自动回退提示
  - 新增 `--format` / `-f` CLI 参数
  - 修正 hsl 模式图层名 "Value" → "Lightness"（与实际输出一致）
  - 8 种模式 TIFF + PSD 全量回归测试通过

- **v1.2.0** (2026-04-28)
  - 性能大幅优化：所有卷积操作改为 numpy 向量化（`stride_tricks` + `einsum`），edge-extract 模式提速约 10-50 倍
  - 非极大值抑制改为向量化实现（角度量化 + 方向切片）
  - 滞后边缘跟踪改用 PIL MaxFilter 膨胀替代逐像素循环
  - 消除全局变量，`edge_threshold` 改为函数参数传递
  - 清理无用 import 和未使用变量
  - 代码量从 767 行精简到 ~550 行
- **v1.1.0** (2026-04-28)
  - 新增 `edge-extract` 边缘清晰图形提取模式
  - 三种算法：Canny 边缘检测、Sobel 梯度幅值、拉普拉斯二值化
  - 新增 `--edge-threshold` 参数控制边缘灵敏度
  - 纯 numpy 实现，scipy 为可选加速依赖
  - 总计 8 种分层模式
- **v1.0.0** (2026-04-28)
  - 初始版本
  - 支持 7 种分层模式
  - 支持批量转换
  - 支持 LZW/Deflate/JPEG 压缩
  - 支持自定义 DPI
  - CMYK ICC Profile 精确转换
