# 多渠道内容分发报告

> 报告生成时间：{{report_time}}
> 内容来源：{{content_source}}
> 操作人员：{{operator_name}}

---

## 一、内容概要

| 维度 | 分析结果 |
|------|---------|
| 核心主题 | {{core_theme}} |
| 内容类型 | {{content_type}} |
| 语气风格 | {{tone_style}} |
| 原文字数 | {{original_word_count}} 字 |
| 段落数量 | {{paragraph_count}} 段 |
| 适配评分 | {{adaptation_score}}/100 |
| 适配等级 | {{adaptation_level}} |

### 核心信息点

{{#each key_points}}
{{@index}}. {{this}}
{{/each}}

---

## 二、平台适配版本

{{#each platform_versions}}

### {{platform_name}}

**基本信息**
| 项目 | 内容 |
|------|------|
| 目标字数 | {{target_word_count}} 字 |
| 实际字数 | {{actual_word_count}} 字 |
| 字数达标 | {{word_count_status}} |
| 内容结构 | {{structure_type}} |

**推荐标题**
{{#each title_candidates}}
{{@index}}. {{this}}
{{/each}}

**正文**

{{content_body}}

**配图建议**
{{#each image_suggestions}}
- {{this}}
{{/each}}

**标签/话题**
{{hashtags}}

**发布时间建议**
{{publish_time_suggestion}}

**互动引导策略**
{{engagement_strategy}}

---

{{/each}}

## 三、质量评估

| 平台 | 钩子评分 | 可读性评分 | 完整度评分 | 互动设计评分 | 综合评分 |
|------|---------|-----------|-----------|------------|---------|
{{#each quality_scores}}
| {{platform}} | {{hook_score}}/100 | {{readability_score}}/100 | {{completeness_score}}/100 | {{engagement_score}}/100 | {{overall_score}}/100 |
{{/each}}

### 评分说明

- **钩子评分**：标题和开头前3行/3秒的吸引力
- **可读性评分**：排版结构、语言流畅度、信息密度
- **完整度评分**：核心信息保留度、论据支撑充分度
- **互动设计评分**：CTA引导、评论区互动预设

---

## 四、敏感词检查

| 检查类别 | 检查结果 | 详情 |
|---------|---------|------|
| 营销词汇 | {{marketing_check}} | {{marketing_details}} |
| 夸大宣传 | {{exaggeration_check}} | {{exaggeration_details}} |
| 平台违规 | {{violation_check}} | {{violation_details}} |
| 专业合规 | {{compliance_check}} | {{compliance_details}} |

{{#if sensitive_word_suggestions}}

### 替换建议

{{#each sensitive_word_suggestions}}
- 原词「{{original}}」→ 建议替换为「{{replacement}}」（原因：{{reason}}）
{{/each}}

{{/if}}

---

## 五、发布排期建议

| 发布顺序 | 平台 | 推荐日期 | 推荐时间 | 发布间隔 | 优先级 |
|---------|------|---------|---------|---------|--------|
{{#each publish_schedule}}
| 第{{step}}步 | {{platform}} | {{date}} | {{time}} | {{interval}} | P{{priority}} |
{{/each}}

### 发布注意事项

{{publish_notes}}

---

## 六、后续互动话术

### 评论区互动预设

{{#each comment_templates}}
**场景**：{{scenario}}
**回复模板**：「{{reply_template}}」

{{/each}}

### 追加内容建议

{{#each follow_up_suggestions}}
{{@index}}. {{this}}
{{/each}}

---

## 七、数据追踪指标

| 平台 | 核心指标 | 目标值 | 追踪周期 |
|------|---------|--------|---------|
{{#each tracking_metrics}}
| {{platform}} | {{metric}} | {{target_value}} | {{tracking_period}} |
{{/each}}

---

*本报告由多渠道内容分发优化器自动生成*
*报告ID：{{report_id}}*
*生成引擎版本：{{engine_version}}*
