---
name: dxf-engineering
description: "图片转DXF工程图生成器。用户发来工程图片，自动提取参数，生成带尺寸标注的预览供确认，确认后生成1:1 DXF文件，再去除标注生成纯净版。触发词：DXF、工程图、dxf、转DXF、生成工程图、图片转DXF、CAD文件。"
description_zh: "图片转DXF工程图生成器"
description_en: "Image to DXF Engineering Drawing Generator"
version: 1.0.0
---

# DXF Engineering Drawing Generator (图片转DXF工程图)

## Overview

从工程图片自动生成 DXF 文件。支持矩形、圆形、多边形、槽孔、圆弧等常见机械零件图形。

## Workflow

完整流程分为 5 个阶段：

### Phase 1: 图片分析 & 参数提取

1. 读取用户发送的工程图片
2. 识别图形类型（矩形板、带孔零件、法兰、异形件等）
3. 提取关键参数：尺寸、位置、孔径、角度等
4. 生成结构化 JSON 参数

### Phase 2: 预览确认（带尺寸标注）

1. 用提取的参数生成带标注的 DXF
2. 生成 PNG 预览图（`--preview`）
3. **必须展示预览给用户确认**
4. 列出所有识别到的参数供用户核对

### Phase 3: 参数修正

根据用户反馈修正参数：
- 调整尺寸数值
- 增减孔/槽等特征
- 修改位置/角度
- 修正单位（mm/inch）

### Phase 4: 生成正式 DXF（带标注）

1. 参数确认后，执行 `scripts/generate_dxf.py` 生成完整 DXF
2. 使用 `--preview` 生成最终预览

### Phase 5: 生成纯净版 DXF

1. 执行 `scripts/clean_dxf.py` 去除所有标注、中心线、文字
2. 只保留轮廓几何体（OUTLINE、INNER、HOLE 图层）
3. 生成纯净版预览
4. **必须展示纯净版给用户最终确认**

## Scripts

### generate_dxf.py - DXF 生成主脚本

```bash
# 从参数 JSON 生成 DXF
python scripts/generate_dxf.py --params params.json --output output.dxf

# 同时生成预览图
python scripts/generate_dxf.py --params params.json --output output.dxf --preview

# 直接生成纯净版（无标注）
python scripts/generate_dxf.py --params params.json --output output.dxf --clean
```

**参数 JSON 格式：**
```json
{
  "title": "零件名称",
  "drawing_number": "DWG-001",
  "material": "Steel 304",
  "scale": "1:1",
  "shapes": [
    {"type": "rectangle", "x": 0, "y": 0, "width": 100, "height": 50, "layer": "OUTLINE"},
    {"type": "circle", "cx": 25, "cy": 25, "radius": 5, "layer": "HOLE"},
    {"type": "slot", "cx": 75, "cy": 25, "length": 20, "width": 8, "angle": 0, "layer": "HOLE"},
    {"type": "arc", "cx": 50, "cy": 0, "radius": 50, "start_angle": 0, "end_angle": 180, "layer": "OUTLINE"}
  ],
  "dimensions": [
    {"type": "linear", "p1": [0, 0], "p2": [100, 0], "offset": 10, "text": "100"},
    {"type": "diameter", "center": [25, 25], "radius": 5, "text": "10"}
  ],
  "settings": {
    "unit": "mm",
    "line_width": 1.0
  }
}
```

**支持的图形类型：**

| 类型 | 必填参数 | 可选参数 |
|------|---------|---------|
| `rectangle` | x, y, width, height | angle, layer |
| `circle` | cx, cy, radius | layer |
| `polygon` | points (数组 [[x,y],...]) | layer, closed |
| `slot` | cx, cy, length, width | angle, layer |
| `arc` | cx, cy, radius, start_angle, end_angle | layer |
| `line` | x1, y1, x2, y2 | layer |

**支持的标注类型：**

| 类型 | 必填参数 | 说明 |
|------|---------|------|
| `linear` | p1, p2 | 线性尺寸 |
| `diameter` | center, radius | 直径标注（自动加%%C前缀） |
| `radius` | center, radius | 半径标注（自动加R前缀） |

### clean_dxf.py - 纯净版生成

```bash
# 去除标注，只保留轮廓
python scripts/clean_dxf.py input.dxf output_clean.dxf
```

**保留的图层：** 0, OUTLINE, INNER, HOLE
**删除的图层：** DIMENSION, CENTER, TEXT, HIDDEN

### extract_params.py - 参数辅助工具

```bash
# 查看可用模板
python scripts/extract_params.py --list-templates

# 从模板生成参数文件
python scripts/extract_params.py --template plate_with_holes --output params.json

# 验证已有参数文件
python scripts/extract_params.py --validate params.json
```

**可用模板：**
- `rectangular_plate` - 矩形板
- `plate_with_holes` - 带孔板
- `flanged_part` - 法兰件

## DXF Layer 规范

| 图层 | 颜色 | 线型 | 线宽 | 用途 |
|------|------|------|------|------|
| 0 | 白(7) | 实线 | 1.0 | 默认轮廓 |
| OUTLINE | 白(7) | 实线 | 1.0 | 外轮廓 |
| INNER | 白(7) | 实线 | 0.5 | 内轮廓 |
| HOLE | 白(7) | 实线 | 0.5 | 孔 |
| CENTER | 红(1) | 中心线 | 0.18 | 中心线（纯净版删除） |
| DIMENSION | 绿(3) | 实线 | 0.18 | 标注（纯净版删除） |
| TEXT | 白(7) | 实线 | 0.25 | 文字（纯净版删除） |

## Dependencies

运行脚本前需确保安装以下 Python 依赖：

```bash
pip install ezdxf matplotlib
```

- **ezdxf** - DXF 文件读写（必需）
- **matplotlib** - 预览图生成（可选，仅 --preview 时需要）

## Notes

- 输出 DXF 格式为 AutoCAD R2010 兼容
- 所有尺寸默认单位为 mm
- 纯净版只保留黑色实线轮廓，无多余图层
- 生成预览时使用 PNG 格式，150 DPI
