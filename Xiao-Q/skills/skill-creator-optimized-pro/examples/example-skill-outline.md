# 示例：把“合同审查流程”沉淀为 Skill

## 触发描述
当用户要求审查合同、识别法律风险、输出修订建议或生成审查清单时使用。

## 入口内容
SKILL.md 只保留触发条件、输入要求、审查流程、输出格式和质量门禁。

## 参考资料
- `references/risk-taxonomy.md`：风险分类与等级。
- `references/output-template.md`：审查报告模板。
- `scripts/extract-clauses.py`：如需稳定抽取条款，可放脚本。

## 质量门禁
- 风险必须分级。
- 每条风险要有依据、影响和建议。
- 不确定事项要标注需律师确认。
