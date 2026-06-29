# 🔄 文件格式转换器 (File Converter)

专业的文件格式转换工具，支持图片格式转换、压缩、视频转GIF、PDF处理等功能。

## ✨ 功能特点

- 🖼️ **图片转换**: PNG ↔ JPG ↔ WebP ↔ GIF，支持批量处理
- 📉 **智能压缩**: 自动优化图片大小，节省80%+存储空间
- 🎬 **视频转GIF**: MP4/AVI/MOV一键转GIF，支持截取片段
- 📄 **PDF处理**: 合并、拆分、转图片
- 📊 **信息查看**: 快速查看文件详细属性

## 🚀 使用方法

### 命令行
```bash
# 图片格式转换
node converter.js convert input.png output.jpg -q 85

# 图片压缩
node converter.js compress image.png -q 60

# 批量转换目录
node converter.js batch ./images -f webp

# 视频转GIF（从第5秒开始，持续10秒）
node converter.js video2gif input.mp4 output.gif -s 5 -t 10 -w 480

# PDF合并
node converter.js merge file1.pdf file2.pdf output.pdf

# 查看文件信息
node converter.js info image.png
```

### 编程调用
```javascript
const converter = require('./converter.js');

// 图片转换
await converter.convertImage('input.png', 'output.jpg', { quality: 85 });

// 图片压缩（节省80%+）
await converter.compressImage('input.png', 'output.jpg', { quality: 60 });

// 视频转GIF
await converter.videoToGif('video.mp4', 'output.gif', {
  start: 5, duration: 10, width: 480, fps: 10
});

// PDF合并
await converter.mergePdfs(['file1.pdf', 'file2.pdf'], 'merged.pdf');
```

## 📋 支持格式

| 类型 | 格式 |
|------|------|
| 图片 | JPG, PNG, WebP, GIF, BMP, TIFF, AVIF |
| 视频 | MP4, AVI, MOV, MKV, WebM, FLV |
| PDF | 合并、拆分、转图片 |

## 🔧 技术栈

- **sharp** - 高性能图片处理 (基于libvips)
- **fluent-ffmpeg** - 视频处理
- **pdf-lib** - PDF操作

## 💡 示例

```bash
# 将PNG批量转为WebP，节省空间
node converter.js batch ./photos -f webp -q 85

# 压缩图片用于网页展示
node converter.js compress photo.jpg -q 70

# 从视频截取精彩瞬间做GIF
node converter.js video2gif demo.mp4 highlight.gif -s 30 -t 5 -w 320
```

## 📦 安装依赖

```bash
cd file-converter-skill
npm install
```

## ⚠️ 注意

- 视频转GIF需要系统安装 ffmpeg
- PDF转图片需要系统安装 poppler-utils (pdftoppm)

---
Made with ❤️ for OpenClaw
