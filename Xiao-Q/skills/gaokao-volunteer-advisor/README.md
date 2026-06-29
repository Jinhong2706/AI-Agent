# 高考志愿填报专家顾问 (gaokao-volunteer-advisor)

> 专业、理性、不制造焦虑的高考志愿规划 AI 助手

## 功能介绍

本技能将 AI 转化为专业的高考志愿规划师，覆盖志愿填报全流程：

| 能力 | 说明 |
|------|------|
| 位次分析 | 基于考生位次计算冲/稳/保三档录取区间 |
| 录取概率计算 | Sigmoid 模型评估目标院校录取概率，支持多年数据趋势分析 |
| 院校推荐 | 结构化表格输出，按冲稳保分档，含推荐理由 |
| 志愿健康度检查 | 自动评估志愿草表的梯度合理性，识别高风险组合 |
| 专业指导 | 易混淆专业辨析、就业前景分析、选科匹配检查 |
| 特殊招生咨询 | 强基计划、专项计划、军校、公费师范生等 8 种通道 |
| 综合报告生成 | 结构化 Markdown 报告，含学生画像、策略、院校表、风险评估 |

## 支持范围

- **省份**：全国各省（含新高考 3+1+2 和 3+3 模式）
- **批次**：提前批、本科批（一批/二批/普通批）、专科批
- **科类**：物理类、历史类、综合、理科、文科

## 快速开始

安装本技能后，在对话中直接描述你的需求即可自动触发。示例：

```
"我孩子今年高考，浙江考生，物理类，考了620分，全省排名32000左右，想学计算机"
"帮我分析一下这个志愿草表合不合理..."
"计算机科学和软件工程有什么区别？"
"强基计划怎么报名？"
```

## 核心特性

### 数据驱动分析

- 优先使用**位次**（而非分数）进行跨年份比较，排除年度波动
- 支持近 3 年录取位次数据输入，检测录取难度趋势
- Sigmoid 概率模型量化评估录取可能性

### 智能风险评估

志愿健康度检查工具可自动检测：

- 无保底志愿 / 保底过少
- 冲刺比例过高
- 排序错乱（保底排在冲刺前面）
- 不服从调剂 + 冲档组合（高风险）
- 重复院校

### 结构化报告输出

每次咨询可生成标准化的志愿填报建议报告，包含：
- 学生画像摘要
- 整体策略说明
- 冲/稳/保三档院校推荐表
- 志愿梯度健康度评估
- 下一步行动建议

## 目录结构

```
gaokao-volunteer-advisor/
├── SKILL.md                          # 技能定义（角色、SOP、沟通原则）
├── README.md                         # 本文件
├── references/
│   └── gaokao-system.md              # 高考录取制度知识库
└── scripts/
    ├── analyze_volunteer.py          # 位次分析 & 报告生成
    ├── calc_probability.py           # 录取概率计算
    └── health_check.py               # 志愿健康度检查
```

## 工具使用

三个 Python 脚本均使用标准库，无需安装第三方依赖。

### 位次分析

```bash
# 基于位次（推荐）
python scripts/analyze_volunteer.py --score 620 --rank 32000 --province 浙江 --type 物理类

# 仅基于分数（粗略估算）
python scripts/analyze_volunteer.py --score 620 --province 浙江 --type 物理类

# 输出 Markdown 报告
python scripts/analyze_volunteer.py --score 620 --rank 32000 --province 浙江 --type 物理类 --output report.md
```

### 录取概率计算

```bash
# 单所院校
python scripts/calc_probability.py --rank 32000 --school_rank 28000 --school_name "南京邮电大学"

# 多所院校
python scripts/calc_probability.py --rank 32000 --school_rank "28000,35000,38000" \
    --school_name "南邮,浙工商,宁大"

# 多年数据（管道符分隔）
python scripts/calc_probability.py --rank 32000 --school_rank "28000|29000|27000" \
    --school_name "南京邮电大学"

# JSON 批量处理
python scripts/calc_probability.py --input schools.json --rank 32000
```

### 志愿健康度检查

```bash
# JSON 文件模式（推荐）
python scripts/health_check.py --input volunteer_draft.json

# 简单模式（仅数量统计）
python scripts/health_check.py --total 10 --rush 3 --stable 4 --safe 2 --unspecified 1
```

## 注意事项

- 本技能**不内置实时数据库**，历史录取数据需用户提供或自行查询
- 建议通过**阳光高考平台**（gaokao.chsi.com.cn）和**各省招生考试院官网**获取官方数据
- 所有建议仅供参考，不构成正式填报依据
- 政策每年可能调整，请以当年官方公告为准

## 知识库覆盖范围

`references/gaokao-system.md` 包含以下主题的结构化知识：

1. 招生录取模式（平行志愿 / 顺序志愿 / 新高考选科 / 院校专业组）
2. 批次与录取流程（批次划分 / 控制线 / 时间线）
3. 核心数据指标（位次 / 一分一段表 / 录取线 / 专业级差）
4. 冲稳保选校策略
5. 专业选择维度（含 9 组易混淆专业辨析）
6. 中外合作办学（培养模式 / 学费 / 考量点）
7. 院校信息查询渠道
8. 特殊类型招生（强基 / 专项 / 军校 / 公安 / 师范 / 艺体）
9. 常见误区与注意事项（8 条）

## 版本信息

- **版本**：v1.1
- **更新日期**：2026-05-24
- **Python 要求**：3.10+（使用标准库，无第三方依赖）
- **平台支持**：WorkBuddy / CodeBuddy
