# PARA Diary Share Obsidian Workflow

这是一个通用 Obsidian 工作流 skill，用来帮助 AI AGENT （Claude， codex等） 初始化和管理采用 `PARA + Diary + Share` 结构的 Obsidian 知识库。

它不绑定任何个人 vault、路径、项目名或语言习惯，适合迁移到不同 Obsidian vault 中使用。

## 技能内容

这个 skill 主要覆盖以下工作：

- 初始化 Obsidian vault 的目录结构
- 按 PARA 方法判断笔记应该放在哪里
- 管理项目笔记、项目日志、项目任务和项目决策
- 将项目经验沉淀为 Area 或 Resources 中的长期知识
- 将整理完成的知识复制到 Share 目录，作为对外分享版本
- 使用 Diary 目录记录每日或每周日志
- 将超过一个月的日记归档到年份子目录
- 使用 Obsidian CLI 进行任务查询、搜索、创建、追加、移动和维护

推荐目录结构：

```text
000-Sketch/
100-Projects/
200-Area/
300-Resources/
400-Archives/
900 - Diary/
Share/
```

## 目录含义

`000-Sketch`  
用于临时想法、粗糙记录、收集箱内容和暂时无法分类的笔记。

`100-Projects`  
用于有明确目标、期限、交付物或结束点的项目。

`200-Area`  
用于长期维护的责任领域、技能领域、角色和持续关注的主题。

`300-Resources`  
用于可复用参考资料，不绑定某个具体项目或持续责任。

`400-Archives`  
用于已经完成、暂停、废弃或不再活跃但仍值得保留的内容。

`900 - Diary`  
用于每日或每周日志。默认最新一个月放在根目录，超过一个月归档到年份子目录。

`Share`  
用于准备分享给他人的整理版笔记。它是分享副本区，不是知识的原始归属地。

## 如何触发

在 Codex 中，你可以直接提到这个 skill：

```text
使用 $obsidian-para-workflow 帮我初始化一个 Obsidian 知识库
```

也可以用自然语言描述需求，例如：

```text
帮我用 PARA + Diary + Share 结构整理这个 Obsidian vault
```

```text
帮我创建一个项目目录，并生成项目入口页和任务页
```

```text
帮我写今天的日记
```

```text
帮我判断这篇笔记应该放到 Projects、Area 还是 Resources
```

```text
帮我把这篇知识整理成可以放到 Share 的版本
```

## 使用前准备

确保本地已安装并启用 Obsidian CLI。

常用检查命令：

```powershell
obsidian version
obsidian vaults verbose
obsidian help
```

如果有多个 vault，使用时需要指定 vault：

```powershell
obsidian vault="<vault>" ...
```

将 `<vault>` 替换为你的 Obsidian vault 名称。

## 初始化目录

skill 会建议通过创建 `_index.md` 的方式初始化目录，因为这样既能创建文件夹，也能在 Obsidian 中作为目录说明页使用。

示例：

```powershell
obsidian vault="<vault>" create path="000-Sketch/_index.md" content="# Sketch\n\nRaw capture and unclear ideas.\n"
obsidian vault="<vault>" create path="100-Projects/_index.md" content="# Projects\n\nActive outcomes and deliverables.\n"
obsidian vault="<vault>" create path="200-Area/_index.md" content="# Area\n\nOngoing responsibilities and domains.\n"
obsidian vault="<vault>" create path="300-Resources/_index.md" content="# Resources\n\nReusable references.\n"
obsidian vault="<vault>" create path="400-Archives/_index.md" content="# Archives\n\nInactive or completed material.\n"
obsidian vault="<vault>" create path="900 - Diary/_index.md" content="# Diary\n\nDaily and weekly logs.\n"
obsidian vault="<vault>" create path="Share/_index.md" content="# Share\n\nPolished copies for sharing.\n"
```

## 日记规则

默认规则：

- 最新一个月的日记放在 `900 - Diary/`
- 超过一个月的日记移动到 `900 - Diary/<year>/`
- 默认使用周记文件，例如 `2026-06-Week-2.md`
- 每天的内容作为日期小节追加到周记文件
- 如果用户明确要求，也可以使用每日单独文件

日记模板：

```markdown
## YYYY-MM-DD

### Progress

- 

### Project Log

- 

### Learned

- 

### Next

- [ ] 
```

## 项目规则

每个项目建议使用下面的结构：

```text
100-Projects/<project>/
  <project>.md
  Logs/
  Decisions/
  Knowledge/
  Tasks.md
```

项目入口页用于记录：

- 项目目标
- 当前重点
- 风险
- 决策
- 待沉淀知识
- 下一步任务

## 知识沉淀流程

这个 skill 推荐使用下面的知识流动方式：

```text
Diary -> Project -> Area / Resources -> Share
```

含义：

- `Diary` 记录当天发生了什么
- `Project` 记录项目上下文和项目推进
- `Area / Resources` 保存可复用知识
- `Share` 保存适合发给别人的整理版副本

## 分享规则

`Share` 目录只放整理完成、适合分享的副本。

准备分享稿时，skill 会遵循这些规则：

- 先确认原始知识笔记在哪里
- 保留原始笔记在 PARA 目录中
- 在 `Share/<title>.md` 创建分享副本
- 去掉不适合外部分享的细节
- 避免覆盖已有分享稿，除非用户明确要求

## 常用请求

```text
使用 $obsidian-para-workflow 初始化我的 vault
```

```text
使用 $obsidian-para-workflow 创建一个名为 Payment Refactor 的项目
```

```text
使用 $obsidian-para-workflow 帮我写今天的日记
```

```text
使用 $obsidian-para-workflow 把这段项目经验整理成 Resources 笔记
```

```text
使用 $obsidian-para-workflow 把这篇笔记整理成 Share 版本
```
