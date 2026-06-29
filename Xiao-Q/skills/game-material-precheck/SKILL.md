---
name: game-material-precheck
description: This skill should be used when auditing game promotional materials, screenshots, CG images, copywriting, event pages, or launch plans for China mainland compliance, legality, IP risk, cultural/religious risk, sensitive-date conflict, and public-opinion risk. It uses the bundled local knowledge base first, optionally refreshes from zzanezhu's Lexiang personal knowledge base when available, cross-checks external public information, and produces a structured HTML audit report.
icon: assets/icon.png
agent_created: true
---

# 游戏素材预审

## Purpose

封装一套面向中国大陆游戏宣发素材的审核流程：优先使用 Skill 内置本地知识库，必要时再读取乐享知识库「zzanezhu的个人知识库 / 游戏合规安全知识库」进行刷新，结合外部公开信息检索，对用户提供的图片、文案、活动日期、投放地区进行合规、合法、知识产权、文化宗教、战争军事、舆情、敏感纪念日等维度审核，并生成可交付的 HTML 报告。

## Trigger

在以下场景使用本技能：

- 审核游戏素材、游戏宣传图、游戏内截图、CG、PV分镜、活动落地页、广告图、文案、运营活动排期。
- 用户要求判断素材是否合规、合法、能不能上线、是否有舆情风险。
- 用户要求结合「zzanezhu的个人知识库」「游戏合规安全知识库」「乐享知识库」进行审核。
- 用户要求输出审核报告、HTML报告、表格化风险结论、修改建议。

## Required workflow

### 1. 明确审核输入

先收集或识别以下信息：

- 素材本体：图片、截图、文案、视频描述、活动页链接或本地文件。
- 目标地区：默认按「中国大陆」审核；如用户说明海外地区，再叠加对应市场规则。
- 发布日期：若未定，输出「敏感日期通用预警」；若已定，联网核查当天及前后 3 天是否存在严肃纪念日、社会热点或重大舆情。
- 素材用途：广告投放、官网公告、社媒宣发、游戏内活动、版本更新、社区运营等。
- 目标受众：成年人、未成年人、泛用户、核心玩家、海外玩家等。

如果用户只发图片，不要要求其重复上传；优先读取图片并根据视觉内容审核。若图片无法解析，再要求用户补充画面描述。

### 2. 读取本地内置知识库

默认优先读取 Skill 自带的本地知识库，不要求使用者连接 zzanezhu 的乐享空间。

必须读取或参考：

- `references/knowledge-baseline.md`：结构化合规规则、风险等级、常见风险点、敏感日期清单。
- `references/source-docs.md`：从乐享知识库或人工整理文档中沉淀的原始/半原始知识内容索引。若该文件为空或未覆盖相关问题，再参考 `knowledge-baseline.md`。
- 与当前审核主题相关的 `references/source-docs-*.md` 原文抽取文件：例如全球监管动态、市场合规趋势、全流程合规、危机公关、知识产权、政策汇总、全球文化宗教风险、女性露肤规则等。
- `references/report-template.md`：HTML 报告结构与视觉规范。

本地知识库优先级：

1. 用户本次提供的新规则、新文档、新审核口径。
2. `references/source-docs.md` 中的完整知识库内容。
3. `references/knowledge-baseline.md` 中的结构化规则。
4. 外部公开信息检索结果。

### 3. 可选：从乐享知识库刷新

仅在以下情况读取乐享知识库：

- 用户明确要求「从乐享重新读取」「同步最新知识库」。
- 本地知识库明显缺失关键内容。
- 当前使用者具备乐享连接权限，且任务需要引用最新内部知识。

乐享读取顺序：

1. 加载 `lexiang` skill。
2. 使用 `mcp__lexiang__whoami` 获取当前账号与 `personal_space`。
3. 从 `personal_space.root_entry_id` 开始列出子条目。
4. 定位文件夹：`游戏合规安全知识库`。
5. 读取其下分类：
   - `1. 游戏合规`
   - `2. 游戏政策`
   - `3. 游戏法务`
   - `4. 游戏公关`
   - `【FOR CODM】全球文化、宗教、合规等风险提示手册（持续更新）`
   - `2026年全球游戏行业法律监管动态`
   - `全球游戏市场合规监管趋势分析`
   - `网络游戏公司全流程合规指南`
   - `游戏公司危机公关应对策略`
   - `游戏知识产权保护与侵权案例`
   - `中国游戏行业政策汇总`
6. 对 page 类型条目使用 `mcp__lexiang__entry_describe_ai_parse_content` 读取正文。
7. 对 folder 类型递归读取子条目。
8. 对 file/xls 类型，优先尝试 `entry_describe_ai_parse_content`；若失败，使用 `file_describe_file` 获取元信息，并在报告中标记「文件型知识库未完全解析，需人工复核」。

关键工具调用注意：

- MCP 工具为 deferred tools 时，先用工具检索确认 schema，再用 deferred tool 执行。
- 不要直接调用未加载的 MCP 工具。
- 不要向用户展示 token、凭证、内部鉴权信息。
- 如果其他使用者没有乐享权限，不能中断审核；改用本地知识库继续完成报告，并在报告中标注「使用本地内置知识库」。

### 4. 外部公开信息交叉验证

根据素材内容与发布日期进行联网检索，至少覆盖：

- 敏感纪念日：七七事变、九一八事变、南京大屠杀死难者国家公祭日、抗战胜利相关纪念日、重大灾难纪念日等。
- 近期游戏行业舆情：文案翻车、IP侵权、AI生成争议、战斗/军事题材争议、劳动节/青年节等节日营销争议。
- 平台审核规范：华为、字节/抖音、支付宝、网易等公开平台规则。
- 如出现外国国旗、军队标识、宗教建筑、历史事件、现实地图、真实战争、民族文化符号，应针对该元素单独检索。

不要只依赖模型记忆回答时效性问题。

### 5. 审核维度

至少从以下维度给出结论：

1. 内容合规：违法犯罪、色情低俗、赌博射幸、血腥暴力、恐怖惊悚、未成年人不适宜。
2. 政策与社会秩序风险：国家安全、地图/领土、国旗国徽军旗、真实军政符号、重大历史事件、现实社会冲突影射。
3. 知识产权：第三方 IP、角色形象、游戏画面、音乐、品牌 logo、表情包、影视/动漫/游戏元素。
4. 广告与运营合规：绝对化用语、虚假宣传、诱导点击、诱导充值、抽奖/盲盒概率与变现风险。
5. 未成年人保护：适龄提示、防沉迷、消费提示、是否诱导未成年人。
6. 文化/宗教/民族风险：宗教符号、祭祀元素、民族服饰、禁忌图案、海外市场文化禁忌。
7. 战争/军事风险：真实近现代战争、真实部队、真实武器、军用 logo、战争实景图、外国国旗与阵营对立。
8. 舆情风险：是否易被玩家解读为抄袭、媚俗、夹带、辱梗、玩烂梗、节日不合时宜、消费社会情绪。
9. 敏感日期风险：发布日期与严肃纪念日/灾难纪念日/社会热点是否冲突。

### 6. 风险等级

统一使用以下等级：

- `P0 红线风险`：建议不得上线；涉及违法违规、重大政治/国家安全/严重侵权/严重色情赌博暴力等。
- `P1 高风险`：必须修改后复审；可能被平台驳回或引发明显舆情。
- `P2 中风险`：建议修改或补充证明；可控但存在被解读/投诉/误伤风险。
- `P3 低风险`：基本可过；保留常规注意事项。
- `OK 未见明显风险`：当前信息下未发现明显问题。

### 7. 输出报告

默认生成 HTML 报告，使用 `references/report-template.md` 中的结构。报告必须包含：

- 报告标题、审核日期、目标地区、素材用途、发布日期状态。
- 素材预览图：若用户提供图片，必须嵌入到 HTML 中；优先复制到报告同目录的 `assets/` 或使用 base64 data URI。
- 素材逐项描述。
- 风险总览表。
- 单素材风险明细表：风险维度、风险等级、问题描述、依据、修改建议。
- 知识库依据：优先列出本地内置知识库文件名与条目；如本次同步读取了乐享，再列出实际读取到的乐享知识库条目名称。
- 外部检索依据：列出核心公开来源名称，不必堆砌链接。
- 敏感日期排查：发布日期已定则做定点排查；未定则给出通用避让清单。
- 舆情风险权衡分析。
- 综合结论：可上线 / 修改后上线 / 不建议上线 / 需法务复核。
- 下一步动作清单。
- 免责声明：报告供合规初筛参考，最终以法务/合规部门正式意见为准。

### 8. HTML视觉要求

报告风格保持专业、清晰、适合汇报：

- 中文字体优先：PingFang SC、Microsoft YaHei、sans-serif。
- 白底卡片、圆角、轻阴影、清晰分区。
- 风险标签使用颜色区分：P0 红、P1 深橙、P2 橙、P3 蓝/绿、OK 绿。
- 图片区域使用边框、圆角、说明文字。
- 表格避免过宽；必要时允许横向滚动。

### 9. 交付要求

完成后必须：

- 保存 HTML 到当前工作空间，文件名建议：`游戏素材合规审核报告_YYYYMMDD.html`。
- 对 HTML 使用预览能力打开。
- 将 HTML 作为附件交付。
- 如果还生成图片副本或其他支持文件，也一并交付。

## References

- `references/source-docs.md`：本地知识库目录与更新说明。
- `references/source-docs-2026-global-game-legal-regulatory.md`：2026 年全球游戏行业法律监管动态抽取内容，覆盖 AI监管、版号、防沉迷、战利品箱/扭蛋、韩国本地代表、欧盟消费者保护等。
- `references/source-docs-global-game-compliance-trends.md`：全球游戏市场合规监管趋势分析抽取内容，覆盖 2024-2026 海外重点市场监管趋势。
- `references/source-docs-online-game-company-full-process-compliance.md`：网络游戏公司全流程合规指南抽取内容，覆盖立项、研发、版号、运营、广告、未成年人保护、数据安全等。
- `references/source-docs-game-company-crisis-pr.md`：游戏公司危机公关应对策略抽取内容，覆盖舆情分级、响应机制、声明口径、玩家沟通与复盘。
- `references/source-docs-game-ip-protection-cases.md`：游戏知识产权保护与侵权案例抽取内容，覆盖著作权、商标、商业秘密、授权合同和侵权案例。
- `references/source-docs-china-game-policy-summary.md`：中国游戏行业政策汇总抽取内容，覆盖版号、内容审核、未成年人保护、个人信息、直播与广告要求。
- `references/source-docs-global-cultural-risk.md`：已导入的《【FOR CODM】全球文化、宗教、合规等风险提示手册（持续更新）》Excel抽取内容，包含 32 条风险条目。
- `references/source-docs-female-exposure-rules.md`：女性角色局部露肤审核细化规则，包含胸部红线区禁止露肤判定口径。
- `assets/female-exposure-redline-example.png`：女性胸部红线区露肤判断示例图。
- `assets/icon.png`：Skill 图标，盾牌、手柄、审核清单和勋章组合图，适合作为游戏素材预审的识别图标。
- `icon.png`：根目录图标副本，便于不同导入/展示方式识别。
- `references/knowledge-baseline.md`：从乐享知识库沉淀的核心审核规则与常见风险。
- `references/report-template.md`：HTML报告结构与字段要求。

## Important cautions

- 不要把无法确认的素材直接判定为违规；使用「疑似」「需确认」「建议复核」表达不确定性。
- 看到国旗、军旗、真实地图、真实战争、现实政治冲突、宗教符号、第三方IP时，提高风险等级并要求复核。
- 审核女性角色素材时，必须检查 `references/source-docs-female-exposure-rules.md` 定义的胸部敏感露肤红线区；该区域出现明显露肤时，强曝光宣发渠道至少按 P1 高风险处理。
- 中国大陆发行素材默认从严审核，尤其是广告投放素材。
- 用户未提供发布日期时，不要编造日期；输出通用避让清单。
- 用户未提供授权证明时，第三方IP一律按「需授权证明，否则建议替换」处理。
