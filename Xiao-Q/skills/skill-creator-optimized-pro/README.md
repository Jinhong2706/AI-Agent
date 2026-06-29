# Skill Creator Optimized Pro

面向 SkillHub 发布和团队复用的高质量 Skill 创建/优化技能包。

## 适用场景

- 从自然语言需求生成标准 Skill 包。
- 优化已有 `SKILL.md` 或 zip 技能包。
- 修复 YAML front matter、description、引用路径、README、元数据和打包结构。
- 将 SOP、业务流程、提示词、专家方法论沉淀为可复用 Skill。
- 发布前执行静态校验和质量门禁。

## 设计理念

本版本结合了腾讯技术工程关于 Skills 的实战经验与 Anthropic/Claude Skills 的通用设计原则：

1. **精准触发**：description 是 Skill 的入口和触发器。
2. **渐进式加载**：front matter 常驻，`SKILL.md` 触发后加载，长资料和脚本按需读取。
3. **工程化交付**：让 AI 做理解、判断和表达，让脚本/检查清单承担确定性校验。
4. **质量可验证**：输出契约、完成标准、测试 Prompt 和静态检查缺一不可。
5. **持续迭代**：将真实使用中的错误沉淀到 references 和质量门禁中。

## 文件结构

```text
skill-creator-optimized-pro/
├── SKILL.md
├── README.md
├── package.json
├── _meta.json
├── scripts/
│   ├── validate-skill.py
│   └── score-skill.py
├── examples/
│   ├── README.md
│   ├── contract-review-skill.md
│   ├── data-analysis-skill.md
│   ├── ppt-generator-skill.md
│   ├── knowledge-base-skill.md
│   ├── lark-api-skill.md
│   ├── excel-automation-skill.md
│   ├── cloud-doc-editing-skill.md
│   ├── legal-compliance-skill.md
│   ├── multi-agent-collaboration-skill.md
│   └── browser-automation-skill.md
├── minimal-skills/
│   ├── README.md
│   ├── excel-automation-minimal/
│   ├── cloud-doc-editing-minimal/
│   ├── legal-compliance-minimal/
│   ├── multi-agent-collaboration-minimal/
│   └── browser-automation-minimal/
└── references/
    ├── excellent-skill-methodology.md
    ├── workflow.md
    ├── qa-checklist.md
    ├── skill-scorecard.md
    ├── error-handling.md
    └── progress-template.md
```

## 使用方式

当用户要求“创建 Skill”“优化技能包”“补齐 YAML front matter”“打包发布 SkillHub”等任务时，本 Skill 会引导或直接执行：需求诊断 → 结构设计 → 编写/优化 → 静态验证 → 打包交付。

## 发布前检查

发布前至少确认：

- `SKILL.md` 顶部 YAML front matter 可解析。
- `name`、`description`、版本号与 README/package metadata 一致。
- description 同时包含触发场景和排除场景。
- 所有本地引用文件存在。
- zip 中无临时文件、上传残留、日志和密钥。

### 自动化校验

发布前建议运行：

```bash
python scripts/validate-skill.py <skill-dir>
python scripts/validate-skill.py --json <skill-dir>
```

该脚本自动检查 YAML front matter、推荐目录结构、Markdown 本地引用、description 长度、禁用词和临时产物。`--json` 输出适合接入 CI、批量审核流水线或质量看板。自动化校验用于发现确定性问题，不替代人工质量评审。

### 半自动评分

发布前建议运行：

```bash
python scripts/score-skill.py <skill-dir>
python scripts/score-skill.py --json <skill-dir>
```

该脚本把 `references/skill-scorecard.md` 的 100 分制评分框架转成可执行静态检查，输出总分、等级、各维度得分和整改建议。建议 80 分以上再进入发布，90 分以上作为标杆候选。

### 示例库

`examples/` 提供 10 类可套用示例：合同审查、数据分析、PPT 生成、知识库、飞书 API、Excel 自动化、云文档编辑、法务合规、多 Agent 协作、浏览器自动化。新建同类 Skill 时，先读取 `examples/README.md`，再按具体类型复制结构并替换触发条件、工具边界和交付契约。

### 最小可安装包

`minimal-skills/` 提供可复制为独立 Skill 的最小包模板，覆盖 Excel 自动化、云文档编辑、法务合规、多 Agent 协作、浏览器自动化 5 个方向。适合一键复制后替换 `SKILL.md` 元数据和业务说明。

### 100 分制评分

`references/skill-scorecard.md` 提供 100 分制评分表，覆盖触发、结构、渐进式加载、可执行性、可审计性、异常处理、交付契约。适合发布前复核、批量审核和 SkillHub 质量分层。
