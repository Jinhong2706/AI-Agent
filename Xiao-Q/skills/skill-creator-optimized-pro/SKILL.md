---
name: skill-creator-optimized-pro
description: "创建、优化、审计和打包 AI Skill 技能包；当用户要求创建技能、生成 Skill、优化 SKILL.md、修复技能包结构、补齐 YAML front matter、打包发布 SkillHub，或把业务流程沉淀为可安装技能时使用。不要用于一次性提示词润色、普通文档写作或与 Skill 无关的软件开发任务。"
version: "1.2.0"
author: "SenseTime Office Raccoon"
tags:
  - skill-creation
  - skillhub
  - yaml-frontmatter
  - package-validation
  - workflow-design
---

# Skill Creator Optimized Pro

将自然语言需求、业务流程、既有技能草稿或旧版技能包，转化为结构标准、内容完整、可安装、可审计、适合 SkillHub 发布的高质量 Skill 包。

## 0. 北极星目标

交付一个**能被正确触发、能稳定执行、能通过静态校验、能被他人安装复用**的 Skill 包，而不只是写一段看起来像提示词的文档。

执行时始终围绕三件事判断质量：

1. **触发准确**：`description` 同时说明能力、使用场景、触发表达和排除场景。
2. **执行稳定**：`SKILL.md` 给出目标、边界、流程、输出契约、异常处理和验证标准；复杂资料按需放入 `references/`、`scripts/`、`assets/`。
3. **交付可信**：YAML 可解析、结构可安装、引用路径存在、无临时文件、版本与说明一致、附带测试 Prompt 与优化说明。

## 1. 何时使用 / 何时不要使用

### 使用本 Skill

当用户提出以下任一意图时使用：

- 创建、新建、生成、封装一个 Skill / 技能包。
- 优化、重构、审计已有 `SKILL.md` 或 `.zip` 技能包。
- 补齐或修复 YAML front matter、description、触发词、排除条件。
- 把 SOP、业务流程、提示词、专家方法论、工作规范沉淀为可安装 Skill。
- 为 SkillHub 发布准备 README、package metadata、质量检查、打包文件。

### 不使用本 Skill

- 用户只是要一次性改写提示词，不需要形成可复用技能。
- 用户只是普通写作、代码开发、数据分析，且没有“沉淀为 Skill”的要求。
- 用户要求安装或执行来源不明、含高风险命令的 Skill；先做安全审计，不直接运行。

## 2. 强制原则

1. **先定边界，再写正文**：如果一个 Skill 同时解决多个不相关任务，拆分或建立任务路由，不把所有内容塞进一个入口。
2. **Description 是触发器**：必须写清“做什么 + 什么时候用 + 典型表达 + 不该用的情况”。避免“帮助处理文档”“提升效率”这类空泛描述。
3. **SKILL.md 只放高频必要信息**：主体建议保持精简；长模板、示例、规范、测试集放入 `references/` 按需读取。
4. **能脚本化就脚本化**：格式校验、目录初始化、打包、静态检查、批量转换等确定性动作，优先放入 `scripts/` 或明确执行校验逻辑。
5. **完成标准可打勾**：每个质量要求必须能被检查，而不是“更专业”“更完整”这类软描述。
6. **文件是权威来源**：优化既有技能包时，先读取当前文件，不依赖记忆中的旧版本；修改后重新验证。
7. **安全优先**：不得生成包含密钥、隐私、恶意命令、绕过权限或破坏性操作的技能包。

## 3. 工作流

### Phase 1 — 需求诊断

收集并确认以下信息；缺失时给出合理默认值并标注假设：

| 问题 | 目的 |
|---|---|
| 这个 Skill 最终帮助用户完成什么交付？ | 定义目标 |
| 用户通常会怎么说来触发它？ | 写 description |
| 哪些场景绝对不该触发？ | 降低误触 |
| 输入材料有哪些？ | 设计前置检查 |
| 输出必须长什么样？ | 设计输出契约 |
| 做到什么程度算完成？ | 设计完成标准 |
| 是否需要脚本、模板、参考资料？ | 设计目录结构 |
| 运行环境和发布目标是什么？ | 适配平台 |

如果用户给的是已有包，先解包审计：读取 `SKILL.md`、README、元数据、`references/`、`scripts/`，列出问题后再优化。

### Phase 2 — 结构设计

按复杂度选择结构：

| 复杂度 | 推荐结构 | 判断标准 |
|---|---|---|
| L1 最小技能 | `SKILL.md` | 单一任务、无外部资料、流程短 |
| L2 标准技能 | `SKILL.md` + `references/` | 有模板、示例、规范、案例 |
| L3 工程化技能 | L2 + `scripts/` | 需要校验、生成、转换、批处理 |
| L4 发布级技能 | L3 + README + metadata + 测试 Prompt | 面向团队/SkillHub 分发 |

默认目录：

```text
skill-name/
├── SKILL.md
├── README.md
├── package.json 或 _meta.json（按平台需要）
├── references/
├── scripts/
└── assets/
```

只创建有实际用途的目录；空目录需要 README 占位说明。

### Phase 3 — 编写或优化 SKILL.md

`SKILL.md` 必须包含：

1. YAML front matter：至少 `name`、`description`；发布级建议补充 `version`、`author`、`tags`。
2. 目标：一句话说明这个 Skill 要交付什么。
3. 使用边界：何时用、何时不用。
4. 输入检查：需要用户提供哪些材料，缺失时如何处理。
5. 工作流：按阶段给出可执行动作和关键决策分支。
6. 输出契约：结构、格式、文件命名、交付方式。
7. 质量门禁：可验证 checklist。
8. 异常处理：缺文件、YAML 错误、引用缺失、打包失败、需求冲突时如何恢复。
9. 资源索引：什么时候读取哪些 `references/` 或脚本。

写法要求：

- 使用动作动词：读取、检查、生成、验证、打包、汇报。
- 对关键规则解释原因，帮助 Agent 在新场景中迁移。
- 给必要自由度：规定目标、约束和验收标准；不要把所有微步骤写死。
- 给正反触发测试 Prompt，尤其是“不应该触发”的反例。

### Phase 4 — 质量验证

交付前执行静态检查：

- YAML front matter 存在，且可被 YAML 解析。
- `name` 使用小写字母、数字、连字符，避免空格和中文。
- `description` 非空、具体，包含触发场景和排除边界；含英文冒号加空格等易破坏 YAML 的内容时使用引号或块标量。
- `SKILL.md` 中引用的本地文件路径存在。
- README、package metadata、`SKILL.md` 的名称和版本一致。
- 无 `.DS_Store`、上传残留、日志、临时文件、密钥文件。
- zip 根目录结构正确：解压后应直接得到技能目录或技能文件集合，不混入无关父目录。

必要时读取 `references/qa-checklist.md` 执行完整门禁；发布级或批量审核任务还应读取 `references/skill-scorecard.md` 进行 100 分制评分。

自动化预检可运行：

```bash
python scripts/validate-skill.py <skill-dir>
python scripts/validate-skill.py --json <skill-dir>
python scripts/score-skill.py <skill-dir>
python scripts/score-skill.py --json <skill-dir>
```

`validate-skill.py` 会检查 YAML front matter、推荐目录、Markdown 本地引用、description 长度、禁用词、临时产物等确定性问题；`--json` 输出可接入 CI、批量审核流水线或质量看板。`score-skill.py` 会按 100 分制给出半自动评分、等级和整改建议。脚本检查通过不代表人工评审通过；仍需结合评分表判断触发边界、可执行性和交付契约。

### Phase 5 — 打包与交付

1. 将最终技能包写入用户指定输出目录。
2. 生成优化说明，列出：解决的问题、设计决策、文件清单、验证结果、后续迭代建议。
3. 重新打包 `.zip`。
4. 汇报任务是否完全完成；如未完成，说明阻塞点和可选方案。

## 4. 输出契约

标准交付至少包含：

```text
<skill-name>.zip
methodology-and-optimization-report.md
optimized/<skill-name>/SKILL.md
optimized/<skill-name>/README.md
```

最终回复中说明：

- 是否完成优化和验证。
- 优化版 zip 链接。
- 方法论报告链接。
- 关键变更摘要。
- 后续可选优化。

## 5. 异常处理

- **缺少输入文件**：停止并请用户上传；不要凭空构造既有包内容。
- **YAML 解析失败**：先修 front matter，再继续正文优化。
- **引用文件缺失**：优先补齐文件；若确实不需要，删除引用。
- **需求过宽**：建议拆分为多个 Skill 或增加任务路由。
- **验证失败**：不要打包发布；列出失败项，修复后重跑验证。
- **工具/权限失败**：停止硬跑，汇报卡点、已尝试内容、失败原因和替代方案。

## 6. 资源索引

- 需要完整创建/优化流程时，读取 `references/workflow.md`。
- 需要发布前门禁时，读取 `references/qa-checklist.md`。
- 需要处理失败和恢复路径时，读取 `references/error-handling.md`。
- 需要保存长期任务进度时，读取 `references/progress-template.md`。
- 需要方法论背景时，读取 `references/methodology.md`。
- 需要对 Skill 质量进行量化评分或批量审核时，读取 `references/skill-scorecard.md`。
- 需要按类型快速起草新 Skill 时，读取 `examples/README.md` 并选择合同审查、数据分析、PPT 生成、知识库、飞书 API、Excel 自动化、云文档编辑、法务合规、多 Agent 协作或浏览器自动化示例。
- 需要复制为独立可安装技能时，读取 `minimal-skills/README.md`，选择最接近的最小包模板后改名扩展。
- 需要执行自动化静态校验时，运行 `scripts/validate-skill.py`；批量审核使用 `--json`。
- 需要执行半自动质量评分时，运行 `scripts/score-skill.py`；批量评分使用 `--json`。
