# 版本更新说明 — skill-creator-king

## v3.6.0 - 2026-05-08

### 新增
- quality-audit 新增第11个评分维度「README 介绍板块」（检测技能 README 是否有"这是什么"介绍段落，5分权重）
- init_skill.py README 模板新增「这是什么」板块（是什么/适合谁/不适合谁）
- review-guide.md 审查流程新增：检测到 README 介绍缺失时自动分析 SKILL.md 生成草稿
- phase-5-verification.md 交付清单新增 README 介绍板块确认项
- upgrade-guide.md 升级检查新增 README 介绍板块要求
- validate.py cross-audit 交叉文档一致性审计（README 版本 vs SKILL.md frontmatter 一致、内容丰富度检查）
- 来源：wechat-article-craft 实战复盘发现文档不一致问题，抽象为通用检查回归 SCK

### 改进
- Token 预算微调 L2 5600→5700

---

## v3.5.0 - 2026-05-08

### 新增
- 原则 10：功能生效阈值（Feature Viability Gate）——新功能提审前过三道门（高频用户/3个独特场景/最简v1）
- 反模式 #13：functional_seduction——识别「因智力漂亮而建」而非「因用户需要而建」的设计类反模式
- review-guide：功能膨胀检查（诊断后追问"哪些不修也能完成80%核心任务"）
- review-guide：Drift Guard 回归检测（修复完成后跑 tests/ 确认原有用例无回归）
- 来源：human-stars 造星功能设计反思

### 变更
- config.yaml 新增 viability_gate 咨询性配置段
- PRINCIPLES.md 原则数 9→10

---

## v3.4.0 - 2026-05-07

### 新增
- self-audit.py D7+D8 检测：未测试代码路径扫描 + 生成物累积扫描（data/cache/ 冗余文件）
- review-guide.md 1.5 审计策略参考：8类错误清单（D1-D8）/ 7条审计策略 / 3种AI认知偏误 / 策略×生命周期映射

### 变更
- SKILL.md version 3.3.0 → 3.4.0，description 补 self-audit
- self-audit.py --list-checks 纪律验证描述补 D7+D8
