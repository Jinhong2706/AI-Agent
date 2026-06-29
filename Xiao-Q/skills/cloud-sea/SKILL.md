---
name: cloud-sea
description: '北京云海预测 — 输入「云海」即可预测北京16峰云海概率。自动抓取气象数据、计算雾底雾顶、生成完整报告。无需手动配置，零门槛使用。【强制触发关键词】云海、云海预测、云海概率、雾海、山地云海、日出云海、云海报告、妙峰山云海、雾灵山云海、海坨山云海、东灵山云海、白石山云海、百花山云海、云蒙山云海、日出质量。功能：多源气象数据、三重核实、12因子评分、雾底计算、雾型诊断、HTML可视化报告。
---

# ☁️ 云海预测 — 零门槛快速开始

> **只需说一句话，自动完成全部流程。** 无需配置、无需指定山峰、无需调用工具。


## ⚡ 最简用法（一句话搞定）

| 你说什么 | 我做什么 |
|---------|---------|
| **「云海预测」** | 自动抓取北京16峰最新气象数据 → 计算概率 → 展示完整报告 |
| **「云海概率」** | 同上，简洁摘要版 |
| **「日出云海」** | 专项分析日出时段云海质量 |
| **「妙峰山云海」** | 精细分析指定山峰 |
| **⚠️ 注意** | 默认16峰不含三香山/佛爷顶/玉渡山/凤凰坟/煤山等非官方山峰 |

## 📋 完整流程（Step 1→5）


```
Step 1  判断任务类型（默认16峰 / 指定山峰 / 日出专项）
   ↓
Step 2  自动抓取 Open-Meteo 气象数据（含露点温度 dew_point_2m）
   ↓
Step 3  12因子综合评分 + 通透度评估
   ↓
Step 4  生成完整 Markdown 报告并展示
   ↓
Step 5  生成 HTML 可视化报告（可选）
```

## 🎯 关键规则（防止出错）

1. **露点温度必须来自 API**，绝不假设
2. **雾顶公式**：`雾顶 = 气象站海拔 + 雾底高度(LCL) + 100m`
3. **山在雾上 = 山顶差 > 0**，山顶差 < 0 说明在雾中看不见
4. **通透度 ≤ 4.0 → 灰霾警告**，即使有云海视觉也差
5. **长城段（金山岭/箭扣）海拔仅 900-1100m**，在辐射雾雾顶(1500-2500m)之下，无云海可见

## 📁 文件结构（供参考）

```
references/peaks.json   ← 16峰官方坐标（自动引用，无需配置）
references/report-template.md  ← 报告模板
scripts/weather_fetch.py      ← 数据获取
scripts/analyzer.py           ← 评分计算
scripts/report_gen.py         ← HTML 生成
```

---

# Cloud Sea 云海预测技能

## ⚡ 核心规则速查（必读）

> 以下规则是云海预测的生死线，每次执行必须遵守。

| # | 规则 | 说明 |
|:--:|------|------|
| 1 | **dew_point_2m 生死线** | 必须从 Open-Meteo API 实测获取，绝不假设。假设 Td=7°C 曾导致云底估算错误 1200m |
| 2 | **雾顶公式** | `fog_top_msl = station_elev + LCL_ag + 100m`（固定雾厚100m，不用 summit_elev） |
| 3 | **LCL V2.0 三层融合** | ECMWF Layer1 + CMA Layer2 + ENS Layer3 自动融合，已取代旧版三重核实 |
| 4 | **通透度阈值** | 评分 ≤4.0 时必须显示灰霾警告；PM2.5>75 标注"灰白为主"；AOD>0.5 标注"远景不可见" |
| 5 | **任务分流** | 日出任务（关键词"云顶高度"/"高云"/"AQI"/"日出质量"）→ 直接跳到 Step 3.5 |
| 6 | **JSON 峰名编码** | weather_data_*.json 中峰名 key 可能乱码，遍历 peaks 取 `.peak` 字段匹配 |
| 7 | **数据复制检测** | 多文件气象数据相同时，对比 hourly[9+] 验证真实性 |
| 8 | **日出评分修正** | above_fog=True + lcl>1500m + RH<65% → 扣-15分（干燥气团中LCL虚高，above_fog为假阳性）|
| 9 | **主会话报告格式** | 主会话 Markdown 输出**强制**使用 `references/report-template.md` 模板，不得省略模块。每次输出前必须先 `read` 模板文件。 |
| 10 | **【强制步骤】主会话显示完整报告** | 每次云海预测完成后，**必须**使用 `read` 工具读取保存的报告文件，然后将文件内容**直接写入 AI 回复中**。`read` 工具的结果显示在工具调用结果中，但必须将内容复制到 AI 的回复文本中。 |
| 11 | **执行检查清单（每步必须打勾）** | 见下方检查清单，每完成一步标记✅，全部✅才能结束 |
| 12 | **【强制】仅用官方16峰** | 报告只能包含 `references/peaks.json` 中的16座官方山峰。禁止添加任何非官方山峰（如三香山、佛爷顶、玉渡山、凤凰坟、煤山等）。用户指定非官方山峰时单独处理，不混入16峰排名表 |

---

## ✅ 执行检查清单（每次预测必须逐项确认）

> **这是防止跳步骤的核心机制。每次云海预测必须逐项打勾，全部✅才能结束任务。**

```
□ Step 1: 判断任务类型（云海预测/日出专项/对比/核实/原理/雾型）
□ Step 2-Step 2: LCL V2.0 三层融合（ECMWF Layer1 + CMA Layer2 + ENS Layer3）
□
 Step 3: 12因子评分计算 + 通透度评估
□ Step 4-1: read references/report-template.md（不读模板=零分）
□ Step 4-2: 按模板逐节填充（16峰排名+雾型+气象+TOP3逐时+行程+装备+结论+速查）
□ Step 4-3: 保存到 cloud-sea-{date}.md
□ Step 4-4: read 保存的报告文件 → 完整写入 AI 回复
□ Step 5: 生成 HTML 可视化报告
```

---

## 执行流程（按顺序执行）

### Step 1 - 判断任务类型

| 用户需求 | 触发关键词 | 输出 |
|---------|---------|------|
| 预测某天云海概率 | "云海"、"云海概率"、"本周云海" | Markdown 报告 + HTML 可视化报告 |
| **预测日出云海质量** | **"日出"、"日出质量"、"云顶高度"、"高云/中云/低云"、"AQI 日出"、"雾凇日出"** | **日出专项报告（含云层高度分类、高/中/低云型分析、大气通透度、雾层日出序列）** |
| 对比多个观测点 | 多地点对比分析（含各站雾底/雾顶精确值）|
| 更新已知预测 | 对比新旧数据，说明变化及修正原因 |
| 核实数据可靠性 | 三重核实专项报告 |
| 解释云海原理 | 气象学知识问答 |
| 判断雾/云海类型 | 辐射雾/上坡雾/平流雾/谷雾/锋面雾诊断 |

### Step 2 - LCL V2.0 三层融合数据获取（强制要求）

> **LCL V2.0 将三重核实内化为三层融合**，自动完成多源交叉验证，不再需要手动执行三轮核实。
> 每次预测自动调用 `weather_fetch.py`，内部完成全部三层融合逻辑。

#### LCL V2.0 三层融合架构

| 层级 | 数据源 | 方式 | 说明 |
|:----:|--------|------|------|
| **Layer 1** | **ECMWF IFS 0.25°** | Open-Meteo API (`models=ecmwf_ifs025`) | 欧洲中期天气预报中心，Windy 默认数据源，高精度数值模型 |
| **Layer 2** | **CMA 中国气象局** | Open-Meteo API（默认模型） | 国内权威实测数据，与 ECMWF 自动交叉验证 |
| **Layer 3** | **ENS 集合预报** | ECMWF 5成员采样 (`ecmwf_ensemble`) | 概率分布估算不确定性，减少单点预测偏差 |

> **注意**：`ecmwf_ifs04` (0.4°) 返回空数据，必须使用 `ecmwf_ifs025` (0.25°)。
>
> **山峰坐标详见 `references/peaks.json`（官方16峰，无需手动配置）。**

---

#### Layer 1：ECMWF IFS 0.25°（每个山峰独立，必做）

对每个山峰坐标调用 ECMWF 模型，**必须包含 `dew_point_2m`**：

```
GET https://api.open-meteo.com/v1/forecast
?latitude=<山峰纬>&longitude=<山峰经>
&models=ecmwf_ifs025
&hourly=temperature_2m,dew_point_2m,relative_humidity_2m,
     precipitation_probability,precipitation,
     wind_speed_10m,wind_direction_10m,cloud_cover,
     weather_code,surface_pressure
&daily=temperature_2m_max,temperature_2m_min
&timezone=Asia/Shanghai&forecast_days=7
```

**⚠️ dew_point_2m 是必取字段**：这是 ECMWF 直接测量的露点温度。当 RH=100% 且 T≈Td 时，LCL_ag≈0（雾在地面）。

---

#### Layer 2：CMA 中国气象局（与 Layer 1 并行）

> CMA 数据通过 Open-Meteo 默认模型获取，与 ECMWF Layer 1 自动交叉验证。
> **禁止使用城区站作为山地观测点的核实数据**——城区在逆温层上方，数据与山地存在系统性偏差。

通过 Open-Meteo 默认模型（综合多数据源）获取，与 Layer 1 并行执行：

```
GET https://api.open-meteo.com/v1/forecast
?latitude=<山峰纬>&longitude=<山峰经>
&hourly=temperature_2m,dew_point_2m,relative_humidity_2m,
     wind_speed_10m,wind_direction_10m,cloud_cover
&timezone=Asia/Shanghai&forecast_days=7
```

---

#### Layer 3：ENS 集合预报不确定性量化

> ENS（Ensemble）集合预报提供 5 个成员采样，自动量化 LCL 预测的不确定性。
> 当 ENS 标准差较大时，置信度降低，需在报告中标注不确定性。

**ENS 融合逻辑**：
- 对每个山峰调用 `ecmwf_ensemble` 获取 5 个成员
- 计算 LCL 均值（mean）和标准差（std）
- 最终 LCL = `Layer1 × 0.5 + Layer2 × 0.3 + ENS_mean × 0.2`（加权融合）
- ENS std > 300m → 标注「预测不确定性较高」

```
GET https://api.open-meteo.com/v1/forecast
?latitude=<山峰纬>&longitude=<山峰经>
&models=ecmwf_ensemble
&hourly=temperature_2m,dew_point_2m
&timezone=Asia/Shanghai&forecast_days=7
```

---

#### 雾顶物理校验（所有层级共用）

> **Magnus 公式在所有层级通用，用于校验融合结果的物理合理性。**

**核心公式**：
- `LCL_ag(m) = 125 × (T − dew_point_2m实测)`
- `fog_top_msl = station_elev + LCL_ag + 100m`

**山顶 vs 雾顶判定**：
- `> 200m` → ✅ 远高于雾顶（可见云海）
- `0~200m` → ⚠️ 接近雾层边缘
- `< 0m` → ❌ 在雾中（看不见云海）

**⚠️ 禁止跳峰**：每个山峰必须独立获取数据，不得共用或假设。

---

### Step 3 - 评分计算

使用 12 因子综合评分模型。

> **完整评分模型、因子权重、计算公式详见 `references/scoring-standards.md`**

#### 大气通透度评估（因子 11 增强版 · 2026-04-17 新增）

> **为什么需要通透度**：云海是否"好看"不仅取决于有没有雾，还取决于大气是否通透。
> 灰霾天气下即使有云海，视觉也是白茫茫一片，无层次、无色彩，拍摄效果差。

**数据来源**（全部免费，无需 API Key）：

| 指标 | 数据源 API | 字段 | 权重 |
|------|-----------|------|:----:|
| PM2.5 | `air-quality-api.open-meteo.com/v1/air-quality` | `pm2_5` (μg/m³) | 30% |
| 能见度 | `api.open-meteo.com/v1/forecast` | `visibility` (m) | 25% |
| US AQI | `air-quality-api.open-meteo.com/v1/air-quality` | `us_aqi` | 20% |
| PM10 | `air-quality-api.open-meteo.com/v1/air-quality` | `pm10` (μg/m³) | 10% |
| AOD | `air-quality-api.open-meteo.com/v1/air-quality` | `aerosol_optical_depth` | 10% |
| NO₂ | `air-quality-api.open-meteo.com/v1/air-quality` | `nitrogen_dioxide` (μg/m³) | 5% |

**通透度等级与云海概率修正**：

| 评分 | 等级 | 视觉描述 | 云海概率修正 |
|:----:|------|---------|:----------:|
| ≥ 8.0 | ★★★★★ 极通透 | 雪山级通透，远山轮廓分明，云海色彩饱满 | **+5%** |
| 6.0-8.0 | ★★★★☆ 通透 | 云海白色纯净，层次清晰，城市轮廓可辨 | ±0% |
| 4.0-6.0 | ★★★☆☆ 一般 | 云海偏灰，远景模糊，色彩饱和度下降 | **-5%** |
| 2.0-4.0 | ★★☆☆☆ 灰霾 | 云海灰白，城市不可见，无层次感 | **-15%** |
| < 2.0 | ★☆☆☆☆ 严重雾霾 | 白茫茫一片，雾和霾混为一体，完全无层次 | **-25%** |

**城区 vs 山峰**：
- 城区监测点（39.92°N, 116.40°E, 45m）代表平原低海拔空气质量
- 各山峰独立获取 visibility（山顶能见度可能优于城区）
- 评分取城区空气质量 + 山峰能见度两者综合

**API 调用示例**：
```
# 空气质量（独立端点，非天气 API）
GET https://air-quality-api.open-meteo.com/v1/air-quality
?latitude=39.92&longitude=116.40
&hourly=pm10,pm2_5,nitrogen_dioxide,ozone,aerosol_optical_depth,us_aqi
&timezone=Asia/Shanghai&forecast_days=7

# 能见度（天气 API 的 visibility 字段）
GET https://api.open-meteo.com/v1/forecast
?latitude=39.92&longitude=116.40
&hourly=visibility
&timezone=Asia/Shanghai&forecast_days=7
```

---

### Step 3.5 - 日出云海质量预测（可选扩展 · 当用户询问日出时使用）

> 当用户询问日出云海质量、云层类型（高云/中云/低云）、日出视觉预测时，执行此步骤。
> 此步骤基于 Step 2 已获取的逐时气象数据，无需额外 API 调用。

#### 3.5.1 日出时间窗口定义

北京4月日出约 **05:30-05:50**，取以下三个关键时次分析：

| 时次 | Open-Meteo index | 含义 |
|------|:----------------:|------|
| 05:00（index 5）| 日出前30分钟 | 雾层最终状态 |
| **06:00（index 6）** | **日出时刻** | **核心判定** |
| 07:00（index 7）| 日出后1小时 | 雾散过程/云量变化 |

#### 3.5.2 云层高度分类（WMO天气码 + LCL 双重判定）

| 云层级别 | 底高范围 | 典型云种 | 日出视觉效果 | 判定条件 |
|---------|:-------:|---------|------------|---------|
| **高云** | > 6000m AGL | 卷云(Ci)、卷层云(Cs)、卷积云(Cc) | 薄纱状金色、红色染色日出，极罕见 | weather_code=0 且 cloud_cover<20% + 无雾 |
| **中云** | 2000–6000m AGL | 高积云(Ac)、高层云(As) | 部分遮挡日出，色彩偏平淡 | weather_code=2-3 且 LCL>2000m |
| **低云** | < 2000m AGL | 积云(Cu)、层积云(Sc) | 可能形成云海，或完全遮蔽 | weather_code=2-3 且 LCL<2000m |
| **辐射雾/层云** | 0–500m AGL | 雾、层云(St) | 山谷淹没、峰顶穿云而出，最壮观 | weather_code∈[0,45,48] 且 LCL<500m 且 RH>80% |
| **无云** | — | 晴空 | 纯净金色日出，色彩最饱和 | weather_code=0 且 cloud_cover=0% 且 above_fog=True |

**LCL 快速判定（无需 Magnus 公式）：**
```
LCL_ag(m) ≈ 125 × (T − dew_point_2m)
```
当 LCL < 300m 时为极低雾层（辐射雾），日出景观最佳。

#### 3.5.3 日出质量评分模型（0-100分）

综合五个维度：

| 维度 | 权重 | 判定规则 |
|------|:----:|---------|
| **① 云量遮挡** | 40% | 0%=40分，每+10%云量扣4分；>80%=5分 |
| **② 云层类型** | 25% | 无云=25分，高云=20分，中云=12分，低云=5分 |
| **③ 雾层位置 vs 山峰** | 20% | 山顶在雾中=15分；雾顶<500m=20分；超出>500m=20分；无雾=5分 |
| **④ 风速** | 10% | <5km/h=10分，5-15=5分，>20=-5分 |
| **⑤ 大气通透度** | 5% | 沿用 Step 3 通透度评分，≥8.0=5分，≥6=3分，<4=0分 |

#### 3.5.4 日出序列输出要求

对每个目标山峰，输出日出前后 3 小时（04:00-08:00）的逐时数据：

```markdown
| 时间 | 云量% | 天气 | 雾层状态 | 风速 | 降水概率% |
|------|:-----:|------|---------|-----:|--------:|
| 04:00 | 100% | Overcast | 在雾中 | 2.9km/h | 0% |
| 05:00 | 100% | Overcast | 在雾中 | 2.9km/h | 0% |
| 06:00 | 81%  | PartlyCloudy | 在雾中 | 2.4km/h | 0% |
| 07:00 | 83%  | PartlyCloudy | 在雾中 | 2.5km/h | 0% |
| 08:00 | 90%  | Overcast | 高于雾顶 | 3.9km/h | 0% |
```

日出序列需包含以下判定：
- **日出瞬间（05:40）天空状况**：晴/多云/雾遮蔽
- **雾层抬升时间**：山峰何时"浮出"云海
- **金色拍摄窗口**：LCL 降至最低、山峰露出、太阳仰角>5°的时间段

#### 3.5.5 日出专题报告内容结构

1. 核心发现（一句话总结）
2. 逐日日出综合评级表（⭐制度，1-4星）
3. 云层类型分类（高云/中云/低云/雾 vs 雾凇/辐射雾）
4. 各峰日出序列（关键时次数据）
5. 最佳日出推荐（综合评分最高日）
6. 风险提示（浓雾安全、山路结冰、拍摄窗口等）

---

### Step 4 - 生成 Markdown 报告（主会话输出 · 强制使用模板）

> ⚠️ **硬性规则**：主会话云海预测输出**必须**使用 `references/report-template.md` 模板格式。
> 不得自行编造格式、省略模块、或使用其他结构。每次输出前，先读模板再填数据。

**执行步骤（必须按序执行，不可跳过任何步骤）：**

1. **读取模板**：`read references/report-template.md`
2. **按模板结构逐节填充数据**（不得跳过任何节）：
   - 16峰综合排名表（含概率🟢🟡🔴、LCL、雾顶、山顶差、风速、通透度、日出评级、雾型、形成机制、最佳出行时间）
   - 雾型与形成机制分类（5种雾型表 + 当日雾型诊断表）
   - 气象分析（能见度、PM2.5、AOD、风速、LCL、湿度 + 形势判断✅⚠️❌）
   - 出行建议（TOP3，每个含逐小时 04:00-08:00 关键数据表）
   - 行程规划（至少2个方案）
   - 推荐优先级矩阵 + 决策建议 + 交通建议 + 实时确认
   - 装备清单（checkbox格式）
   - 结论
   - 格式规范速查（概率颜色、日出评级、通透度评级、山顶差判定）
3. **保存到工作区**：`cloud-sea-{date}.md`（单日）或 `cloud-sea-weekly-{date}.md`（周报）
4. **【强制步骤】主会话显示完整报告**
   - ⚠️ **这是强制步骤**，每次预测完成后必须执行，无需用户额外要求
   - **执行方式**：使用 `read` 工具读取刚保存的文件，然后将文件内容**直接写入 AI 回复中**
   - **关键理解**：`read` 工具的结果显示在工具调用结果中，但必须将内容**复制到 AI 的回复文本中**
   - **不得**仅输出摘要、链接或"报告已生成"等简略信息
   - **必须执行**：读取文件后，将内容全部复制到 AI 回复中，确保用户能直接看到完整报告
   - 使用 `read` 工具读取刚保存的文件，然后将文件内容**复制粘贴到 AI 回复中**
   - 不得仅输出摘要、链接或"报告已生成"等简略信息
   - 主会话输出必须与模板结构完全一致（不得省略任何模块）

**常见错误（禁止）：**
- ❌ 省略格式规范速查节（"太长"不是理由，模板规定必须完整输出）
- ❌ 自行简化排名表（必须包含模板定义的全部12列）
- ❌ 省略TOP3逐小时数据表
- ❌ 不读模板直接凭记忆输出（记忆会遗漏模块）

---


---

### Step 5 - 生成 HTML 可视化报告

> **HTML 模板路径：`assets/report-template.html`（v2 动态占位符版本）**
>
> 模板使用 `{{PLACEHOLDER}}` 语法，由 `scripts/report_gen.py`（推荐，含雾型诊断引擎）或 `assets/_build_html_v3.py` 填充数据。
> 完整占位符清单见模板文件顶部 HTML 注释中的 DATA CONTRACT。
>
> 必含模块：Header、概率仪表盘、三重核实结论卡片、雾底/雾顶 vs 山顶对比表、逐小时概率曲线（SVG柱状图）、五维评分、大气通透度、雾型分类、时间线、行程规划、优先级矩阵、装备清单、结论、图例。
>
> 配色规则：>= 45% 绿色 / >= 30% 蓝色 / >= 15% 黄色 / < 15% 深灰
>
> **标准工作流**（v2）：
> ```bash
> python scripts/analyzer.py --date 2026-04-25 --all   # 获取数据 + 生成 config
> python scripts/report_gen.py scripts/report_config.json cloud-sea-2026-04-25.html
> python scripts/html_to_image.py cloud-sea-2026-04-25.html cloud-sea-2026-04-25.png
> ```

---

## 北京及周边云海观测点（经三重核实后修正）

> **完整山峰坐标、天气网编码、区域信息详见 `references/peaks.md`**

### 典型观测点概率参考（历史数据）

| 排名 | 地点 | 海拔 | 观测特征 |
|:----:|------|-----:|---------|
| 🥇 | **海坨山**（延庆）| 2198m | 云海最壮观，冬奥主赛场 |
| 🥈 | **东灵山**（门头沟）| 2303m | 北京最高峰，云层最厚 |
| 🥉 | **雾灵山**（密云）| 2116m | 日出评级⭐⭐⭐⭐⭐，视野最佳 |
| 4 | **妙峰山**（门头沟）| 1291m | 城市+云海双景（⚠️ 实测险差+211m，非+624m，俯视视角；见 scoring-standards.md 因子6） |
| 5 | **白石山**（涞源）| 2099m | 云海+佛光双绝，大理岩峰林 |
| 6 | **云蒙山**（怀柔）| 1414m | LCL 极低，湿度汇聚佳 |
| — | **长城段**：箭扣长城(~900m)、金山岭长城(~1100m) | — | 浓雾锁峰（需注意：山顶在雾中，无云海可见） |

> **注意**：实际概率需根据当日气象数据计算，上表仅作历史参考。

---

## 质量标准

1. **数据必须来自真实来源，不得编造数值**，尤其是 dew_point_2m 必须从 API 实测获取
2. 不确定时明确标注概率和风险，**云底/雾顶估算须标注置信区间**
3. 降水概率 > 20% 必列为高风险
4. 综合概率上限 85%（留出不确定性空间）
5. 推荐出行条件：综合概率 >= 45% 且无高风险项
6. **所有峰云底估算必须使用实测 dew_point_2m，绝不假设 Td 值**
7. HTML 配色：深色主题（#0a0e1a 背景）
8. 三重核实是**强制要求**，不可跳过
9. **通透度评分 ≤ 4.0 时必须在报告中标注"灰霾警告"，即使云海概率高也需提示视觉打折**
10. **城区 PM2.5 > 75 μg/m³ 时，云海色彩以灰白为主，需在报告中标注**
11. **AOD > 0.5 时，远山轮廓不可见，需在报告中标注**
12. **雾顶公式统一为：`fog_top_msl = station_elev + LCL_ag + 100m`**（不得用 summit_elev − station_elev 作雾厚）
13. **长城段（金山岭/箭扣）海拔仅 900-1100m，远低于华北辐射雾雾顶（通常 1500-2500m），山顶在雾中，无云海可见**，报告中须明确标注
14. **雾型必须从当日实时气象数据动态计算**（风向+风速+RH+T-Td），禁止使用硬编码地理假设。判断规则：北风(0-90°或290-360°)+风速≥3km/h+RH<65%→无雾；静风+RH>80%+T-Td<4°C→辐射雾；南风(90-270°)+RH≥75%→上坡雾

---

## 云海形成机制分类

> **完整诊断标准、物理机制、判定条件、快速诊断流程、各峰雾型偏好详见 `references/fog-types.md`**

### 五种雾型速查

| 类型 | 形成机制 | 最佳观测时段 | 典型地点 |
|------|---------|-------------|---------|
| **辐射雾型** | 夜间辐射冷却，晴夜+微风+高湿度 | 日出前后 | 海坨山、雾灵山 |
| **平流雾型** | 暖湿空气流经冷地面 | 全天可持续 | 白石山 |
| **上坡雾型** | 暖湿空气沿山坡上升 | 风向稳定时段 | 雾灵山、百花山 |
| **蒸发雾型** | 冷空气流经暖水面 | 清晨或夜间 | 长峪城、东指壶 |
| **锋面雾型** | 锋面过境，暖雨滴蒸发 | 锋面过境时 | 各峰均可 |

---

## 自动化脚本

```bash
# 获取气象数据（含 dew_point_2m）
cloud_sea_shared.py         ← 共享常量与辅助函数（唯一真相源）
python scripts/weather_fetch.py

# 生成 HTML 报告
python scripts/report_gen.py report_config.json output.html
```

---

## 文件结构

```
cloud-sea/
├── SKILL.md                          ← 本文件
├── scripts/
│   ├── cloud_sea_shared.py         ← 共享常量与辅助函数（唯一真相源）
│   ├── weather_fetch.py              ← 多源气象数据（含 dew_point_2m）
│   ├── analyzer.py                   ← 数据分析与评分
│   ├── report_gen.py                 ← HTML 报告生成器（含雾型诊断引擎）
│   ├── sunrise_analysis.py           ← 日出云海质量分析（云层分类+评分）
│   └── html_to_image.py              ← HTML 转 PNG（Playwright）
├── references/
│   ├── peaks.md                      ← 17峰坐标 + 区域编码 + 三重核实分配（权威来源）
│   ├── scoring-standards.md          ← 12因子评分模型（雾型交互引用 fog-types.md）
│   ├── fog-types.md                  ← 雾型诊断 + 雾底实时估算 + 组合效应（权威来源）
│   ├── report-template.md            ← Markdown 报告输出模板
│   ├── data-sources.md               ← 数据源说明
│   ├── locations.md                  ← 观测点位置详情
│   └── SELF-IMPROVEMENTS.md          ← 自我改进日志
└── assets/
    ├── report-template.html           ← HTML 报告模板（v2 动态占位符版，{{PLACEHOLDER}} 语法）
    └── _build_html_v3.py                 ← 独立 HTML 生成器（读取模板 + config → HTML）
```

> **⚠️ 共享常量（2026-04-23 新增，2026-04-24 扩展）：** 禁止在各文件中重复定义以下常量/函数，统一在 `scripts/cloud_sea_shared.py` 中定义（唯一真相源）：
> - **数据**: `PEAK_INFO` / `PEAK_ELEVATIONS` / `FOG_TYPES` / `FOG_COMBO_BONUS` / `FACTOR_WEIGHTS` / `FACTOR_WEIGHT_VALUES`
> - **雾型映射**: `FOG_MECHANISM_MAP` / `FOG_BEST_TIME_MAP` / `FOG_ICONS` / `FOG_STARS`
> - **函数**: `calc_fog_type()` / `estimate_transparency()` / `prob_class()` / `diff_class()` / `fog_mechanism()` / `fog_best_time()` / `fog_icon()` / `fog_stars()`
> - **配置**: `DEFAULT_EQUIP_ITEMS`

> **模板系统**：两套并存，均为纯占位符模板。
> - v2（`report-template.html`）：35占位符，含雾型诊断、12因子、透明度等，由 `scripts/report_gen.py` 驱动（推荐）。
> - v3（`report-template-v3.html`）：11占位符，深色科技风简洁设计，由 `assets/_build_html_v3.py` 驱动。
> `_build_html.py` 已废弃（2026-04-23 删除）。

> **雾型基础分和组合加分的权威来源是 `references/fog-types.md`**
> `scoring-standards.md` 中的雾型矩阵引用 fog-types.md，不单独定义数值。
>
> **模板系统**：`report-template.html` 是纯占位符模板，不含硬编码数据。
> 生成器（`scripts/report_gen.py` 或 `assets/_build_html_v3.py` 读取模板并填充 `{{PLACEHOLDER}}` 占位符。
> 占位符清单见模板文件顶部 HTML 注释。