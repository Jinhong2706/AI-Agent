# skill-creator-king

> 超强skill创建、评价、维护、迭代的元工具。从对话建、用分数验、持续迭代——skill 全生命周期 total solution。v3.23.1 自审缺陷修复（9 项：footer 版本号 / 过时文本 / 死引用 / 副本清理）；v3.23.0 SCK 自审机制建立（.consistency.yml + check_consistency.py，首次自审抓 plugin.json 滞后 bug）+ 3 个代码 bug 修复（os 未 import / mtime 换骨 / re.MULTILINE 缺失）+ 豁免规则扩展；v3.22.0 autofix 瘦身为安全骨架（backup→verify→rollback），via negativa 三修复；v3.21.x 杠铃架构+反脆弱 fuzz+trust test 双层质量门。

## 这是什么

**skill-creator-king** 是用来创建、审查、评分、升级 skill 的元工具。支持 WorkBuddy / OpenClaw / Hermes / Universal 四平台。
它的核心价值是：**把 skill 开发的实战踩坑经验变成可复用的流程和自动化检测**。

**定位**：静态分析工具（linter）——查形式不查功能。检查 YAML 语法、版本一致性、文件完整性、反模式；不跑代码、不验证行为、不判断工作流是否合理。功能质量留给人和 LLM。

适合谁：
- skill 开发者：创建新 skill 时不用从零想结构，SCK 帮你搭骨架
- 已有 skill 想完善的：SCK 帮你做体检、评分、针对性改进
- skill 质量把控者：用 SCK 的 quality-audit 和 validate 做自动化检查

不适合谁：
- 只想生成一个模板就跑的人：SCK 强调双向讨论、持续迭代，不是一次性填充器

## 快速开始

直接对 WorkBuddy 说 "帮我建一个 skill" 或 "审查这个 skill"。SCK 会自动检测你的平台（WorkBuddy / OpenClaw / Hermes / Universal）并走对应流程。无需安装依赖、无需配置——发话即用。

**其他平台用户**：将 SCK 目录放到对应平台的 skills 目录下（如 OpenClaw → `~/.openclaw/skills/skill-creator-king/`），加载 SKILL.md 即可。命令行工具零依赖，直接 `python3 scripts/validate.py your-skill/`。

## 触发方式

直接说出意图即可触发，支持中英文：
- **创建**：帮我建一个 skill / create a skill
- **审查**：审查这个 skill / audit this skill
- **评分**：给 skill 打个分 / score this skill
- **升级**：升级到完整版 / upgrade this skill

## 核心理念

好用的 skill 是聊出来的，不是生成出来的。skill-creator-king 不是模板填充工具——AI 是助手，用户拍板，每一步都带着真实踩坑经验帮用户绕开陷阱。

## 四大入口

| 入口 | 做什么 |
|------|--------|
| 🆕 创建 | 从零建一个 skill，支持轻量/完整/数据驱动三通道 |
| 🔄 升级 | 把轻量 skill 补全为完整版 |
| 🩺 审查 | 体检+治疗+教学，三位一体报告 |
| 📊 评分 | 14维度质量审计，135分制，通道自适应 |

- **Phase 0 出发前确认 + 五阶段创建流程**：Pre-flight → 定位 → 需求设计 → 实现 → 交付验证 → 持续迭代
- **双通道选择**：🚀 轻量（30分钟出活）或 🏗️ 完整（架构经得起迭代）
- **审查打磨**：自动扫描 + 三位一体报告（亮点/改进/学习要点）
- **质量评分**：14维度自动化审计，轻量/完整通道自适应
- **四平台支持**：WorkBuddy / OpenClaw / Hermes / Universal，路径自动检测
- **自进化**：审查中主动学习好模式，经用户拍板纳入自身
- **Frontmatter 安全扫描**：自动检测 26 种已知反模式（含 AP-023~026 安全扫描）
- **输出文件约定确认**：涉及文件产出的 skill 在 DESIGN 阶段强制确认输出目录/命名/格式/错误输出方式
- **Token 预算估算**：实测每个文件的 Token 数
- **缓存加速**：同skill同版本审查秒出结果，Token节省60%+
- **预检辅助**：手动维度脚本预检，辅助AI一致裁定
- **Ralph Loop 自反思**：Phase 3/5 双层自反思（客观+主观），最多3轮止损
- **自检先于交付**：validate.py --strict 自动嵌入 self-audit，覆盖引用完整性/配置活性/测试覆盖/保鲜度/纪律验证
- **自动交付物**：README.md + CHANGELOG.md + 交付报告
- **升级机制**：轻量 skill 随时升级到完整版
- **跨平台审计**：`--platform universal` 检查可移植性

## 怎么用

直接说：
- "帮我建一个 skill"（创建）
- "升级到完整版"（升级）
- "帮我看看这个 skill"（审查）
- "帮我打一下分"（评分）
- "我想做一个工具"
- "给 skill 做个体检"
- "帮我检查一下这个 skill 的健康度"（自检）
- "自检"

## 文件结构

```
skill-creator-king/
├── SKILL.md                 # L1 — frontmatter + workflow + 14维审计定义
├── DESIGN.md                # 需求规格 + 架构决策
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
├── PRINCIPLES.md
├── rules/
│   └── operational-rules.md
├── data/
│   ├── anti-patterns.yaml   # 26 个结构化反模式坑位
│   ├── checklists/          (2个文件)
│   ├── platforms/           (4个文件)
│   └── templates/           (8个文件)
├── references/              (13个文件: Phase 0~5 工作流 + 施工规范 + 审查指南等)
├── scripts/
│   ├── init_skill.py / validate.py / quality-audit.py / platform.py
│   ├── yaml_utils.py / self-audit.py / estimate-tokens.py / phase-check.py
│   ├── check_consistency.py
│   └── autofix/             (3个文件: engine + backup + __init__)
└── tests/                   (3个文件: __init__ + anti_patterns + strict)
```

## 技术架构

- **无外部依赖**：所有脚本仅使用 Python 标准库（pyyaml 为可选项）
- **纯文本驱动**：所有规则、模板、检查清单均以 markdown/yaml 文件存储，不依赖数据库
- **无状态设计**：每次会话从头开始，不持久化跨会话状态
- **三级加载**：L0 frontmatter / L1 core / L2 deep 三级 Token 预算管理

## 环境要求

- 支持 skill 机制的 AI 平台（WorkBuddy / OpenClaw / Hermes 等）
- Python 3.8+（仅 local 运行 validate/audit 脚本时需要）
- **零外部依赖**——纯标准库，无需 pip install 任何包

## 安全与限制

- 所有文件操作限定在用户指定的 skill 目录内
- 脚本仅读取和写入用户指定的 skill 目录
- 不发起外部网络请求
- 不依赖其他 skill

## 更新日志

详见 [CHANGELOG.md](./CHANGELOG.md)

---

当前版本见 [SKILL.md](./SKILL.md) frontmatter 或 [CHANGELOG.md](./CHANGELOG.md)。

## 安装

```bash
git clone https://github.com/Odinary-AI/skill-creator-king.git ~/.{平台}/skills/skill-creator-king/
```

需要 Python 3.8+，零外部依赖。

## License

MIT © [Odinary-AI](https://github.com/Odinary-AI)