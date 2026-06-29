# LinkedIn 商机识别规则

本文档定义了 LinkedIn 潜客动态的商机识别规则和评分标准。

---

## 一、信号类型与权重

### 1.1 高优先级信号 (权重 40-50 分)

| 信号类型 | 触发条件 | 关键词示例 | 建议响应时间 |
|----------|----------|------------|--------------|
| 职位变动 | 潜客更换工作 | "excited to announce", "new role", "joined", "started as" | 24 小时内 |
| 融资动态 | 公司获得投资 | "funding", "investment", "series A/B/C", "raised" | 24 小时内 |
| 扩张计划 | 公司宣布扩张 | "expansion", "growing", "new market", "opening office" | 48 小时内 |
| 高管任命 | 新任命决策者 | "appointed", "named as", "welcome to the team" | 48 小时内 |

### 1.2 中优先级信号 (权重 20-30 分)

| 信号类型 | 触发条件 | 关键词示例 | 建议响应时间 |
|----------|----------|------------|--------------|
| 产品发布 | 公司发布新产品 | "launch", "new product", "introducing", "release" | 72 小时内 |
| 内容提及需求 | 发布内容提及痛点 | "challenge", "struggle", "looking for", "need" | 72 小时内 |
| 招聘动态 | 大量招聘信息 | "hiring", "join our team", "we're hiring" | 1 周内 |
| 获奖/认证 | 公司或个人获奖 | "award", "recognition", "certified", "top 100" | 1 周内 |

### 1.3 低优先级信号 (权重 5-15 分)

| 信号类型 | 触发条件 | 关键词示例 | 建议响应时间 |
|----------|----------|------------|--------------|
| 日常分享 | 分享文章/观点 | "article", "thoughts", "sharing", "read this" | 日报汇总 |
| 活动参与 | 参加会议/活动 | "event", "conference", "webinar", "summit" | 日报汇总 |
| 学习认证 | 获得新证书 | "certificate", "completed", "course", "learning" | 日报汇总 |
| 互动行为 | 点赞/评论他人 | (无特定关键词) | 日报汇总 |

---

## 二、职位关键词库

### 2.1 决策者职位 (高优先级)

```
C-Level: CEO, CTO, CMO, CFO, COO, CIO, CDO
VP Level: VP, Vice President, 副总裁
Director: Director, 总监，部长
Head: Head of, Department Head, 部门负责人
Founder: Founder, Co-Founder, 创始人，合伙人
Owner: Owner, 老板，企业主
```

### 2.2 影响者职位 (中优先级)

```
Manager: Manager, 经理，主管
Senior: Senior, 资深，高级
Lead: Lead, 负责人，组长
Specialist: Specialist, 专家，专员
Consultant: Consultant, 顾问
```

### 2.3 执行者职位 (低优先级)

```
Junior: Junior, 初级，助理
Assistant: Assistant, 助手，文员
Intern: Intern, 实习生
Coordinator: Coordinator, 协调员
```

---

## 三、行业关键词库

### 3.1 Kingsway 目标行业

| 行业 | 关键词 | 商机匹配度 |
|------|--------|------------|
| B2B 外贸 | "外贸", "export", "B2B", "wholesale" | ⭐⭐⭐⭐⭐ |
| 跨境电商 | "电商", "e-commerce", "DTC", "独立站" | ⭐⭐⭐⭐⭐ |
| 制造业 | "制造", "manufacturing", "factory" | ⭐⭐⭐⭐ |
| 物流服务 | "物流", "shipping", "freight", "supply chain" | ⭐⭐⭐⭐ |
| 企业服务 | "SaaS", "软件", "technology", "solutions" | ⭐⭐⭐⭐ |
| 营销机构 | "营销", "marketing", "agency", "广告" | ⭐⭐⭐ |

### 3.2 需求信号关键词

```
视频营销相关:
- "video marketing", "视频营销", "video content"
- "video production", "视频制作", "video creation"
- "video hosting", "视频托管", "video platform"

获客转化相关:
- "lead generation", "获客", "lead gen"
- "conversion", "转化", "conversion rate"
- "customer acquisition", "客户获取"

痛点信号:
- "struggle with", "challenge", "pain point"
- "looking for", "need a solution", "recommend"
- "too expensive", "too complicated", "not working"
```

---

## 四、评分算法

### 4.1 基础分

```
潜客优先级基础分:
- 高优先级潜客：30 分
- 中优先级潜客：20 分
- 低优先级潜客：10 分
```

### 4.2 活动类型加分

```
- 职位变动：+40 分
- 公司动态 (融资/扩张): +35 分
- 产品发布：+25 分
- 内容发布：+15 分
- 互动行为：+10 分
```

### 4.3 关键词匹配加分

```
高优先级关键词匹配：每个 +15 分 (上限 30 分)
中优先级关键词匹配：每个 +10 分 (上限 20 分)
低优先级关键词匹配：每个 +5 分 (上限 10 分)
```

### 4.4 职位加分

```
决策者职位 (C-Level/VP/Director): +15 分
影响者职位 (Manager/Senior): +10 分
执行者职位：+5 分
```

### 4.5 最终等级判定

```
总分 ≥ 70: 高优先级 (立即跟进)
总分 ≥ 40: 中优先级 (48 小时内跟进)
总分 < 40: 低优先级 (日报汇总)
```

---

## 五、跟进策略

### 5.1 高优先级商机

**响应时间**: 24 小时内

**跟进方式**:
1. 发送个性化祝贺消息
2. 介绍 Kingsway 核心价值 (30 字以内)
3. 提供试用链接 (14 天免费)

**话术模板**:
```
Hi {name}, 恭喜履新{position}! 

注意到{company}在{industry}领域发展迅速，
Kingsway 已帮助 2050+ 企业通过视频营销提升获客转化，
或许能为您新团队的业务目标提供支持。

14 天免费试用：https://kingswayvideo.com
```

### 5.2 中优先级商机

**响应时间**: 48-72 小时

**跟进方式**:
1. 在动态下评论互动 (提供价值)
2. 发送连接请求 (附个性化说明)
3. 等待接受后发送产品介绍

### 5.3 低优先级商机

**响应方式**: 
- 计入日报汇总
- 适度点赞保持存在感
- 等待更高优先级信号

---

## 六、风险控制

### 6.1 避免过度营销

- 同一潜客 7 天内最多联系 1 次
- 避免在敏感时期联系 (裁员、负面新闻)
- 尊重对方不回复的信号

### 6.2 合规使用

- 遵守 LinkedIn 服务条款
- 不使用自动化批量操作
- 仅监控已建立业务联系的潜客

### 6.3 数据隐私

- 不存储敏感个人信息
- 数据本地加密存储
- 定期清理过期数据

---

## 七、规则更新日志

| 日期 | 更新内容 | 版本 |
|------|----------|------|
| 2026-03-31 | 初始版本 | v1.0 |

---

**维护说明**: 
- 根据实际转化率调整评分权重
- 每季度回顾关键词库有效性
- 收集销售团队反馈优化规则
