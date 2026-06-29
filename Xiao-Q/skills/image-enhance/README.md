# 图片一键增强 (Image Enhance)

一个完整的 OpenClow 图片增强 Skill，提供超分辨率、去噪、模糊图修复功能。

## 功能特性

- 超分辨率放大（支持 1.5x、2x、3x）
- 智能降噪
- 模糊图片修复
- 对比度和清晰度增强
- 支持 URL、base64、本地文件输入

## 价格策略

- 单次调用：0.5 元（CNY）
- 支付方式：ClawTip 微支付
- 支付地址：6fb189ee1c9bfc8923d3827542b470fe2026033115341800100064388llvPmVmVKbo0HcGsd68TEfRVwV5ICFkDmUeEB827p2hkqnlpJGM2NwsCYjaAM4QETH1VhKA

## 系统要求

- Windows 10/11
- Node.js 16.0 或更高版本
- Python 3.8 或更高版本
- 4GB+ RAM（推荐 8GB）

## 安装步骤

### 1. 安装 Node.js 依赖

```bash
cd C:\Users\Admin\.openclaw\workspace\skills\image-enhance
npm init -y
npm install --save requests opencv-python pillow
```

### 2. 安装 Python 依赖

```bash
cd C:\Users\Admin\.openclaw\workspace\skills\image-enhance\scripts
pip install opencv-python pillow numpy requests
```

### 3. 配置文件

编辑 `configs/config.json`：

```json
{
  "api": {
    "type": "local"
  }
}
```

如需使用腾讯云 API：

```json
{
  "api": {
    "type": "tencent",
    "tencent": {
      "secretId": "你的腾讯云 SecretId",
      "secretKey": "你的腾讯云 SecretKey",
      "region": "ap-beijing"
    }
  }
}
```

## 使用方法

### 方式一：通过 OpenClaw 触发

发送消息：
- "增强图片 [图片 URL]"
- "图片增强 [图片 base64]"
- "修复模糊 [图片文件路径]"

### 方式二：直接调用 Node.js

```bash
node C:\Users\Admin\.openclaw\workspace\skills\image-enhance\scripts\enhance.js <image_input> [quality] [output_format]
```

参数说明：
- `image_input`: 图片 URL、base64 或本地文件路径
- `quality`: 增强质量等级（low/medium/high，默认 medium）
- `output_format`: 输出格式（png/jpeg，默认 png）

示例：

```bash
# 从 URL 增强图片
node scripts\enhance.js https://example.com/image.jpg medium png

# 从本地文件增强
node scripts\enhance.js C:\path\to\image.png high jpeg

# 使用 base64
node scripts\enhance.js data:image/png;base64,iVBORw0KGgo... medium png
```

### 方式三：直接调用 Python

```bash
python C:\Users\Admin\.openclaw\workspace\skills\image-enhance\scripts\enhance.py <image_input> [quality] [output_format]
```

## 输出格式

成功的响应：

```json
{
  "success": true,
  "data": {
    "enhancedImage": "data:image/png;base64,iVBORw0KGgoAAAA..."
  },
  "metadata": {
    "originalSize": {
      "width": 800,
      "height": 600
    },
    "enhancedSize": {
      "width": 1600,
      "height": 1200
    },
    "processingTime": 2.35,
    "inputType": "url",
    "quality": "medium",
    "outputFormat": "png",
    "apiType": "local"
  }
}
```

失败的响应：

```json
{
  "success": false,
  "error": "Failed to load image: Invalid URL",
  "metadata": {
    "processingTime": 0.12
  }
}
```

## 质量等级说明

- **Low**（低）: 1.5x 放大，轻度降噪，快速处理
- **Medium**（中）: 2x 放大，中度降噪，平衡效果（推荐）
- **High**（高）: 3x 放大，重度降噪，最佳效果

## 注意事项

1. 图片大小限制：最大 10MB
2. 支持的输入格式：PNG、JPG、JPEG、BMP、WebP
3. 支持的输出格式：PNG、JPEG
4. 处理时间取决于图片大小和质量等级
5. 使用腾讯云 API 需要相应的腾讯云账户和配额

## 故障排查

### Python 脚本无法运行

确保已安装所有 Python 依赖：

```bash
pip install opencv-python pillow numpy requests
```

### OpenCV 安装失败

对于 Windows，可以使用预编译版本：

```bash
pip install opencv-python-headless
```

### 模块找不到错误

确保 Python 路径已添加到系统环境变量。

## 技术细节

### 本地增强（默认）
- 使用 OpenCV 进行图像处理
- 双三次插值放大
- fastNlMeansDenoising 降噪
- CLAHE 对比度增强
- 锐化滤波器

### 腾讯云 API
- 腾讯云图像增强 API
- 需要有效的腾讯云凭证
- 支持更高级的 AI 增强算法

## 开发与环境

- 开发环境：Windows 10/11
- Node.js 版本：16.0+
- Python 版本：3.8+
- OpenCV 版本：4.5+
- Pillow 版本：8.0+

## 许可证

本 Skill 由 OpenClow 提供，遵循 ClawTip 支付协议。

## 联系支持

如遇问题，请联系 OpenClow 支持团队。

## 更新日志

### v1.0.0 (2026-04-02)
- 初始版本发布
- 支持本地和腾讯云 API
- 提供 3 种质量等级
- 完整的错误处理和日志
