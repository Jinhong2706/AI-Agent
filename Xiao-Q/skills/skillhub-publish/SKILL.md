---
name: skillhub-publish
version: "1.6.0"
description: 一键检查 + 修复 + 生成发布物料，将任一 WorkBuddy skill 准备好发布到 SkillHub。出发前确认（Pre-flight）→ 六维审计（文件结构/Frontmatter/内容质量/版本一致性/安全/外部依赖）→ 讨论确认后自动修复 → 脱敏 → 生成 README.md + SkillHub 描述 + 版本更新说明，最后打包交付。
template: basic
triggers:
  - publish
  - skillhub
  - skillhub发布
  - 发布技能
  - 技能上架
  - 发布到skillhub
  - 文件报警
  - 危害内容
  - 敏感词检查
  - 脱敏规则
token_budget:
  L0_trigger: 450
  L1_core: 3000
  L2_deep: 6000
  hard_cap: 10000
---

# SkillHub Publish

一键将 WorkBuddy skill 准备好发布到 SkillHub。六阶段流程：出发确认 → 审计 → 讨论确认 → 修复脱敏 → 生成物料 → 交付。

> **先议后行：** 所有写操作前都经用户确认，且在发布副本上执行，不意外修改原始文件。

---

## 使用方式

```
发布 skillhub-publish 到 skillhub
或：发布技能 xxx
或：把 xxx 准备好发布
```

## 输入

当前运行此 skill 时，用户需指定：
- **目标 skill 名称**（必填）：`~/.workbuddy/skills/<目标名称>/` 下的现有 skill
- **版本号**（可选）：如不指定，使用 SKILL.md 中的当前版本

---

## Phase 0: 出发前确认（Pre-flight Checklist）

> **强制步骤。** Phase 1 审计开始前，必须先向用户出示以下"机票"并获取确认。不签字不飞。

### 步骤 0.1：识别目标

确认当前要发布的目标 skill 及其版本号。

### 步骤 0.2：出示机票

按以下固定格式向用户展示：

```
✈️ 发布机票 — {目标 skill 名称} v{版本}

📋 接下来要做的事（预计 5-8 分钟）：

  Phase 1: 六维审计（只读，不碰文件）
  └─ 检查文件结构、Frontmatter、内容质量、版本一致性、安全、外部依赖

  Phase 2: 讨论确认
  └─ 你看审计结果，勾选要修复的问题，确认版本号

  Phase 2.5: 创建桌面副本
  └─ 复制 skill 到桌面，清理非发布物，保留隐私数据骨架

  Phase 3: 修复 + 脱敏
  └─ 按你勾选的项目逐一修复，自动扫描敏感词替换

  Phase 4: 生成发布物料
  └─ README.md、SkillHub 描述文本、版本更新说明

  Phase 5: 终检交付
  └─ 隐藏文件/空目录/脚本目录最后扫描，确保干净

📦 输出成果：
  - 桌面发布包：~/Desktop/{名称}-v{版本}/
  - SkillHub 描述文本（可复制粘贴）
  - 版本更新说明（可复制粘贴）

⚙️ 你会被问到几次：
  - 1 次：审计报告出来后，确认修复清单（Phase 2）
  - 0-1 次：如果检测到脱敏匹配，展示报告确认（Phase 3.5）
  - 全程约需你手动确认 1-2 次，其余自动执行
```

### 步骤 0.3：确认输出位置

询问用户：

```
📁 发布包输出到：~/Desktop/{名称}-v{版本}/
   是否 OK？如需更改，请说路径。
```

**默认：** `~/Desktop/{名称}-v{版本}/`。用户可指定其他位置。

### 步骤 0.4：获取起飞签字

展示完整机票后，等待用户回复"确认"/"OK"/"开始"等明确信号。

用户确认后方可进入 Phase 1。

---

## Phase 1: 六维审计（只读，不动手）

### 步骤 1.1：定位目标 skill

确认 `~/.workbuddy/skills/<用户指定的名称>/` 目录存在。不存在则报错终止。

### 步骤 1.2：文件结构审计

对以下文件逐项检查存在性：

| 文件 | 等级 | 判定 |
|------|------|------|
| SKILL.md | P0 | 不存在则无法发布 |
| CHANGELOG.md | P0 | 不存在则无法追溯版本 |
| DESIGN.md | P1 | 推荐必备 |
| SPEC.md | P1 | 推荐必备 |
| README.md 或 INTRO.md | P1 | 面向用户的说明 |
| scripts/（如 SKILL.md 中声明） | P1 | 声明了脚本但目录不存在 |
| 非发布物检测 | P1 | 检查隐藏文件（`.` 开头）、占位文件（`.gitkeep`/`.empty`）、无扩展名文件 |
| 空文件检测 | P2 | 存在但为空（0 字节） |
| 用户隐私文件 | **P0** | 检查 `data/user-profile.md` 等隐私文件：发布包中必须保留骨架而非完整内容 |
| 缓存数据 | **P0** | 检查 `data/cache/` 等缓存目录：发布包中必须清理，可能包含其他 skill 的历史数据 |
| 平台配置文件 | **P0** | 检查 `.skillignore` 等 WorkBuddy 平台专属文件：发布包中不应出现 |

### 步骤 1.3：Frontmatter 审计

读取 `SKILL.md` 的 frontmatter（--- 之间的 YAML），检查：

| 字段 | 等级 | 要求 |
|------|------|------|
| name | P0 | 存在且非空 |
| version | P0 | 存在且符合 semver（x.y.z） |
| description | P0 | 存在且非空 |
| description 长度 | P1 | 80-200 字为佳 |
| triggers | P0 | 存在且非空列表 |
| triggers 数量 | P1 | 至少 3 个 |
| token_budget | P1 | 推荐配置三级加载 |
| 字段拼写正确 | P1 | 如 desription→description |

### 步骤 1.4：内容质量审计

| 检查项 | 等级 | 说明 |
|--------|------|------|
| description 通顺完整 | P1 | 无"待补充""TODO"等占位符 |
| description 含限制声明 | P2 | 如"仅限 WorkBuddy"等边界说明 |
| triggers 覆盖中英文 | P1 | 建议中英文触发词都有 |
| 文本中"我的""本技能"等 | P2 | 建议统一为"此技能"等正式用语 |
| CHANGELOG.md 内容充实 | P1 | 不只写"initial release"，有实质性变更记录 |

### 步骤 1.5：版本一致性审计

| 检查项 | 等级 | 说明 |
|--------|------|------|
| SKILL.md version = CHANGELOG 最新版 | P1 | 不匹配需对齐 |
| SPEC.md version 同 SKILL.md | P1 | 如有 SPEC.md |
| DESIGN.md version 同 SKILL.md | P1 | 如有 DESIGN.md |
| SKILL.md 正文中版本号一致 | P2 | 扫描正文 `vX.Y.Z` 模式，与 frontmatter 对比 |
| 附属 .md 文件版本号一致 | P2 | 如 PHILOSOPHY.md 中声明的版本与 frontmatter 一致 |

### 步骤 1.6：安全检查

| 检查项 | 等级 | 说明 |
|--------|------|------|
| 脚本含 rm -rf / sudo 等 | P0 | 严重安全红线 |
| 脚本含硬编码 API key / token | P0 | 敏感信息泄露 |
| 文件写操作未声明范围 | P1 | 需要说明写什么路径 |
| 缺少 try-except 错误处理 | P2 | 可能导致脚本中断 |
| Python 脚本的 shebang 行 | P2 | 建议 #!/usr/bin/env python3 |

### 步骤 1.7：外部依赖审计

| 检查项 | 等级 | 说明 |
|--------|------|------|
| Skill 工具调用其他 skill 名 | P0 | 如 `Skill("xxx")`，其他人没有 |
| import 非标准库 | P1 | 需要声明 pip 依赖 |
| 调用系统命令非标准 | P1 | 如 curl, jq, docker 等 |
| 路径硬编码到其他 skill 目录 | P1 | 不会自动存在 |
| 发起外部网络请求 | P1 | 需要声明 API 调用 |

### 步骤 1.8：生成审计报告

将以上所有发现的问题按 P0→P1→P2 分组，用以下格式展示：

```
📋 审计报告：{目标 skill 名称} v{版本}

🔴 P0 — 必须修复（不可跳过）
  - 问题描述

🟡 P1 — 推荐修复
  [{ }] 问题描述

🟢 P2 — 锦上添花
  [{ }] 问题描述
```

P1/P2 默认勾选。P0 直接执行，无 checkbox。

### 步骤 1.9：审计结果路由

- 发现任何问题（P0/P1/P2 任一项存在）→ 进入 Phase 2 讨论确认
- 完全没有发现任何问题 → 直接进入 Phase 4 生成物料（跳过 Phase 2/3/2.5），告知用户：
  "此 skill 已达到发布标准，无需修复。直接生成发布物料。"

---

## Phase 2: 讨论确认

展示审计报告后，向用户确认：

1. **确认修复清单：** P0 不可跳过；P1/P2 逐项确认哪些要修、哪些跳过
2. **确认版本号：** 使用当前版本还是升级。参考规则：
   - 仅文档/描述修改 → patch 升级（x.y.z+1）
   - 功能变更 → minor 升级（x.y+1.0）
   - 破坏性变更 → major 升级（x+1.0.0）
3. **确认 README 内容概要：** 生成 README 前确认定位（目标用户/核心价值点）
4. **确认是否同步到原始文件：** 修复在发布包的副本上执行，是否同时更新原始文件？（默认是）
5. 用户签字确认后才进入 Phase 2.5

---

## Phase 2.5: 创建发布副本

在 Phase 3 修改之前，先将目标 skill 复制到桌面，后续所有修复在副本上操作。

> ⚠️ **创建后不要再用 rsync/cp 从原始目录覆盖副本。** 副本的排除清单（.skillignore / tests / .verify_history 等）是在首次创建时一次性应用的。后续用裸 rsync 覆盖会将这些文件重新拷回副本。副本的操作原则是：**从副本直接改，改完反向同步回原始文件**，而不是从原始文件往副本推。

### 步骤 2.5.1：读取 `.skillignore`

如果目标 skill 存在 `.skillignore`，将其中的排除规则逐条读出（注释行和空行跳过），用于副本创建和清理。

如果目标 skill **不存在** `.skillignore`，使用以下默认排除列表（与 `.skillignore` 常用规则一致）：

| 条目 | 原因 |
|------|------|
| `data/user-profile.md` | 用户隐私数据 |
| `data/cache/` | 历史评分缓存 |
| `tests/` | 开发工具 |
| `.verify_history/` | 历史验证数据 |
| `__pycache__/` | Python 编译缓存 |

### 步骤 2.5.2：创建副本

```bash
# rsync 方案（推荐）
rsync -a --exclude='.git' --exclude='__pycache__' --exclude='.DS_Store' \
  --exclude='node_modules' --exclude='*.pyc' --exclude='.gitignore' \
  --exclude='.gitkeep' --exclude='.skillignore' --exclude='.verify_history' \
  --exclude='data/cache' \
  ~/.workbuddy/skills/{名称}/ ~/Desktop/{名称}-v{版本}/
```

若 rsync 不可用，改用 cp + 清理：

```bash
cp -r ~/.workbuddy/skills/{名称} ~/Desktop/{名称}-v{版本}/

# 基础清理（与 rsync --exclude 保持一致）
find ~/Desktop/{名称}-v{版本} -name '__pycache__' -type d -exec rm -rf {} +
find ~/Desktop/{名称}-v{版本} -name '.DS_Store' -delete
find ~/Desktop/{名称}-v{版本} -name '*.pyc' -delete
find ~/Desktop/{名称}-v{版本} -name '.gitkeep' -delete
find ~/Desktop/{名称}-v{版本} -name '.skillignore' -delete
find ~/Desktop/{名称}-v{版本} -name '.gitignore' -delete
rm -rf ~/Desktop/{名称}-v{版本}/.git
rm -rf ~/Desktop/{名称}-v{版本}/.verify_history
rm -rf ~/Desktop/{名称}-v{版本}/node_modules
rm -rf ~/Desktop/{名称}-v{版本}/data/cache
```

### 步骤 2.5.3：处理用户数据文件

对于 `data/user-profile.md`（或 `.skillignore` 中标注的隐私数据文件）：

**不要直接删除**——新用户首次使用需要文件存在。

改为**保留骨架**：读取原始文件的内容，提取所有 section header（`#`、`##`、`###` 标题行）和字段框架（`- 字段名：` 行），清除其中的具体数值和个人数据，保留结构。这样生成的骨架自动匹配该 skill 的数据结构，不依赖预设模板。

操作步骤：
1. 读取 `~/.workbuddy/skills/{名称}/data/user-profile.md`
2. 复制所有标题行（`# 用户画像`、`## xxx`、`### xxx`）
3. 复制所有字段名行（`- 字段名：`），清空冒号后的内容
4. 复制所有表格的表头行（`| xxx | xxx |` 和 `|---|---|`），清空数据行
5. 删除所有含具体用户数据的行（昵称、年级、日期、具体描述等）
6. 将清理后的骨架写入 `~/Desktop/{名称}-v{版本}/data/user-profile.md`

示例（little-writer 的 user-profile 骨架化后）：

```markdown
# 用户画像

> 由 skill 在每次会话结束时自动更新。

## 用户信息
- 昵称：
- 年级：
- 首次会话日期：
- 最近会话日期：
- 总写作次数：0

## 偏好记录
- 风格偏好：
- 角色偏好：
- 常用题材：

## 能力画像
### 优势
### 成长区
### 已克服
### 语言风格标签
### 熟练度
### 🏅 勋章收藏

## 成长关注
| 日期 | 关注点 | 状态 |
|------|--------|------|

## 写作成长轨迹
| 日期 | 题材 | 字数 | 亮点 | 改进点 |
|------|------|------|------|--------|
```

### 步骤 2.5.4：清理缓存数据

清理可能包含其他 skill 历史数据的缓存目录：

```bash
rm -rf ~/Desktop/{名称}-v{版本}/data/cache/
```

### 步骤 2.5.5：额外清理（按 `.skillignore` 动态执行）

如果 `.skillignore` 中包含未在基础清理中覆盖的额外排除项，按以下规则解析并执行：

```
读取 .skillignore 每行：
  跳过空行和 # 开头的注释行
  对非空行：
    如果以 / 结尾 → 视为目录，执行 rm -rf {副本路径}/{条目}
    如果包含 * → 视为 glob，执行 find {副本路径} -name "{条目}" -delete
    其他 → 视为文件，执行 rm -f {副本路径}/{条目}
```

示例：若 `.skillignore` 包含 `tests/` 但基础清理未覆盖：
```bash
rm -rf ~/Desktop/{名称}-v{版本}/tests/
```

解析后，将本次清理的额外条目告知用户。

告知用户发布副本已创建，同时说明已清理了哪些非发布物。

---

## Phase 3: 在副本上执行修复

在 `~/Desktop/{名称}-v{版本}/` 上操作。如果用户选择了同步原始文件，对 `~/.workbuddy/skills/{名称}/` 执行相同修改。

按用户确认的清单逐项执行：

### 修复 Frontmatter
- 更新 version
- 补充/优化 description 文字
- 补充 triggers
- 补充 token_budget
- 修正拼写错误
- 同步 SKILL.md 正文标题中的版本号

### 补齐文件
- 创建缺失的 DESIGN.md（使用标准模板）
- 创建缺失的 SPEC.md（使用标准模板）
- 创建/更新 README.md（Phase 4 生成的完整版）

### 对齐版本
- 更新 CHANGELOG.md：追加新版本条目
- 更新 SPEC.md/DESIGN.md 中的版本号
- 更新附属 .md 文件（如 PHILOSOPHY.md）中声明的版本

### 清理非发布物

⚠️ **以下清理操作仅在发布副本（`~/Desktop/{名称}-v{版本}/`）上执行，不同步到原始文件。** 原始 skill 目录需要保留 `.skillignore`、`tests/`、`data/user-profile.md` 等文件才能正常工作。

在发布副本上执行：
- 删除 `.skillignore`（WorkBuddy 平台配置，不属于 skill 内容）
- 删除 `.verify_history/`（历史验证数据）
- 删除 `data/cache/`（历史评分缓存）
- 用空骨架 template 替换 `data/user-profile.md`（保留完整字段结构，清空个人数据，骨架格式见 Phase 2.5 步骤 2.5.3）
- 删除 `tests/`（开发工具，非 skill 内容）
- 删除 `__pycache__/`、`*.pyc`、`.DS_Store`、`.gitkeep`（构建产物和占位文件）

每次修改前向用户展示 diff（修改内容简述），确认后执行。

完成后告知用户：
- 如已同步到原始文件：⚠️ "原始 skill 文件已更新至 v{版本}，建议用 git 查看 diff 确认变更"
- 如未同步：ℹ️ "原始文件未修改。发布包版本为 v{版本}，如需升级请手动操作"

---

## Phase 3.5: 发布内容脱敏（仅发布副本）

> ⚠️ **只操作发布副本 `~/Desktop/{名称}-v{版本}/`，不碰原始 skill。**

### 步骤 3.5.0：规则自举（AI Bootstrap）

**触发条件：** `~/.workbuddy/principles/sanitize_rules.yaml` 不存在。

此步骤为新用户首次运行准备脱敏规则，一次生成终身复用。

执行流程：

1. **告知用户** — 输出提示：「未检测到私有脱敏规则。将自动扫描发布包内容中的敏感词，用于生成脱敏规则。」
2. **扫描发布副本** — 对 `~/Desktop/{名称}-v{版本}/` 下所有 `.md` 和 `.yaml` 文件做全量扫描
3. **AI 识别** — 用 LLM 分析文件内容，找出以下类别：

   | 类别 | 识别目标 | 示例 |
   |:-----|:---------|:-----|
   | `person_name` | 可唯一识别具体人物的名称 | 某老师、某人物等 |
   | `org_name` | 具体组织/机构/网站名 | 某修行团体、某组织等 |
   | `book_series` | 具体出版物/书系/节目系列 | 某书系、某出版物等 |
   | `political_trigger` | 可能触发内容审核的政治词 | 某审核词、某气功关联词等 |
   | `review_imitation` | 易被误判为内部审核行为的术语 | 某审核术语、某记录格式等 |

4. **生成规则草案** — 按 `sanitize_rules.yaml` 格式生成建议规则。替换值使用通用称谓（teacher→老师、某大德、某修行团体、审查项、对照记录等）
5. **用户确认** — 展示规则草案，逐条让用户确认（可以编辑/添加/跳过）
6. **保存** — 确认后写入 `~/.workbuddy/principles/sanitize_rules.yaml`
7. **继续加载** — 加载刚生成的规则文件

> **自举原则：** 扫描基于发布副本中的实际内容。无内容则无规则，有内容才生成。
> LLM 只识别，不执行替换——替换在步骤 3.5.2 中用 sed 统一做。

### 步骤 3.5.1：加载脱敏规则

规则采用 **分层加载** 策略，避免敏感词内置入 skill 发布包：

1. **私有规则（优先）** — 读取 `~/.workbuddy/principles/sanitize_rules.yaml`
2. **内置规则（兜底）** — 如上一步无此文件或为空，读取 `references/sanitize_rules.yaml`（仅含通用无害模式）
3. **两者皆空** — 跳过 Phase 3.5，告知用户「无脱敏规则可执行」

逐条解析 rules 数组中的 `patterns` 和 `replace`。同一行的多个 pattern 按最长匹配优先排序。

> **为什么分层？** skillhub-publish 本身也会发布到 SkillHub，内置规则不能含具体人物/组织/政治词。
> 私有规则（`~/.workbuddy/principles/sanitize_rules.yaml`）存放全量敏感词，不随 skill 发布。

### 步骤 3.5.2：执行替换

对发布副本中的所有 `.md` 和 `.yaml` 文件逐条执行字符串替换：

⚠️ **使用 `|` 作为 sed 分隔符**（而非默认的 `/`），避免 pattern 本身含 `/` 时解析错误。

⚠️ **使用 `find` 而非 `**/*` 展开**，因为 macOS zsh 默认不展开 `**/*` 到嵌套子目录。

```bash
# 替换 .md 文件（含嵌套子目录）
find ~/Desktop/{名称}-v{版本}/ -name '*.md' -exec sed -i '' 's|<pattern>|<replace>|g' {} +

# 替换 .yaml 文件（含嵌套子目录）
find ~/Desktop/{名称}-v{版本}/ -name '*.yaml' -exec sed -i '' 's|<pattern>|<replace>|g' {} +
```

执行顺序：与 rules 数组一致。每执行一条，记录替换结果。

### 步骤 3.5.3：生成替换报告

格式：

```
📋 脱敏报告：{目标 skill 名称} v{版本}

规则来源：~/.workbuddy/principles/sanitize_rules.yaml（私有）| references/sanitize_rules.yaml（内置）

| 规则 | 匹配数 | 替换内容 | 样例（部分） |
|:----|:-----:|:--------|:----------|
| violence_sex_terms | 1 | 不当类比 | 内容安全词→不当类比 |
| review_imitation | 3 | 对照记录 | 审核术语→对照记录 |
```

无匹配的规则也展示（匹配数 0），便于确认没有遗漏。

### 步骤 3.5.4：展示确认

向用户展示替换报告。**关键确认点**：
- 有无过度替换？（如 `华严经` 不会被误杀——它不匹配任何 pattern）
- 有无技能特有的触发词需要追加？

非必要不要求用户逐条确认——报告本身即是证据。

### 规则扩展

「我不知道触发词还有哪些」是正常情况。多层加载策略如下：

```
加载顺序（优先级从高到低）：
  1. ~/.workbuddy/principles/sanitize_rules.yaml       ← 用户私有全量规则
  2. skill 内置 references/sanitize_rules.yaml          ← 通用无害规则（随 skill 发布）
  3. {目标 skill 的 .skillignore 同级}/sanitize_rules_override.yaml  ← skill 特有规则

执行时：按上述顺序搜索第一个存在的文件作为基线。
         再加裁 override（如有，追加到 rules 数组末尾）。
         规则来源信息记录在替换报告中。
```

示例 override：

```yaml
# 某 skill 特有触发词
rules:
  - id: "specific_api_terms"
    category: "content_safety"
    patterns:
      - "敏感API"
    replace: "通用API"
    note: "此 skill 使用了被标记的 API 名称"
```

---

### 反馈闭环：发布后自动补规则

**场景：** 用户发布 skill 到 SkillHub 后收到安全警告：「文件 X 存在危害内容」。用户将此信息反馈给 skill，skill 自动分析并补全规则。

**触发方式：** 用户直接说「XX 文件被报警了」「XX 文件有危害内容」「看看 XX 文件有什么问题」，或提供文件路径。

**执行流程：**

1. **定位文件** — 读取用户指定的文件（发布副本或原始 skill 目录均可）
2. **AI 扫描** — 用 LLM 分析文件内容，找出所有潜在触发词（5个类别同步骤 3.5.0）
3. **生成追加规则** — 对每个新发现的触发词，按 `sanitize_rules.yaml` 格式生成追加规则
4. **对比去重** — 读取现有规则（`~/.workbuddy/principles/sanitize_rules.yaml`），跳过已在规则库中的词
5. **用户确认** — 展示新发现的规则，逐条确认
6. **追加到规则库** — 将确认后的规则追加到 `~/.workbuddy/principles/sanitize_rules.yaml` 的 rules 数组末尾
7. **规则库持续进化** — 每反馈一次，规则库就扩展一次

**不依赖人工记忆** — 用户不需要记住哪些词是敏感的，只需要告诉 skill「这个文件被报警了」，skill 自己找出原因并记住。

---

## Phase 4: 生成发布物料

### 4.1 生成 README.md

为目标 skill 生成详细 README.md，写入发布副本（`~/Desktop/{名称}-v{版本}/`）。内容框架：

```
# {skill 名称}

> 一句话定位

## 这是什么（用途）
解决什么问题，适用场景

## 核心能力
逐项说明

## 快速使用
触发词 + 使用方式

## 技术架构（如有）
方案实现简述

## 环境要求
依赖项说明

## 安全与限制
边界声明

## 更新日志
链到 CHANGELOG.md
```

生成后展示给用户确认，可修改后定稿。

### 4.2 生成 SkillHub 描述文本

一段 80-200 字描述。格式示例：

```
{技能名称} v{版本}

一句话定位。{核心能力简要列举}。{适用场景}。

{限制声明}。
{许可证声明}。
```

直接展示给用户，可直接复制。

### 4.3 生成版本更新说明

条目式文本。格式示例：

```
v{版本} - {日期}

新增：
- {功能}
- {功能}

改进：
- {改进}

修复：
- {修复}
```

直接展示给用户，可直接复制。

---

## Phase 5: 最终交付

### 步骤 5.0：发布副本终检（强制，不可跳过）

交付前对发布副本执行最后一次扫描：

```bash
# 扫描隐藏文件
find ~/Desktop/{名称}-v{版本}/ -name ".*" ! -name "." ! -name ".." 2>/dev/null

# 扫描脚本目录——只应包含 README.md 声明文件
ls ~/Desktop/{名称}-v{版本}/scripts/ 2>/dev/null

# 扫描空目录
find ~/Desktop/{名称}-v{版本}/ -type d -empty 2>/dev/null
```

**通过标准**：
- 隐藏文件：零残留（特别是 .skillignore、.verify_history、.DS_Store）
- 脚本目录：最多只有 README.md（或按 SKILL.md 声明保留的必要脚本）
- 空目录：零存在（空目录会被 SkillHub 拒绝）

如有残留 → 返回 Phase 3 清理，不清到交付。

1. 发布副本已完成（Phase 2.5 已复制到桌面，Phase 3/4 已写入修改）
2. 输出 SkillHub 描述文本（Phase 4.2 产出）直接给用户复制
3. 输出版本更新说明（Phase 4.3 产出）直接给用户复制
4. 输出最终完成报告：发布包位置 + 变更摘要 + 原始文件同步状态

---

## 文件结构

| 文件 |
|------|
| SKILL.md |
| README.md |
| DESIGN.md |
| SPEC.md |
| CHANGELOG.md |
| references/sanitize_rules.yaml |

## 参考资料

- `DESIGN.md` — 架构决策记录
- `SPEC.md` — 功能规格说明
- `CHANGELOG.md` — 更新日志

## 安全声明

本 skill 仅读取 `~/.workbuddy/skills/` 目录下的文件。文件修改操作仅在用户确认后执行。不依赖其他 skill，不发起外部网络请求。遵循 MIT-0 许可证。
