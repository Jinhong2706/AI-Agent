# 健康科普海报生成器（专业版）

![健康海报示例](https://img.shields.io/badge/类型-图片生成-blue)
![技能版本](https://img.shields.io/badge/版本-1.0.0-green)
![依赖要求](https://img.shields.io/badge/依赖-seedream--image--generation-orange)
![许可证](https://img.shields.io/badge/许可证-MIT-lightgrey)

## 📋 简介

专业版的健康科普海报生成技能，基于现有技能修改，符合技能市场要求：
- **不包含定时设置**：用户安装后不会自动创建定时任务
- **不包含通道配置**：不会自动发送到特定通信通道
- **商会文字可配置**：左上角文字可由用户配置，默认为空
- **依赖管理完善**：自动检查并提示安装所需依赖

## ✨ 功能特性

- **🎨 高质量海报生成**：使用火山引擎Seedream API生成专业健康科普海报
- **⚙️ 灵活配置**：组织名称、输出目录、知识库路径均可配置
- **📚 丰富知识库**：内置120+健康主题，涵盖各类疾病预防知识
- **📅 智能日期显示**：自动在图片底部显示当天日期和星期
- **🔄 随机主题**：每次运行随机选择不同健康主题，确保内容多样性
- **🔧 完善错误处理**：详细的错误提示和解决方案指南

## 🚀 快速开始

### 安装依赖
```bash
# 安装seedream技能（必需）
clawhub install seedream-image-generation
```

### 配置火山引擎API key
1. 访问 [火山引擎控制台](https://www.volcengine.com/)
2. 注册并登录
3. 进入「人工智能」→「智能创作」→「Seedream」
4. 创建API Key并获取Access Key和Secret Key
5. 在seedream技能中配置API key

### 基本使用
```bash
# 生成随机主题的海报
python3 scripts/generate_health_poster_pro.py

# 生成指定主题的海报
python3 scripts/generate_health_poster_pro.py --theme "口腔健康"

# 配置组织名称
python3 scripts/generate_health_poster_pro.py --org-name "广东省江西青原商会"
```

## 📖 详细使用

### 配置技能
```bash
# 进入配置界面
python3 scripts/generate_health_poster_pro.py --configure

# 显示当前配置
python3 scripts/generate_health_poster_pro.py --show-config
```

### 查看可用主题
```bash
# 列出所有健康主题（118个）
python3 scripts/generate_health_poster_pro.py --list-themes
```

### 自定义生成
```bash
# 指定组织名称和输出目录
python3 scripts/generate_health_poster_pro.py \
  --theme "感冒预防" \
  --org-name "广东省江西青原商会" \
  --output-dir "~/health_posters"
```

## 🏗️ 系统架构

### 文件结构
```
health-poster-generator-pro/
├── SKILL.md                      # 技能说明文档
├── manifest.json                 # 技能清单文件
├── README.md                     # 本文件
├── scripts/
│   └── generate_health_poster_pro.py    # 主脚本
└── references/
    └── health_knowledge_enhanced_fixed.json  # 修复后的默认知识库
```

### 配置管理
配置文件位置：`~/.config/health-poster/config.json`

默认配置：
```json
{
  "organization_name": "",
  "output_base": "~/health_posters",
  "knowledge_file": null
}
```

## 🔧 技术细节

### 图片生成规格
- **尺寸**：动态调整（宽度固定1440px，高度根据内容自适应）
- **比例**：9:16手机竖屏（标准）、10:16（中等内容）、11:16（丰富内容）
- **格式**：JPEG/PNG
- **风格**：卡通插画风格，专业但不严肃
- **文字**：清晰可读的中文字体

### 知识库系统
- **主题数量**：118个健康主题
- **分类**：呼吸系统、心血管、消化系统、神经系统等
- **内容**：每个主题包含标题、副标题、描述和4条预防措施
- **格式**：修复后的描述，无"预防"字样问题

### 错误处理
- **依赖检查**：自动检查seedream技能是否安装
- **API验证**：检查火山引擎API key配置和余额
- **知识库验证**：确保知识库文件格式正确
- **路径验证**：检查输出目录权限和空间

## 📊 输出示例

### 生成的文件
```
~/health_posters/20260410/
├── image_1775787610_0.jpeg    # 生成的海报图片
├── content.json                # 海报内容数据（JSON格式）
└── poster.txt                  # 海报内容文本（可读格式）
```

### 海报内容示例
```json
{
  "title": "普通感冒预防指南",
  "subtitle": "保护呼吸道健康",
  "description": "普通感冒是由病毒引起的上呼吸道感染，具有自限性但易传播。",
  "points": ["保持通风", "个人防护", "增强免疫", "及时就医"],
  "theme": "普通感冒预防",
  "date": "2026年04月10日",
  "weekday": "周五",
  "image_path": "/path/to/image.jpeg"
}
```

## 🚨 故障排除

### 常见问题

#### Q1: seedream技能未安装
**错误信息**：`❌ 依赖检查失败`
**解决方案**：
```bash
clawhub install seedream-image-generation
```

#### Q2: 火山引擎API key未配置
**错误信息**：`❌ 导入seedream模块失败`
**解决方案**：
1. 获取火山引擎API key
2. 在seedream技能中配置API key
3. 确保账户有足够余额

#### Q3: API余额不足
**错误信息**：`❌ 图片生成失败: 余额不足`
**解决方案**：
1. 登录火山引擎控制台
2. 进入费用中心充值
3. 检查Seedream服务余额

#### Q4: 主题不存在
**错误信息**：`❌ 主题 'XXX' 不存在`
**解决方案**：
```bash
python3 scripts/generate_health_poster_pro.py --list-themes
```

## 📝 更新日志

### v1.0.0 (2026-04-10)
- **基于现有技能重构**，符合技能市场要求
- **移除定时任务**和固定通道配置
- **添加组织名称配置**功能
- **完善依赖检查**和错误提示
- **优化配置管理**系统
- **使用修复后的知识库**（无"预防"字样问题）

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出功能建议！

### 报告问题
请在GitHub Issues中提供：
1. 错误信息和完整日志
2. 使用的命令和参数
3. 系统环境和技能版本

### 功能建议
欢迎提出新功能建议和改进意见。

## 📄 许可证

本项目基于 MIT 许可证开源。

## 🙏 致谢

- 感谢火山引擎提供Seedream API
- 感谢OpenClaw社区的支持
- 感谢所有贡献者和用户

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- OpenClaw社区论坛
- 技能市场反馈

---

**健康科普海报生成器（专业版）** - 让健康知识传播更简单、更专业！