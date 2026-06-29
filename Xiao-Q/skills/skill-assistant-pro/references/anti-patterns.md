# Skill 反模式清单（NEVER List）

> skill-assistant 在历次评测、用户反馈、真实事故中沉淀的"绝对不要做"清单。从 SKILL.md 主体迁移到此处保留全文措辞 —— 措辞强烈是因为每条都是踩过坑后用代价换来的边界。
>
> SKILL.md 主体只保留 5-8 条最致命的，其余按模块归在本文件。各模块在自己 SKILL.md 中遇到对应场景时**主动加载本文件对应章节**。

---

## 目录

- [前置检查 / 路由 / 工具探测](#前置检查--路由--工具探测)
- [搜索模块（modules/search.md）](#搜索模块modulessearchmd)
- [安装模块（modules/install.md）](#安装模块modulesinstallmd)
- [质检模块（modules/inspect.md）](#质检模块modulesinspectmd)
- [诊断模块（modules/diagnose.md） / 棘轮迭代](#诊断模块modulesdiagnosemd--棘轮迭代)
- [Workspace / 产物路径](#workspace--产物路径)
- [子 Agent 与 dry_run 评测](#子-agent-与-dry_run-评测)
- [报告生成](#报告生成)
- [time-budget / 性能控制](#time-budget--性能控制)
- [盲评 / Comparator](#盲评--comparator)

---

## 前置检查 / 路由 / 工具探测

- **NEVER 跳过前置检查直接搜索/安装** — API Token 未加载会导致全部需认证渠道失败，浪费用户时间
- **NEVER 跳模块混合执行** — 模块间有数据依赖（如搜索结果 → 安装输入），混合执行破坏流程完整性
- **NEVER 跳过 eval_mode 确认直接开始评审或优化** — **inspect 和 diagnose 都适用**：用户说"评审/质检/review/optimize/诊断"等任何评测或优化意图时，若未在原始输入中明确说明策略（static/dynamic/hybrid/blind），**第一步必须**展示策略选择菜单（inspect 用入口菜单 / diagnose 用 Step -1），再执行任何实质操作。"评审和优化"、"帮我看看这个 skill"等模糊意图**绝不视为已指定策略**。eval_mode 决定测试集是否必须、子 Agent 是否 spawn、报告深度——跳过等于让用户在不知情的情况下走了 structure_only 流程
- **NEVER 现场判断工具可用性** — 如 `which gh && gh auth status` 与其他 `echo`/`ls` 混写在一行，shell 退出码、stdout 顺序、权限前缀会让 Agent 把可用工具误判为不可用（真实事故：gh 实际装在 `/opt/homebrew/bin/gh` 但被误判为 missing，导致整个 GitHub 路降级）。工具/Key/网络三类状态**必须**通过 `modules/search.md` 第 0.5 步的结构化快照脚本一次性采集，结果写入 `diagnostics.environment`，后续步骤只读快照，不得重复探测

---

## 搜索模块（modules/search.md）

- **NEVER 在多平台搜索时只发窄路不发宽路** — 窄路用复合关键词在部分平台可能全部返空，宽路是召回率的基础保障
- **NEVER 对双语平台只用英文关键词** — SkillHub 等双语平台收录大量中文 Skill，纯英文复合词可能漏匹配，必须同时生成中文变体关键词
- **NEVER 在 `gh search repos` 第一轮叠加 `--language` / `--stars` 过滤** — 会踢掉其他语言的大型项目（如 Go ⭐38K）和新锐高质量项目；第一轮必须用 Level 3 单核心词无过滤，过滤只能作为第二轮补充或在结果集内 Agent 侧筛选
- **NEVER 用复合长查询调用 `gh search repos`** — 如 `"resume AI generator"` 会漏掉只含 `resume` 的头部仓库；遵循「简单核心词优先」原则，第一轮用 1 个最短核心词 limit=30
- **NEVER 隐藏搜索参数** — 搜索输出必须包含诊断头（关键词/渠道候选数/漏斗收敛/异常清单），不得只返回"找到 N 条结果"而不展示用了什么关键词、查了多少条。用户不认可结果时，诊断头是定位偏差的唯一依据
- **NEVER 漏专有名词** — 用户输入含人名/品牌名/中文译名（如"达尔文""花叔"）必须强制触发 L4 扩展，不受"L1-L3 已 ≥ 5 条"阈值限制；详见 `references/search-templates.md` Level 4 强制触发条件
- **NEVER 仅看头部 Top 5/10 就丢弃宽路结果** — skills.sh 按 installs 降序会让"贴脸但安装量较低"的精确匹配（如 `darwin-skill@2878`）被挤出 Top；宽路 limit=30 必须全部读 description 做语义二次筛选
- **NEVER 用列表/卡片/段落替代 Top N 表格** — 搜索输出的所有结构化信息（诊断头关键词/漏斗、每个来源分区的 Top N、跨源比较、推荐方案四档）**必须**用 markdown 表格展示，即使只有 1 条结果也必须有表头 + 1 行数据。列表、每条一个 `###` 小标题、散文描述都会破坏搜索透明度主线——用户无法快速扫读对比。违反会触发 🚨 阻断级 `LAYOUT_NON_TABLE`，Agent 必须回退重写后才能交付。规则详见 `modules/search.md` §6.3.1
- **NEVER 悄悄 refine** — 用户通过菜单 7-11 发起 refine 时，输出必须用诊断头 diff 版展示"调整带来了什么变化"（候选量/置信度/命中率），不得只给新结果不给变化归因

---

## 安装模块（modules/install.md）

- **NEVER 用 `npx skills add` 安装** — 侵入性强，会写 `skills-lock.json` + `~/.agents/`，统一用 `install_skill.sh`

---

## 质检模块（modules/inspect.md）

- **NEVER 质检/诊断完成后不展示报告选择菜单就结束** — inspect 报告生成后必须展示「[1]进diagnose棘轮 / [2]完整HTML报告 / [3]成果卡片 / [4]查看细则 / [5]完成」；diagnose 优化收尾必须展示 Step 6 的「[1]完整HTML报告 / [2]成果卡片 / [3]两者都要 / [4]不生成」——即使用户明确说"不需要"，也必须输出菜单等用户明确选 [4] 或 [5]，不得静默结束

---

## 诊断模块（modules/diagnose.md） / 棘轮迭代

- **NEVER 把 CLI 新进程混入常规动态 eval 决策** — CLI 新进程（codebuddy / claude-internal）专门用于**触发率测试**（D10.2 / description 加速器 Step 4.6），不是"更好的输出质量评测引擎"；常规输出质量对比（D.1-D.3）用子 Agent 即可，不要向用户推销 CLI 作为动态 eval 默认选项
- **NEVER 触发率数据和输出质量数据混算** — CLI 新进程输出的 true trigger rate 和子 Agent 输出质量分不在同一维度，报告中必须分区展示，不得合并为单一评分
- **NEVER 用固定 0.5σ 阈值做棘轮决策** — 4.1.5 的 keep/revert/unchanged 三档阈值必须按 N_repeats 动态算：`threshold(N) = t(α=0.10, df=N-1) × σ/√N`（N=3 → ≈1.09σ，N=10 → ≈0.44σ）。固定 0.5σ 在 N=3 时假阳性率 ~30%——会把噪声当好转 keep 下来。N=2 强制降级标 confidence=low；CV>0.30 标 high_variance 提示用户升 N 再决策
- **NEVER 把 N_repeats 一刀切应用到所有 prompt** — 4.1.4.b 必须按 prompt 优先级差异化分配 N：P0=5 / P1=3 / P2=2 / 缺 priority 字段=3。每条 prompt 独立记录 N（benchmark.json 含 `per_prompt_runs`），让"核心场景决策更严谨、锦上场景花更少时间"。一刀切 N=3 在 P0 上不够稳、在 P2 上又浪费成本
- **NEVER 把 preview 模式结果写进 results.tsv 主分** — preview eval_mode 单点采样仅用于决策"下一步跑啥"，污染历史分会让棘轮跨次对比失真。preview 必须写到独立的 `preview-results.tsv`，且报告里明确标"preview · 单点采样不代表整体"
- **NEVER 在 Step 6 把"用户说不需要"等同于"选 [4]"** — 用户自然语言输入"不需要"/"不用"/"skip" 时，**必须**先输出确认提示「这等同选 [4] 不生成，直接结束吗？[4] 是 / [1] 改主意要完整报告」让用户 STOP 显式选择。直接静默结束 = 让用户事后无报告归档无法挽回；同样不允许在 inspect 收尾跳过菜单

---

## Workspace / 产物路径

- **NEVER 凭直觉拼 workspace 路径** — workspace 容器名是**固定的 `skill-assistant-workspace/`**（不是 `<skill>-workspace/`、不是 `<skill>_eval/`），下面再按 skill 名分子目录。建任何评测产物前**必须**：① 读 [references/workspace-layout.md](workspace-layout.md) 解析规则；② 调 `scripts/resolve_workspace.py --skill <path>` 拿到唯一权威路径；③ Glob 现有 sibling workspace 验证模板一致。inspect / diagnose / batch_baseline / 加速器入口都受此约束。真实事故：未走解析直接建 `.cursor/skills/<skill>-workspace/`，27 个产物文件全建错位置后被迫迁移
- **NEVER 把新建 test-prompts.json 写到 `<skill_dir>` 内** — 产物统一写 workspace（`<workspace>/<skill>/test-prompts.json`，其中 `<workspace>` 严格指 `skill-assistant-workspace/`，由 `resolve_workspace.py` 解析得到，不许手拼），skill 目录内旧文件仅兼容读取；如检测到旧位置有文件，必须提示用户迁移
- **NEVER 用 `path.write_text(yaml.dump(data))` 直接覆盖 manifest.yaml** — 必须走 `scripts/manifest_io.py write_manifest_atomic`（.tmp + fsync + POSIX rename）；直写在 IDE 崩溃 / Ctrl-C / 断电时机会留下半截 yaml，下次 resume YAML 解析失败丢失整个评测会话。残留 `manifest.yaml.tmp` **不得静默吃掉** ——必须告知用户上次崩溃由用户决定是否信任 .tmp 兜底

---

## 子 Agent 与 dry_run 评测

- **NEVER 只判断 test-prompts.json 是否存在就继续** — 存在性检查通过后，必须执行 [test-prompts-design.md](test-prompts-design.md) Step P.3 完整性 checklist（与 [auto-judgement-generator.md](auto-judgement-generator.md) Phase 3.5 同款标准——功能覆盖 100% / P0 场景 ≥95% / category ≥4 / 判别力 / negative 防偏置 / 场景类型至少 3 类）；不通过时必须展示交互菜单（自动补全/手动追加/优化judgement/跳过），不得静默继续
- **NEVER 未走 test-prompts-design.md 共用流程就开始动态评测** — 进入动态评测（inspect D.1）或诊断棘轮（diagnose Step 4）前，**必须**调 [references/test-prompts-design.md](test-prompts-design.md) Step P.1-P.5（定位 → 展示 → 丰富度 → STOP 用户确认 → 写 hash），inspect/diagnose 共用一份逻辑。**例外**：同一会话中 inspect 已写 `manifest.test_prompts_confirmation.hash`、当前 test-prompts.json 内容 hash 一致、用户**未**输入"review test-prompts"——此时 diagnose Step 0 可跳过 P.2-P.4 重复展示，仅打印简短"✓ 测试集与本会话上次确认一致"。其他情况必须走完整 STOP 流程
- **NEVER 跳过 Phase 2.5 矩阵确认直接生成测试 prompt** — 自动生成测试集时，必须先按 [auto-judgement-generator.md](auto-judgement-generator.md) Phase 1 抽出功能模块清单，再按 Phase 2.5 规划"功能 × 5 类场景 × 优先级"4 维矩阵让用户对齐后才生成。直接凭直觉写几条 prompt = 必有功能盲区，棘轮决策可信度直接 -50%
- **NEVER 生成只覆盖 happy_path 的测试集** — 5 类场景至少要覆盖 3 类（happy + complex 各 ≥1，edge/negative/error 至少 1 类有覆盖）。只有 happy 路径的测试集等于"只测顺风路况"——无法发现 skill 在边界 / 反例 / 异常下的脆弱点
- **NEVER 在 dry_run 降级路径下不落盘 eval 结果** — inspect D.1 / diagnose Step 4.1.4.c 降级到 dry_run 时，主 Agent 必须把每条 test-prompt 的 baseline / with_skill 推演输出 + 逐条 judgement 评分按标准 schema 写到 `<workspace>/iteration-N/eval-<scenario>/{baseline,with_skill}/run-1/{outputs/report.md,grading.json}`。"只在对话记忆里推演"等于报告生成阶段读到空 `eval-*/` 目录，`{{EVAL_RESULTS_DETAIL}}` 只能渲染 static 占位文本——这是修复过的真实事故。dry_run 不是"免落盘"，只是"主 Agent 自己当 Grader"
- **NEVER 把 dry_run 落盘 sanity check 延后到 Step 6 报告生成时** — 必须在 4.1.4.c / D.1 写完 grading.json 后**就地**校验 7 项（见各模块）：① baseline + with_skill 双 grading.json 存在且 size>50B ② expectations 数量 == judgements 数 ③ 每条 expectation 含 text/passed/evidence ④ evidence 不为空话 ⑤ 不允许"全 passed=true"（with_skill）/"全 passed=false"（baseline） ⑥ outputs/report.md 首行含"⚠️ dry_run 推演"标记 ⑦ 任一不通过立刻回写本条不进 4.1.5 / D.2。把 sanity check 拖到 Step 6 = 让用户等到看报告时才发现"评测整轮白做"
- **NEVER 凭直觉自拟 grading.json / eval_metadata.json schema** — 子 Agent 与 dry_run 主 Agent 都必须按 [references/sub-agent-protocol.md §grading.json 完整 schema](sub-agent-protocol.md) 字段表落盘：顶层必含 `passed_count` + `total_count` + `expectations[]`（**不是** `summary.passed/total` + `judgements[]` —— 后者是修复过的真实事故，导致报告 ⑥ 段空白且 sanity 误以为通过）；写完后**必须立即调** `scripts/validate_eval_artifacts.py <iter_dir>`，failed 立即修，**绝不带病调 generate-full-report.mjs**。manifest 必须在 `evaluation.eval_mode` + `iterations[].eval_mode` 两处都写 eval_mode（前者是权威源）
- **NEVER 让 Grader/Comparator/Analyzer 子 Agent 自己读 test-prompts.json** — 主 Agent 装配 `_subagent_input.json` 单向传递给子 Agent，子 Agent 只读这个 + transcript_path + outputs_dir。让子 Agent 自读会导致 scenario 漂移（错配 prompt） / 数据 inflation（扫描整个文件） / 盲评破坏（Comparator 反推身份）。装配协议 + 7 项收尾校验全文见 [references/sub-agent-protocol.md](sub-agent-protocol.md)

---

## 报告生成

- **NEVER 用 Write 工具从零拼接 HTML 替代 `templates/full-report.html`** — 详细诊断报告（`iteration-N/detailed-report.html`，原 full-report.html）必须通过 `scripts/generate-full-report.mjs`，单轮摘要报告（`iter-summary.html`，原 report.html）必须通过 `templates/iteration-report.html` + str.replace 渲染。手写 HTML 会跳过新模板的 `{{COVERAGE_MATRIX}}` / `{{MUST_READ_ITEMS}}` / `{{D_DIMENSIONS_ROWS}}` / `{{D10_SUB_ROWS}}` / `{{EVAL_RESULTS_DETAIL}}` 等占位符注入和 sanity check，导致用户视角 8 章节缺失。脚本落盘后会自动 sanity check：① 渲染产物无残留 `{{` ② 有 `eval-card` 或 `static 模式` 或 `dry_run` 任一标记 ③ 非 static 非 dry_run 模式下 `eval-*/grading.json` 至少 1 个；任一失败 exit code = 3
- **NEVER 评测完成后不落盘 detailed-report.html** —— 无论 `eval_mode` 是 static / preview / dynamic / hybrid / blind_hybrid / dry_run，也无论用户 Step 6 最终选 [1]/[2]/[3]/[4]，`<workspace>/iteration-N/detailed-report.html` **必须**在每轮 diagnose Step 4.1.6.5 / inspect 报告生成后立即通过 `scripts/generate-full-report.mjs` 强制生成落盘。Step 6 菜单仅控制"是否打开浏览器 + 是否追加 PNG 卡片"，不再触发 HTML 首次生成。静默不生成 = 事后用户需二次指令补生成（历史 iter-6 / iter-7 事故），违反"每次评测都要有可归档 HTML 产物"原则。Node 不可用时必须在 results.tsv 记 `html_report=node_missing` 异常行并提示用户装 Node，**不得**以"没 Node"为由跳过

---

## time-budget / 性能控制

- **NEVER 把 fidelity_mode 默认升档到 `cli_fresh_process`** — 输出质量评测默认 `subagent_default` 子 Agent 双跑足够，CLI 新进程耗时 1.5-2× 必须用户明示才启用；results.tsv 必须有 `fidelity` 列一行可见，不允许默默升档浪费用户预算
- **NEVER 不显式记 `time_budget.started_at` 就开跑评测** — 每个 eval_mode 必须按 [references/time-budget.md](time-budget.md) 表写入 soft/hard deadline + started_at，每完成 scenario 边界更新 elapsed_checkpoints；soft 超时弹 5 选项菜单 STOP 等用户、hard 超时按表自动降级（preview→3min / dynamic→10min / hybrid→12min / blind_hybrid→20min）。partial 评测 results.tsv 加 `time_budget=hard_exceeded` 标记，4.1.5 棘轮决策跳过判 unchanged
- **NEVER 在 hard_deadline 超时时优先牺牲 P0 prompt** — time-budget hard 超时降级时牺牲顺序必须是 P2 → P1 → P0，**P0 任何时候都保留**（除非整个评测中止）。优先级反转 = 核心场景被砍 = 决策可信度归零

---

## 盲评 / Comparator

- **NEVER hybrid/blind_hybrid 跑完不算 Grader vs static 一致性校验** — 4.1.5.5 / D.3.5 必须算 `delta = abs(static_score − dynamic_score)`，>15 在报告 Must-Read 加橙色警告、>25 红色严重警告；典型分歧（静态高 + 动态低 = "摆设型"，静态低 + 动态高 = "干货但格式糙"）必须显式归类。delta>15 + D10.3<0.5 时警告升级为"测试集可能没区分度"，建议先回 Step 0 重做测试集
- **NEVER 给 Comparator 任何能反推身份的信息** — `winner_role` / `anon_mapping` / SKILL.md 路径泄漏 = 盲评设计直接失效。装配 `_subagent_input.json` 时必须把这些字段排除（仅 Analyzer 揭盲后调用时才接受 `winner_role`）
