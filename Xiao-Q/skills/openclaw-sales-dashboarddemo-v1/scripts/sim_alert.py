#!/usr/bin/env python3
"""
OpenClaw 销售演示 - 异常告警模拟器
模拟各种异常场景下的告警通知（企业微信/邮件/短信/Webhook 格式）
"""

import json
import random
from datetime import datetime
from typing import Optional


class AlertSimulator:
    """异常告警模拟器，用于演示场景中展示告警能力"""

    # 预设异常场景库
    ALERT_SCENARIOS = {
        "E01-connection-fail": {
            "name": "数据源连接失败",
            "level": "ERROR",
            "icon": "🔌",
            "flow": "销售日报自动汇总",
            "step": "CRM数据拉取",
            "detail": "数据库连接超时 (connection timeout after 30s)",
            "impact": "华东区销售日报无法按时生成",
            "channels": ["企业微信", "邮件"],
            "auto_actions": ["已自动重试 3 次", "间隔：1min → 3min → 5min", "重试均失败，已升级告警"],
            "suggestion": "请检查 CRM 数据库服务状态，确认端口 3306 可达",
        },
        "E02-data-format-error": {
            "name": "数据格式异常",
            "level": "WARN",
            "icon": "📛",
            "flow": "库存同步（全渠道）",
            "step": "数据标准化处理",
            "detail": "检测到 23 条 SKU 编码格式不匹配（预期：SKU+6位数字）",
            "impact": "部分商品库存数据未同步至电商平台",
            "channels": ["企业微信"],
            "auto_actions": ["异常记录已隔离", "正常数据处理继续执行"],
            "suggestion": "检查 WMS 导出配置中的 SKU 编码规则是否变更",
        },
        "E03-threshold-exceed": {
            "name": "业务指标超限预警",
            "level": "WARN",
            "icon": "📊",
            "flow": "运营监控看板",
            "step": "阈值检测引擎",
            "detail": "退款率达到 6.8%（安全阈值 ≤ 5%）| 检测时间窗口：最近24小时",
            "impact": "可能影响店铺评分和用户信任度",
            "channels": ["企业微信", "Webhook"],
            "auto_actions": ["已生成异常商品 TOP10 清单", "已关联最近差评数据"],
            "suggestion": "建议立即核查高退款率商品的售后问题",
        },
        "E04-api-call-fail": {
            "name": "外部 API 调用失败",
            "level": "ERROR",
            "icon": "🌐",
            "flow": "财务月报生成",
            "step": "汇率接口调用",
            "detail": "汇率服务返回 HTTP 500 Internal Server Error | Provider: 中国银行外汇牌价 API",
            "impact": "外币科目无法完成汇率折算，月报数据不完整",
            "channels": ["邮件", "短信"],
            "auto_actions": ["已切换至备用汇率源（上日收盘价）", "流程继续执行并标记该字段为预估"],
            "suggestion": "确认外汇牌价 API 服务状态；如持续异常请联系技术支持",
        },
        "E05-execution-timeout": {
            "name": "流程执行超时",
            "level": "CRITICAL",
            "icon": "⏰",
            "flow": "ERP 数据备份任务",
            "step": "全量数据导出",
            "detail": "单步执行超过设定上限（上限：30分钟，实际已运行 32:15）",
            "impact": "备份任务未完成，存在数据丢失风险",
            "channels": ["短信", "电话", "企业微信", "邮件"],
            "auto_actions": ["⚠️ 已强制终止当前步骤", "✅ 上一步骤快照已保留", "🔄 下次调度将自动恢复增量备份"],
            "suggestion": "请 DBA 立即检查数据库负载和锁等待情况",
        },
    }

    # 告警级别配色与样式
    LEVEL_STYLES = {
        "INFO": {"color": "#2563eb", "bg": "rgba(37,99,235,0.1)", "tag": "ℹ️ 信息"},
        "WARN": {"color": "#f59e0b", "bg": "rgba(245,158,11,0.1)", "tag": "⚠️ 警告"},
        "ERROR": {"color": "#ef4444", "bg": "rgba(239,68,68,0.1)", "tag": "❌ 错误"},
        "CRITICAL": {"color": "#dc2626", "bg": "rgba(220,38,38,0.15)", "tag": "🚨 严重"},
    }

    def __init__(self, scenario_id: str = None):
        if scenario_id and scenario_id not in self.ALERT_SCENARIOS:
            available = ", ".join(self.ALERT_SCENARIOS.keys())
            raise ValueError(f"未知场景 '{scenario_id}'，可选：{available}")
        self.scenario_id = scenario_id or random.choice(list(self.ALERT_SCENARIOS.keys()))
        self.alert = self.ALERT_SCENARIOS[self.scenario_id]
        self.triggered_at = datetime.now()

    def generate_wecom_message(self) -> dict:
        """生成企业微信卡片消息格式"""
        a = self.alert
        style = self.LEVEL_STYLES[a["level"]]

        return {
            "msgtype": "template_card",
            "template_card": {
                "card_type": "text_notice",
                "source": {"desc": "OpenClaw 智能自动化", "desc_color": 0},
                "main_title": {
                    "title": f"{style['tag']} {a['name']}",
                    "desc": f"{a['flow']} — {a['step']}"
                },
                "sub_text": f"影响范围：{a['impact']}\n建议操作：{a['suggestion']}",
                "horizontal_content_list": [
                    {"keyname": "流程名称", "value": a["flow"]},
                    {"keyname": "失败步骤", "value": a["step"]},
                    {"keyname": "异常详情", "value": a["detail"][:50]},
                    {"keyname": "发生时间", "value": self.triggered_at.strftime("%Y-%m-%d %H:%M:%S")},
                ],
                "card_action": {"type": 1, "url": "https://openclaw.console/alerts/latest"}
            }
        }

    def generate_email_html(self) -> str:
        """生成邮件 HTML 格式"""
        a = self.alert
        style = self.LEVEL_STYLES[a["level"]]
        auto_items = "".join(f"<li>{item}</li>" for item in a.get("auto_actions", []))
        channels = " + ".join(a.get("channels", []))

        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
body{{font-family:-apple-system,sans-serif;background:#f5f5f5;padding:20px;color:#333;}}
.container{{max-width:640px;margin:0 auto;background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.1);}}
.header{{background:{style['bg']};padding:20px 24px;border-bottom:3px solid {style['color']};}}
.header h1{{margin:0;font-size:18px;color:{style['color']};}}
.header .meta{{font-size:12px;opacity:.7;margin-top:4px;}}
.body{{padding:24px;line-height:1.7;font-size:14px;}}
.info-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:16px 0;}}
.info-item{{background:#f9fafb;padding:12px;border-radius:6px;border-left:3px solid {style['color']};}}
.info-label{{font-size:11px;color:#888;text-transform:uppercase;}}
.info-value{{font-weight:600;margin-top:2px;}}
.section{{margin:16px 0;}}
.section-title{{font-weight:600;font-size:15px;margin-bottom:8px;display:flex;align-items:center;gap:6px;}}
.action-list{{list-style:none;padding:0;}}
.action-list li{{padding:6px 0;padding-left:18px;position:relative;font-size:13px;color:#555;}}
.action-list li::before{{content:'→';position:absolute;left:0;color:{style['color']};}}
.footer{{text-align:center;padding:16px;background:#f9fafb;font-size:11px;color:#999;border-top:1px solid #eee;}}
.btn{{display:inline-block;background:{style['color']};color:white;padding:8px 20px;
      border-radius:6px;text-decoration:none;font-size:13px;margin-top:8px;}}
</style></head>
<body>
<div class="container">
<div class="header">
<h1>{style['tag']} {a['name']}</div>
<div class="meta">触发于 {self.triggered_at.strftime('%Y-%m-%d %H:%M:%S')} · 告警通道：{channels}</div>
</div>
<div class="body">

<div class="info-grid">
<div class="info-item"><div class="info-label">所属流程</div><div class="info-value">{a['flow']}</div></div>
<div class="info-item"><div class="info-label">失败步骤</div><div class="info-value">{a['step']}</div></div>
<div class="info-item"><div class="info-label">告警级别</div><div class="info-value" style="color:{style['color']}">{a['level']}</div></div>
<div class="info-item"><div class="info-label">通知通道</div><div class="info-value">{channels}</div></div>
</div>

<div class="section">
<div class="section-title">📋 异常详情</div>
<div style="background:#fefce8;padding:12px;border-radius:6px;font-family:monospace;font-size:13px;border:1px solid #fde047;">
{a['detail']}
</div>
</div>

<div class="section">
<div class="section-title">💥 影响范围</div>
<p>{a['impact']}</p>
</div>

<div class="section">
<div class="section-title">🔧 系统自动处置</div>
<ul class="action-list">{auto_items}</ul>
</div>

<div class="section">
<div class="section-title">💡 建议操作</div>
<p>{a['suggestion']}</p>
<a href="https://openclaw.console/alerts/{self.scenario_id}" class="btn">查看详情 →</a>
</div>

</div>
<div class="footer">此告警由 OpenClaw 智能自动化助手自动发出 · 请勿直接回复此邮件</div>
</div>
</body></html>"""

    def generate_sms_text(self) -> str:
        """生成短信格式文本（控制在 70 字以内）"""
        a = self.alert
        level_tag = {"INFO":"[信息]", "WARN":"[警告]", "ERROR":"[错误]", "CRITICAL":"[严重]"}
        text = (
            f"【OpenClaw】{level_tag[a['level']]}{a['name']}！"
            f"{a['flow']}-{a['step']}异常。"
            f"{a['impact'][:20]}。请及时处理。"
        )
        return text

    def generate_webhook_payload(self) -> dict:
        """生成 Webhook JSON Payload"""
        return {
            "alert_id": f"ALERT-{self.scenario_id}-{int(self.triggered_at.timestamp())}",
            "timestamp": self.triggered_at.isoformat(),
            "severity": self.alert["level"],
            "event_type": "automation_failure",
            "flow_name": self.alert["flow"],
            "failed_step": self.alert["step"],
            "error_detail": self.alert["detail"],
            "impact_scope": self.alert["impact"],
            "auto_remediation": self.alert.get("auto_actions", []),
            "recommended_action": self.alert["suggestion"],
            "notification_channels_triggered": self.alert.get("channels", []),
            "console_url": f"https://openclaw.console/alerts/{self.scenario_id}",
        }

    def display_all_formats(self):
        """在终端展示所有格式的告警消息"""
        a = self.alert
        style = self.LEVEL_STYLES[a["level"]]
        
        print("\n" + "=" * 60)
        print(f"  🚨 OpenClaw 告警模拟器")
        print(f"  场景：{a['name']} ({a['level']})")
        print(f"  时间：{self.triggered_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        print(f"\n  ━━ 📱 企业微信卡片消息 ━━")
        wecom = self.generate_wecom_message()
        card = wecom["template_card"]
        print(f"  标题：{card['main_title']['title']}")
        print(f"  副标题：{card['main_title']['desc']}")
        print(f"  概要：{card['sub_text']}")
        for item in card["horizontal_content_list"]:
            print(f"  • {item['keyname']}：{item['value']}")

        print(f"\n  ━━ 📧 邮件通知 ━━")
        print("  （HTML 格式，包含完整异常信息、影响分析、系统处置和建议操作）")

        print(f"\n  ━━ 📲 短信通知 ━━")
        sms = self.generate_sms_text()
        print(f"  内容：{sms} ({len(sms)} 字)")

        print(f"\n  ━━ 🔗 Webhook Payload ━━")
        webhook = self.generate_webhook_payload()
        print(json.dumps(webhook, ensure_ascii=False, indent=4))

        print("\n" + "-" * 60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw 异常告警模拟器")
    parser.add_argument("-s", "--scenario", 
                        choices=list(AlertSimulator.ALERT_SCENARIOS.keys()),
                        help="指定异常场景（默认随机选择）")
    parser.add_argument("--list", action="store_true", help="列出所有可用场景")
    parser.add_argument("-o", "--output", help="输出 JSON 结果到文件")
    
    args = parser.parse_args()

    if args.list:
        print("\n可用异常场景：\n")
        for sid, s in AlertSimulator.ALERT_SCENARIOS.items():
            style = AlertSimulator.LEVEL_STYLES[s["level"]]
            print(f"  {sid}")
            print(f"    名称：{s['name']}")
            print(f"    级别：{style['tag']} ({s['level']})")
            print(f"    流程：{s['flow']}")
            print(f"    描述：{s['detail'][:60]}...")
            print()
        return

    sim = AlertSimulator(scenario_id=args.scenario)
    sim.display_all_formats()

    if args.output:
        import os
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        payload = sim.generate_webhook_payload()
        payload["formats"] = {
            "wecom": sim.generate_wecom_message(),
            "sms": sim.generate_sms_text(),
            "email_preview": sim.alert["suggestion"],
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n  💾 完整结果已保存至：{args.output}")


if __name__ == "__main__":
    main()
