---
name: "image-enhance"
description: >-
  图片一键增强 Skill - 提供超分辨率、去噪、模糊图修复功能。
  收费：0.5 元/次，通过 ClawTip 结算。
  触发词：增强图片、图片增强、修复模糊
version: "1.0.0"
price: 0.5
currency: "CNY"

categories:
  - image
  - enhancement
  - ai

triggers:
  - 增强图片
  - 图片增强
  - 修复模糊
  - 提高图片质量
  - 清晰图片

metadata:
  payTo: "6fb189ee1c9bfc8923d3827542b470fe2026033115341800100064388llvPmVmVKbo0HcGsd68TEfRVwV5ICFkDmUeEB827p2hkqnlpJGM2NwsCYjaAM4QETH1VhKA"
  sm4Key: "pqa2+964kqiBYxayAj1FYQ=="

## 使用流程
1. 用户发送图片URL或base64编码
2. Skill 调用图像增强服务
3. 返回增强后的图片

## 技术实现
- 主程序：scripts/enhance.js (Node.js)
- Python 辅助：scripts/enhance.py (调用 Real-ESRGAN 或腾讯云 API)
- 配置文件：configs/config.json

## 输入参数
- image: 图片 URL 或 base64 编码（必需）
- options: 可选参数
  - quality: 增强质量等级 (low/medium/high) - 默认 medium
  - outputFormat: 输出格式 (png/jpeg) - 默认 png

## 输出结果
- enhancedImage: 增强后的图片（base64 或 URL）
- metadata: 处理元数据
  - originalSize: 原始尺寸
  - enhancedSize: 增强后尺寸
  - processingTime: 处理时间（秒）
