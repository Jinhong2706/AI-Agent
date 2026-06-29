# WeChat Sticker Generator

一键生成符合微信规范的动态(GIF)及静态(PNG)系列表情包套件。

## 功能特点

- 🎨 **12种预设画风** — 从二次元到3D黏土，像素风到水墨国风
- 🎭 **10大场景主题** — 综合、节日、恋爱、问候、职场、学习、游戏、萌宠、美食、运动
- 👤 **灵活角色系统** — 支持原创角色、知名IP、真人Q版化
- 📸 **真人照片转Q版** — 上传照片→自动转换→生成表情包
- 🔒 **角色一致性锁定** — 通过参考图保证多套件角色长相统一
- ⚡ **全自动流水线** — 一键生成宫格图→切片→GIF合成

## 安装依赖

```bash
pip install rembg onnxruntime pillow requests google-genai dashscope
```

## 配置

### 环境变量

```bash
# Gemini（推荐）
export GEMINI_API_KEY="你的API_Key"

# 或 千问
export DASHSCOPE_API_KEY="你的API_Key"
```

## 使用方式

本 Skill 为 AI Agent 设计，详见 [SKILL.md](./SKILL.md)。

## License

MIT License - See [LICENSE](./LICENSE)