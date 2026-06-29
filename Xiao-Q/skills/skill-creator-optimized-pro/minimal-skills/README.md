# 最小可安装 Skill 包模板

本目录提供可复制、可安装、可继续扩展的最小 Skill 包。它们不是完整生产级技能，而是用于快速启动新技能开发的脚手架。

| 模板 | 适用方向 | 起步目录 |
| --- | --- | --- |
| Excel 自动化 | Excel/CSV 清洗、报表、批量处理 | `excel-automation-minimal/` |
| 云文档编辑 | 飞书/在线文档读取、改写、有限编辑 | `cloud-doc-editing-minimal/` |
| 法务合规 | 合同、隐私政策、数据合规、AI 合规初审 | `legal-compliance-minimal/` |
| 多 Agent 协作 | 批量单元并行处理、主流程合并验证 | `multi-agent-collaboration-minimal/` |
| 浏览器自动化 | Web 交互、后台配置、截图巡检、端到端回归 | `browser-automation-minimal/` |

## 推荐复制流程

1. 选择最接近业务目标的目录。
2. 复制为新技能目录，并修改目录名与 `SKILL.md` 的 `name`。
3. 根据真实任务补充 `references/`、`templates/`、`examples/`、`scripts/`。
4. 回到主技能包运行：
   - `python scripts/validate-skill.py <new-skill-dir>`
   - `python scripts/score-skill.py <new-skill-dir>`
5. 达到校验 0 error、评分 80+ 后再发布；90+ 可作为标杆候选。
