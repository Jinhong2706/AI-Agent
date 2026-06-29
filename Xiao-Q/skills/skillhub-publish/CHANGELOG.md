# Changelog — skillhub-publish

## [1.6.0] - 2026-05-09

### Added
- **Phase 0 出发前确认（Pre-flight Checklist）** — 审计开始前必须先向用户出示完整"机票"：
  - 列出接下来要做的所有阶段（Phase 1-5 概览）
  - 列出输出成果（发布包位置、描述文本、版本说明）
  - 确认输出位置（默认 `~/Desktop/`，可改）
  - 告知全程约需手动确认 1-2 次
  - 用户明确签字（"确认"/"OK"）后才进入 Phase 1 审计

### Changed
- 工作流从"五阶段"升级为"六阶段"
- SKILL.md / README.md / SPEC.md / DESIGN.md 全线同步

## [1.5.0] - 2026-05-06

### Added
- **Phase 3.5.0 规则自举（AI Bootstrap）** — 首次运行时若未检测到私有规则文件，自动扫描发布副本内容，用 LLM 识别人名/组织/政治触发词等敏感信息，生成脱敏规则供用户确认后保存
- **反馈闭环** — 发布后若收到安全警报，用户告知 skill「XX 文件被报警了」，skill 自动扫描该文件识别触发词并追加到规则库，无需人工记忆敏感词清单

### Changed
- **脱敏规则分层架构** — 敏感词从内置规则中剥离到用户私有路径 `~/.workbuddy/principles/sanitize_rules.yaml`，内置 `references/sanitize_rules.yaml` 只保留通用无害模式
- 原因：skillhub-publish 发布到 SkillHub 时自身不能含敏感词（人名/组织名/政治触发词）
- Phase 3.5 加载逻辑：私有规则优先 → 内置规则兜底
- 更新版本号 1.4.0 → 1.5.0

### Fixed (Round 3 audit)
- 反馈闭环增加独立触发词（文件报警/危害内容/敏感词检查/脱敏规则），支持独立入口
- SPEC.md 降级策略补充 Phase 3.5 场景
- SPEC.md 触发词同步新增反馈闭环入口词

## [1.4.0] - 2026-05-06

### Added
- **Phase 3.5 发布内容脱敏** — 通用脱敏引擎，在生成物料前自动清洗发布副本中的触发词
- `references/sanitize_rules.yaml` — 脱敏规则（v1.5.0 后已剥离敏感词至用户私有路径）
- 技能特有 override 机制：在 `.skillignore` 同级放置 `sanitize_rules_override.yaml` 追加规则
- 脱敏报告：展示每类规则匹配数 + 样例，用户确认

### Changed
- 版本号 1.3.1 → 1.4.0

## [1.3.1] - 2026-05-06

### Fixed
- 删除空目录 references/ / scripts/ / templates/
- 版本号 1.3.0 → 1.3.1

## [1.3.0] - 2026-05-06

### Added
- ❗ Phase 2.5 重写：发布副本创建增加5个子步骤（读取.skillignore→创建副本→处理用户数据→清理缓存→额外清理）
- ❗ Phase 1 审计新增3项检查：用户隐私文件、缓存数据、平台配置文件
- ❗ Phase 3 新增"清理非发布物"节

### Fixed
- 🐛 发布包未排除 `.skillignore`（WorkBuddy 平台配置不应上传）
- 🐛 发布包直接删除 `data/user-profile.md` 而非保留骨架模板
- 🐛 未清理 `data/cache/` 中的历史评分缓存
- 🐛 未按 `.skillignore` 规则自动清理排除项（如 `tests/`）

### Changed
- 🛠 rsync 命令增加 `--exclude='.skillignore' --exclude='.verify_history'`
- 🛠 cp 清理命令增加 `.skillignore` 删除和 `.verify_history` 清理

## [1.2.0] - 2026-05-04

### Fixed
- 审计新增「非发布物检测」P1 检查：隐藏文件、占位文件（`.gitkeep`/`.empty`）、无扩展名文件
- 副本创建阶段新增 `.gitkeep` 自动清理（rsync exclude + cp fallback 双保险）
- 原因：little-writer 发布时 SkillHub 因 `.gitkeep` 文件类型不合规拒绝提交

## [1.1.0] - 2026-05-02

### Added
- **初始发布：** 一键将 WorkBuddy skill 准备好发布到 SkillHub
- 六维审计：文件结构 / Frontmatter / 内容质量 / 版本一致性 / 安全 / 外部依赖
- P0/P1/P2 分级审计报告，P0 不可跳过
- 先议后行：展示报告后与用户讨论确认，确认后才执行修改
- 副本优先：修复在桌面副本上执行，原始文件可选同步
- 自动修复：补文件、改描述、对齐版本，每步确认后执行
- 物料生成：自动生成 README.md + SkillHub 描述文本 + 版本更新说明
- 零发现路由：审计无问题时跳过修复流程，直接生成物料
- 干净打包：创建副本时自动排除 `.git`/`__pycache__`/`.DS_Store` 等垃圾文件
- 纯指令式实现，零外部依赖，不依赖其他 skill
