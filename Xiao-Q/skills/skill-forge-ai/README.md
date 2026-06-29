# Skill Forge v3.3

> 高质量 Skill 锻造引擎 — 自适应访谈 → 创建 → 自测验证 → 同类比对，全流程交付可自动触发、稳定输出的 Skill

[![版本](https://img.shields.io/badge/version-3.3.0-blue)](https://github.com/EdwardWason/skill-forge)
[![License](https://img.shields.io/badge/license-MIT--0-green)](LICENSE)
[![ClawHub](https://img.shields.io/badge/ClawHub-skill--forge-orange)](https://clawhub.ai/skills/skill-forge)

## 功能

- **自适应访谈**：2-5轮渐进式访谈，行为追问+偏误检测+选项法，精准锁定需求
- **三条铁律**：Description先行 / 一Skill一职 / 150行以内，确保自动触发可靠
- **4模块结构**：任务/输出格式/规则/示例，符合腾讯 Skills 手册规范
- **自测验证流水线**：Schema检查 → 安全红线(7条) → 触发测试 → Dogfood模拟
- **SkillHub同类比对**：搜索Top3同类Skill，腾讯9维度合规比对，差异化分析
- **Progressive Disclosure**：SKILL.md精简<170行，详细方法论移入references/

## 快速开始

```bash
# ClawHub 安装
clawhub install skill-forge

# 或手动安装
git clone https://github.com/EdwardWason/skill-forge.git
cp -r skill-forge ~/.trae/skills/
```

## 使用方法

在 TRAE SOLO 中，当你说以下内容时，Skill Forge 会自动触发：

- "创建一个skill"
- "帮我做一个技能"
- "添加一个自定义skill"
- "我想新建一个skill"

### 两种模式

1. **上下文充足模式**：如果你已经和AI有多轮对话且创建要素齐全，直接进入创建流程
2. **访谈模式**：新任务启动时，通过2-5轮自适应访谈逐步锁定需求

### 创建流程

```
Phase 0: 意图识别 → 要素检查(5项) → 自适应访谈(2-5轮)
Phase 1: 创建 → Description先行 → 4模块内容 → 自测验证(含安全红线)
Phase 2: SkillHub同类比对 → 搜索排名 → 腾讯9维度比对 → 差异化分析
```

## 文件结构

```
skill-forge/
├── SKILL.md                              # 主入口（frontmatter + 执行流程）
├── references/
│   ├── interview-flow.md                 # 访谈流程详细参考
│   ├── interview-methods.md              # 访谈方法论深度参考
│   ├── benchmarking-guide.md             # SkillHub比对指南
│   └── meeting-action-extractor-example.md  # 完整Skill示例
├── README.md                             # 本文件
├── CHANGELOG.md                          # 版本变更日志
├── LICENSE                               # MIT-0 许可证
└── .claude-plugin/
    └── plugin.json                       # Claude Code 插件元数据
```

## 核心方法论

### 三条铁律

| 铁律 | 说明 | 违反后果 |
|------|------|---------|
| Description先行 | AI每轮对话扫描所有Skill的description，模糊=永远不触发=死Skill | 自动触发失败 |
| 一Skill一职 | 多功能Skill触发混乱、输出不一致 | 输出不可预测 |
| 150行以内 | 超200行AI准确率下降，详细内容移入references/ | 质量衰减 |

### 安全红线（7条）

创建的Skill必须通过安全检查，以下任何一条出现即拒绝交付：

1. curl/wget向未知URL发送数据
2. 无正当理由请求凭证/Token/API密钥
3. 读取~/.ssh、~/.aws、~/.config等敏感目录
4. 使用base64解码/eval()/exec()处理外部输入
5. 修改工作区外的系统文件或请求sudo权限
6. 包含混淆代码（压缩/编码/混淆）
7. 访问浏览器Cookie/会话或凭证文件

## 文档

| 文档 | 说明 |
|------|------|
| [访谈流程参考](references/interview-flow.md) | B1-B6规则、轮次模板、递归搜索模式 |
| [访谈方法论](references/interview-methods.md) | 行为追问、偏误检测、选项法设计 |
| [比对指南](references/benchmarking-guide.md) | SkillHub API用法、质量排序公式、9维度比对模板 |
| [完整示例](references/meeting-action-extractor-example.md) | 会议行动项提取器Skill示例 |

## License

MIT-0 © 2026 AI花生

---

# Skill Forge

> High-quality Skill forging engine — adaptive interview → creation → self-validation → peer benchmarking, delivering Skills that auto-trigger reliably and produce stable, structured output.

[![Version](https://img.shields.io/badge/version-3.3.0-blue)](https://github.com/EdwardWason/skill-forge)
[![License](https://img.shields.io/badge/license-MIT--0-green)](LICENSE)
[![ClawHub](https://img.shields.io/badge/ClawHub-skill--forge-orange)](https://clawhub.ai/skills/skill-forge)

## Features

- **Adaptive Interview**: 2-5 round progressive interview with behavioral probing, bias detection, and option-first design
- **Three Iron Rules**: Description-first / One-Skill-One-Job / Under 150 lines, ensuring reliable auto-triggering
- **4-Module Structure**: Task / Output Format / Rules / Example, compliant with Tencent Skills Manual
- **Self-Validation Pipeline**: Schema check → Security red line (7 items) → Trigger test → Dogfood simulation
- **SkillHub Peer Benchmarking**: Search Top 3 peers, 9-dimension Tencent Manual compliance comparison, differentiation analysis
- **Progressive Disclosure**: SKILL.md kept under 170 lines, detailed methodology in references/

## Quick Start

```bash
# Install via ClawHub
clawhub install skill-forge

# Or manual install
git clone https://github.com/EdwardWason/skill-forge.git
cp -r skill-forge ~/.trae/skills/
```

## Usage

Skill Forge auto-triggers when you say:
- "Create a skill"
- "Add a custom skill"
- "I want to make a new skill"

### Two Modes

1. **Context-rich mode**: Skip interview if 4+ essential elements are already present in conversation
2. **Interview mode**: 2-5 round adaptive interview to progressively lock down requirements

### Pipeline

```
Phase 0: Intent recognition → Element check (5 items) → Adaptive interview (2-5 rounds)
Phase 1: Creation → Description-first → 4-module content → Self-validation (with security check)
Phase 2: SkillHub peer benchmarking → Search & rank → Tencent 9-dimension comparison → Gap analysis
```

## Core Methodology

### Three Iron Rules

| Rule | Description | Consequence of Violation |
|------|-------------|--------------------------|
| Description-first | AI scans all Skill descriptions every conversation; vague = never triggers = dead Skill | Auto-trigger failure |
| One-Skill-One-Job | Multi-purpose Skills trigger chaotically and output inconsistently | Unpredictable output |
| Under 150 lines | Over 200 lines degrades AI accuracy; move details to references/ | Quality decay |

### Security Red Lines (7 items)

Any created Skill must pass security check. Any red flag below = reject:

1. curl/wget to unknown URLs or sending data to external servers
2. Requesting credentials/tokens/API keys without clear reason
3. Reading ~/.ssh, ~/.aws, ~/.config, MEMORY.md, USER.md, IDENTITY.md
4. Using base64 decode / eval() / exec() with external input
5. Modifying system files outside workspace or requesting sudo
6. Obfuscated code (compressed, encoded, minified)
7. Accessing browser cookies/sessions or credential files

## Documentation

| Document | Description |
|----------|-------------|
| [Interview Flow](references/interview-flow.md) | B1-B6 rules, round templates, recursive search pattern |
| [Interview Methods](references/interview-methods.md) | Behavioral probing, bias detection, option design |
| [Benchmarking Guide](references/benchmarking-guide.md) | SkillHub API usage, quality ranking formula, 9-dimension template |
| [Full Example](references/meeting-action-extractor-example.md) | Meeting action extractor Skill example |

## License

MIT-0 © 2026 AI花生
