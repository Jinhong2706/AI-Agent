# Skill Creator Optimized

面向办公小浣熊 Skill 包的创建、优化、校验与打包技能。

本优化版重点解决三个问题：

1. **异常处理更系统**：把模糊需求、缺失文件、元数据错误、结构不完整、写入失败、打包失败等情况拆成可执行的诊断路径。
2. **功能完善性更强**：新增输入诊断、YAML front matter 校验、结构校验、质量门禁、输出清单和安装前检查。
3. **运行稳定性更高**：引入阶段性进度保存、失败重试边界、降级交付策略和恢复模板，降低复杂任务中断后的返工成本。

## 适用场景

- 从自然语言需求创建新 Skill。
- 根据已有 `SKILL.md`、项目说明或压缩包优化 Skill。
- 检查 Skill 是否缺少 YAML front matter 注册元数据。
- 生成可审计的 Skill 包目录、参考文档、示例和交付 zip。
- 对复杂或模糊需求进行自动澄清、自动补齐和自纠错。

## 目录结构

```text
skill-creator-optimized/
├── SKILL.md
├── AGENTS.md
├── README.md
├── package.json
├── examples/
│   └── usage.md
└── references/
    ├── workflow.md
    ├── qa-checklist.md
    ├── error-handling.md
    └── progress-template.md
```

## 核心改进

### 1. 输入诊断

执行前先判断用户处于哪类模式：

- 新手引导：需求模糊，需要结构化提问。
- 专业快速：目标明确，可直接生成。
- 已有技能优化：需要读取现有文件并提出修改方案。
- 故障修复：围绕报错、缺失、不可安装等问题定位。

### 2. 自动校验

每次生成或优化后，必须检查：

- `SKILL.md` 是否存在。
- `SKILL.md` 是否包含 YAML front matter。
- front matter 是否包含 `name`、`description` 等关键字段。
- 是否存在占位文本、空章节、重复标题或路径错误。
- 是否所有新增文件都位于目标输出目录内。

### 3. 自纠错与恢复

当发现错误时，不直接交付，而是先尝试修复：

- 缺少元数据：自动补齐。
- 描述过泛：改成更可触发的描述。
- 文件结构不完整：补齐 `references/`、`examples/` 或 README。
- 写入/打包异常：保留进度，说明原因并换路径。
- 复杂任务中断：通过 `references/progress-template.md` 恢复。

## 使用建议

如果用户只说“帮我做个技能”，先进入新手引导模式。
如果用户已经提供压缩包或目录，先审计再优化，不要盲目重写。
如果发现缺少 YAML front matter，必须自动修复。
如果任务涉及 5 个以上相似文件/章节，建议拆分并行起草，再统一合并和 QA。

## 交付标准

最终应交付：

- 优化后的 Skill 目录。
- 可安装 zip 包。
- 本次优化说明或变更摘要。
- QA 检查结果。
- 如未完全完成，明确失败原因和下一步建议。

## 工程级校验

本优化版新增 `scripts/validate-skill.sh`，用于安装前自动检查技能包质量。

### 运行方式

在技能目录内执行：

```bash
bash scripts/validate-skill.sh . reports
```

如果需要同时校验 zip 包：

```bash
bash scripts/validate-skill.sh . reports ../skill-creator-optimized.zip
```

### 输出报告

脚本会生成：

- `reports/qa-report.json`：机器可读报告，适合自动化流程使用。
- `reports/qa-report.md`：人工可读报告，适合交付和复盘。

### 检查范围

- 必需文件是否存在且非空。
- `SKILL.md` 是否包含 YAML front matter。
- front matter 是否包含 `name` 和 `description`。
- 是否覆盖输入诊断、自纠错、质量门禁、进度恢复等关键能力。
- 是否存在占位文本。
- 是否存在空文件。
- 如提供 zip，是否通过完整性测试，且 zip 根目录是否包含技能目录。

交付前建议以 `qa-report.json` 中的 `status` 字段作为最终质量门禁。
