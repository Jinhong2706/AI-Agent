# OpenClaw 异常告警模式与配置参考

> 告警通道、规则模板与最佳实践

---

## 告警通道矩阵

| 通道 | 适用场景 | 响应速度 | 成本 | 配置复杂度 |
|------|---------|---------|------|-----------|
| 企业微信 | 日常运营告警 | 秒级 | 免费 | ⭐ |
| 邮件 | 详细报告/非紧急 | 分钟级 | 免费 | ⭐⭐ |
| 短信 (SMS) | P0 紧急告警 | 秒级 | 低 | ⭐⭐ |
| Webhook | 对接第三方系统 | 实时 | 免费 | ⭐⭐⭐ |
| 电话语音 | P0 超时未处理 | 即时 | 中 | ⭐⭐⭐ |

## 告警分级标准

### Level 1：信息通知（INFO）

**触发条件**：流程正常完成、周期性报告生成

```yaml
level: INFO
channels: [企业微信]
template: "✅ [流程名] 执行完成 | 耗时: {duration} | 处理记录: {count}条"
frequency: 每次执行后
```

### Level 2：警告（WARN）

**触发条件**：性能下降、接近阈值、数据量异常

```yaml
level: WARN
channels: [企业微信, 邮件]
template: "⚠️ [流程名] 警告 | {metric}: {value} (阈值: {threshold}) | 时间: {timestamp}"
escalation: 同一问题30分钟内重复则升级至ERROR
```

### Level 3：错误（ERROR）

**触发条件**：执行失败、数据源不可达、关键步骤超时

```yaml
level: ERROR
channels: [企业微信, 邮件, Webhook]
template: "❌ [流程名] 执行失败 | 步骤: {step} | 错误: {error_detail} | 时间: {timestamp}"
auto_retry: true
retry_count: 3
retry_interval: 5min
```

### Level 4：严重致命（CRITICAL）

**触发条件**：数据丢失风险、安全事件、核心业务完全中断

```yaml
level: CRITICAL
channels: [短信, 电话, 企业微信, 邮件, Webhook]
template: "🚨 [流程名] 严重故障! | 影响: {impact_scope} | 需立即处理! | 时间: {timestamp}"
phone_escalation: 15分钟未确认阅读则自动拨打电话
management_cc: [CTO邮箱, 运维负责人]
```

## 常用告警规则模板

### R01：数据源连接失败

```
IF 数据源连接状态 == 失败
THEN 
  - 立即发送 ERROR 级告警
  - 自动重试 3 次，间隔递增（1min → 3min → 5min）
  - 重试全失败 → 升级为 CRITICAL，通知值班人员 + 主管
```

### R02：数据处理异常率超标

```
IF 异常数据数 / 总数据数 > 5%
THEN
  - 发送 WARN 级告警，附带异常数据样例（脱敏）
  - 标记该批次需人工复核
  - 记录异常模式用于后续规则优化
```

### R03：流程执行超时

```
IF 单步执行时间 > 历史均值 × 3
OR 总执行时间 > 设定上限
THEN
  - 发送 ERROR 级告警
  - 输出当前执行堆栈和资源占用情况
  - 可选：自动终止并保留现场快照
```

### R04：业务阈值触达

```
IF 业务指标 < 下限 OR 业务指标 > 上限
THEN
  - 根据偏离程度选择 WARN 或 ERROR
  - 附带趋势图表（最近7天数据）
  - 推送相关干系人（按业务维度匹配）
```

### R05：连续失败检测

```
IF 同一流程连续失败 >= 2 次
THEN
  - 强制升级告警级别 +1
  - 触发根因分析任务
  - 暂停后续自动执行（需人工确认后恢复）
```

## 告警消息格式规范

### 企业微信卡片消息结构

```json
{
  "msgtype": "template_card",
  "template_card": {
    "card_type": "text_notice",
    "source": {
      "desc": "OpenClaw 智能自动化",
      "desc_color": 0
    },
    "main_title": {
      "title": "🔴 流程执行告警",
      "desc": "销售日报生成 - 数据源连接失败"
    },
    "sub_text": "影响范围：华东区销售日报无法按时生成\n建议操作：检查数据库服务状态",
    "horizontal_content_list": [
      {"keyname": "流程名称", "value": "销售日报自动汇总"},
      {"keyname": "失败步骤", "value": "CRM数据拉取"},
      {"keyname": "错误代码", "value": "E_CONNECTION_TIMEOUT"},
      {"keyname": "发生时间", "value": "2026-04-09 08:32:15"}
    ],
    "card_action": {
      "type": 1,
      "url": "https://openclaw.console/flows/sales-daily/runs/latest"
    }
  }
}
```

### 邮件告警 HTML 模板要点

- **标题**：包含级别标识 🔴🟡🟢 + 流程名 + 一句话摘要
- **首屏信息**：发生时间、影响范围、当前状态、建议操作（4 格布局）
- **详细信息**：折叠区域展示完整错误日志和技术细节
- **快捷操作**：「查看详情」「立即重试」「暂停流程」按钮链接

### 短信告警文本（控制在 70 字以内）

```
【OpenClaw】[CRITICAL] 销售日报流程执行失败！数据源连接超时，影响华东区报表输出。请立即处理。查看详情: https://xxx
```

## 告警降噪策略

### 时间窗口聚合

```
同类告警在 10 分钟内只发送一次
末尾追加："本窗口内已发生 N 次类似告警"
```

### 维护期静默

```yaml
maintenance_windows:
  - name: "周末例维护"
    schedule: "每周六 02:00-06:00"
    silence_levels: [INFO, WARN]
    action: "延迟到维护结束后批量推送摘要"
```

### 自动恢复静默

```
IF 告警发出后 5 分钟内自动恢复成功
THEN 追加一条恢复通知："✅ 已自动恢复正常"
ELSE 保持原告警状态不变
```

## 最佳实践清单

- [ ] 所有生产环境流程必须至少配置一个告警通道
- [ ] CRITICAL 级别必须覆盖 2 个以上独立通道
- [ ] 告警消息中必须包含可操作的链接或指引
- [ ] 定期（每月）审查告警规则有效性，关闭无效告警
- [ ] 建立告警响应 SLA 并纳入团队考核
- [ ] 重要变更前先在预发环境验证告警逻辑
- [ ] 告警联系人信息每季度更新一次
