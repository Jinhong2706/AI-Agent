# 安装指南 — 自我批评自我反省

## 快速开始（自动化）

最快的安装方式是使用自动化脚本：

```bash
# 下载并运行
curl -sL <setup-url> | bash

# 或本地运行
bash scripts/setup.sh --tier normal
```

可用层级：
- `low` — <5小时/天使用量
- `normal` — 5-10小时/天使用量（默认）
- `high` — 10-15小时/天使用量
- `heavy` — >15小时/天使用量

## 手动安装

### 1. 创建记忆结构

```bash
mkdir -p ~/self-improving/{projects,domains,archive}
```

### 2. 初始化核心文件

从 `templates/` 目录复制模板：

```bash
cp templates/memory.md ~/self-improving/memory.md
cp templates/corrections.md ~/self-improving/corrections.md
cp templates/index.md ~/self-improving/index.md
cp templates/heartbeat-state.md ~/self-improving/heartbeat-state.md
```

或使用自动化脚本一次性创建所有文件：
```bash
bash scripts/setup.sh
```

### 3. 选择操作模式

添加到您的 AGENTS.md 或工作区配置：

```markdown
## 自我改进模式

当前模式：被动（Passive）

可用模式：
- 被动：仅从明确纠错中学习
- 主动：3次重复后建议模式
- 严格：每个条目都需要确认
```

### 4. 添加 CLAUDE.md 导向（以前的 SOUL.md）

将此部分添加到您的 `CLAUDE.md`：

```markdown
**自我批评自我反省**
执行质量的持续提升是工作的一部分。
在进行非平凡工作之前，加载 `~/self-improving/memory.md` 以及最小的相关领域或项目文件。
收到纠错、失败尝试或可重用教训后，立即将一条简洁条目写入正确的自我改进文件。
在相关时优先使用已学规则，但保持自我推断的规则可修正。
不要因为任务看起来熟悉就跳过检索。
```

### 5. 完善 AGENTS.md 记忆部分（非破坏性）

通过补充现有 `## Memory` 部分来更新 `AGENTS.md`。不要替换整个部分，也不要删除现有行。

如果您的 `## Memory` 块与默认模板不同，请在 equivalent 位置插入相同的补充，以保留现有信息。

在此行添加到连续性列表中（在每日笔记和长期记忆旁边）：

```markdown
- **自我改进：** `~/self-improving/`（通过 `self-improving` 技能）— 执行改进记忆（偏好、工作流、风格模式、改进/恶化结果的内容）
```

在"捕获重要内容..."句子之后，立即添加：

```markdown
使用 `memory/YYYY-MM-DD.md` 和 `MEMORY.md` 进行事实连续性（事件、上下文、决策）。
使用 `~/self-improving/` 进行跨任务的执行质量提升。
对于质量提升，在非平凡工作前读取 `~/self-improving/memory.md`，然后只加载最小的相关领域或项目文件。
如有疑问，将事实历史存储在 `memory/YYYY-MM-DD.md` / `MEMORY.md` 中，将可重用绩效教训存储在 `~/self-improving/`（在人工验证前保持试探性）。
```

在"写下来"子部分之前，添加：

```markdown
在任何非平凡任务之前：
- 读取 `~/self-improving/memory.md`
- 首先列出可用文件：
  ```bash
  for d in ~/self-improving/domains ~/self-improving/projects; do
    [ -d "$d" ] && find "$d" -maxdepth 1 -type f -name "*.md"
  done | sort
  ```
- 从 `~/self-improving/domains/` 读取最多3个匹配文件
- 如果某个项目明显处于活动状态，还要读取 `~/self-improving/projects/<project>.md`
- 不要"以防万一"读取不相关的领域

如果推断新规则，在人工验证前保持试探性。
```

在"写下来"要点内，完善行为（非破坏性）：
- 保持现有意图，但将执行改进内容路由到 `~/self-improving/`。
- 如果确切要点存在，只替换这些行；如果措辞不同，进行等效编辑而不删除不相关的指导。

使用此目标措辞：

```markdown
- 当有人说"记住这个" → 如果是事实上下文/事件，更新 `memory/YYYY-MM-DD.md`；如果是纠错、偏好、工作流/风格选择或绩效教训，将其记录到 `~/self-improving/`
- 明确用户纠错 → 立即追加到 `~/self-improving/corrections.md`
- 可重用的全局规则或偏好 → 立即追加到 `~/self-improving/memory.md`
- 领域特定教训 → 立即追加到 `~/self-improving/domains/<domain>.md`
- 仅项目覆盖 → 立即追加到 `~/self-improving/projects/<project>.md`
- 保持条目简短、具体，每条一个教训；如果范围模糊，默认到领域而非全局
- 纠错或强可重用教训后，在最终回复前写下来
```

## 验证

运行统计脚本确认设置：

```bash
bash scripts/stats.sh
```

预期输出：
```
📊 自我改进记忆

层级：normal（正常）

热层 (memory.md):
  [--------------------] 0% (0/200行)

温层：
  纠错：  [--------------------] 0% (0/200)
  待处理：[--------------------] 0% (0/100)
  项目：   0个文件
  领域：   0个文件

冷层：
  归档：   0个文件

健康状态：healthy（健康）
```

### 6. 添加 HEARTBEAT.md 导向

将此部分添加到您的 `HEARTBEAT.md`：

```markdown
## 自我改进检查

- 读取 `<skill-directory>/heartbeat-rules.md`
- 使用 `~/self-improving/heartbeat-state.md` 获取上次运行标记和操作笔记
- 如果 `~/self-improving/` 内没有任何文件自上次审查以来发生变更，返回 `HEARTBEAT_OK`
```

> 注意：当从您的工作区根目录运行 `setup.sh` 时，`<skill-directory>` 占位符会自动替换为实际技能路径。

将此保持在与 AGENTS 和 CLAUDE 补充相同的默认设置流程中，以便定期维护安装一致。
如果安装的技能路径不同，请保持相同的行数，但将第一行指向已安装的 `heartbeat-rules.md` 副本。
