# 微信公众号AI内容创作与发布 Skill v3.0

从新闻素材中挖掘选题，生成原创观点文章，自动排版发布到微信公众号草稿箱。

## 功能特点

- **智能选题**：四维打分评估（热度/实战价值/差异化/人设契合），宁缺毋滥
- **原创撰写**：4套写作模板（资讯速递/深度解读/工具实测/观点专栏）
- **去AI味润色**：8条AI痕迹识别清单，零改字原则
- **智能标题**：6种标题模式，含完整禁用词过滤
- **AI配图**：即梦CLI一键生成封面图
- **自包含发布**：内置发布脚本，一行命令完成全部操作
- **质量保障**：发布前12项检查清单

## 适用人群

- AI领域自媒体创作者
- 技术博主 / 独立开发者
- AI创业者 / 产品经理
- 企业AI培训讲师
- 任何想持续输出AI原创内容的人

## 快速开始

### 1. 安装依赖

```bash
pip install requests

# 可选：AI配图
pip install dreamina-cli
dreamina login
```

### 2. 运行配置向导

```bash
python3 scripts/setup.py
```

### 3. 添加IP白名单

公众号后台 → 设置与开发 → 基本配置 → IP白名单

### 4. 验证配置

```bash
python3 scripts/test_publish.py
```

## 使用方法

### 自动选题创作

```
帮我看看今天有什么值得写的选题
```

### 指定类型创作

```
帮我写一篇深度分析 / 工具实测 / 观点专栏
```

### 基于热点创作

```
针对【某个热点】，帮我写一篇深度解读
```

### 直接发布已有文章

```bash
python3 scripts/publish.py \
  --app_id "你的AppID" \
  --app_secret "你的AppSecret" \
  --title "文章标题" \
  --article "drafts/article.md" \
  --cover "images/cover.jpg"
```

## 工作流程

```
Step 1: 收集素材（6个维度多源搜索）
Step 2: 选题决策（四维打分 → 类型路由）
Step 3: 原创撰写（4套模板）
Step 3.5: 去AI味润色（8条识别清单）
Step 4: 标题生成（6种模式 + 禁用词）
Step 5: AI配图（即梦CLI封面 + 正文配图）
Step 6: 排版发布（MD转HTML + 上传封面 + 创建草稿）
Step 7: 质量检查（12项检查清单）
```

## 目录结构

```
wechat-ai-publisher/
├── SKILL.md               # Skill 主文件（完整流程说明）
├── README.md              # 本文件
├── config.template.toml   # 配置模板
├── config.toml            # 你的配置（自动生成）
├── _skillhub_meta.json    # SkillHub 元数据
├── scripts/
│   ├── publish.py         # 自包含发布脚本（核心）
│   ├── setup.py           # 配置向导
│   └── test_publish.py    # 测试脚本
├── images/                # 图片目录
└── drafts/                # 草稿目录
```

## 踩坑经验

1. **IP白名单**：出口IP变动时需更新
2. **图片压缩**：建议压缩到600KB以内
3. **敏感词**：避免极端化表述
4. **本地图片**：HTML中不能有本地路径，必须替换为微信素材URL
5. **API权限**：普通权限只能创建草稿，不能直接群发

## 更新日志

### v3.0.0
- 新增自包含发布脚本 publish.py（一键发布，无需外部依赖）
- 发布脚本支持 --app_id --app_secret 参数和环境变量
- 发布脚本内置 Markdown → 公众号HTML转换器
- 新增观点专栏模板（4种模板完整覆盖）
- 优化标题生成流程（6种模式 + 禁用词）
- 优化质量检查清单（12项）
- 发布脚本支持传入HTML文件（跳过MD转HTML）

### v2.0.0
- 重构为通用版，适配所有公众号作者
- 内置选题打分体系
- 内置写作模板和去AI味润色指南

### v1.0.0
- 初始版本

## 许可证

MIT License
