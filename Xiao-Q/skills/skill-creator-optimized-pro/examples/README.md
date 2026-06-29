# 多类型 Skill 示例库

本目录提供可复制、可裁剪、可组合的 Skill 示例，用于在创建新技能时快速套用成熟结构。示例不是完整业务实现，而是“结构标杆”：重点展示触发条件、渐进式加载、工具边界、异常处理和交付契约。

## 示例清单

| 类型 | 文件 | 适合场景 | 复用重点 |
| --- | --- | --- | --- |
| 合同审查类 | [contract-review-skill.md](contract-review-skill.md) | 合同审核、隐私政策审查、合规意见、批量条款风险检查 | 风险分级、逐条审查、法律边界、修订建议 |
| 数据分析类 | [data-analysis-skill.md](data-analysis-skill.md) | Excel/CSV 分析、经营看板、异常诊断、可视化报告 | 数据清洗、口径确认、图表输出、可复核分析 |
| PPT 生成类 | [ppt-generator-skill.md](ppt-generator-skill.md) | 演示文稿、路演材料、培训课件、汇报页 | 内容规划、版式约束、素材策略、视觉 QA |
| 知识库类 | [knowledge-base-skill.md](knowledge-base-skill.md) | 知识检索、资料沉淀、口径统一、引用型回答 | 搜索策略、写入边界、引用规范、隐私控制 |
| 飞书 API 类 | [lark-api-skill.md](lark-api-skill.md) | 飞书文档读取、总结、有限编辑、API 诊断 | token/权限边界、版本识别、失败降级、回写契约 |
| Excel 自动化类 | [excel-automation-skill.md](excel-automation-skill.md) | 多表清洗、公式检查、批量拆分合并、经营报表 | 数据质量、公式/格式边界、可复核文件交付 |
| 云文档编辑类 | [cloud-doc-editing-skill.md](cloud-doc-editing-skill.md) | 飞书/在线文档读取、改写、追加、有限编辑 | API 版本、权限边界、编辑前确认、回写验证 |
| 法务合规类 | [legal-compliance-skill.md](legal-compliance-skill.md) | PIPL、数据跨境、AI 合规、隐私政策审查 | 法域边界、风险分级、非律师替代声明、证据链 |
| 多 Agent 协作类 | [multi-agent-collaboration-skill.md](multi-agent-collaboration-skill.md) | 多文件审查、批量生成、并行 QA、多维分析 | 拆分粒度、写入隔离、主流程合并、最终验证 |
| 浏览器自动化类 | [browser-automation-skill.md](browser-automation-skill.md) | Web 表单、后台配置、截图巡检、端到端回归 | 真实页面定位、交互稳定性、截图证据、回归验证 |

## 使用方法

1. 先选择与目标业务最接近的示例。
2. 复制其中的 YAML front matter 示例，改写 `name`、`description`、触发词和边界。
3. 保留“适用/不适用场景”“异常处理”“交付契约”“质量检查清单”四类内容。
4. 如入口文档过长，应将详细流程拆到 `references/`，入口 `SKILL.md` 只保留触发与加载规则。
5. 发布前运行 `scripts/validate-skill.py`；如需流水线集成，使用 `scripts/validate-skill.py --json`。
6. 使用 `scripts/score-skill.py` 做半自动 100 分评分，再结合 `references/skill-scorecard.md` 做人工复核。
7. 如果要快速新建可安装技能，可从 `minimal-skills/` 复制最接近的最小包，再替换业务说明和资源文件。

## 示例改写原则

- 不要直接照搬不相关业务术语。
- 不要把工具调用细节写成不可变承诺，应写清“何时使用、失败如何降级”。
- 不要把敏感信息、token、账号、密钥、客户隐私写入示例。
- 不要让示例绕过平台安全策略、权限确认或用户授权。
- 每个新技能至少应包含：触发条件、输入要求、执行流程、异常处理、交付标准、质量检查。
