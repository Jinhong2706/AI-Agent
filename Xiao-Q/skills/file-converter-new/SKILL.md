# file-converter-skill

文件格式转换技能 - 支持图片格式转换、视频转GIF、PDF处理等。

## 功能

### 1. 图片格式转换
- PNG ↔ JPG ↔ WebP ↔ GIF
- 支持批量转换
- 支持质量/尺寸调整

### 2. 视频转GIF
- MP4/AVI/MOV → GIF
- 支持截取片段
- 支持调整帧率

### 3. PDF处理
- PDF合并
- PDF拆分
- PDF转图片

## 安装

```bash
cd ~/file-converter-skill
npm install sharp fluent-ffmpeg pdf-lib
```

## 使用

### 图片转换
```bash
# 转换单个图片
node converter.js convert input.png output.jpg

# 批量转换
node converter.js batch ./images -f jpg

# 压缩图片
node converter.js compress input.png -q 80
```

### 视频转GIF
```bash
# 视频转GIF
node converter.js video2gif input.mp4 output.gif -t 10

# 截取片段转GIF
node converter.js video2gif input.mp4 output.gif -s 5 -t 10 -w 480
```

### PDF操作
```bash
# 合并PDF
node converter.js merge file1.pdf file2.pdf output.pdf

# PDF转图片
node converter.js pdf2img document.pdf ./output/
```

## API

技能暴露以下函数：
- `convertImage(input, output, options)` - 图片转换
- `compressImage(input, output, quality)` - 图片压缩
- `videoToGif(input, output, options)` - 视频转GIF
- `mergePdf(files, output)` - PDF合并
- `pdfToImages(input, outputDir)` - PDF转图片