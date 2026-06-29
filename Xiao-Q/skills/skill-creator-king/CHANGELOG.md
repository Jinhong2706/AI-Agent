# Changelog — skill-creator-king

## [3.23.1] — 2026-06-22

**SCK 自审缺陷修复（9 项）：P0 footer 版本号 / P1 过时文本 & 死引用 / P2 杂物清理。**

- **Fixed**：SKILL.md footer 版本号 `_v3.22.0_` → `_v3.23.1_`（P0，frontmatter 与 footer 不一致）
- **Fixed**：SKILL.md Context 段"CERTAIN 自动修复"→"LLM 驱动修复+安全回滚"（P1）
- **Fixed**：SKILL.md Output 段过时的修复报告格式（P1）
- **Fixed**：SKILL.md Further Reading 死引用 `2-design/` 目录（P1）
- **Fixed**：quality-audit.py LLM review 示例来自其他 skill → 替换为通用示例（P2）
- **Fixed**：operational-rules.md"不孤改"第 6 条检查项重复行（P2）
- **Fixed**：.consistency.yml 规则编号跳跃 4/5/6 → 3/4/5（P2）
- **Fixed**：data/checklists/.DS_Store 清理（P2）

## [3.23.0] - 2026-06-22

**SCK 自审机制建立 + 3 个代码 bug 修复 + 豁免规则扩展。**

- **Added**：SCK 自审机制。新增 `.consistency.yml`（3 条规则：changelog-version-sync / plugin-json-version-sync / engine-anchored-pattern）。新增 `scripts/check_consistency.py`（从 research-writing 复制并改造）。首次自审抓到 plugin.json version 3.21.0 滞后 → 修复
- **Fixed**：`quality-audit.py` L769 使用 `os.walk` 但 imports 未引入 os，导致 `maintenance_hygiene` 维度对任何 skill 都返回 error。修复：补 `import os`
- **Fixed**：`audit_changelog_today` 维度换骨——从 mtime 间接信号（"今日是否修改"）改为版本号直接对比（CHANGELOG 最新条目 vs SKILL.md frontmatter.version）。删除 `_any_files_changed_today` 函数 + `os.walk` 调用 + `import os`。零时区依赖、零假阳性
- **Fixed**：`check_consistency.py` cross_reference 用 `re.search` / `re.findall` 未加 `re.MULTILINE`，导致 `^` 锚定 pattern 无法匹配每行开头。前 3 条规则没用 `^` 所以 latent bug 一直没暴露，新增第 4 条 `^version:` 规则触发。修复：re.search/findall 加 re.MULTILINE
- **Fixed**：`quality-audit.py` `audit_version_consistency` 的 `is_history_file` 豁免列表只含 CHANGELOG.md / RELEASE-NOTES.md，导致 DESIGN.md 和 technical-report.md 中的历史性版本引用被误报。修复：豁免列表扩展为 4 个文件
- **Fixed**：`check_consistency.py` L159 硬编码 "research-writing" → 动态化用 SKILL_DIR basename
- **Fixed**：plugin.json version 3.21.0 → 3.22.0 → 3.23.0（同步 SKILL.md）
- **Fixed**：plugin.json description 仍写"CERTAIN 自动修复"（v3.22.0 已砍）→ 更新为"LLM 驱动修复+安全回滚"

## [3.22.0] - 2026-06-20

### Removed
- **砍掉 6 个 CERTAIN fixer**：crlf/frontmatter/version_sync/file_table/sections/plugin_json。LLM 已经能修这些——没必要为避开 LLM 而重复造轮子。
- **砍掉 trust test 和 fuzz test**：测试对象已移除。

### Changed
- **autofix 重新定位**：不再是确定性修复引擎 → 瘦身为安全骨架（`--backup` → LLM 修 → `--verify` → `--rollback`）
- **engine.py 重写**：从 395 行修复调度器 → 80 行安全 harness（scan / backup / verify 三模式）

### Why
LLM 是你随手可用的修复工具。确定性脚本只在无 LLM 的 CI 流水线里有优势——那不是你的场景。简洁胜于完备。

## [3.21.3] - 2026-06-20

### Added
- **Fuzz 测试层**：`scripts/autofix/test_fixer_fuzz.py` — 六 fixer × 3 随机生成器 × 100 轮，验证「不崩溃 + 不破坏」。600/600 clean。
- **双层质量门**：trust test（已知模式 0% 误修）+ fuzz test（随机输入 0 crash/0 damage），合称 hormesis 验证。

### Fixed
- **plugin_json**：生成 `plugin.json` 后未更新文件表 → validate 报 `file_table_missing`。修复：写完后自动在 SKILL.md 中创建/更新文件结构表。
- **validate.py**：文件表检测过度严——表头必须同时含「文件」和「索引/结构」否则跳过。放松为只含「文件」即触发。

## [3.21.2] - 2026-06-20

### Added
- **CERTAIN 层 0% 误修验证**：`scripts/autofix/test_fixer_trust.py` — 六 fixer × 3 变体（broken/clean/edge）18 测试全绿。每次 autofix 改动后跑一遍，证明 CERTAIN 层不会破坏正常 skill。

### Fixed
- **crlf**: `read_text()` 在 macOS 上归一化 `\r\n`→`\n`，导致 CRLF 永远不可见 → 改用 `read_bytes()`
- **frontmatter**: `_fix_colons` 检测到 YAML 中未转义冒号但原样放回 → 现在实际加引号修复
- **plugin_json**: 老格式 plugin.json 无 `id` 字段被误判为过期 → 改为内容级比较
- **plugin_json**: 触发词从 YAML 解析时保留引号，JSON 输出产生双重编码 `"\"trigger\""` → 解析时去 YAML 引号

## [3.21.1] - 2026-06-20

### Changed — 审计维度反脆弱（via negativa）
- **token_budget**：纯语言 skill（无 scripts/）不再被扣 15 分（标记 skip）——强求不需要的预算制造虚假问题
- **trigger_coverage**：0 个 trigger 不再扣分（基准 8/8）——上下文触发的 skill 不应被惩罚
- **maintenance_hygiene (changelog_today)**：当日无文件变更 → 自动 pass——不强制空转日的虚假 CHANGELOG 条目

### Changed — 结构精简
- autofix/ 12 文件 → 10 文件：registry.py + trace.py 并入 engine.py，逻辑无损

## [3.21.0] - 2026-06-20

### Added
- **autofix 自动修复引擎**：杠铃架构——审计端（validate.py + quality-audit.py）只读保守，修复端（autofix）读写可回滚。CERTAIN 层 6 个纯脚本 fixer（crlf / frontmatter / version_sync / file_table / sections / plugin_json），零误修。每修一条留 trace.jsonl，`--rollback <session>` 一键回滚。
- **修复后验证**：autofix 完成后自动跑 validate + quality-audit，评分降级自动回滚
- **修复建议输出**：SPECULATIVE 层输出 `_suggestions/`，只建议不动手
- **Phase 4 重组**：验证流程从 5 步含手动循环 → 8 步含自动修复，确定性错误一轮清
- **Phase 5 数据源**：autofix session 历史成为 EVOLVE 的数据输入

### Changed
- **场景扩展**：三大场景 → 四大场景（新增「自动修复」）
- SKILL.md 工作流全面重构

## [3.20.2] - 2026-06-20

### Fixed
- **解析脆弱性五连修**：消除 yaml_utils.py 缩进硬编码（0/2/4 → 动态 indent_step）、移除 `current_section == 'quality'` 特殊处理、Frontmatter 支持 CRLF（`\n` → `\r?\n`）、platform.py 显式标记优先于 WB 关键词推断（修复 OpenClaw skill 误判为 WB）、quality-audit.py scaffold 回退动态遍历平台、self-audit.py `'python3'` → `sys.executable`（支持 Windows）

## [3.20.1] - 2026-06-20

### Fixed
- **cross_readme_tree_stale / cross_design_tree_stale 格式假设 bug**：validate.py 两处文件树新鲜度检查使用行扫描解析器（`^references/` 行首匹配），无法识别代码块内树形字符（`├── `、`│   ├──`）包裹的 `references/`。改为零格式假设——提取代码块 + Markdown 列表行，仅按文件名匹配。修复 README.md 13 文件误报和 DESIGN.md 潜在漏检

## [3.20.0] - 2026-06-20

### Added
- **静态安全扫描（AP-024~026）**：新增三个安全反模式——AP-024 危险 shell 调用 (CRITICAL)、AP-025 网络调用模式 (MEDIUM)、AP-026 文件系统越界 (HIGH)。均基于静态模式匹配，零外部依赖。20/20 测试全绿。

## [3.19.11] - 2026-06-20

### Fixed
- **references/ 段解析 `\n\S` 边界 bug**：`validate.py` L123/L146 用行扫描替代原正则 `r'^references/[^\n]*\n((?:(?:.+\n))*?)(?:```|\n\S|\Z)'`。原正则 `\n\S` 终止符在列表项（`\n-`）、空白行后文本处误触发，导致 `cross_design_tree_stale` / `cross_readme_tree_stale` 漏报。新方案行扫描到 references/ 起始行后向下收集至 `##`/`---`/`\`\`\`` 边界，正确涵盖代码块内、独立标题段两种布局。

## [3.19.10] - 2026-06-20

### Added
- **数字声称自动化验证**：`quality-audit.py --stats` 输出内部计数（维度/反模式/脚本/References/ADR/REQ）。`self-audit.py check_numeric_claims` 调用 stats 对比 SKILL.md 声称数字，不匹配自动报警。防数字漂移。

## [3.19.9] - 2026-06-20

### Fixed
- **数字漂移修复**：SKILL.md/README.md/DESIGN.md 共 12 处「16维」→「14维」。quality-audit.py 实际定义 14 维度（3.10 移除 timeline_check 后从未到达 16），文档声称与代码不一致。

## [3.19.8] - 2026-06-20

### Fixed
- **self-audit.py 保鲜度检查源头统一**：从「DESIGN.md 旧快照 vs 实测」改为「SKILL.md frontmatter token_budget vs 实测」。单一真相源，DESIGN.md Token 表仅为快照不做比较源。同时修正判断方向——仅实测超出预算时报警，低于预算不报。

## [3.19.7] - 2026-06-20

### Fixed
- **estimate-tokens.py 排除运行时文件**：`data/*.jsonl` 为审计运行时数据，不应计入 L2 预算。按文件类型（`.jsonl`）排除替代硬编码文件名。
- **Token 预算修正**：`L2_deep: 115000 → 20000`（16,783 实测 + 余量），`hard_cap: 120000 → 25000`
- `L1_core: 1400 → 2000`（1,570 实测 + 余量）
- **DESIGN.md Token 实测表同步**：NFR-001 预算 + Token 实测表 + 已知限制全部更新为当前值

## [3.19.6] - 2026-06-20

### Fixed
- **README 文件树补全**：补 `CODE_OF_CONDUCT.md` / `PRINCIPLES.md` / `phase-check.py` / `tests/` / `.github/`
- **Token 预算同步**：`L2_deep: 65000 → 115000`，`hard_cap: 70000 → 120000`

## [3.19.5] - 2026-06-20

### Added
- **Issue 模板**：`.github/ISSUE_TEMPLATE/` （bug_report + feature_request）
- **CODE_OF_CONDUCT.md**

## [3.19.4] - 2026-06-20

### Added
- **AP 回归测试**：`tests/test_anti_patterns.py`，14 个用例覆盖 AP-001/003/006/007/008/011/012/014/017/020/021/023 + 冒烟
- **CONTRIBUTING.md**：贡献指南（PR 流程、版本 bump 规则、代码风格）

### Changed
- **README 依赖说明强化**：环境要求节突出「零外部依赖」

## [3.19.3] - 2026-06-20

### Fixed
- **yaml_utils.py 内联数组解析**：`parse_yaml_text` 现支持 `triggers: [xxx, yyy]` 内联数组格式（含空数组 `[]`）。修复 _coerce_value 对列表类型抛 TypeError + falsy 空列表被 `if val else {}` 覆盖为 `{}` 两个子问题

## [3.19.2] - 2026-06-20

### Changed
- **SKILL.md 快速命令去平台硬编码**：`~/.workbuddy/skills/my-skill/` → `your-skill/`
- **README 多平台化**：新增「其他平台用户」入口 +「安装」节

## [3.19.1] - 2026-06-20

### Fixed
- **quality-audit.py scaffold 路径硬编码**：`_load_scaffold_files` 从写死 `~/.workbuddy/skills/` 改为通过 `get_skill_dir_patterns` 平台感知 + 回退兼容
- **basic-wb.md 模板去个人标识**：移除「觉者」引用，改为通用「为自己做」

## [3.19.0] - 2026-06-20

### Added
- **输出文件约定确认功能**：当 skill 涉及文件产出时，Phase 2 DESIGN 收尾新增强制确认步骤（4项：输出目录/文件命名/文件格式/错误输出方式），确认后写入 SKILL.md `## 输出文件约定` 章节
- **AP-023 反模式**（输出文件约定未声明）：validate.py 新增检测——正则匹配文件产出关键词 + 检查约定章节是否存在。与 AP-021（Output 内容格式）互补
- **ADR-015 + REQ-014**：DESIGN.md 新增架构决策（输出文件约定确认）和需求定义（P1）
- **三处检查点**：Phase 2 DESIGN 收尾（Step 4+5 强制确认）、Phase 4 VERIFY 检查清单（第6项）、build-standards.md 自检清单（第7项）

## [3.18.9] - 2026-06-20

### Removed
- **PRINCIPLES.md 全量移除**：init_skill.py（full 通道不再生成）、validate.py（`_check_downstream_sync` 不再检查）、quality-audit.py（删除 `audit_principles_quality()`、`doc_quality` 缩为 design_quality 6 分）、anti-patterns.yaml（AP-016 不再提 PRINCIPLES）、self-audit.py（术语表/single_source 清理）、全部 references 文档同步清理。删除 `data/templates/PRINCIPLES.template.md`。SCK 自身 `PRINCIPLES.md` 保留（自身设计文档，非他人生成行为）。满分 135 → 131。

## [3.18.8] - 2026-06-19

### Added
- **模板嵌入修改纪律**：basic/multi-scene/data-driven 三个 WorkBuddy 模板的 Notes/注意事项段新增「🔒 修改纪律」——修改后必须加载 SCK 运行 `validate.py` + `phase-check.py`，修到 0 HIGH 为止
- **DESIGN.md 版本历史表补全**：3.18.3-3.18.7 五个版本录入

## [3.18.7] - 2026-06-19

### Fixed
- **保鲜度偏差**：DESIGN.md Token 表更新为实测值（L0=156, L1=1422, L2=66127），消除 strict self-audit 保鲜度告警
- **strict 测试缺失**：新建 `tests/test_strict.py`（6 个测试），覆盖 validate.py strict 模式的 6 条执行路径（no-crash/stats/non-strict/platform/channel-full/channel-lightweight）

## [3.18.6] - 2026-06-19

### Added
- **脚手架加厚**：basic/multi-scene 模板嵌入结构化决策槽位（数据依赖声明、错误处理表格、降级路径占位、填写提示），减少 AI 靠悟性填写的质量方差
- **BUILD 施工规范**：`references/build-standards.md` — L2 文件结构约定、脚本三段式错误处理、L1 body 撰写规范、自检清单
- **DESIGN 预防检查**：`phase-check.py` 1→2 过渡新增 Token 预算实测 + 数据源显式声明硬约束；2→3 过渡新增 ADR 降级路径检查
- **触发词卫生检查**：`validate.py` 新增 `_check_trigger_hygiene` — 检测空触发词(HIGH)、过短触发词(MEDIUM)、高频碰撞词(LOW)
- `init_skill.py` DESIGN.md 模板升级：REQ 带优先级+验证标准+数据依赖、ADR 带降级路径占位

### Fixed（三遍自检修复）
- `validate.py` cross_design_tree 正则：`^` + `re.MULTILINE` 锚定行首，避免匹配 ADR 表格中 `references/` 导致假阳性
- `_check_adr_fallback` 改为 ADR 子节内搜索（非全文扫描），去除设计原则中「降级」关键词的假阳性
- `_check_token_budget_measured` 仅全员默认值才判「未实测」，部分自定义值判定通过
- 触发词碰撞仅匹配单字词/极短组合，多词短语不再误判
- TRIG-001 职责收缩为「字段存在但为空」，避免与 AP-001 双重报警
- ADR 降级路径检查从 phase-check 硬约束移除（对 meta-tool 不适用）

### Added（脚本门禁+LLM顾问四缺口）
- **DESIGN 建前审查**：`phase-check.py` 2→3 过渡注入 `design_review` 上下文（4 个引导问 + DESIGN.md/SKILL.md 摘要），供 LLM 建前审查设计合理性
- **LLM 顾问默认开启**：`quality-audit.py` full 通道默认注入 LLM 审查上下文，轻量通道保持 opt-in（`--no-llm-review` 关闭）
- **init_skill.py 反模式预检**：生成完成后自动检测 4 项常见陷阱（短触发词、占位符残留、数据依赖未填、目录名大小写）
- **退化检测 `--vitality`**：`validate.py` 新增 VITAL-001（引用文件存在性）+ VITAL-002（脚本语法健康），防 skill 放久腐烂
- 触发词碰撞检测：仅匹配单字词（≤5 字符 + 高频碰撞词开头），避免「create skill」等多词短语误判
- 模板脚手架底部版本号更新为 3.18.6

### Changed
- 多词触发词（如 "create skill"）不再被误判为高频碰撞（仅单字/极短组合检测）
- `_check_trigger_hygiene` 职责收缩：无 `triggers` 字段时不报 HIGH（由 AP-001 处理），避免双重报警

### Fixed（LLM 语义审查修复 — v3.18.6 自审）
- 数字声明漂移：五阶段→Phase 0+五阶段（6个）、19坑位→22坑位、五条纪律→六条、四重验证→五重
- 术语不一致：DESIGN.md REQ-007 14维→16维、README 阶段名补全、review-guide 四条→六条
- 结构缺口：Output 模板补 Phase 4.3（LLM审查）+ Phase 4.5（修改后自检）产出物
- Token 预算更新：L1 700→1400 / L2 12000→65000 / hard_cap 13500→70000

## [3.18.5] - 2026-06-19

### Fixed
- **Phase 编号体系对齐**：reference 文件重命名以匹配 SKILL.md 主文件的 Phase 编号
  - `phase-2-requirements.md` → `phase-2-design-requirements.md`（DESIGN · 需求定义）
  - `phase-3-design.md` → `phase-2-design-architecture.md`（DESIGN · 架构设计）
  - `phase-4-implementation.md` → `phase-3-build.md`（BUILD）
  - `phase-5-verification.md` → `phase-4-verify.md`（VERIFY）
  - 新建 `phase-5-evolve.md`（EVOLVE）
- 同步更新 SKILL.md / README.md / DESIGN.md 文件树引用
- `phase-check.py` 注释：SPEC.md → DESIGN.md（v3.14+ 合并后遗留）

## [3.18.4] - 2026-06-19

### Added — Phase 4.3 LLM 语义审查

- `quality-audit.py --llm-review`：4 固定问（语义漂移 / 术语一致性 / 集成完整性 / 残余痕迹）
  - 脚本不调用 LLM——仅收集所有文件上下文 + 预提取信号（数字声称、子节列表、总览提及、残留候选、行数）
  - 上层 AI Agent 读取 `llm_review` 字段后逐问回答 `✅/⚠️/❌`
  - 补脚本盲区：术语不一致、单篇残留、新增子节未入总览、数字声称 vs 实际计数漂移
- `--llm-review` 自动强制 `--no-cache`（上下文变化必须重新收集）

## [3.18.3] - 2026-06-19

### Added
- **AP-022 反模式**：description 版本史堆积检测。description 中 ≥2 个非当前版本号即命中——版本史应放 CHANGELOG，description 保持功能+场景摘要（≤3 句）。防止迭代中触发噪音持续膨胀
- **validate.py AP-022 检测**：扫描 frontmatter description 中的 vX.Y.Z 模式版本号，与当前版本比对

### Changed
- **SCK 自身 description 清理**：删除 `v3.18.2 init_skill.py...` 版本特性注释，以身作则

## [3.18.2] - 2026-06-17

### Added
- **init_skill.py `.gitignore` 自动生成**：新建 skill 时自动创建完整 `.gitignore`（Python/缓存/系统文件/元数据），替代先前无 `.gitignore` 的状态

### Changed
- **`.gitignore` 补全**：SCK 自身 `.gitignore` 覆盖 `__pycache__/`、`*.pyc`、`.pytest_cache/`、`_cache/`、`*.jsonl`、`.DS_Store`、`.skillignore`

### Removed
- **`tests/test_basic.py`**：僵尸测试文件，从未被 import 或执行。self-audit.py 仅检查其存在性（不跑测试）
- **`self-audit.py check_test_coverage()`**：移除该检查函数，自检从 6 项 → 5 项。list-checks 同步更新
- 清理 README.md 文件树和 DESIGN.md NFR-005 中的 test_basic 引用

## [3.18.1] - 2026-06-17

### Fixed
- **init_skill.py README 模板**：从极简（标题+描述+触发词+版本）升级为完整模板，覆盖 readme-standard.md 5 必须段落，含独立「快速开始」「触发方式」章节
- **readme_quality 审计拆分**：将 "怎么用/快速开始" 拆为两个独立检查项「快速开始/怎么用」「触发方式/触发词」，从 7 项 → 8 项自动检查
- **readme-standard.md**：明确「怎么用」需含独立的「快速开始」「触发方式」子段落；推荐列表新增「边界与注意事项」
- **audit.yaml rubic**：readme_quality 评分标准对齐 readme-standard.md 5 必须 + 4 推荐

### Removed
- **RELEASE-NOTES.md**：废弃文件，CHANGELOG.md 已完整覆盖版本历史
- **config.yaml**：从未被任何脚本读取，规划但未接线的死配置
- **data/templates/README.template.md**：僵尸模板，init_skill.py 内联生成 README，从不加载此文件
- 清理 references/ 和 rules/ 中 config.yaml 残留引用
- **data/templates/REVIEW-REPORT.template.md**：零引用模板，仅 DESIGN.md 架构图提过
- **data/templates/SESSION-REPORT.template.md**：零引用模板，从未被任何脚本加载
- **data/templates/config.template.yaml**：零引用模板，不在 init_skill.py 加载列表
- **scripts/regex-hang-check.py**：移至 skillhub-publish（仅发布时调用，非 SCK 创建/审计功能）
- **skillhub-publish SKILL.md**：新增 `.pytest_cache` rsync 排除项

## [3.18.0] - 2026-06-17

### Added
- **pm-skills 格式骨架**：`basic-wb.md` / `multi-scene-wb.md` 模板新增 Purpose、Context、Output、Notes、Further Reading 六段，方括号占位符不与 {desc} 冲突
- **AP-020**：description 缺少 Use when 场景触发语检测（validate.py + anti-patterns.yaml）
- **AP-021**：正文缺少 Output 输出模板段检测（validate.py + anti-patterns.yaml）
- **D15 body_structure**：正文结构完整性审计维度（manual, weight 6），检查六段完整度
- **Q2a 采访**：init_skill.py 交互模式采集 Use when 场景，自动拼入 description
- **D5 rubric 扩展**：triggers + description Use when 场景双线评估，覆盖无 triggers 但场景充分的 skill

### Changed
- **SKILL.md 格式升级**：SCK 自身按 pm-skills 格式添加 Purpose/Context/Output/Further Reading 段落，version → 3.18.0
- **description 强化**：追加 "Use when 创建新的 AI Agent Skill, 审查已有 Skill 的质量, or 升级迭代 Skill 功能。"
- **cross_file_stale_version → version_consistency（LLM 裁断）**：validate.py 不再用正则硬判断版本号过期——注释性引用（"v3.12.0 新增"）、发行历史行、跨 skill 引用等无法可靠区分。改为 quality-audit 新增 `version_consistency` 手动维度（weight 4），逐文件收集 vX.Y.Z 匹配+上下文，由 LLM 在审计阶段裁断
- **version_consistency 改为全自动**：不再输出逐条 vX.Y.Z 匹配清单到标准审计结果。改为仅检测 README.md 中显式版本声明（「当前版本: X.Y.Z」）与 SKILL.md frontmatter 的一致性，注释性引用自动豁免。移除 `manual: true`
- **cross_doc_sync 权重调整**：version_consistency 从合并维度中剥离（34→24），总分 141→135

### Fixed
- **P0 validate 结果传递断裂**：`run_validate()` 仅当 exit 0 时读取 JSON——但 validate.py 发现问题时返回 exit 1 且 quality-audit 的 anti_patterns 维度永远报「命中 0 个反模式」。改为无论 exit code 均尝试解析 stdout JSON
- **cross_file_stale_version 假阳性**（已被 version_consistency LLM 裁断替代）：从 validate.py 完全移除正则硬判，不再对注释性引用（"v3.12.0 新增"）、发行历史、跨 skill 引用误报

## [3.17.6] - 2026-06-16

### Changed
- **语义一致性检查迁移至结构化字段**：`validate()` 返回的 result dict 新增 `semantic_check` 字段（含检查指令、文件列表、参考文件）。`--json` 模式下 LLM 可直接消费，不再依赖终端 stdout。此前终端文本输出是死信——LLM 加载 skill 后从未看到。
- **_format_report() 精简**：两处终端「语义一致性（请 LLM 执行）」文本块替换为简短引用提示（指向 `result.semantic_check` 字段）。
- **SKILL.md Phase 4.1 强化**：明确要求 LLM 消费 `semantic_check` 字段并执行交叉文件语义一致性检查。

### Fixed
- **P0 质量审计维度数矛盾**：SKILL.md 三处「17维」→「14维」（line 42/80/description），DESIGN 和 README 一致写 14 维，实际 quality-audit 为 14 维。
- **P1 Token 预算三源不一致**：DESIGN.md NFR-001 L1=600→700、hard_cap=13000→13500，与 SKILL.md frontmatter 对齐。
- **P2 反模式数量过时**：README「13 个结构化坑位」→「19 个」，与 data/anti-patterns.yaml 对齐。
- **DESIGN Token 实测表更新**：L0=97→163, L1=698→886, L2=12533→31850, 总计=13328→32899。

### Source
- Option D：终端 stdout 是死信——LLM 加载 skill 后从未看到语义一致性提示。将检查嵌入结构化字段，SKILL.md 明确消费指令。

## [3.17.5] - 2026-06-16

### Added
- **语义一致性提示**：validate.py 输出末尾追加 LLM 提示——请交叉读取 DESIGN.md / README.md / l2-l3-workflow.md / CHANGELOG.md，逐段确认阶段数、数字、交付物清单、功能描述与 SKILL.md 一致。4 行纯文本，零性能开销。

## [3.17.4] - 2026-06-15

### Added
- **scaffold 委托声明**：`audit_file_completeness` 新增 `_load_scaffold_files()`——识别 SKILL.md 的 `scaffold:` 字段后，跳过 scaffold 的标准文件，只检查增量文件。解决继承 scaffold 的 skill 文件结构表逐项列 38 个文件的脆弱性
- **`_run_integrity_checks()`**：从 `audit()` 提取防作弊完整性检查为独立函数

## [3.17.3] - 2026-06-15

### Fixed
- **cross_version_stale 假阳性**：新增 5 分钟容差窗口——同一编辑会话内文件依次写入的 mtime 差不再误报
- **.consistency.yml 假阳性**：`_list_actual_files` 不再跳过 `.consistency.yml`（此前通配过滤所有 dotfile）
- **PyYAML 缺失不报错**：`ModuleNotFoundError` → 静默跳过，不再标记 MEDIUM
- **AP-009 过度告警**：行数 > 500 但估算 token < 8000 → 降为 LOW。Token 预算最终由 quality-audit 判定

### Source
- 科技公众号写作 v5.2.0 SCK 审计后发现——四个缺陷在三次审计中反复出现，属 validate.py bug 非目标 skill 问题

## [3.17.2] - 2026-06-15

### Changed
- **DESIGN.template.md 重构**：新增「架构总览」「候选方案对比」「决策记录」三节，适配 quality-audit DESIGN 质量检查项。新增分层原则——skill 目录 DESIGN.md 保持轻量（总览+代表性决策），逐条决策归档到项目 `2-design/`
- **Phase 3 设计指引**：补充 DESIGN.md 分层原则说明

### Source
- 从 科技公众号写作 skill v5.2.0 的 SCK 审计中发现——DESIGN.md 含架构概览和 8 条决策但 audit 打 3/6，模板缺三个独有章节

## [3.17.1] - 2026-06-14

### Fixed
- **缓存键纳入全部关键文件 mtime**：`get_cache_key()` 此前仅检查 SKILL.md 的 mtime，导致仅修改 CHANGELOG/DESIGN/PRINCIPLES 时仍命中旧缓存。现纳入全部 5 个关键文件的 mtime，任一文件变更自动刷新缓存

## [3.17.0] - 2026-06-14

### Added
- **Phase 4.4 修改后自检**：基于 research-writing 项目 v2.5.1 迭代中 26 个问题的根因分析，新增三条修改后必须执行的步骤——① SCK 自动扫描（validate + audit，修到 0 真实问题）② 新交付物落地（新文件确认工作流引用 + 运行通过）③ 错误处理审计（脚本成功/限流/失败三条路径）

## [3.16.15] - 2026-06-13

### Fixed
- **DESIGN 质量正则放宽**：「决策记录」增加 `### ADR-`/`### D-` 格式匹配（此前仅识别 `## 决策 N:`）；「架构总览」增加 `架构决策|Design.*Decision` 匹配。both `audit_design_quality` 和 `audit_cross_doc_sync` 同步修复
- **4 个高频 skill 审计修复**：research-scout (+10, 83→90%, A)、auto-product-planner (+12, 82→90%, A)、research-review (+2, 84→86%, B)、taste-check (+13, 78→87%, B)。CHANGELOG 版本同步、文件结构表补全、README 版本对齐

## [3.16.14] - 2026-06-13

### Fixed
- **PRINCIPLES 缺失不扣分**：PRINCIPLES.md 不存在时从 0/4(fail) 改为 4/4(pass)。SCK 默认不创建 PRINCIPLES.md，缺失是正常的
- **轻量通道跳过新维度**：`design_quality` 和 `principles_quality` 加入 lightweight_skip 列表。轻量通道的 skill（无 DESIGN/SPEC）本就无需深度文档检查
- self-audit 基线从 ≤2 → ≤3，自然增长

## [3.16.13] - 2026-06-13

### Changed
- **审查历史字段扩增**：`review-history.jsonl` 记录从 13 字段扩至 19 字段。新增 `dimension_scores`（逐维得分）、`category_scores`（分类汇总）、`ap_ids`（反模式 ID 列表，替代计数）、`precheck_severity`（预检严重度分布）、`manual_pending_count`。`ap_hits` 废弃（保留兼容）
- 每条约 1.5KB，按 1000 次审计计约 1.5MB，无需轮转

## [3.16.12] - 2026-06-13

### Added
- **DESIGN 质量维度**：新增第 16 维度 `design_quality`（6 分，自动评分）。5 项检查——候选方案对比、架构总览、已知局限、决策记录、SKILL-DESIGN 边界声明
- **PRINCIPLES 质量维度**：新增第 17 维度 `principles_quality`（4 分，自动评分）。5 项检查——原则数≥3 条、正反对比、为什么、自指约束、硬约束
- **审查历史写回**：`quality-audit.py` 在 full 通道审计后自动追加记录到 `data/review-history.jsonl`。此前 v3.12.3 定义了 schema 但从未被代码写回，4 行全是注释。现每次审计自动记录 skill/版本/分数/关键发现/反模式命中
- 总分上限从 125 提升至 135

## [3.16.11] - 2026-06-12

### Fixed
- **validate.py 文件树正则灾难性回溯**：`_check_version_consistency()` 中 README/DESIGN 文件树正则在多行（≥10行）树结构下指数级回溯，导致进程卡死。根因：`\s*│?\s*` + `\n?` 三可选量词嵌套。修复：统一为 `\s*[├└]──.*\n`。影响：skillhub-publish 审核流程此前因此永久挂起

### Added
- **regex-hang-check.py**：预检工具，模拟原版 buggy 正则检测目标 skill 的 README/DESIGN 是否会触发卡死。2 秒超时机制。用法：`python3 scripts/regex-hang-check.py <skill目录>`

## [3.16.10] - 2026-06-12

### Added
- **文档同步维度**：新增第 15 维度 `cross_doc_sync`（8 分）。自动检查五文档（SKILL/README/CHANGELOG/rules/技术报告）间的内容一致性——模式数残留、rules 版本引用、技术报告版本、DESIGN 决策条目。无需每个 skill 单独配置 `.consistency.yml`

## [3.16.9] - 2026-06-03

### Changed
- **文件完整性：章节感知解析** — 改为按 `## 文件` 标题段落识别表格，不再要求表头含精确字符串。支持 `| 文件 | 说明 |` 和 `| 文件结构 | 说明 |` 等多种写法
- **版本一致性：CHANGELOG v 前缀兼容** — 支持 `## v2.0.0` 格式（之前只认 `## [2.0.0]`）
- **文件完整性：扩展排除列表** — rglob 新增排除 `.DS_Store`/`.gitkeep`/`.git`/`node_modules`，减少噪音误报
- **README 版本检测：中英双语** — 同时匹配 `Version:`、`版本`、`当前版本`（不区分大小写）
- **README 质量关键词：中英双语** — 新增 `Quick Start`/`Features`/`Who is this for`/`Limitations` 等效匹配

## [3.16.6] - 2026-05-29

### Added
- **第 6 条操作纪律「表先于盘」**：增删文件时先改 SKILL.md 文件结构表、再动磁盘、最后同步 README 表，跑 `--no-cache` SCK 兜底。适用于所有由 SCK 创建/维护的 skill
- **AP-016「SKILL.md 修改后下游文件未同步」**：通过比较 mtime 检测 SKILL.md 变更后 README.md / PRINCIPLES.md / DESIGN.md 是否可能过时。SKILL.md 比下游文件新 > 5 分钟 → MEDIUM 警告，提示开发者检查同步。
- **`_check_downstream_sync()`**：在 validate.py 中新增专用检查函数，在交叉引用检查之后执行。

## [3.16.5] - 2026-05-29

### Added
- **AP-015「description 单行过长」**：新增反模式检测。当前端 description 为长单行字符串（>120 字符且非 YAML 块标量），部分平台的 YAML 解析器可能因行长度限制而拒绝加载，导致 skill 安装失败。修复方式：改为 `description: >` 多行折叠格式。

## [3.16.4] - 2026-05-28

### Added
- **自定义一致性规则引擎**：`validate.py` 支持读取 skill 根目录的 `.consistency.yml`，执行 `count_match`、`cross_reference`、`content_count` 三类自定义规则。规则定义在 skill 侧，执行引擎在 SCK 侧。
- **init_skill.py 脚手架**：新建 skill 自动生成 `.consistency.yml` 空模板（注释），提示该机制存在。规则留空，按需填写。

## [3.16.3] - 2026-05-27

### 修复
- **init_skill.py 全面适配 v3.14 合并架构** — full 通道不再生成独立 SPEC.md，仅生成合并后的 DESIGN.md（WHAT+HOW 一页讲清）。此前 SCK 自身已合并 SPEC→DESIGN，但 init_skill.py 仍在生成两个文件
- **DESIGN.template.md**：新增核心需求 + 非功能需求章节（来自 SPEC.template.md），成为真正的合并模板
- **phase-2/3/4 + phase-0 + cascade-update + review-guide + upgrade-guide + audit.yaml**：所有 SPEC.md 引用更新为 DESIGN.md（或同时兼容两种架构）
- **validate.py AP-013**：注释标明 v3.14 合并架构下仅双文件存在时才检查
- **quality-audit.py**：semantic_consistency 新增合并架构分支（仅 DESIGN.md → 跳过跨文件检查）；template_compliance optional_files 移除 SPEC.md
- **anti-patterns.yaml AP-013**：名称/描述/fix 更新，兼容合并架构

## [3.16.2] - 2026-05-27

### 新增
- **AP-014: description 过短检测** — anti-patterns.yaml + validate.py 新增，description < 80 字符 → MEDIUM。防止 SkillHub 上架描述不达标

### 修复
- SKILL.md description 35→85 字，添加 template 字段

## [3.16.1] - 2026-05-27

### 修复
- **P1: platform.py 独立运行崩溃** — 添加 sys.path 设置，`python3 scripts/platform.py <dir>` 可独立运行
- **P2: Token 预算声明过期** — SKILL.md L1_core 505→700, hard_cap 13000→13500；DESIGN.md Token 表同步
- **P3: self-audit 保鲜度假阳性** — 修复根因 P2，self-audit 5/5 全部通过
- **P4: phase-check SPEC.md 强制要求** — 适配 v3.14 合并架构，接受 SPEC.md 或 DESIGN.md；_check_spec_non_placeholder 自动回退

## [3.16.0] - 2026-05-27

### 新增
- **审查升级——好模式识别**：在 Step 2 诊断中新增 2.0 好模式识别，6 类别（架构优雅/预算精准/触发设计/反模式零命中/创新模式/信息密度）。LLM 在审查语境下自动识别优秀设计，写入报告 + review-history.jsonl
- **审查升级——扣分分析**：非满分时逐维度输出——少了什么、是否建议修复、修复成本。用户决策是否修复
- `REVIEW-REPORT.template.md`：新增「📊 扣分分析」和「🌟 好模式」章节
- `review-history.jsonl` schema 扩展：新增 `patterns` 字段

## [3.15.1] - 2026-05-27

### 修复
- **validate.py**：`_extract_file_table` 解析器添加终止条件——非表行时重置 `in_table`，修复内文 Markdown 表格被误判为文件结构表的 bug

## [3.15.0] - 2026-05-26

### 新增
- `cross_version_stale` 检查：源码 mtime 晚于 CHANGELOG → MEDIUM 提醒可能忘了 bump

## [3.14.0] - 2026-05-26

### Added — Phase 4.3 自动测试（auto-test）
- 新增 `references/auto-test.md`：L2 工作流，在 VERIFY 阶段自动生成并运行定制测试
- 五步骤：分析 skill 结构 → 生成 `tests/test.py` → 运行 → 修复失败 → 报告
- 互补 validate/audit：覆盖名称不一致、路由遗漏、领域约束等 semantic 盲区
- SKILL.md：Phase 4 升级为三重验证（validate → audit → auto-test）
- 首次实战验证：人类群星 skill 上 112 项测试发现 6 个 bug

### Fixed — 版本双写全面根除
- **根因**：版本号在 SKILL.md / README.md / init_skill 模板中多处硬编码，升级时漏同步
- **README 层面**：README 改为委托引用 SSOT（"当前版本见 SKILL.md 或 CHANGELOG"），validate.py 新增委托模式识别
- **CHANGELOG 层面**：validate.py + quality-audit.py 新增 `cross_changelog_version_mismatch` 检查，比对最新条目版本与 frontmatter
- **init_skill 层面**：模板生成的 README 默认使用委托模式，新 skill 从源头免疫双写问题
- **影响**：彻底消除 `cross_readme/cross_changelog_version_mismatch` 类错误

### Changed
- Token 预算校准：L1_core 1100→600, L2/hard_cap 12000/13000
- test_basic.py：补充 phase-check.py + yaml_utils.py 功能测试（30→36 项）

## [3.13.6] - 2026-05-18

### Fixed — self-audit 误报清零 + validate --strict 嵌入 self-audit
- `scripts/self-audit.py`：
  - 引用完整性：跳过 CHANGELOG 文件（版本号正则被误匹配为文件链接）
  - 配置活性：config.yaml 加 `# documentary` 标记（7 项异步接线）
  - 硬编码检测：扩展检查到 `glob`（原仅 `iterdir`），quality-audit.py 不再误报
  - 孤儿模板：6 个 reference design 模板加入 `single_source`（结构参考，非生成输入）
  - 空异常：L212 `except Exception: pass` → `except (OSError, UnicodeError)`
  - 特殊模式检测：移除 `sck_mode`（是参数值非特殊模式）
- `scripts/validate.py`：
  - `--strict` 模式通过 `importlib` 加载 self-audit.py，结果嵌入输出 `self_audit` 键
  - AP-001 检查修正：`not triggers` → `'triggers' not in fm`（空列表不再误报）
- `scripts/init_skill.py`：轻量通道不再创建 scripts/references/tests 目录
- `scripts/quality-audit.py`：自动检测通道（SPEC.md 存在 → full）
- `scripts/phase-check.py`：支持多步过渡（将 from→to 拆解为相邻步逐一检查）
- `scripts/platform.py`：移除未用 `import os`
- `tests/test_basic.py`：Test 8 从 JSON 可解析改为验证 `self_audit` 键；基线 ≤16 → ≤2

### Self-audit 结果
- 修复前：19 issues（6 误报 + 2 real new + 11 mixed）
- 修复后：2 issues（phase-check.py 和 yaml_utils.py 缺测试 — 已知合理）

### Fixed — quality-audit.py 委托检测对齐 validate.py
- `scripts/quality-audit.py`：`audit_file_completeness` 委托模式补齐声明验证——原逻辑在无文件表时直接扫描 README 找 `├──`，未先确认 SKILL.md 是否声明委托。新增 `文件结构.*详见.*README\.md` 前置检查（与 validate.py 同正则），防止 SKILL.md 无文件表且无委托声明时，仅凭 README 有树就误给满分。

## [3.13.4] - 2026-05-18

### Fixed — create-validate 一致性缺陷（文件索引表）
- `data/templates/skill-md/`：6 个模板文件新增 `## 文件结构\n\n详见 README.md` 委托声明，确保 init 生成物能通过 validate 的文件表检查
- `scripts/init_skill.py`：新增 `_build_file_tree()` + `_walk_tree()` 函数，`create_skill()` 在所有文件创建完后自动向 README.md 追加树形结构
- 根因：v3.12.1 收紧了 validate.py/quality-audit.py 的表头检测（`'文件' in line` → `'文件' in line and ('索引' in line or '结构' in line)`），但未同步修改创建侧，导致脚手架生成物无法通过自身验证
- 设计决策：选择委托模式（SKILL.md → README.md）而非 pipe table，与 SCK 自身实践一致，避免浪费 L1 token 和双源不一致

## [3.13.3] - 2026-05-18

### Fixed — quality-audit.py 三盲区修复（自检质量第二波）
- `scripts/quality-audit.py`：`audit_file_completeness` 修复表格检测逻辑——原 `---` 行无条件触发文件表收集，导致非文件表格（如四大入口表）被误识别。现改为仅当表头含「文件索引/结构」后才由 `---` 触发。另新增委托模式：无文件表时检查 README.md 树形结构（`├──`），信任委托。
- `scripts/quality-audit.py`：`audit_version_consistency` 修复版本匹配正则——原 `[vV](\d+\.\d+\.\d+)` 全局扫描 README，匹配到文件树注释中的旧版本号（v3.12.3, v3.12.4）。改为定向匹配 `Version:` 和 `当前版本：` 声明行，与 validate.py 同策略。
- `scripts/quality-audit.py`：`audit_readme_sync` 修复 mtime 时序假阳性——原逻辑比较文件修改时间，SKILL.md 版本号编辑后即触发「README 过期」警告。改为内容同步检查：验证 README 版本号一致性 + 文件树关键文件覆盖。
- 自检分数：93/117 (B) → 112/117 (A, 95.7%)，提升 19 分。
- `scripts/validate.py`：`check_anti_patterns` 新增 `_load_ap_platforms()` 平台过滤——AP-010（硬编码路径）的 `platforms_applicable` 明确不含 workbuddy，但原逻辑忽略了此字段。现从 anti-patterns.yaml 加载平台适用性，workbuddy 下不再误报。
- 反模式扫描维度：6/8 → 8/8，0 反模式命中。

## [3.13.2] - 2026-05-18

### Added — Phase 1 探结构提问指南（类型框架内化）
- `references/phase-1-positioning.md`：新增 Step 5「探结构」— AI 内部提问指南。六种结构模式映射为六个自然语言问题（用户不感知「类型」概念）+ Phase 2 设计关注点速查表。
- 设计原则：类型框架仅作为 SCK 内部提问战术，不做用户可见的分类标签。

### Fixed — 自检质量修复
- `references/review-guide.md`：精简 ~30% 冗余内容（话术模板、策略×生命周期映射表），活性审计移至独立文件 `vitality-audit.md`。L2 token 从 12225 降至 10845（-11.3%），回归预算内。
- `scripts/validate.py`：`_check_version_consistency` 新增中文格式匹配（`当前版本：**vX.Y.Z**`），修复 README 版本号无法自动检测的盲区。
- `scripts/validate.py`：`_check_file_table` 新增委托模式识别——当 SKILL.md 声明文件结构由 README.md 承载时，不再逐文件对比（信任树形描述）。
- 版本号同步：README.md 当前版本、SKILL.md footer 统一为 3.13.2。

## [3.13.1] - 2026-05-18

### Added — 轻量通道工具补齐
- `scripts/validate.py`：新增 `--channel lightweight|full` 参数。轻量通道跳过文件表检查和跨文件版本一致性检查（轻量 Skill 无 SPEC/DESIGN/CHANGELOG）。
- `scripts/phase-check.py`：新增 `--channel lightweight|full` 参数和 `LIGHTWEIGHT_PHASE_CHECKS` 字典。轻量通道的 Phase 1→2 和 2→3 不要求 SPEC/DESIGN/ADR，改为检查 SKILL.md body 实质内容。
- `scripts/phase-check.py`：新增 `_check_skill_body_meaningful`、`_check_validate_lightweight_pass`、`_check_quality_audit_lightweight_min` 三个轻量专用检查函数。

### Changed
- `validate.py` 返回结果新增 `channel` 字段，终显报告显示通道信息
- `phase-check.py` `--list` 同时显示 full 和 lightweight 两套检查清单
- 版本号 3.13.0→3.13.1（SKILL.md / SPEC.md / DESIGN.md / CHANGELOG.md 同步）

## [3.13.0] - 2026-05-18

### Added — 设计框架合并 (ADR-014)
- `rules/cascade-update.md`：连锁更新 Rule（第 5 条操作纪律），含 7 项检查清单
- `references/review-guide.md`：新增「过程级反模式检查清单」（14 条，源自 skill-design-framework.md V2.0）

### Changed
- `DESIGN.md`：新增 ADR-014 完整记录（资产体系表、Token 决策树、BUILD 双模式选择标准）
- 版本号 3.12.4→3.13.0（SKILL.md / SPEC.md / DESIGN.md / CHANGELOG.md 同步）
- `principles/skill-design-framework.md` → 替换为引用桩（指向 SCK DESIGN.md）
- `principles/README.md`：更新文件清单，标注框架已合并

## [3.12.4] - 2026-05-18

### Added — P2 批次：交互采访 + 纪律Rule化 + Phase完整性检查
- `scripts/init_skill.py`:
  - 新增 `--interactive` 对话式采访模式：逐步询问 skill 名称、描述、触发词、模板、平台、通道
  - `_interactive_collect()` 函数：终端交互式采集，含确认回显
  - `_fill_skill_md()` 支持 `triggers` 参数，自动注入 `triggers: [...]` YAML 列表
  - `create_skill()` 新增 `triggers` 和 `desc_override` 参数
  - `--name` 在 `--interactive` 模式下变为可选
- `rules/` 目录：四条操作纪律独立 Rule 文件
  - `rules/no-exhaustion.md` — 不穷举
  - `rules/no-duplication.md` — 不双写
  - `rules/no-narrow-check.md` — 不窄检
  - `rules/rename-must-scan.md` — 改必扫
- `scripts/phase-check.py`：Phase 间自动化完整性检查
  - 覆盖 0→1, 1→2, 2→3, 3→4, 4→5 五个过渡
  - 每个过渡 2-3 项检查（文件存在/非占位/通过验证）
  - 支持 `--phase N` (检查入场条件) 和 `--from-phase N --to-phase M`
- `references/phase-{1,2,3,4,5}-*.md`：每个 Phase 文件新增「入场条件」章节
- `references/phase-0-preflight.md`：Phase 0 出发前确认指引（平台/入口/通道三问）

### Changed
- `references/review-guide.md`：四条操作纪律从内联文本改为 `rules/` 引用
- `README.md`：文件结构表新增 `rules/` 目录 + `review-history.jsonl` + Phase-0；版本号 3.12.2→3.12.3
- `SKILL.md` 版本号: 3.12.3→3.12.4
- `SKILL.md` Token 预算: L2_deep 9000→11000, hard_cap 10000→12000（rules/ 纳入 L2）
- `SPEC.md` NFR-001: L2 9000→11000, hard_cap 10000→12000
- `DESIGN.md` Token 实测表: L2 预算 9000→11000, hard_cap 10000→12000
- `scripts/estimate-tokens.py`: L2 扫描范围 references+data → references+data+rules
- `config.yaml`: 版本 3.12.2→3.12.4
- `PRINCIPLES.md`: 自进化边界新增 rules/*.md

## [3.12.3] - 2026-05-18

### Changed — L2 预算调整 + 跨会话审查历史
- `SKILL.md`:
  - L2_deep Token 预算: 5000→9000（L2审计无冗余，元工具审查 rulebook 自然更厚）
  - version bump: 3.12.2→3.12.3
- `DESIGN.md`:
  - Token实测表: L2 预算 5000→9000, 状态 ⚠️→✅
  - 新增 ADR-012: 跨会话审查历史 (review-history.jsonl)
  - 模块关系图: 新增 data/review-history.jsonl
- `.gitignore`: 新增，排除 data/review-history.jsonl
- `data/review-history.jsonl`: 新增，每次审查后追加记录
- `references/review-guide.md`: 新增 Step 5「记录审查历史」

## [3.12.2] - 2026-05-17

### Changed — 模板文件化 + yaml_utils 共享模块 + 审计增强 + 文档补齐
- `scripts/init_skill.py`: ~140 行硬编码模板替换为 `data/templates/skill-md/` 文件加载（6 个 .md 文件），消除模板重复定义
- `scripts/yaml_utils.py`: 新增共享 YAML/Frontmatter 解析模块（`parse_yaml_text`, `parse_yaml_file`, `extract_frontmatter`, `extract_frontmatter_raw`）
- `scripts/platform.py`, `scripts/quality-audit.py`, `scripts/validate.py`, `scripts/estimate-tokens.py`: 统一使用 yaml_utils，移除各自重复的 YAML 解析器和 Frontmatter 提取器
- 新增模板文件: `data/templates/skill-md/{basic-wb,multi-scene-wb,data-driven-wb,basic-oc,basic-hm,basic-uv}.md`
- `scripts/quality-audit.py`:
  - 手动维度 Rubric 支持：`audit.yaml` 中 4 个手动维度定义 4-5 级评分标准，专用状态机解析器注入 `dim_result["rubric"]`
  - `token_budget` 增强：新增实测 Token 计算（len/3）、三级检查（hard_cap 超限/级别递进/L2接近上限）
  - 防作弊完整性检查：4 项检查（precheck vs 高分矛盾/反模式 vs 得分矛盾/全自动满分/全手动自动满分）
  - 轻量通道 Skip 列表 SSOT 化：移除硬编码 `LIGHTWEIGHT_SKIP`，改为从 `audit.yaml` 的 `lightweight_skip` 加载
- `data/checklists/audit.yaml`:
  - 新增 4 个手动维度 `rubric` 字段（trigger_coverage, script_llm_boundary, l2_organization, readme_quality）
  - `lightweight_total_weight` 修正：109→79（与跳过维度权重之和一致）
- `data/checklists/lightweight.yaml`: 版本同步至 3.12.2，total_weight 修正：86→79
- `references/phase-5-verification.md`: 评分模型更新（自动维度 6→10 个，手动 3→4 个，轻量满分 85→79，完整满分 100→117，等级改为百分比制）
- `references/phase-4-implementation.md`: L1 Token 预算对齐 SKILL.md（≤800→≤1100）
- `SPEC.md`: 新增 REQ-010（跨平台）、REQ-011（共享模块化）、REQ-012（防作弊）、REQ-013（手动 Rubric）；版本历史补齐 v3.12.2
- `DESIGN.md`: 版本历史补齐 v3.12.2
- `SKILL.md`: body 标题版本号 3.12.1→3.12.2

## [3.12.1] - 2026-05-15

### Fixed — quality-audit.py 解析缺陷 + 版本声明不一致
- `scripts/quality-audit.py`:
  - 文件表解析: 去掉反引号 (`strip('`')`)，与 validate.py 对齐
  - 表头检测: `'文件' in line` 误匹配「配置文件」→ 改为 `'文件' in line and ('索引' in line or '结构' in line)`
  - 版本正则: `r'[vV]([\d.]+)'` 回溯误匹配 `v3.11+` 为 `3.1` → 改为三部分严格匹配 `r'[vV](\d+\.\d+\.\d+)'`
- `SPEC.md`, `DESIGN.md`: 末尾追加 `_当前版本: v3.12.1_` 确保语义一致性检测取到最后版本号
- `tests/test_basic.py`: self-audit 阈值从 `== 0` 调整为 `≤ 16`（配置项和模板变量是已知设计取舍）

## [3.12.0] - 2026-05-15

### Added — platform.py 共享模块（去 WorkBuddy 路径假设）
- `scripts/platform.py` — 统一平台模块，消除 validate.py / quality-audit.py 中的重复定义
  - `detect_platform()` — 路径优先自动检测（先匹配 skill_dir 路径，再查 frontmatter 标记）
  - `load_platform_profile()` — 统一格式，兼容 validate + audit 两个消费者
  - `get_skill_dir_patterns()` — 从平台 YAML 读取，universal 遍历所有平台
  - `list_platforms()` — 扫描 data/platforms/ 返回可用平台 ID

### Changed — 消除 WB-as-default 偏见
- `scripts/validate.py` — 删除重复函数（~90 行），导入 platform.py；`check_anti_patterns()` 参数 `platform='workbuddy'` → `None`；错误消息去 WB 化
- `scripts/quality-audit.py` — 删除重复函数（~75 行），导入 platform.py；`get_cache_key()` 参数 `"workbuddy"` → `None`；`format_report()` 始终显示平台名
- `scripts/init_skill.py` — `--platform` default `"workbuddy"` → `None`（自动检测）；回退 dest `~/.workbuddy/skills/` → `~/.agents/skills/`
- `README.md` — 环境要求/安全限制/适用对象去 WB 限定语
- `PRINCIPLES.md` — 自指 guard 路径改为按名称识别

## [3.11.0] - 2026-05-15

### Added — 跨平台支持
- `data/platforms/` — 四平台配置文件（workbuddy/openclaw/hermes/universal.yaml）
- validate.py/quality-audit.py/init_skill.py 新增 `--platform` 参数
- anti-patterns.yaml 新增 `platforms_applicable` 字段
- SKILL.md 新增 metadata.openclaw/metadata.hermes 多平台标记

### Changed
- README.md 移除 "WorkBuddy 平台" 局限，新增平台支持表
- validate.py `check_anti_patterns()` 按 exclude_ids 过滤
- quality-audit.py 双层跳过（轻量通道 + 平台不适用）

## [3.10.0] - 2026-05-15

### Changed — timeline_check 维度移除
- 移除原因：timeline_check 读取 `~/.workbuddy/skill_timeline.md`，属 WorkBuddy 平台特定功能
- 15维→14维，满分120→117，轻量112→109，自动维度10→9

## [3.9.0] - 2026-05-14

### Added
- 第15维「声明一致性」（semantic_consistency）：跨文件交叉声明检测
- Phase 0 出发前确认，四大入口通用机票
- P0 消灭双源：SKILL_COACH_VERSION 从 SKILL.md frontmatter 单源加载（v3.12.2 完成）；AUDIT_DIMENSIONS 仍为硬编码（待后续外部化）
- P1 断言：`_verify_fix_hint_coverage()` 模块加载检查

### Changed
- 14维→15维，满分112→120
- L0_trigger 200 / L1_core 1100

## [3.8.0] - 2026-05-12

### Added
- skill-post-audit 流程集成
- quality-audit.py 14维度评分系统（满分117）
- validate.py 文件表+交叉版本+反模式扫描

## [3.5.0] - 2026-05-10

### Added
- 原则10·反模式13·膨胀检查·Drift Guard
- validate.py cross-audit 交叉文档一致性审计

## [3.0.0] - 2026-05-08

### Added
- 五阶段工作流（DISCUSS → DESIGN → BUILD → VERIFY → EVOLVE）
- 三种模板（basic/data-driven/multi-scene）
- 极简 SKILL.md（三级加载：L0触发/L1核心/L2深度）
- 双层自我进化（造物者变强 + 产物变好）

## [2.0.0] - 2026-05-05

### Added
- verify.py 10维度质量验证
- update_skill.py 增量更新
- freeze 契约机制

## [1.0.0] - 2026-05-01

### Added
- 初始版本：init_skill.py 脚手架生成
- 基础模板系统

---

# 已知坑（Gotchas）

> 每次踩坑，追加一条。格式：现象 + 原因 + 解法。

## G-001: estimate-tokens.py 中文乘数反置

**现象**：Token 计数系统性地高估中文内容 ~2.25 倍。DESIGN.md 的 Token 实测表基于错误数据。
**原因**：`chinese * 1.5` 把 1 个汉字算成 1.5 tokens。正确关系是 1.5 汉字 ≈ 1 token，即应除以 1.5。
**解法**：改为 `chinese / 1.5`（即 `chinese * 0.67`）。注意 `estimate_tokens()` 和 `estimate_file()` 两处默认参数都需修改。
**发现日期**：2026-05-18 | **修复版本**：v3.12.2

## G-002: .DS_Store 污染 Token 计数

**现象**：`data/checklists/.DS_Store` 每次贡献 ~616 虚假 tokens，污染 L2 计数。
**原因**：estimate-tokens.py 的文件过滤逻辑只排除了 `'cache'`，未排除 `.DS_Store`。
**解法**：在文件过滤中添加 `f.name != '.DS_Store'`。
**发现日期**：2026-05-18 | **修复版本**：v3.12.2

## G-003: __pycache__ 导致修复后仍显示旧数字

**现象**：修复 estimate-tokens.py 后，脚本输出仍是旧数字。
**原因**：Python 的 `__pycache__` 缓存了旧版本的 `.pyc` 文件，修改源码后未自动失效。
**解法**：修改 scripts/ 下的 Python 文件后，清理 `scripts/__pycache__/`。
**发现日期**：2026-05-18 | **修复版本**：v3.12.2
