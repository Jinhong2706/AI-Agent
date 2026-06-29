---
name: "pdf-piano-sheet-color-remover"
description: "PDF钢琴简谱颜色去除工具：拆分PDF -> 转换为图片 -> 去除红蓝色简谱 -> 转回PDF -> 合并。当用户需要处理钢琴谱PDF，删除红色（右手）和蓝色（左手）简谱数字，同时保留黑色指法标注时调用。"
---

# PDF钢琴简谱颜色去除

一个完整的钢琴谱PDF处理流程，用于删除红色（右手）和蓝色（左手）数字简谱，同时保留黑色的指法标注。

## 概述

本技能提供完整的钢琴谱PDF处理工作流：
1. **拆分PDF** - 将多页PDF拆分为单页
2. **转换为图片** - 将PDF页面转换为PNG图片
3. **去除彩色简谱** - 使用图像处理去除红色和蓝色数字简谱
4. **转回PDF** - 将处理后的图片转换回PDF格式
5. **合并PDF** - 将所有处理后的页面合并为最终的PDF

## 目录结构

```
skill/
├── SKILL.md                    # 本文档
└── scripts/                    # 脚本目录
    ├── 1_split_pdf.py          # 步骤1: 拆分PDF
    ├── 2_pdf_to_images.py      # 步骤2: PDF转图片
    ├── 3_remove_color_notes.py # 步骤3: 去除红蓝简谱
    ├── 4_images_to_pdf.py      # 步骤4: 图片转PDF
    ├── 5_merge_pdfs.py         # 步骤5: 合并PDF
    └── process_sheet_music.py  # 主脚本: 运行完整流程
```

## 前置要求

安装所需的Python包：
```bash
pip install pypdf pdf2image pillow scipy numpy
```

同时安装poppler（pdf2image需要）：
```bash
# macOS
brew install poppler

# Ubuntu/Debian
apt-get install poppler-utils
```

## 使用方法

### 快速开始 - 运行完整流程

```bash
python3 skill/scripts/process_sheet_music.py 输入.pdf 输出.pdf
```

### 分步骤使用

#### 步骤1: 拆分PDF
```bash
python3 skill/scripts/1_split_pdf.py 输入.pdf ./pdf-pages/
```

#### 步骤2: PDF转图片
```bash
python3 skill/scripts/2_pdf_to_images.py ./pdf-pages/ ./pdf-images/
```

#### 步骤3: 去除红蓝简谱
```bash
python3 skill/scripts/3_remove_color_notes.py ./pdf-images/ ./pdf-processed-images/
```

#### 步骤4: 图片转PDF
```bash
python3 skill/scripts/4_images_to_pdf.py ./pdf-processed-images/ ./pdf-processed-pdfs/
```

#### 步骤5: 合并PDF
```bash
python3 skill/scripts/5_merge_pdfs.py ./pdf-processed-pdfs/ 最终输出.pdf
```

## 工作原理

### 颜色检测算法

去除过程使用两阶段方法：

1. **激进删除阶段**：使用宽松的颜色阈值捕获所有红/蓝色像素
   - 红色检测：R > 130, G < 150, B < 150，且R明显高于G和B
   - 蓝色检测：B > 100, R < 140, G < 160，且B明显高于R和G

2. **恢复阶段**：恢复被误删的黑色指法数字
   - 检测原图中的深色像素（RGB < 120）
   - 如果处理后的图像该区域为白色，则恢复原像素

### 处理流程

```
输入PDF
    ↓
[拆分] → 单页PDF
    ↓
[转换] → PNG图片
    ↓
[去除颜色] → 处理后的图片（无红蓝简谱）
    ↓
[转换] → 单页PDF
    ↓
[合并] → 最终PDF
```

## 输出文件

处理过程中会创建以下目录：
- `pdf-pages/` - 拆分后的PDF页面
- `pdf-images/` - 转换后的PNG图片
- `pdf-processed-images/` - 去除红蓝简谱后的图片
- `pdf-processed-pdfs/` - 单页处理后的PDF
- `{原文件名}_黑白版本.pdf` 或指定名称 - 最终合并的PDF

## 注意事项

- 本算法针对带有红色（右手）和蓝色（左手）数字简谱的钢琴谱进行了优化
- 黑色的指法标注会被保留
- 处理大型PDF可能需要几分钟时间
- 中间文件会被保留以便检查
