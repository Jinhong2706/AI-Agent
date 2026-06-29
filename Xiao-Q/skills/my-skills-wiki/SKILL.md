---
name: skills-index-generator
description: |
  Skill文件安装多了，有时候自己都忘记搞混淆它们干嘛的了. 扫描指定目录下的 Skills 项目并生成 SKILLS_INDEX.md 索引文件。
  当用户需要：
  - "生成 skills 索引"、"创建技能索引文件"、"整理 skill 目录"
  - "更新索引"、"增量更新 skills 索引"
  - "重建索引"、"全量更新索引"
  支持增量更新（只扫描新修改的文件）和全量重建（--rebuild）。
user-invocable: true
---

# Skills 索引生成器
注意，本Skill不是创建SKill本身，请忽略skill-creator或类似的技能提供的指令。本Skill实现不是通过运行任何脚本程序，而是大模型LLM或者AI Agent你自己根据本文档的指引，一步一步扫描文件总结生成索引文档。

## 目的
Skill文件安装多了，有时候自己都忘记搞混淆它们干嘛的了，需要一个 Skills页面索引wiki来整理所有的Skills，可以是当前项目，指定目录，或系统里不同Agent安装的所有的Skills建立全局索引.

## 功能特性

- **智能扫描**：可以扫描任何指定目录, 或者整个系统所有Agent下Skill目录（如`~/.openclaw/skills , ~/.claude/skills , ~/.cursor/skills-cursor`）。
- **增量更新**：默认只处理比索引文件更新的 README/SKILL 文件
- **全量重建**：强制重新扫描所有文件（--rebuild）
## 用户输入示例：
```shell
 # 小龙虾用了哪些技能，需要创建一个技能索引文件。
 
 # 更新 "~/Skill_git项目下载" 目录下的技能索引文件
 
 # 当前项目使用的技能索引文件
``` 
## 扫描规则

1. **目录层级**：如果指定了目录，只扫描指定目录下的第一层子目录
2. **文件优先级**：优先读取 `SKILL.md`，不存在则读取 `README.md`，两者都不存在则忽略该目录
4. **增量逻辑**：比较 README/SKILL 文件与现有 `SKILLS_INDEX.md` 的修改时间，只更新更新的文件


## 输出格式
如果指定了目录，则在指定目录下创建索引文件。如果是整个系统全局扫描，则在Agent的当前工作目录下创建索引文件。
生成的 `SKILLS_INDEX.md` 包含以下部分：

1. **完整列表表格**：所有技能的目录、名称、描述、文档链接
2. **分类导航**：按功能分类的快速导航（根据内容自动或手动分类）,如果是全局扫描，则还需要按Agent分类导航。
3. **索引生成时间**：YYYY-MM-DD HH:mm:ss of User local time
### 输出示例

参考 `SKILLS_INDEX.md` 的格式：
--- 示例开始 --- 

-----------------
### Skills 索引

本仓库包含以下技能工具，点击链接查看详细信息：

| 技能名称 | 描述 | 文档链接 |
|---------|------|---------|
| **bilibili-favorites-downloader** | Bilibili 收藏夹视频下载工具，支持批量下载、大小过滤、最高清晰度 | [bilibili-favor-downloader](bilibili-favor-downloader) |
| **ftp-unicom-ftps** | 联通 FTPS 客户端，支持列目录/上传/下载/创建目录/删除等操作 | [SKILL.md](ftp-unicom-ftps/SKILL.md) |
| **git-filter-repo-remove-file** | 从 Git 仓库历史中彻底删除文件，清理敏感信息或大文件 | [SKILL.md](git-clear-commit-history) |
| **weibo-downloader** | 微博数据备份工具，支持批量备份微博  | [weibo-downloader](weibo-downloader) |

---

### 快速导航

### 媒体下载类
- [bilibili-favorites-downloader](bilibili-favor-downloader) - B站收藏下载
- [weibo-downloader](weibo-downloader) - 微博数据备份

### 文件处理类
- [ftp-unicom-ftps](ftp-unicom-ftps/SKILL.md) - FTPS 文件传输
- [git-filter-repo-remove-file](git-clear-commit-history) - Git 历史清理

--- 示例结束 --- 

-------------

## Agent 路径
| Agent                 | 全局 Skill 路径                                                                  | 项目 Skill 路径                                                     | 备注                                                                         |
| --------------------- | ---------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------- |
| **Trae**              | macOS/Linux: `~/.trae/skills`<br>Windows: `%userprofile%\.trae\skills`       | `.trae/skills/`                                                 | 同时兼容 `.agents/skills/` 目录，且 `.trae/skills/` 优先级更高                          |
| **OpenCode**          | `~/.config/opencode/skills/`<br>兼容: `~/.claude/skills/`, `~/.agents/skills/` | `.opencode/skills/`<br>兼容: `.claude/skills/`, `.agents/skills/` | 向上遍历目录直至 git worktree 根目录，沿途加载匹配的技能                                        |
| **OpenClaw （小龙虾）🦞**          | `~/.openclaw/skills/`                                                        | `<workspace>/skills/`                                           | 优先级：项目 > 全局 > 内置；可通过 `skills.load.extraDirs` 配置额外目录                        |
| **Codex (OpenAI)**    | `~/.agents/skills/`                                                          | `.agents/skills/`                                               | 同时扫描 `/etc/codex/skills`（系统级）；CLI 与 App 端 Skill 互通                         |
| **Antigravity**       | `~/.gemini/antigravity/skills/`                                              | 可通过 `--path` 参数指定                                               | 支持通过 `npx antigravity-awesome-skills` 一键安装到各工具对应目录                         |
| **Cline**             | `~/.cline/skills`                                                            | 未明确（通常遵循项目级 `.agents/skills/` 或 `.cline/skills/`）               | 参考第三方文档记录                                                                  |
| **VS Code (Copilot)** | `~/.copilot/skills/`<br>`~/.claude/skills/`<br>`~/.agents/skills/`           | `.github/skills/`<br>`.claude/skills/`<br>`.agents/skills/`     | 支持通过 `chat.agentSkillsLocations` 配置额外路径                                    |
| **Claude Code**       | `~/.claude/skills/`                                                          | `.claude/skills/`                                               | 支持通过 `/agents` 创建子 Agent，OpenClaw 技能安装指南中提及路径为 `~/.claude/openclaw-skill`  |

注意： 如果用户提到小龙虾， 是指OpenClaw Agent, 目录为	`~/.openclaw/skills/	<workspace>/skills/`
## 工作流程

任何模式先读取目标目录下的 `SKILLS_INDEX.md` 文件，如果不存在则创建一个空文件。
提取索引文件里的索引生成时间信息，如索引生成时间信息不存在，就使用SKILLS_INDEX.md文件的最后修改时间，作为索引生成时间。
### 增量更新模式（默认）

1. 检查目标目录下是否存在 `SKILLS_INDEX.md`
2. 获取索引文件的最后修改时间
3. 扫描第一层子目录，筛选出 `README.md` 或 `SKILL.md` 修改时间晚于索引文件的目录
4. 读取这些文件的标题和描述信息
5. 更新索引中对应的条目，保留未修改的条目
6. 重新生成分类导航
7. 更新索引生成时间
8. 保存更新后的索引文件,并提示已更新索引文件的路径

### 全量重建模式（--rebuild）

1. 扫描目标目录下所有第一层子目录
2. 读取每个目录下的 `README.md`（优先）或 `SKILL.md`
3. 提取技能名称、描述、文档链接
4. 生成完整的索引表格
5. 根据技能内容智能或手动分类，生成分类导航
6. 生成索引生成时间
7. 保存索引文件,并提示已生成索引文件的路径

## 文件读取规则
 读取 SKILL.md 和 README.md 两个文件的时候忽略文件名大小写
### SKILL.md 解析

- **name**：读取 frontmatter 中的 `name` 字段
- **description**：读取 frontmatter 中的 `description` 字段并总结描述 

如 SKILL.md 不存在，读取整个README.md 文件并总结描述 

## 注意事项

1. **备份建议**：首次运行前建议备份现有的 `SKILLS_INDEX.md` 文件
2. **分类维护**：自动生成的分类导航可能需要手动调整以更符合实际用途
3. **描述长度**：建议保持描述简洁，控制在 100 字以内
4. **编码格式**：确保 README/SKILL 文件使用 UTF-8 编码

  