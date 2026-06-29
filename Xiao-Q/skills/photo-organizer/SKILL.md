---
name: photo-organizer
description: 智能照片整理助手。支持按时间（年/月/日）、按内容类型（风景/人像/截图等）、按序号批量重命名三种方式整理照片。适用场景：(1) 用户要求整理照片文件夹，(2) 需要按拍摄日期分组照片，(3) 想按照片内容自动分类，(4) 需要批量重命名照片文件，(5) 任何涉及照片整理、分类、排序的需求。触发关键词：整理照片、照片分类、按时间分组、按日期排序、重命名照片、照片管理。
---

# Photo Organizer - 照片整理助手

智能整理照片工具，支持三种整理模式。

## 快速开始

### 1. 按时间整理

将照片按拍摄日期分组（自动读取EXIF信息）：

```bash
python3 scripts/organize_by_time.py <照片目录> -o <输出目录> -g <分组方式>
```

参数：
- `-g, --group-by`: `year`(按年) / `month`(按月,默认) / `day`(按日)
- `-o, --output`: 输出目录（默认 `./organized_by_time`）

示例：
```bash
# 按月整理
python3 scripts/organize_by_time.py ~/Photos -o ./sorted_by_month -g month

# 按年整理
python3 scripts/organize_by_time.py ~/Photos -g year
```

输出结构：
```
organized_by_time/
├── 2024-01/
├── 2024-02/
└── 2023-12/
```

### 2. 按内容分类

使用图像特征识别自动分类（风景/人像/截图等）：

```bash
python3 scripts/organize_by_content.py <照片目录> -o <输出目录>
```

示例：
```bash
python3 scripts/organize_by_content.py ~/Photos -o ./sorted_by_content
```

输出结构：
```
organized_by_content/
├── 风景/日常/
├── 人像/竖拍/
├── 全景/风景/
└── 截图/
```

### 3. 按序号重命名

批量重命名照片，支持自定义前缀和编号规则：

```bash
python3 scripts/rename_photos.py <照片目录> -o <输出目录> -p <前缀> -s <起始编号> -d <位数>
```

参数：
- `-p, --prefix`: 文件名前缀（默认 `photo`）
- `-s, --start`: 起始编号（默认 `1`）
- `-d, --digits`: 编号位数，自动补零（默认 `3`）
- `--sort-by`: 排序方式 `name`(文件名,默认) / `date`(日期) / `size`(大小)

示例：
```bash
# 基础用法
python3 scripts/rename_photos.py ~/Photos -o ./renamed

# 自定义前缀和编号
python3 scripts/rename_photos.py ~/Photos -p "vacation" -s 100 -d 4

# 按拍摄日期排序后重命名
python3 scripts/rename_photos.py ~/Photos --sort-by date
```

输出：
```
renamed_photos/
├── photo_001.jpg
├── photo_002.jpg
└── photo_003.jpg
```

## 组合使用

可以组合多种整理方式：

```bash
# 先按时间分组，再在每个组内按内容分类
python3 scripts/organize_by_time.py ~/Photos -o ./temp -g month
python3 scripts/organize_by_content.py ./temp -o ./final_sorted
```

## 依赖安装

脚本需要以下Python包：

```bash
pip install Pillow exifread imagehash
```

## 注意事项

- 脚本不会删除原始照片，只会复制到输出目录
- 如果输出目录已存在同名文件，会自动跳过
- EXIF读取失败时会使用文件修改时间作为备选
- 支持的格式：jpg, jpeg, png, tiff, bmp, heic, cr2, nef

## 常见问题

**Q: 照片日期读取不准确？**
A: 检查照片是否包含EXIF信息。如果没有，会使用文件修改时间。

**Q: 分类结果不理想？**
A: 当前使用启发式规则，对于特殊需求可以手动调整分类逻辑。

**Q: 如何只整理某个文件夹下的照片？**
A: 直接指定路径即可，脚本会递归处理子目录。
