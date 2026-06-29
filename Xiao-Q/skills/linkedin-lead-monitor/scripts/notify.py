#!/usr/bin/env python3
"""
LinkedIn 潜客监控 - 消息推送模块
直接使用飞书 API 推送消息
"""

import json
import os
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class FeishuNotifier:
    """飞书消息推送 - 使用飞书 API"""
    
    def __init__(self):
        self.user_id = os.getenv('FEISHU_USER_ID', 'ou_c3f7154393d37a4f09b784dde48cbf5d')
        # 使用 OpenClaw 飞书集成的 webhook（需要配置）
        # 或者直接用飞书机器人 webhook
        self.webhook_url = os.getenv('FEISHU_WEBHOOK_URL', '')
    
    def send_opportunity_alert(self, lead_info: dict, activity: dict, analysis: dict):
        """发送商机提醒 - 单条动态推送（保留接口兼容性）"""
        # 现在统一用报告模式，这个方法暂时不做处理
        print(f"ℹ️  单条推送已跳过，使用报告模式")
        return True
    
    def send_dynamic_report(self, lead_name: str, activities: list, lead_info: dict):
        """发送潜客动态报告 - 汇总成一条消息"""
        
        if not activities:
            print("[INFO] 无动态需要报告")
            return False
        
        date = datetime.now().strftime("%Y-%m-%d %H:%M")
        url = lead_info.get('linkedin_url', '#')
        company = lead_info.get('company', '未知')
        
        # 构建汇总报告（控制在 500 字以内）
        report_lines = [
            f"📊 LinkedIn 潜客动态报告",
            f"潜客：{lead_name}",
            f"公司：{company}",
            f"时间：{date}",
            f"",
            f"最新动态（{len(activities)}条）:",
        ]
        
        # 添加动态摘要（每条 50 字）
        for i, act in enumerate(activities[:5], 1):
            content = act.get('content', '')[:50].replace('\n', ' ')
            report_lines.append(f"{i}. {content}...")
        
        # 添加跟进建议和链接
        report_lines.extend([
            f"",
            f"💡 建议：点赞互动 + 关注动态 + 寻找沟通时机",
            f"",
            f"主页：{url}"
        ])
        
        # 合并成一条消息
        report_msg = "\n".join(report_lines)
        
        print(f"\n[报告内容]\n{report_msg}")
        
        # 只发送一条消息
        return self._send_message(report_msg, 'report')
    
    def _send_message(self, message: str, level: str = 'medium'):
        """使用 OpenClaw message 工具发送飞书消息"""
        try:
            import subprocess
            
            # 使用 OpenClaw message 工具
            openclaw_path = r'C:\Users\caizheyu\AppData\Roaming\npm\openclaw.cmd'
            
            # 使用 UTF-8 编码执行
            cmd = f'"{openclaw_path}" message send --target {self.user_id} --channel feishu --message "{message}"'
            
            # 使用 chcp 65001 设置 UTF-8 编码
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.dwFlags |= subprocess.STARTF_USESTDHANDLES
            
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace',
                creationflags=subprocess.CREATE_NO_WINDOW,
                env=env
            )
            
            if result.returncode == 0:
                print(f"✓ 飞书消息发送成功（优先级：{level}）")
                return True
            else:
                print(f"✗ 飞书消息发送失败：{result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ 飞书消息发送异常：{e}")
            return False
    
    def _translate_type(self, activity_type: str) -> str:
        """翻译活动类型"""
        translations = {
            'job_change': '职位变动',
            'company_update': '公司动态',
            'post': '内容发布',
            'interaction': '互动行为'
        }
        return translations.get(activity_type, activity_type)


class NotificationManager:
    """推送管理器"""
    
    def __init__(self):
        self.feishu = FeishuNotifier()
    
    def send_alert(self, lead_info: dict, activity: dict, analysis: dict):
        """发送商机提醒"""
        level = analysis.get('level', 'low')
        
        # 高优先级和中优先级：发送飞书
        if level in ['high', 'medium']:
            self.feishu.send_opportunity_alert(lead_info, activity, analysis)
        
        # 低优先级：不推送
        else:
            print(f"ℹ️  低优先级动态，计入日报汇总")
    
    def send_dynamic_report(self, lead_name: str, activities: list, lead_info: dict):
        """发送潜客动态报告"""
        return self.feishu.send_dynamic_report(lead_name, activities, lead_info)


if __name__ == '__main__':
    # 测试示例
    manager = NotificationManager()
    
    test_lead = {
        'name': 'John Doe',
        'company': 'TechCorp',
        'position': 'Marketing Director',
        'linkedin_url': 'https://www.linkedin.com/in/john-doe'
    }
    
    test_activity = {
        'type': 'job_change',
        'content': 'Excited to announce my new role as Marketing Director at TechCorp!'
    }
    
    test_analysis = {
        'level': 'high',
        'score': 85,
        'analysis': '职位变动是最佳接触时机，建议 24 小时内联系。',
        'suggested_action': '发送祝贺消息并介绍 Kingsway 核心价值。'
    }
    
    manager.send_alert(test_lead, test_activity, test_analysis)
