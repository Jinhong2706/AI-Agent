# Research Methodology Precedent / 研究方法论沉淀（参考样例）

> ⚠️ **Important / 重要提醒**：This document records methodology lessons from a real research project (a console publishing study covering 60+ cases). It is a **reference precedent, NOT a template**. Do NOT directly apply the path taxonomy mentioned here to new research — every research must induce its own taxonomy from current data.
>
> 本文档记录了一次真实研究项目（覆盖 60+ 案例的主机推广研究）沉淀下来的方法论经验。这是**参考样例，不是模板**——下次研究新课题时不要直接套用本案例的路径分类，必须从新数据归纳。

---

## 一、可借鉴的方法论 / Reusable Methodology

### 1. 三智能体协作流程 / Three-agent Collaboration

将研究拆成三个 Agent 角色（即使实际是同一个 AI 在做）：

- **Agent 1（案例池 / Case Pool）**：横向扫案例，做结构化清单
- **Agent 2（单案分析 / Single-case Analysis）**：深度分析每个案例
- **Agent 3（综合洞察 / Synthesis）**：跨案归纳路径

每个 Agent 的产物分目录存放（`01_case_pool/` / `02_case_analysis/` / `03_synthesis/`），便于追溯。

### 2. 分类轴迭代史 / Taxonomy Axis Iteration

主机推广研究的分类轴经历了 3 次大改：

| 版本 | 分类轴 | 失败/成功原因 |
|---|---|---|
| **v1** | 按平台分（Sony / Nintendo / Microsoft）| ❌ 平台间动作太多重叠（例如全平台同步首发跨多个平台），分类不干净 |
| **v2** | 按资源类型分（线上商店 / 线下展会 / 硬件实体）| ⚠️ 部分有用，但混淆了"曝光手段"和"策略选择"——首发独占、跨平台联机这类是策略不是曝光 |
| **v3** | 按发行动作类型分（5 条路径）| ✅ 最终稳定，每条路径有明确判断标准 |

**关键收获 / Key takeaway**：第一版分类轴不一定对，**敢于在第三轮研究时把整个框架推翻重排**——这是综合洞察阶段最重要的能力。

### 3. F2P 与付费 3A 分开建立分类 / Separate F2P and Premium Taxonomies

虽然都是主机推广，但 F2P 和付费 3A 的发行逻辑差异巨大，无法用同一套分类。最终分两套：

**F2P 五路径**（仅作参考，下次研究不可直接套用）：
1. 深度绑定 Sony PS / Deep PS Partnership
2. PC 顺带主机 / PC-First Console Add-on
3. 突击上线 / Shadow Drop
4. 主机延迟二次首发 / Console Delayed Re-Launch
5. Switch 先行 / Switch First (with platform IP licensing)

**付费 3A 五路径**（仅作参考）：
1. 产品力驱动零广告型 / Product-Driven Zero-Marketing
2. 长线打磨口碑长跑型 / Long-Polish Word-of-Mouth
3. 第一方独占大作高举高打型 / First-Party Exclusive Heavyweight
4. 本土文化输出型 / Local Culture Export
5. 诚意驱动型 / Sincerity-Driven (cross-platform play, free demos, etc.)

⚠️ 这两套分类是**当时主机推广这个题目下归纳出的**，不一定适合下次的赛道（手游买量 / 电竞赛事 / IP 运营等都需要重新归纳）。

### 4. 多维度分析（独立维度） / Multi-dimensional Analysis (Orthogonal Axis)

除了"发行动作类型"五路径，还从同一批案例里归纳出"主机厂商合作 11 种模式"作为独立分析维度（线上商店 5 种 + 线下展会 2 种 + 硬件与实体 4 种）。

**关键收获**：同一份案例数据可以从多个正交维度归纳——下次研究也可以这样做，多维度合在一起会比单一维度更立体。

### 5. 应用层落地 / Application Layer

研究做到最后，落地到一个具体产品的发行启示。结构精简为：

- **TL;DR 一句话版前置 / TL;DR upfront**——首屏抓住核心
- 当前现状（含合作机制详解）/ Current state with mechanism explanations
- 阶段 1（参考某路径）/ Stage 1 (referencing one path)
- 阶段 2（参考某些路径组合 + 钩子触发条件）/ Stage 2 (path combinations + trigger conditions)
- 不写"不适合产品的路径"清单
- 不写验证指标和退出条件
- 整体定位"启示型思考"，不是正式方案

---

## 二、可借鉴的视觉规范 / Visual Spec

HTML 集合页的视觉细节：

- 单文件无外部依赖（双击可开）/ Single self-contained HTML
- 左侧暗色固定 sidebar + 右侧浅灰几何主区 / Dark sidebar + light geometric main area
- Hero 渐变区按视图区分颜色（综述蓝 / F2P 绿 / 付费 3A 橙 / 应用层蓝青）/ Per-view Hero gradient
- 路径卡彩色左边框（每条路径不同颜色）/ Colored left border per path
- 关键传播素材黄底高亮（`<span class="highlight">`）/ Yellow highlight on viral phrases
- 结论框绿底 + 💡 / 警告框红底 + ⚠️ / Conclusion green + Warning red
- 案例库导航 emoji 区分（🎮 F2P / 🕹️ 付费 3A / 🎯 应用层）/ Emoji per case category
- 路径前缀（"路径 1 · 案例游戏"）/ Path prefix in nav
- 每个案例视图底部"📚 数据来源与参考资料" / Source & references block per case

---

## 三、踩过的 8 个坑（避免下次再踩）/ 8 Pitfalls to Avoid

### 坑 1：路径分类首版不能预设 / Don't preset taxonomy on v1

**EN**: Initial taxonomy was "split by platform (Sony/Nintendo/MS)" but quickly proved wrong because actions overlap across platforms. Lesson: **observe data first, induce taxonomy second**, never bring presupposed conclusions.

**中文**：第一次给的分类是"按平台分"，被推翻；第二次给"按资源类型"也只是部分对。**正确做法是先观察数据、再归纳**，不要带着结论去找证据。

### 坑 2：反面教材一开始单独立章 / Don't make counter-examples standalone

**EN**: Initially I created a "counter-examples" chapter listing Concord / Suicide Squad failures. It distracted readers. Lesson: **counter-examples should be embedded as foil within main paths, never standalone**.

**中文**：最初我把反面教材单独立了一章"反面教材清单"，但分散读者注意力。**正确做法是反面教材在路径里反衬，不单独立章**。

### 坑 3：服务对象的区域 / 渠道偏好必须前置确认 / Confirm region/channel preference upfront

**EN**: I initially recommended overseas trade shows (Cologne / PAX / TGS) for a project that was actually targeting one specific local market. Lesson: **the region/audience of the service target dictates which channels are viable** — never assume from the case mother.

**中文**：服务对象的区域和渠道偏好必须前置确认。同一案例在不同区域市场的渠道选择完全不同。**正确做法**：推广动作的渠道列表必须基于服务对象所在区域回答，不能从案例母本的市场假设照搬。

### 坑 4：长跑案例叙事不要简化为线性因果 / Don't flatten long-running cases into linear causality

**EN**: I initially wrote a long-running F2P case as "first prove revenue, then earn platform resources". The user corrected me — Day-One simultaneous launch on console was the key early commitment, not a later reward. Lesson: **distinguish "early commitment" from "long-term accumulation"; don't flatten them as linear cause-effect**.

**中文**：最初我把某长跑 F2P 案例写成"先证明能给平台带来收入和硬件价值，再换平台资源"——但用户指出 Day One 同步首发主机本身就是关键动作，平台一开始就重视该项目。**正确做法**：把"早期承诺"和"长期合作积累"分清楚，不能简化为"先证明再换资源"的线性叙事。

### 坑 5：不同合作机制不能混为一谈 / Don't conflate cooperation tiers

**EN**: I initially wrote "this F2P's PS Plus pack is similar to mounting a Steam Bundle" — wrong. PS Plus pack is a platform member-benefit slot (free for subscribers, jointly announced by platform), one tier heavier than a Steam discount Bundle. Lesson: **carefully distinguish cooperation mechanism tiers — surface similarity hides structural difference**.

**中文**：最初我把某产品的 PS Plus 加成包写成"和挂 Steam Bundle 类似的常规上架动作"——但 PS Plus 包是平台的会员福利位，玩家免费领取，比 Steam 打折 Bundle 重一档。**正确做法**：仔细区分合作机制层级，不是所有"上 Bundle"都一样。

### 坑 6：综合洞察不能写得过于精简 / Don't make synthesis too thin

**EN**: My first synthesis had only path names + one-line core logic. Readers wouldn't open every single-case MD, so synthesis lacked enough actionable info. Lesson: **synthesis MD must contain each representative case's specific actions** — goal is "reader only reads synthesis and still understands every path".

**中文**：最初综合洞察 MD 只写了路径名 + 一段核心逻辑，用户读完不打算翻每个单案 MD，所以信息密度不够。**正确做法**：综合洞察 MD 必须包含每个代表案例的具体动作——目标是"读者只看综合洞察也能理解每条路线"。

### 坑 7：标题避免英文术语和口语化 / Avoid English jargon and casual tone in titles

**EN**: I used "TL;DR · One-Liner Version" as a section title. The user replaced it with a more direct Chinese title. Lesson: **in formal-ish reports, avoid English jargon and casual phrasing in section titles** — match register to audience.

**中文**：英文 TL;DR 缩写在汇报场景里不专业，用户改成了更直接的中文标题。**正确做法**：标题避免口语化和英文术语——风格要和读者匹配。

### 坑 8：分类轴维度内部要一致 / Keep taxonomy dimension internally consistent

**EN**: An early v2 taxonomy mixed "exposure path" (online store / offline event / hardware) with "strategy choice" (exclusivity, cross-play). This is two dimensions in one axis — wrong. Lesson: **keep taxonomy axis on a single dimension; don't mix exposure and strategy in one axis**.

**中文**：最初的分类轴里包含了"首发独占策略"和"跨平台互通"两类，但这是"策略选择"不是"曝光路径"——必须删除策略类，保留曝光类。**正确做法**：分类轴要内部一致——所有路径要在同一维度（不能既包含曝光又包含策略）。

---

## 四、典型产物结构 / Typical Output Structure

```
{your-research-project}/
├── 01_case_pool/          # Agent 1 case pool list
├── 02_case_analysis/      # Agent 2 single-case MDs (30+)
├── 03_synthesis/          # Agent 3 synthesis (paths + cooperation modes + application layer)
├── 04_html_export/        # HTML collection page
└── shared/internal_reports/  # Internal first-hand reports (do NOT distribute externally)
```

---

## 最后提醒 / Final Reminder

下次跑新研究时 / When running new research:

- ✅ **Borrow / 借鉴**：workflow（5 阶段流程）、写作风格、HTML 视觉规范、决策选项化提问
- ❌ **Don't directly copy / 不要直接套用**：上面提到的 F2P 五路径 / 付费 3A 五路径 / 11 合作模式 — these were induced from the specific console publishing topic at that time, may not fit the next research

**每次都要从立题阶段重新跑一遍，分类轴必须从新数据归纳得出 / Always restart from topic alignment; induce the taxonomy from new data.**
