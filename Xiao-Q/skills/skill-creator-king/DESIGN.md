# DESIGN.md — skill-creator-king

> 需求规格 + 架构决策记录。WHAT（做什么）和 HOW（怎么做）一页讲清。

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **3.23.1** | **2026-06-22** | **SCK 自审缺陷修复（9 项）：P0 footer 版本号 / P1 过时文本 & 死引用 / P2 副本清理** |
| **3.23.0** | **2026-06-22** | **SCK 自审机制建立：新增 .consistency.yml（3 规则）+ check_consistency.py。3 个代码 bug 修复（os 未 import / audit_changelog_today mtime→版本号换骨 / check_consistency.py re.MULTILINE 缺失）。豁免列表扩展（+DESIGN.md/technical-report.md）。plugin.json version/description 同步** |
| **3.22.0** | **2026-06-20** | **autofix 瘦身为安全骨架：砍 fixers + tests，保留 backup/verify/rollback。定位从「确定性修复引擎」转为「LLM修复安全网」。via negativa：token_budget 纯语言 skill 不扣分、trigger_coverage 0 trigger→8/8 基准、maintenance_hygiene 无变更日免检** |
| **3.21.3** | **2026-06-20** | **Hormesis fuzz 测试（600/600 clean）+ fixer trust 验证（18/18）。修复 4 个潜伏 bug（crlf 归一化、frontmatter 空修、plugin_json 比较+双编码）。validate.py 表头检测放宽** |
| **3.21.0** | **2026-06-20** | **杠铃架构：autofix CERTAIN 层 6 fixer 纯脚本零误修。反脆弱四启发（via negativa/杠铃/Lindy/hormesis）驱动设计。Phase 4 验证流程重组** |
| **3.20.1** | **2026-06-20** | **validate.py 文件树检查去格式假设：代码块+列表行 → 文件名搜索，修复 README 误报 + DESIGN 漏检** |
| **3.20.0** | **2026-06-20** | **静态安全扫描：AP-024 危险 shell / AP-025 网络调用 / AP-026 文件越界（3 CRITICAL/MEDIUM/HIGH）** |
| **3.19.11** | **2026-06-20** | **validate.py references/ 段解析边界修复：`\\n\\S` → 行扫描** |
| **3.19.10** | **2026-06-20** | **quality-audit.py --stats + self-audit.py 数字声称验证（防数字漂移）** |
| **3.19.9** | **2026-06-20** | **数字漂移修复：12处「16维」→「14维」，文档声称与代码实际一致** |
| **3.19.8** | **2026-06-20** | **self-audit.py 保鲜度检查统一从 SKILL.md frontmatter 读预算（单一源头），仅超预算时报警** |
| **3.19.7** | **2026-06-20** | **estimate-tokens.py 排除 .jsonl 运行时文件 + Token 预算从虚胖 115K 修正为真实 20K** |
| **3.19.6** | **2026-06-20** | **自检修复：README 文件树补全 + Token 预算同步** |
| **3.19.5** | **2026-06-20** | **P3 社区标配：Issue 模板 + CODE_OF_CONDUCT.md** |
| **3.19.4** | **2026-06-20** | **P2 发布准备：AP 回归测试 + CONTRIBUTING.md + 零依赖强调** |
| **3.19.3** | **2026-06-20** | **yaml_utils.py 内联数组解析修复** |
| **3.19.0** | **2026-06-20** | **输出文件约定确认功能：ADR-015 + REQ-014 + AP-023 + 三处检查点（DESIGN收尾/VERIFY交付/BUILD自检）** |
| **3.18.9** | **2026-06-20** | **PRINCIPLES.md 全量移除：生成/检查/反模式/自审全部去 PRINCIPLES。SCK 自身 PRINCIPLES.md 保留（自身文档）** |
| **3.18.7-3.18.8** | **2026-06-19** | **保鲜度偏差修复 + strict 测试补全（6项）+ 模板嵌入修改纪律 + DESIGN 版本历史补全** |
| **3.18.5-3.18.6** | **2026-06-19** | **全面升级：Phase编号对齐→四维质量提升→四缺口补齐→12处语义修复。脚本门禁+LLM顾问分界确立。详见 CHANGELOG.md** |
| **3.18.4** | **2026-06-19** | **Phase 4.3 LLM 语义审查（quality-audit --llm-review 四固定问，补脚本盲区）** |
| **3.18.3** | **2026-06-19** | **AP-022 description 版本史堆积检测 + SCK 自身 description 清理** |
| **3.18.2** | **2026-06-17** | **init_skill.py 自动生成 .gitignore + SCK 自身 .gitignore 补全** |
| **3.18.1** | **2026-06-17** | **init_skill.py README 模板升级 + readme_quality 审计拆分快速开始/触发方式独立检查** |
| **3.18.0** | **2026-06-17** | **pm-skills 格式升级：模板新增 Purpose/Context/Output 六段 + AP-020/021 + D15 body_structure + Q2a 采访 + validate exit 1 修复** |
| **3.16.3** | **2026-05-27** | **init_skill.py 全面适配合并架构：不再生成独立 SPEC.md，仅生成合并 DESIGN.md** |
| **3.16.2** | **2026-05-27** | **AP-014: description 过短检测，SKILL.md 描述扩展至 85 字 + template 字段** |
| **3.16.1** | **2026-05-27** | **P1-P4 全面修复：platform独立运行、Token同步、phase-check合并架构适配** |
| **3.16.0** | **2026-05-27** | **审查升级：好模式识别 + 非满分扣分分析。review-history.jsonl 扩展 patterns 字段** |
| **3.15.0** | **2026-05-26** | **cross_version_stale：源码 mtime 晚于 CHANGELOG 自动提醒 bump** |
| **3.14.0** | **2026-05-26** | **Phase 4.3 自动测试 + 版本双写根除 + DESIGN 同步检查 + 幽灵版本清理** |
| **3.13.0** | **2026-05-18** | **设计框架合并：资产体系+Token决策树+BUILD双模式+连锁更新Rule+反模式清单 (ADR-014)** |
| **3.12.4** | **2026-05-18** | **P2批次: --interactive采访 + rules/纪律Rule化 + phase-check完整性检查 + Phase-0指引 + 预算9000→11000** |
| **3.12.3** | **2026-05-18** | **L2预算 5000→9000 + ADR-012跨会话审查历史** |
| **3.12.2** | **2026-05-17** | **模板去双写 + yaml_utils 共享模块 + 手动维度 Rubric + token_budget 增强 + 评分防作弊 + lightweight SSOT + REQ-010~013** |
| **3.12.1** | **2026-05-15** | **quality-audit.py 解析缺陷修复 + 版本声明一致性补全** |
| **3.12.0** | **2026-05-15** | **platform.py 共享模块 + 消除 WB 路径假设 + 四平台一等公民** |
| **3.11.0** | **2026-05-15** | **跨平台支持：data/platforms/ + anti-patterns platforms_applicable** |
| **3.10.0** | **2026-05-15** | **timeline_check 移除（WB特定）15→14维，满分120→117** |
| **3.9.0** | **2026-05-14** | **新增15维「声明一致性」+ P0消灭双源 + Phase 0 出发前确认** |
| **3.6.0** | **2026-05-08** | **validate.py 新增交叉文档一致性审计（cross-audit）** |
| **3.5.0** | **2026-05-08** | **原则10·反模式13·膨胀检查·Drift Guard（human-stars设计反思）** |
| **3.4.0** | **2026-05-07** | **self-audit D7+D8 扩展 + review-guide 审计策略方法论** |
| **3.3.0** | **2026-05-07** | **双层自检架构（scripts/self-audit.py）+ ADR-011 + Token 预算更新** |
| **3.2.1** | **2026-05-07** | **全量工程审计修复（14问题）+ Token 预算更新** |
| **3.2.0** | **2026-05-07** | **PHILOSOPHY.md → PRINCIPLES.md 重命名** |
| **3.1.4** | **2026-05-07** | **目录自动发现 + 删死模板 + 三条操作纪律** |
| **3.1.3** | **2026-05-07** | **文件结构表单列化 + init_skill.py 自动生成索引** |
| **3.1.2** | **2026-05-07** | **validate.py 新增文件表一致性检查 + sources.template.yaml 补表** |
| **3.1.1** | **2026-05-07** | **活性审计四问法（references/vitality-audit.md + review-guide集成）** |
| **3.1.0** | **2026-05-07** | **审查前自反思规则集** |
| **3.0.2** | **2026-05-06** | **2层版本规则：validate.py重写+5模板移VERSION+review-guide同步** |
| **3.0.1** | **2026-05-05** | **移除第7条信念，信念8→7、9→8** |
| 3.0.0 | 2026-05-04 | 初始版本 |

---

## 核心需求

### 定位边界（v3.22.0 明确）

SCK 是**静态分析工具（linter）**，不是测试框架。查形式不查功能：

| SCK 负责（形式） | SCK 不负责（功能，留给 LLM/人） |
|----------|---------------------|
| YAML 语法 / 版本号一致 / 文件存在 / 反模式 | 脚本逻辑是否正确 |
| 章节完整性 / README 段数 / token 预算 | 工作流是否合理 |
| mtime 驱动的文档同步检测 | 触发词是否真的命中 |
| 文件表 ↔ 磁盘一致性 | 语义表述是否准确 |

脚本只做机械验证（零误报、跨会话一致），语义判断留给有判断力的那一边。manual 维度标记 `manual` 正因形式够不等同内容对——这些留给 LLM/人裁定。

### REQ-001: 四大入口路由
**描述**：用户从创建/升级/审查/评分四个入口进入，AI 按入口引导对应流程。
**优先级**：P0

### REQ-002: 五阶段创建流程
**描述**：引导用户从定位到交付，Phase 1-5 按顺序引导，三通道选择在 Phase 1 前完成。
**优先级**：P0

### REQ-003: 审查打磨
**描述**：给已有 skill 做体检+诊断+治疗，输出三位一体报告（🌟亮点/⚠️需改进/💡学习要点）。
**优先级**：P0

### REQ-004: 升级机制
**描述**：轻量 skill 补全为完整版，不重写已有产出。
**优先级**：P1

### REQ-005: 自进化
**描述**：审查其他 skill 时发现好模式，经三道门过滤后纳入自身。
**优先级**：P1

### REQ-006: 三个强制交付物
**描述**：每次创建或审查结束自动生成 README + CHANGELOG + 交付报告。
**优先级**：P0

### REQ-007: 质量评分（v3.0）
**描述**：14维度自动化质量审计，4个手动维度标记待 AI 裁定。轻量通道 79 分，完整通道 131 分。（v3.10 从 15 维减至 14 维，之后未再扩展）
**优先级**：P1

### REQ-008: 自反思循环（Ralph Loop, v3.0）
**描述**：Phase 3 和 Phase 5 各执行一次双层自反思，最多 3 轮。全过或 3 轮后 SPEC/DESIGN 冻结。
**优先级**：P1

### REQ-009: 双层自检（v3.3）
**描述**：`scripts/self-audit.py` 覆盖 5 项通用检查 + 1 项 SCK 专属检查。嵌入 `validate.py --strict`。
**优先级**：P1

### REQ-010: 跨平台一等公民支持（v3.11+）
**描述**：支持 WorkBuddy / OpenClaw / Hermes / Universal 四平台，每平台一等公民。
**优先级**：P1

### REQ-011: 共享代码模块化（v3.12）
**描述**：`scripts/yaml_utils.py` 提供共享 YAML 解析和 Frontmatter 提取函数。
**优先级**：P1

### REQ-012: 评分防作弊完整性检查（v3.12.2）
**描述**：quality-audit.py 评分后 4 项完整性检查，检测评分虚高、反模式矛盾等异常。
**优先级**：P1

### REQ-013: 手动维度评分标准化 Rubric（v3.12.2）
**描述**：4 个手动维度在 audit.yaml 中定义 4-5 级评分标准。
**优先级**：P1

### REQ-014: 输出文件约定声明（v3.19.0）
**描述**：创建和审查 skill 时，若 skill 涉及文件产出动作（生成/导出/保存/输出/写入等），须在 SKILL.md 中声明 `## 输出文件约定` 章节，明确输出目录、文件命名规则、文件格式、错误输出方式四要素。
**优先级**：P1

---

## 非功能需求

| 需求 | 说明 |
|------|------|
| NFR-001 Token预算 | L0:200, L1:2000, L2:20000, hard_cap:25000 |
| NFR-002 语言风格 | 打磨式（"一起踩过的坑"语气），不说教 |
| NFR-003 安全 | Frontmatter 安全清单 6 项自动扫描 |
| NFR-004 诚实 | 不承诺做不到的事（如跨会话状态） |
| NFR-005 自检 | validate.py --strict 嵌入 self-audit（引用完整性 + 配置活性 + 保鲜度 + 纪律验证 + 名称一致性） |
| NFR-006 缓存 | 同skill同版本缓存复用（键含mtime），默认1小时TTL |

---

## 架构决策记录

### ADR-001: basic 模板 → 现为 multi-scene（v3.10+ 演进）
**背景**：三个入口（创建/升级/审查）功能差异大。
**决策**：初期使用 basic 模板，v3.10+ 改为 `template: multi-scene`，利用 scene routing 进行平台×模板×通道三维路由。三个入口仍是"不同起点的同一件事"。

### ADR-002: 双通道设计（轻量/完整）
**背景**：不同用户有不同的时间和质量需求。
**决策**：两个通道共享五阶段框架，复杂度在产出物深度上分化。轻量不生成 SPEC/DESIGN/scripts/tests，但升级后可达完整标准。

### ADR-003: 三位一体审查报告
**背景**：传统验证工具只报错，不教人。
**决策**：审查报告包含 🌟亮点 + ⚠️需改进 + 💡学习要点。从"挑错"变成"教学"。

### ADR-004: 🧬 自进化三道门
**背景**：审查中发现的好模式可能适合 SCK 自身。
**决策**：三道门过滤（适合吗？冲突吗？用户拍板？）+ CHANGELOG 标注来源。

### ADR-005: 无 SPEC/DESIGN → 补上
**背景**：SCK 最初没有 SPEC/DESIGN，违反自己的完整通道标准。
**决策**：v3.0.0 补上。v3.14.0 合并为单一 DESIGN.md。

### ADR-006: 10维度 → 14维度质量评分（v3.10 稳定）
**背景**：评分系统从 10 维度扩展到 14 维度，新增声明一致性、CHANGELOG、README 同步、防作弊等。3.10 移除 WB 特定 timeline_check 后稳定在 14 维。

### ADR-007: 缓存与预检（v3.0）
**决策**：quality-audit.py 内置缓存层。键含 mtime，文件改后自动失效。4 个手动维度增加脚本预检标记辅助 AI 裁定。

### ADR-008: Ralph Loop 自反思（v3.0）
**决策**：Phase 3 和 Phase 5 各嵌入双层自反思循环（客观+主观）。最多 3 轮，全过后 SPEC/DESIGN 冻结。

### ADR-009: 配置与逻辑分层（v3.2）
**决策**：SKILL.md frontmatter 是配置层，workflow/references 是逻辑层。每层只写自己的职责。

### ADR-010: 入口内嵌同步清单（v3.2）
**决策**：操作波及多个文件时，在触发变化的位置内嵌同步清单。不另开文件。

### ADR-011: 双层自检架构（v3.3）
**决策**：`scripts/self-audit.py` 通用层（5 项）+ SCK 专属层（1 项）。嵌入 `validate.py --strict`。

### ADR-012: 跨会话审查历史（v3.12.3）
**决策**：`data/review-history.jsonl` 记录每次审查的 skill/版本/分数/关键发现。.gitignore 排除。

### ADR-013: P2 批次强化（v3.12.4）
**决策**：① init_skill.py 新增 --interactive 模式；② 四条纪律 Rule 化（rules/ 目录）；③ Phase 完整性检查（scripts/phase-check.py）。

### ADR-014: 设计框架合并（v3.13.0）
**决策**：将 `~/.workbuddy/principles/skill-design-framework.md` 独有内容纳入 SCK，框架文件替换为引用桩。吸收资产体系表、Token 决策树、BUILD 双模式、反模式清单。新增 `rules/operational-rules.md`（含 cascade-update 等五条纪律）。

### ADR-015: 输出文件约定确认（v3.19.0）
**背景**：部分 skill 产出文件，但输出路径、命名、格式、错误处理方式未在任何文档中声明，导致用户不知道文件输出到哪里、AI 每次输出行为不一致。
**决策**：
1. 触发条件：skill 涉及文件产出动作（正则匹配 生成|导出|保存|输出|写入|create|export|save|generate 等关键词 + 文件语义）
2. 确认时机：Phase 2 DESIGN 收尾（作为进入 Phase 3 BUILD 的前置阻塞条件）
3. 确认内容：输出目录 / 文件命名 / 文件格式 / 错误输出方式（4 项）
4. 记录位置：SKILL.md 中增加 `## 输出文件约定` 章节
5. 验证层：AP-023 反模式扫描 + Phase 4.6 验证 + BUILD 自检清单
**后果**：
- 涉及文件产出的 skill 在 DESIGN 阶段多一步确认交互
- 不涉及文件产出的 skill 无额外负担
- AP-023 与 AP-021（缺少 Output 段落）互补：一个管内容格式，一个管文件路径

---

## 资产类型体系表

| 目录/文件 | 类型 | 用途 | L2加载级 |
|-----------|------|------|:--:|
| SKILL.md | 路由+指令 | AI 入口 | L0+L1 |
| README.md | 人类文档 | 人类入口 | — |
| DESIGN.md | 架构契约 | 需求+决策追溯（v3.14.0 合并） | — |
| CHANGELOG.md | 变更日志 | 版本追溯 | — |
| scripts/ | 可执行代码 | 业务逻辑 | L2 |
| references/ | 深度文档 | 详细指南 | L2 |
| rules/ | 操作纪律 | 可解析规则 | L2 |
| data/ | 数据资产 | 缓存/模板 | L2 |
| templates/ | 输出模板 | 格式定义 | L2 |

## Token 预算决策树

L2 预算超限时的判断流程：

```
L2 实测 > 预算？
  │
  ├─ 1. 能否砍内容？
  │   优先砍：冗余示例、重复说明、装饰性文字
  │   → 能砍则砍，重测
  │
  ├─ 2. 内容都是核心资产？
  │   → 调预算（上调 L2_deep 和 hard_cap）
  │
  ├─ 3. 联动更新：SKILL.md + DESIGN.md + CHANGELOG.md
  │
  └─ 4. hard_cap 为绝对红线，不可逾越
```

## Token 实测

| 组件 | Token | 预算 | 状态 |
|------|-------|------|:---:|
| L0 (frontmatter) | 156 | 200 | ✅ |
| L1 (SKILL.md body) | 1570 | 2000 | ✅ |
| L2 (references+data+rules) | 16783 | 20000 | ✅ |
| 总计 | 18509 | 22200 | ✅ |

## 模块关系图

references/ 文件清单（按 Phase 编号）：
- `phase-0-preflight.md` — Phase 0 出发前确认
- `phase-1-positioning.md` — Phase 1 DISCUSS
- `phase-2-design-requirements.md` — Phase 2 DESIGN · 需求定义
- `phase-2-design-architecture.md` — Phase 2 DESIGN · 架构设计
- `phase-3-build.md` — Phase 3 BUILD
- `phase-4-verify.md` — Phase 4 VERIFY
- `phase-5-evolve.md` — Phase 5 EVOLVE
- `build-standards.md` — BUILD 施工规范
- `auto-test.md` / `readme-standard.md` / `vitality-audit.md` — 辅助文档
- `upgrade-guide.md` / `review-guide.md` — 升级与审查指南

```
用户输入
  │
  ├─ "帮我建一个 skill" → 🆕 创建
  │    └─ Phase 0 → Phase 1-5 (references/phase-*.md)
  │         └─ data/checklists/ + data/templates/
  │
  ├─ "升级到完整版" → 🔄 升级
  │    └─ references/upgrade-guide.md
  │
  └─ "帮我看看这个 skill" → 🩺 审查
       └─ references/review-guide.md
            ├─ scripts/validate.py
            ├─ scripts/estimate-tokens.py
            ├─ scripts/quality-audit.py (评分)
            ├─ data/anti-patterns.yaml
            ├─ data/checklists/audit.yaml
            ├─ data/review-history.jsonl (审查历史)
                    │
                    └─ 🧬 Step 4: 自进化 → CHANGELOG.md
```

---

## 候选方案对比

| 决策 | 选项 A（选定的） | 选项 B（放弃的） | 选 A 的理由 |
|------|------|------|------|
| 验证方式 | Python 脚本（validate.py + quality-audit.py） | LLM 口头评估 | 脚本结果跨会话一致，不受模型温度影响；反模式检测可穷举 |
| 元工具自检 | self-audit.py 跑在自己身上 | 靠开发者自觉 | 不自检的场景不允许交付，脚本化强制执行 |
| 文档架构 | 合并 DESIGN.md（WHAT+HOW 一页） | 独立 SPEC.md + DESIGN.md | 减少双写同步债，降低维护成本 |
| 平台支持 | 四平台共享核心脚本 | 仅 WorkBuddy | platform.py 抽象层成本低，SKILL.md 跨平台复用 |

---

## 已知局限

1. **CHANGELOG 版本解析**：多版本共存时偶尔挑错最新版本（如 3.16.15 和 3.17.0 并存时可能误判），需要更健壮的首行匹配
2. **文件结构表解析**：Markdown 表格中描述列被误当文件路径，导致误报 file_table_stale
3. **Token 预算**：当前配置充裕，L2 实测 16783 / 预算 20000，hard_cap 25000 有充足余量
4. **跨文档引用检测**：仅做 pattern match，不做语义级别的"引用是否过时"判断
5. **不覆盖**：工作流逻辑错误、脚本运行期错误、业务领域正确性
6. **autofix v3.22.0 重新定位**：从 6 fixer 确定性引擎瘦身为安全骨架（backup→verify→rollback）。修复由 LLM 在对话中完成，脚本只做安全网。未来如需 CI 场景的确定性修复，可在 engine 上重新挂 fixer
