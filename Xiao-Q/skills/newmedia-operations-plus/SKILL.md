---
name: newmedia-operations
description: |
  全链路新媒体运营技能，覆盖行业分析→竞品分析→账号养号→爆款内容创作→互动钩子设计的完整运营闭环。每步自动写入 llm-wiki 结构化知识库、可选写入 ima 笔记，结合 opencli 浏览器直操控，持续积累可复用的运营知识资产。适用于抖音、视频号、小红书三大平台。
  
  触发场景：
  - 用户说"帮我做新媒体运营方案"
  - 用户说"分析竞品账号"
  - 用户说"帮我养号" / "账号冷启动"
  - 用户说"帮我写爆款内容" / "二次创作"
  - 用户说"设计互动钩子" / "提升评论互动"
  - 用户说"做行业分析报告"
  - 用户说"监控对标账号"
  - 用户提供了品牌/产品 PPT，要求制定内容运营策略
---

# 全链路新媒体运营

## 🚀 初始化检查（每次启动必做）

### ⛔ 必须：检查 llm-wiki（强制安装）

> **llm-wiki 是本 skill 的核心知识积累工具，必须安装后才能继续。**

检查 `skillhub --version` 和 `llm-wiki` 是否可用。

**若 SkillHub CLI 未安装**：
```
⛔ 检测到 SkillHub CLI 尚未安装，无法继续运营流程。

请先安装 SkillHub CLI（仅安装 CLI，不安装图形界面）：
📖 安装指南：https://skillhub.cn/install/skillhub.md

完成后运行 skillhub --version 验证，然后告诉我。
```

**若 SkillHub 已安装但 llm-wiki 未安装**：
```
⛔ 检测到 llm-wiki 技能未安装，无法继续运营流程。

请执行安装命令：
skillhub install llm-wiki

完成后告诉我，我将引导初始化 wiki 知识库目录结构。
```

**若 llm-wiki 已安装**：初始化 wiki 目录（若首次使用）：
```
wiki/
├── index.md、log.md
├── 行业分析/ 竞品/ 内容策略/ 话术库/ 客户档案/
```
详细说明见 [LLM_WIKI.md](references/LLM_WIKI.md)

---

### ✅ 推荐：检查 ima-skill

检查 `~/.cursor/skills/` 下是否存在 `ima-skill`。

**若未安装**，提示（可跳过）：
```
📦 安装：https://app-dl.ima.qq.com/skills/ima-skills-1.1.2.zip
🔑 API Key：https://ima.qq.com/agent-interface
```
已安装则确认 API Key 已配置、「新媒体运营」分类已创建。

### ✅ 推荐：检查 opencli

运行 `opencli list` 验证。未安装则提示：
```
📦 安装：https://github.com/jackwener/opencli  （可跳过，将用内置脚本替代）
```
详细说明见 [IMA_KNOWLEDGE.md](references/IMA_KNOWLEDGE.md) | [OPENCLI.md](references/OPENCLI.md)

---

## 知识管理策略（全局）

**每步执行节奏**：

```
开始前：llm-wiki Query + ima 检索 → 利用历史积累，避免重复工作
执行中：数据获取（全量执行，见下方规则）
完成后：llm-wiki Ingest（自动，必须执行）+ ima 保存（询问用户）
```

**数据获取优先级**：
```
① llm-wiki Query + ima 检索  → 历史积累优先
② 5118关键词挖掘              → opencli web 调用，每个词跑全网/抖音/小红书三平台
③ opencli 平台直接抓取        → 有浏览器登录态时最优
④ 内置 Python 脚本           → 批量处理和清洗
⑤ WebSearch / WebFetch       → 兜底
```

### ⚡ 查询泛化原则（必须遵守）

> **任何搜索任务，必须将原词扩展为 3-5 个相似 query，全部执行，不允许只跑单一查询词。**

**泛化维度**（从目标词派生）：
```
原词       →  [目标词]（直接搜索）
推荐型     →  [目标词] 推荐 / 哪个好 / 排行榜
痛点/疑问型 →  [目标词] 怎么选 / 踩雷 / 注意事项
人群细分型 →  [人群特征] + [目标词]（如：敏感肌+护肤品）
趋势/结果型 →  [目标词] 趋势 2025 / 效果 / 多久见效
```

每个 query 维度，在以下数据源各执行一遍（目标：10+数据源、30+query 组合）：
- 5118（全网 / 抖音 / 小红书 三平台）
- 小红书 / 抖音 / 微博 / 知乎 / B站 / 36氪（via opencli）
- 内置脚本（批量爬取）
- WebSearch / WebFetch（兜底）

详细模板见 [QUERY_EXPANSION.md](references/QUERY_EXPANSION.md)

**llm-wiki vs ima 分工**：
- **llm-wiki**：结构化 wiki 页面，持续编译更新，自动执行（爆款标题库/违禁词库/竞品档案）
- **ima**：快速检索笔记，选择性保存（报告、临时性内容）

---

## 内置脚本（scripts/ 目录）

```
fetch_xiaohongshu.py / fetch_douyin.py / fetch_weibo.py / fetch_wechat_video.py
fetch_ecommerce_reviews.py / clean_data.py / extract_demands.py
analyze_industry.py / monitor_competitors.py
detect_forbidden_words.py / generate_hook_templates.py
```

---

## 工作流程总览

```
[初始化] llm-wiki（强制）→ ima-skill（推荐）→ opencli（推荐）
    ↓
Step 1: 行业分析  →  Step 2: 竞品分析  →  Step 3: 账号养号
                                                  ↓
                    Step 5: 互动钩子设计  ←  Step 4: 爆款内容创作

每步节奏：Query(wiki+ima) → 执行 → Ingest(wiki,自动) + 保存(ima,询问)
```

---

## Step 1：行业分析

详细指南：[INDUSTRY_ANALYSIS.md](references/INDUSTRY_ANALYSIS.md)

### 【开始前】双检索
```
llm-wiki Query：「[行业名]的用户画像、关键词体系、市场规模」
  → 参考 wiki/行业分析/[行业名].md

ima 搜索：「[行业名] 分析报告」「[行业名] 用户画像」
```
有历史内容 → 增量更新；无内容 → 执行完整分析。

### 核心任务
1. 读取客户 PPT/资料，识别核心诉求（涨粉/引流/转化/品牌曝光）
2. 了解现有账号状态（抖音/视频号/小红书基础、历史内容方向）
3. 调研行业大盘数据

### 泛化查询组（必须全部执行）

以「[品类词]」为例，生成 5 个查询维度，每个维度跑全部数据源：
```
Q1: [品类词]                    ← 原词
Q2: [品类词] 推荐 / 哪个好      ← 推荐型
Q3: [人群] + [品类词]           ← 人群细分（如：敏感肌护肤品）
Q4: [品类词] 怎么选 / 踩雷      ← 痛点/疑问型
Q5: [品类词] 趋势 2025 / 排行榜 ← 趋势/榜单型
```

### 数据获取（逐一执行，全量覆盖）

| 来源 | opencli 命令 | 说明 |
|------|-------------|------|
| **5118全网** | `opencli web read "https://www.5118.com/ci?keyword=[词]"` | 长尾词/暴涨词 |
| **5118抖音** | 同上，页面切换「抖音」 | 抖音平台高指数词 |
| **5118小红书** | 同上，页面切换「小红书」 | 小红书平台高指数词 |
| 小红书 | `opencli xiaohongshu search "[词]"` × Q1~Q5 | 真实笔记内容 |
| 抖音 | `opencli douyin videos --keyword "[词]"` × Q1~Q5 | 视频内容热度 |
| 微博 | `opencli weibo hot` / `opencli weibo search "[词]"` | 舆情热搜 |
| 知乎 | `opencli zhihu hot` / `opencli zhihu search "[词]"` | 深度讨论 |
| 36氪/B站 | `opencli 36kr hot` / `opencli bilibili ranking` | 行业资讯 |
| 艾媒报告 | WebFetch `https://www.iiimedia.cn/` | 行业大盘数据 |
| 批量脚本 | `python scripts/fetch_xiaohongshu.py` / `fetch_douyin.py` | 大量原始数据 |

**输出**：[templates/industry_report.md](templates/industry_report.md)

### 【完成后】双写入
```
① llm-wiki Ingest（自动执行）→ wiki/行业分析/[行业名].md
   写入：市场规模、用户画像、关键词体系、平台趋势（增量更新，标注变化）
   更新：wiki/log.md 记录本次操作

② ima 保存（询问用户）：
   A. 新笔记「[行业名]-行业分析报告-[日期]」
   B. 追加到已有笔记  C. 暂不保存
```

---

## Step 2：竞品分析

详细指南：[COMPETITOR_ANALYSIS.md](references/COMPETITOR_ANALYSIS.md)

### 【开始前】双检索
```
llm-wiki Query：「[竞品名]的内容策略、爆款特征、用户痛点」
  → 参考 wiki/竞品/[账号名].md

ima 搜索：「[竞品名] 账号分析」「[行业] 爆款拆解」
```

### 泛化查询组（必须全部执行）

以「[竞品名]」为例，生成 5 个查询维度：
```
Q1: [竞品名]                           ← 品牌名直接搜索
Q2: [竞品名] 怎么样 / 值得买吗         ← 评价型
Q3: [竞品名] vs [同类品牌]             ← 对比型
Q4: [竞品名] 踩雷 / 差评 / 缺点        ← 负面/差评型
Q5: [竞品名] [核心功能/人群]           ← 功能/场景型
```

### 数据获取（逐一执行，全量覆盖）

| 来源 | opencli 命令 | 说明 |
|------|-------------|------|
| **5118全网** | `opencli web read "https://www.5118.com/ci?keyword=[竞品名]"` | 了解用户真实搜索习惯 |
| **5118抖音/小红书** | 同上切换平台 | 平台用户搜索词对比 |
| 小红书竞品账号 | `opencli xiaohongshu user "[账号]"` / `opencli xiaohongshu creator-notes-summary` | 账号数据 |
| 小红书竞品内容 | `opencli xiaohongshu search "[词]"` × Q1~Q5 | 用户真实评价 |
| 抖音竞品账号 | `opencli douyin profile` / `opencli douyin stats` / `opencli douyin videos` | 账号&内容数据 |
| 微博竞品舆情 | `opencli weibo search "[词]"` × Q1/Q4 | 实时负面/正面声音 |
| 知乎竞品讨论 | `opencli zhihu search "[词]"` × Q2/Q3 | 深度对比分析 |
| 电商评价 | `opencli jd item "[产品]"` / `opencli smzdm search "[产品]"` | 购买评价 |
| 批量脚本 | `python scripts/fetch_ecommerce_reviews.py` | 大量差评数据 |

**实时监测**：`python scripts/monitor_competitors.py --accounts templates/accounts_config.json`

### 【完成后】双写入
```
① llm-wiki Ingest（自动执行）→ wiki/竞品/[账号名].md
   写入：本次数据快照、爆款拆解（追加）、用户痛点（合并）、策略变化标注
   更新：wiki/竞品/竞品策略矩阵.md（提炼跨账号规律）

② ima 保存（询问用户）：
   A. 新笔记「[行业]-竞品分析-[日期]」
   B. 追加到「[竞品名] 账号分析」  C. 暂不保存
```

---

## Step 3：账号养号

详细指南：[ACCOUNT_NURTURING.md](references/ACCOUNT_NURTURING.md)

### 【开始前】双检索
```
llm-wiki Query：「[平台]养号权重提升的关键行为有哪些」
  → 参考 wiki/行业分析/[行业名].md（内含平台运营规律）

ima 搜索：「养号策略」「[平台] 冷启动」
```

### 资料完善 & 每日养号计划

- [ ] 实名认证 / 昵称（品牌+品类+关键词）/ 头像（高清）/ 简介 / 行业标签

| 行为 | 数量 | opencli 辅助 |
|------|------|-------------|
| 搜索核心关键词 | 每日 | `opencli xiaohongshu search "[词]"` |
| 浏览行业内容（完播≥80%） | 10+ | `opencli xiaohongshu feed` / `opencli douyin videos` |
| 查看互动通知 | 每日 | `opencli xiaohongshu notifications` |
| 了解平台活动 | 每日 | `opencli douyin activities` |

### 【完成后】双写入
```
① llm-wiki Ingest（自动执行）→ wiki/客户档案/[品牌名].md
   写入：账号设置记录、养号阶段计划、发现的平台规律

② ima 保存（询问用户）：
   A. 新笔记「[品牌名]-账号设置建议-[日期]」  B. 暂不保存
```

---

## Step 4：爆款内容创作

详细指南：[VIRAL_CONTENT.md](references/VIRAL_CONTENT.md)

### 【开始前】双检索
```
llm-wiki Query：「[行业]最有效的爆款标题公式和违禁词」
  → 参考 wiki/内容策略/爆款标题库.md、wiki/内容策略/违禁词库.md

ima 搜索：「[行业] 爆款标题」「违禁词库」「内容日历模板」
```
有历史标题库 → 直接复用拓展；有违禁词 → 合并使用。

### 泛化查询组（必须全部执行）

以「[品类词]」为例，生成 5 个内容方向查询：
```
Q1: [品类词]                        ← 行业大词
Q2: [品类词] 踩雷 / 避坑 / 种草     ← 避坑种草型
Q3: [品类词] 知识 / 成分 / 原理     ← 科普型
Q4: [品类词] + [当前热点/节日]      ← 热点融合型
Q5: 用了[品类词]后 / [品类词] 效果  ← 结果/反馈型
```

### 内容生产流程（全量执行）

1. **5118 关键词挖掘**（优先）：
   ```bash
   # 分别查询 Q1~Q5，切换全网/抖音/小红书三平台
   opencli web read "https://www.5118.com/ci?keyword=[Q1]"
   opencli web read "https://www.5118.com/ci?keyword=[Q2]"
   # ...依次执行 Q3/Q4/Q5
   # → 提取高指数词作为标题关键词
   ```

2. **热点选题**（全平台扫描）：
   ```bash
   opencli weibo hot        # 微博实时热搜
   opencli zhihu hot        # 知乎热榜
   opencli 36kr hot         # 36氪商业热点
   opencli bilibili hot     # B站热门
   opencli douyin hashtag "[行业标签]"  # 抖音话题热度
   ```

3. **爆款参考内容**（Q1~Q5 各搜一遍）：
   ```bash
   opencli xiaohongshu search "[词]" × Q1~Q5   # 小红书热门笔记
   opencli bilibili ranking                      # B站热门排行
   opencli zhihu search "[词]" × Q2/Q4          # 知乎高赞回答
   ```
   补充：WebFetch `https://www.yizhuan5.com/` / WebSearch `[词] site:weixin.qq.com`

3. **违禁词检测**：
   ```bash
   python scripts/detect_forbidden_words.py --text "[内容]" --platform [平台]
   ```

4. **二次创作**：保留逻辑/替换案例，结合客户产品，加入品牌专属卖点

5. **内容发布**：`opencli douyin publish` / `opencli xiaohongshu publish`

**内容类型矩阵**：

| 类型 | 标题公式 | 发布账号 |
|------|----------|----------|
| 品牌宣传 | 品牌名 + 核心价值 + 场景 | 大号（360浏览器） |
| 产品种草 | 痛点 + 解决方案 + 效果 | 小号1（QQ浏览器） |
| 科普知识 | 问题 + 答案 + 干货 | 小号2（谷歌浏览器） |
| 招商文章 | 机会 + 数据 + 行动号召 | 大号 |

### 【完成后】双写入
```
① llm-wiki Ingest（自动执行）：
   → wiki/内容策略/爆款标题库.md：追加本次新标题公式（注明行业/来源）
   → wiki/内容策略/违禁词库.md：追加新违禁词和替换建议
   → wiki/内容策略/内容模板库.md：追加优质模板
   → wiki/客户档案/[品牌名].md：更新内容策略章节

② ima 保存（询问用户，可多选）：
   A. 爆款标题库追加到「[行业]-爆款标题库」
   B. 30天日历新笔记「[品牌]-内容日历-[月份]」
   C. 违禁词追加到「通用-违禁词库」  D. 暂不保存
```

---

## Step 5：互动钩子设计

详细指南：[ENGAGEMENT_HOOKS.md](references/ENGAGEMENT_HOOKS.md)

### 【开始前】双检索
```
llm-wiki Query：「[行业]互动率最高的评论钩子和私域引导话术」
  → 参考 wiki/话术库/互动钩子.md、wiki/话术库/私域引导话术.md

ima 搜索：「互动话术」「评论钩子」「私域引导」「用户唤醒」
```

### 泛化查询组（必须全部执行）

以「[品类词]」为例，挖掘用户真实痛点和疑问：
```
Q1: [品类词] 痛点 / 困扰           ← 痛点型
Q2: [品类词] 怎么 / 为什么         ← 疑问型
Q3: [品类词] 哪个好 / 怎么选       ← 决策型
Q4: [品类词] 有效果吗 / 多久见效   ← 效果预期型
Q5: [场景] 用什么 [品类词]         ← 使用场景型
```

### 数据支撑 & 话术生成（全量执行）

```bash
# 5118 挖掘用户真实痛点词
opencli web read "https://www.5118.com/ci?keyword=[品类词] 痛点"  # Q1
opencli web read "https://www.5118.com/ci?keyword=[品类词] 怎么"  # Q2
# → 提取高频疑问词作为互动钩子设计依据

# opencli 收集真实互动数据
opencli xiaohongshu creator-notes-summary       # 笔记互动数据汇总
opencli douyin stats                            # 各视频互动对比
opencli xiaohongshu creator-note-detail [id]    # 竞品评论区声音
opencli zhihu search "[词]" × Q1~Q5            # 知乎真实用户提问

# 生成定制话术
python scripts/generate_hook_templates.py \
  --industry "[行业]" --brand "[品牌]" \
  --pain_point "[核心痛点]" --resource "[资料名]" \
  --output data/hooks_[品牌名].md
```

**私域引导**：欢迎语 + 7天未互动唤醒 + 强意向识别转人工

### 【完成后】双写入
```
① llm-wiki Ingest（自动执行）：
   → wiki/话术库/互动钩子.md：追加新钩子（注明行业/场景/效果）
   → wiki/话术库/私域引导话术.md：追加欢迎语/唤醒/转人工话术
   → wiki/客户档案/[品牌名].md：更新私域策略章节

② ima 保存（询问用户）：
   A. 新笔记「[品牌/行业]-互动话术库-[日期]」
   B. 追加到「通用-互动话术模板库」  C. 暂不保存
```

---

## 输出 & 知识资产

### 运营方案报告
```
运营方案报告/
├── 01_行业分析报告.md
├── 02_竞品分析报告.md
├── 03_账号设置建议.md
├── 04_内容创作计划.md（含30天日历）
└── 05_互动话术库.md
```

### 全套完成后
```
① llm-wiki Lint：检查 wiki 目录完整性、矛盾标注、过期内容
② ima 询问：是否将整套方案导入「[品牌名] 运营档案」笔记
③ wiki/log.md：记录本次完整运营分析的时间线摘要
```

---

## 参考资料

- [QUERY_EXPANSION.md](references/QUERY_EXPANSION.md) - **查询泛化原则 + 5118使用指南 + 各步全量执行清单**
- [LLM_WIKI.md](references/LLM_WIKI.md) - llm-wiki 安装、三大操作、各步 wiki 写入指南
- [OPENCLI.md](references/OPENCLI.md) - opencli 安装 + 5118调用 + 各步命令速查
- [IMA_KNOWLEDGE.md](references/IMA_KNOWLEDGE.md) - ima知识库集成指南
- [INDUSTRY_ANALYSIS.md](references/INDUSTRY_ANALYSIS.md) - 行业分析完整指南
- [COMPETITOR_ANALYSIS.md](references/COMPETITOR_ANALYSIS.md) - 竞品分析框架
- [ACCOUNT_NURTURING.md](references/ACCOUNT_NURTURING.md) - 账号养号操作手册
- [VIRAL_CONTENT.md](references/VIRAL_CONTENT.md) - 爆款内容创作指南
- [ENGAGEMENT_HOOKS.md](references/ENGAGEMENT_HOOKS.md) - 互动钩子设计与话术库
