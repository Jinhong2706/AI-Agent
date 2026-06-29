---
name: foreign-trade-hotspot
description: 追踪多平台外贸热点视频，分析高赞内容并生成原创视频号口播文案；当需要每日监控热点或创作外贸口播视频时使用
---

# 外贸热点视频文案生成

## 任务目标
本 Skill 用于帮助用户从视频号、抖音、小红书等平台追踪外贸主题的热点视频，特别是高点赞高转发的口播视频，并基于热点内容生成符合视频号规则的原创口播文案（原创度>70%）。

## 能力包含
- 外贸热点视频识别与筛选
- 口播视频内容分析与核心观点提取
- 高原创度文案创作（>70%）
- 视频号规则合规性校验
- 口播风格适配与节奏把控

## 触发条件
- 用户表达"帮我看看今天外贸圈有什么热点"
- 用户说"我要写个外贸相关的视频号文案"
- 用户提供热点视频信息并要求创作文案
- 用户询问"这个视频号内容违规吗"

## 操作步骤

### 1. 热点信息收集
用户提供以下任一形式的热点信息：
- 视频链接 + 平台名称 + 关键数据（点赞数、转发数）
- 视频标题/封面描述 + 观看感受总结
- 口述发现的优质外贸视频内容

智能体根据 [references/hotspot-criteria.md](references/hotspot-criteria.md) 中的标准判断是否为有效热点。

### 2. 内容分析与观点提取
智能体分析热点视频内容：
- 提取核心主题与观点
- 识别外贸相关知识点
- 分析数据表现背后的原因
- 提炼可借鉴的表达方式

### 3. 原创文案生成
基于分析结果，智能体创作新文案：
- 使用 [references/script-structure.md](references/script-structure.md) 中的标准结构
- 借鉴 [assets/script-templates/](assets/script-templates/) 中的模板元素
- 应用 [references/originality-guide.md](references/originality-guide.md) 中的改写技巧
- 确保原创度超过70%

### 4. 合规性校验
智能体检查文案是否违反视频号规则：
- 参考 [references/compliance-rules.md](references/compliance-rules.md) 中的违规清单
- 识别敏感词汇与内容风险
- 提供修改建议

### 5. 输出优化文案
智能体输出：
- 完整口播文案（包含时长预估）
- 文案结构说明
- 原创度说明
- 合规性确认

## 资源索引
- 领域参考：
  - [references/compliance-rules.md](references/compliance-rules.md)（视频号违规规则与敏感词）
  - [references/hotspot-criteria.md](references/hotspot-criteria.md)（外贸热点判断标准）
  - [references/script-structure.md](references/script-structure.md)（口播文案结构模板）
  - [references/originality-guide.md](references/originality-guide.md)（原创度提升方法）
- 模板资源：
  - [assets/script-templates/opening-lines.txt](assets/script-templates/opening-lines.txt)（开场白示例）
  - [assets/script-templates/closing-lines.txt](assets/script-templates/closing-lines.txt)（结尾示例）

## 注意事项
- 所有工作由智能体主导，无需调用脚本
- 用户可根据实际浏览习惯提供热点信息，格式灵活
- 原创度>70%是硬性要求，必须通过改写、重组、补充等方式实现
- 合规性校验需重点关注广告法、平台规则和敏感内容
- 口播文案时长建议控制在15-60秒（约100-400字）

## 使用示例

### 示例1：基于用户描述生成文案
用户：抖音上有个外贸视频火了，讲的是"如何用AI工具优化外贸客户开发"，点赞5万，转发8000，你可以帮我写个类似的视频号文案吗？

智能体执行：
1. 确认为有效热点（高数据表现 + 外贸主题）
2. 分析可能包含的观点（AI工具类型、使用方法、效果展示）
3. 按标准结构创作新文案，采用不同表达方式和案例
4. 检查合规性后输出

### 示例2：多平台热点对比
用户：今天视频号、抖音、小红书三个平台外贸圈有什么热点？帮我挑个最好的写个文案

智能体执行：
1. 询问用户提供各平台热点信息（或基于已有信息分析）
2. 按 hotspot-criteria.md 对比筛选最佳热点
3. 生成原创文案并确保合规

### 示例3：文案合规性检查
用户：我写了个外贸文案，帮我看看有没有违规

智能体执行：
1. 读取用户文案
2. 参考 compliance-rules.md 逐项检查
3. 标出风险点并提供修改建议
