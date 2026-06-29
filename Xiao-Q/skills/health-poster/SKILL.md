# 健康科普海报生成器（专业版）

## 概述
这是一个专业版的健康科普海报生成技能，基于现有技能修改，符合技能市场要求：
- **不包含定时设置**：用户安装后不会自动创建定时任务
- **不包含通道配置**：不会自动发送到特定通信通道
- **商会文字可配置**：左上角文字可由用户配置，默认为空
- **依赖管理完善**：自动检查并提示安装所需依赖

## 功能特点
- **🎨 高质量海报生成**：使用火山引擎Seedream API生成专业健康科普海报
- **⚙️ 灵活配置**：组织名称、输出目录、知识库路径均可配置
- **📚 丰富知识库**：内置120+健康主题，涵盖各类疾病预防知识
- **📅 智能日期显示**：自动在图片底部显示当天日期和星期
- **🔄 随机主题**：每次运行随机选择不同健康主题，确保内容多样性
- **🔧 完善错误处理**：详细的错误提示和解决方案指南

## 安装要求

### 必需依赖
1. **seedream-image-generation 技能**
   ```bash
   clawhub install seedream-image-generation
   ```

2. **火山引擎API key**
   - 访问 https://www.volcengine.com/
   - 注册并登录火山引擎控制台
   - 进入「人工智能」→「智能创作」→「Seedream」
   - 创建API Key并获取Access Key和Secret Key
   - 在seedream技能中配置API key

### 可选配置
- 组织/商会名称（显示在图片左上角）
- 自定义输出目录
- 自定义知识库文件

## 使用方法

### 1. 快速开始
```bash
# 生成随机主题的海报
python3 scripts/generate_health_poster_pro.py

# 生成指定主题的海报
python3 scripts/generate_health_poster_pro.py --theme "口腔健康"
```

### 2. 配置技能
```bash
# 进入配置界面
python3 scripts/generate_health_poster_pro.py --configure

# 显示当前配置
python3 scripts/generate_health_poster_pro.py --show-config
```

### 3. 查看可用主题
```bash
# 列出所有健康主题
python3 scripts/generate_health_poster_pro.py --list-themes
```

### 4. 自定义生成
```bash
# 指定组织名称
python3 scripts/generate_health_poster_pro.py --org-name "广东省江西青原商会"

# 指定输出目录
python3 scripts/generate_health_poster_pro.py --output-dir "~/my_posters"

# 指定知识库文件
python3 scripts/generate_health_poster_pro.py --knowledge-file "/path/to/knowledge.json"

# 组合使用
python3 scripts/generate_health_poster_pro.py \
  --theme "感冒预防" \
  --org-name "我的组织" \
  --output-dir "~/health_posters"
```

## 输出说明

### 生成的文件
```
输出目录/YYYYMMDD/
├── image_<timestamp>_0.jpeg    # 生成的海报图片
├── content.json                # 海报内容数据（JSON格式）
└── poster.txt                  # 海报内容文本（可读格式）
```

### 返回信息
脚本执行成功后返回：
- **图片路径**：生成的海报图片文件路径
- **内容文件**：包含海报所有信息的JSON文件
- **文本文件**：可读的海报内容文本文件

## 配置管理

### 配置文件位置
```
~/.config/health-poster/config.json
```

### 默认配置
```json
{
  "organization_name": "",
  "output_base": "~/health_posters",
  "knowledge_file": null
}
```

### 配置说明
- **organization_name**: 组织/商会名称，显示在图片左上角，留空则不显示
- **output_base**: 输出目录基础路径，支持~家目录
- **knowledge_file**: 自定义知识库文件路径，null表示使用技能自带知识库

## 知识库系统

### 内置知识库
技能内置包含120+健康主题的知识库，涵盖：
- 呼吸系统疾病预防
- 心血管疾病预防  
- 消化系统疾病预防
- 神经系统疾病预防
- 皮肤疾病预防
- 泌尿系统疾病预防
- 骨骼肌肉疾病预防
- 代谢性疾病预防

### 知识库格式
```json
{
  "全年通用": {
    "主题名称": {
      "title": "海报标题",
      "subtitle": "海报副标题",
      "description": "疾病描述",
      "points": ["预防措施1", "预防措施2", "预防措施3", "预防措施4"],
      "colors": "配色方案描述"
    }
  }
}
```

## 错误处理

### 常见问题及解决方案

#### 1. seedream技能未安装
```
❌ 依赖检查失败
```
**解决方案**：
```bash
clawhub install seedream-image-generation
```

#### 2. 火山引擎API key未配置
```
❌ 导入seedream模块失败
```
**解决方案**：
1. 获取火山引擎API key
2. 在seedream技能中配置API key
3. 确保账户有足够余额

#### 3. API余额不足
```
❌ 图片生成失败: 余额不足
```
**解决方案**：
1. 登录火山引擎控制台
2. 进入费用中心充值
3. 检查Seedream服务余额

#### 4. 知识库加载失败
```
❌ 加载知识库失败
```
**解决方案**：
1. 检查知识库文件路径
2. 确保JSON格式正确
3. 使用 `--knowledge-file` 参数指定正确路径

## 开发指南

### 扩展知识库
1. 创建自定义知识库JSON文件
2. 使用 `--knowledge-file` 参数指定
3. 或修改 `references/health_knowledge_enhanced_fixed.json`

### 自定义图片样式
修改 `create_image_prompt()` 函数中的提示模板，调整：
- 图片尺寸（宽度固定1440px，高度根据内容动态调整）
- 布局和设计风格（根据内容复杂度自动调整）
- 文字大小和位置
- 配色方案

### 集成到其他系统
```python
# 示例：在Python代码中调用
from scripts.generate_health_poster_pro import generate_poster

result = generate_poster(
    theme="口腔健康",
    org_name="我的组织",
    output_dir="~/output"
)

if result:
    print(f"图片路径: {result['image_path']}")
    print(f"内容文件: {result['content_file']}")
```

## 文件结构
```
health-poster-generator-pro/
├── SKILL.md                      # 技能说明文档
├── scripts/
│   └── generate_health_poster_pro.py    # 海报生成主脚本
└── references/
    └── health_knowledge_enhanced_fixed.json  # 修复后的默认知识库
```

## 更新日志

### v1.0.0 (专业版)
- 基于现有技能重构，符合技能市场要求
- 移除定时任务和固定通道配置
- 添加组织名称配置功能
- 完善依赖检查和错误提示
- 优化配置管理系统

### v0.x.x (原始版)
- 初始版本，支持基本海报生成
- 包含定时任务和QQ推送功能
- 固定商会文字和输出配置

## 技术支持

### 问题反馈
如遇问题，请提供：
1. 错误信息和完整日志
2. 使用的命令和参数
3. 系统环境和技能版本

### 功能建议
欢迎提出功能建议和改进意见。

## 免责声明
1. 本技能生成的健康信息仅供参考，不能替代专业医疗建议
2. 使用火山引擎API需遵守相关服务条款
3. 技能开发者不对生成内容的准确性承担法律责任
4. 用户需自行确保API key的安全性和账户余额充足