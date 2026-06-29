---
name: skillhub-skill
description: Project-level portable wrapper for Skillhub CLI (https://skillhub.cn). Search, install, list, and upgrade skills from the Skillhub marketplace. Use when the user asks about finding skills, installing skills from Skillhub, or mentions "skillhub", "技能商店". Provides project isolation and portability compared to global installation.
---

# Skillhub 技能商店

Skillhub (https://skillhub.cn) 是一个中文技能市场，提供各类 Claude 技能。本 skill 将官方 CLI 工具封装为项目级可移植版本。

## 何时使用此技能

当用户：
- 想要搜索或安装 Skillhub 市场中的技能
- 询问"Skillhub 上有什么技能"、"如何安装技能"
- 需要查看已安装的技能列表
- 想要升级已安装的技能
- 提到"技能商店"、"skillhub"等关键词

## 核心功能

### 1. 搜索技能

使用内置脚本搜索 Skillhub 商店中的技能：

```bash
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py search <关键词>
```

**示例：**
```bash
# 搜索技能
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py search <关键词>

# 搜索中文关键词
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py search 数据分析

# 搜索英文关键词
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py search data
```

**输出格式：**
搜索结果会显示：
- 技能名称（英文标识符）
- 技能标题（中英文）
- 功能描述
- 版本号

### 2. 安装技能

将技能安装到当前工作区：

```bash
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py install <技能名称>
```

**示例：**
```bash
# 安装技能
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py install <技能名称>

# 示例
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py install data-analyzer
```

安装后的技能会出现在 `skills/` 目录下。

### 3. 查看已安装技能

```bash
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py list
```

### 4. 升级技能

检查并升级已安装的技能到最新版本：

```bash
# 检查所有技能的更新
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py upgrade --check-only

# 升级所有技能
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py upgrade

# 升级特定技能
python .claude/skills/skillhub-skill/scripts/skills_store_cli.py upgrade <技能名称>
```

## 工作流程

当用户请求搜索或安装技能时，按以下步骤操作：

### 搜索流程

1. **理解需求**：确定用户想要什么类型的技能
2. **执行搜索**：运行搜索命令
3. **解析结果**：提取技能名称、描述、版本
4. **展示推荐**：根据用户需求推荐最相关的 2-3 个技能
5. **询问意向**：问用户是否要安装某个技能

### 安装流程

1. **确认技能名**：确保使用正确的技能标识符（英文名称）
2. **执行安装**：运行安装命令
3. **验证结果**：检查安装是否成功
4. **使用指导**：告诉用户如何使用新安装的技能

## 输出格式建议

当展示搜索结果时，使用以下格式：

```
找到 X 个相关技能：

1. **技能名称** - 技能标题
   - 功能描述
   - 安装命令：`python .claude/skills/skillhub-skill/scripts/skills_store_cli.py install 技能名称`

2. **技能名称** - 技能标题
   ...
```

## 注意事项

1. **中文显示问题**：搜索结果中的中文可能显示为乱码，但技能名称（英文标识符）是准确的
2. **安装位置**：技能默认安装到 `skills/` 目录
3. **重启要求**：安装新技能后，某些 Agent 可能需要重启才能识别
4. **网络要求**：需要访问 skillhub.cn，确保网络连接正常

## 技能目录结构

```
.claude/skills/skillhub-skill/
├── SKILL.md                      # 本文档
└── scripts/
    ├── skills_store_cli.py       # Skillhub CLI 主程序
    ├── skills_upgrade.py         # 技能升级模块
    ├── config.json               # 配置文件
    ├── metadata.json             # 元数据
    └── version.json              # 版本信息
```

## 示例对话

**用户**：帮我搜索数据分析相关的技能

**助手**：让我搜索一下 Skillhub 上的数据分析技能...

[执行搜索]

找到以下技能：

1. **data-analyzer** - 数据分析器
   - 数据清洗、分析和可视化
   
2. **data-processor** - 数据处理器
   - 批量数据处理和转换

你想安装哪个？

---

**用户**：安装 data-analyzer

**助手**：好的，正在安装 data-analyzer...

[执行安装命令]

✓ 安装完成！data-analyzer 已安装到 skills/ 目录。

重启后即可使用。
