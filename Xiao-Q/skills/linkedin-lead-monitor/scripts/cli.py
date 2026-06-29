#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn 潜客监控 - 命令行工具
提供潜客管理、监控执行、记录查询等功能
"""

import argparse
import sqlite3
import json
import os
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 修复 Windows 中文输出问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DB_PATH = Path(__file__).parent.parent / 'data' / 'leads.db'


def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建潜客表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            linkedin_url TEXT UNIQUE,
            company TEXT,
            position TEXT,
            priority TEXT DEFAULT 'medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    
    # 创建设动态记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY,
            lead_id INTEGER,
            activity_type TEXT,
            content TEXT,
            opportunity_score INTEGER,
            opportunity_level TEXT,
            ai_analysis TEXT,
            suggested_action TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notified BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (lead_id) REFERENCES leads(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ 数据库初始化完成")


def add_lead(name: str, url: str, priority: str = 'medium', company: str = '', position: str = ''):
    """添加潜客"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO leads (name, linkedin_url, company, position, priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, url, company, position, priority))
        conn.commit()
        print(f"✓ 已添加潜客：{name} ({url})")
    except sqlite3.IntegrityError:
        print(f"✗ 潜客已存在：{url}")
    finally:
        conn.close()


def remove_lead(name: str):
    """删除潜客"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM leads WHERE name = ?', (name,))
    if cursor.rowcount > 0:
        print(f"✓ 已删除潜客：{name}")
    else:
        print(f"✗ 未找到潜客：{name}")
    
    conn.commit()
    conn.close()


def list_leads():
    """列出全部潜客"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, linkedin_url, company, position, priority, created_at FROM leads ORDER BY priority, created_at')
    rows = cursor.fetchall()
    
    if not rows:
        print("暂无监控的潜客")
        return
    
    print("\n" + "=" * 80)
    print(f"{'姓名':<20} {'公司':<20} {'职位':<20} {'优先级':<10}")
    print("=" * 80)
    
    for row in rows:
        name, url, company, position, priority, created_at = row
        company = company or '未知'
        position = position or '未知'
        priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority, '⚪')
        print(f"{priority_emoji} {name:<18} {company:<18} {position:<18} {priority:<10}")
    
    print("=" * 80)
    print(f"共 {len(rows)} 个潜客\n")
    
    conn.close()


def import_leads(file_path: str):
    """批量导入潜客 (CSV 格式)"""
    import csv
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added = 0
    skipped = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cursor.execute('''
                    INSERT INTO leads (name, linkedin_url, company, position, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    row.get('name', ''),
                    row.get('url', ''),
                    row.get('company', ''),
                    row.get('position', ''),
                    row.get('priority', 'medium')
                ))
                added += 1
            except sqlite3.IntegrityError:
                skipped += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ 导入完成：新增 {added} 个，跳过 {skipped} 个")


def export_leads(format: str = 'csv', output: str = ''):
    """导出潜客数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name, linkedin_url, company, position, priority FROM leads')
    rows = cursor.fetchall()
    
    if format == 'csv':
        import csv
        output_file = output or 'leads_export.csv'
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'url', 'company', 'position', 'priority'])
            writer.writerows(rows)
        print(f"✓ 已导出到：{output_file}")
    
    elif format == 'json':
        output_file = output or 'leads_export.json'
        data = [
            {
                'name': row[0],
                'url': row[1],
                'company': row[2],
                'position': row[3],
                'priority': row[4]
            }
            for row in rows
        ]
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ 已导出到：{output_file}")
    
    conn.close()


def show_history(lead_name: str = '', since: str = ''):
    """查看监控记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = '''
        SELECT a.created_at, l.name, a.activity_type, a.opportunity_level, a.content
        FROM activities a
        JOIN leads l ON a.lead_id = l.id
        WHERE 1=1
    '''
    params = []
    
    if lead_name:
        query += ' AND l.name = ?'
        params.append(lead_name)
    
    if since:
        query += ' AND a.created_at >= ?'
        params.append(since)
    
    query += ' ORDER BY a.created_at DESC LIMIT 50'
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    if not rows:
        print("暂无监控记录")
        return
    
    print("\n" + "=" * 80)
    print(f"{'时间':<20} {'潜客':<15} {'类型':<15} {'等级':<10} {'内容':<20}")
    print("=" * 80)
    
    for row in rows:
        created_at, name, activity_type, level, content = row
        level_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(level, '⚪')
        content_preview = content[:20] + '...' if len(content) > 20 else content
        print(f"{created_at:<20} {name:<15} {activity_type:<15} {level_emoji} {level:<8} {content_preview:<20}")
    
    print("=" * 80)
    print(f"共 {len(rows)} 条记录\n")
    
    conn.close()


def show_stats():
    """显示统计报表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 潜客总数
    cursor.execute('SELECT COUNT(*) FROM leads')
    total_leads = cursor.fetchone()[0]
    
    # 按优先级统计
    cursor.execute('SELECT priority, COUNT(*) FROM leads GROUP BY priority')
    priority_stats = dict(cursor.fetchall())
    
    # 今日动态
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('SELECT COUNT(*) FROM activities WHERE DATE(created_at) = ?', (today,))
    today_activities = cursor.fetchone()[0]
    
    # 未读通知
    cursor.execute('SELECT COUNT(*) FROM activities WHERE notified = FALSE')
    unread = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n" + "=" * 50)
    print("📊 LinkedIn 潜客监控统计")
    print("=" * 50)
    print(f"监控潜客总数：{total_leads}")
    print(f"  - 高优先级：{priority_stats.get('high', 0)}")
    print(f"  - 中优先级：{priority_stats.get('medium', 0)}")
    print(f"  - 低优先级：{priority_stats.get('low', 0)}")
    print(f"\n今日动态：{today_activities} 条")
    print(f"未读通知：{unread} 条")
    print("=" * 50 + "\n")


def setup_config():
    """初始化配置"""
    env_template = Path(__file__).parent.parent / '.env.template'
    env_file = Path(__file__).parent.parent / '.env'
    
    if env_file.exists():
        print("✓ 配置文件已存在")
        return
    
    template_content = """# LinkedIn 账号 (用于浏览器登录)
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password

# 推送配置 (飞书)
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
FEISHU_USER_ID=ou_xxxxxxxxxxxxx

# 推送配置 (微信 - 可选)
WECHAT_ENABLED=false
WECHAT_SESSION_KEY=xxx

# 推送配置 (邮件 - 可选)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your_app_password

# 监控设置
CHECK_INTERVAL_MINUTES=30
TIMEZONE=Asia/Shanghai
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("✓ 配置文件已创建，请编辑 .env 文件填写实际配置")


def main():
    parser = argparse.ArgumentParser(description='LinkedIn 潜客监控工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # setup 命令
    subparsers.add_parser('setup', help='初始化配置')
    
    # add 命令
    add_parser = subparsers.add_parser('add', help='添加潜客')
    add_parser.add_argument('--url', required=True, help='LinkedIn 主页链接')
    add_parser.add_argument('--name', required=True, help='潜客姓名')
    add_parser.add_argument('--company', default='', help='公司名')
    add_parser.add_argument('--position', default='', help='职位')
    add_parser.add_argument('--priority', choices=['high', 'medium', 'low'], default='medium', help='优先级')
    
    # remove 命令
    remove_parser = subparsers.add_parser('remove', help='删除潜客')
    remove_parser.add_argument('--name', required=True, help='潜客姓名')
    
    # list 命令
    subparsers.add_parser('list', help='列出全部潜客')
    
    # import 命令
    import_parser = subparsers.add_parser('import', help='批量导入潜客')
    import_parser.add_argument('--file', required=True, help='CSV 文件路径')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出潜客数据')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='导出格式')
    export_parser.add_argument('--output', default='', help='输出文件路径')
    
    # check 命令
    check_parser = subparsers.add_parser('check', help='检查潜客动态')
    check_parser.add_argument('--name', default='', help='潜客姓名 (不填则检查全部)')
    
    # watch 命令
    watch_parser = subparsers.add_parser('watch', help='持续监控')
    watch_parser.add_argument('--interval', type=int, default=30, help='检查间隔 (分钟)')
    
    # history 命令
    history_parser = subparsers.add_parser('history', help='查看监控记录')
    history_parser.add_argument('--lead', default='', help='潜客姓名')
    history_parser.add_argument('--since', default='', help='起始日期 (YYYY-MM-DD)')
    
    # stats 命令
    subparsers.add_parser('stats', help='查看统计报表')
    
    # status 命令
    subparsers.add_parser('status', help='查看监控状态')
    
    # logs 命令
    subparsers.add_parser('logs', help='查看日志')
    
    # login 命令
    subparsers.add_parser('login', help='手动登录 LinkedIn 并保存会话')
    
    args = parser.parse_args()
    
    # 初始化数据库
    if args.command != 'setup':
        init_db()
    
    # 执行命令
    if args.command == 'setup':
        setup_config()
    elif args.command == 'add':
        add_lead(args.name, args.url, args.priority, args.company, args.position)
    elif args.command == 'remove':
        remove_lead(args.name)
    elif args.command == 'list':
        list_leads()
    elif args.command == 'import':
        import_leads(args.file)
    elif args.command == 'export':
        export_leads(args.format, args.output)
    elif args.command == 'check':
        # 调用 monitor.py 执行检查
        from monitor import run_check
        run_check(args.name)
    elif args.command == 'watch':
        # 持续监控
        import time
        interval = args.interval
        print(f"🔍 启动持续监控，每 {interval} 分钟检查一次...")
        print("按 Ctrl+C 停止监控\n")
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始检查...")
                from monitor import run_check
                run_check('')
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 检查完成，等待 {interval} 分钟...")
                time.sleep(interval * 60)
        except KeyboardInterrupt:
            print("\n\n⚠️  监控已停止")
    elif args.command == 'history':
        show_history(args.lead, args.since)
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'status':
        # 显示监控状态
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM leads')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM activities WHERE notified = FALSE')
        unread = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM activities WHERE created_at >= date("now")')
        today = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n📊 LinkedIn 潜客监控状态")
        print("=" * 40)
        print(f"监控潜客：{total} 个")
        print(f"今日动态：{today} 条")
        print(f"未读通知：{unread} 条")
        
        # 检查配置
        if os.getenv('LINKEDIN_EMAIL'):
            print(f"LinkedIn 账号：✅ 已配置")
        else:
            print(f"LinkedIn 账号：❌ 未配置")
        
        if os.getenv('FEISHU_WEBHOOK_URL'):
            print(f"飞书推送：✅ 已配置")
        else:
            print(f"飞书推送：❌ 未配置")
        
        print("=" * 40 + "\n")
    elif args.command == 'logs':
        # 查看最近日志
        log_file = Path(__file__).parent.parent / 'data' / 'monitor.log'
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print("最近 50 条日志：")
                print("=" * 60)
                for line in lines[-50:]:
                    print(line.strip())
                print("=" * 60)
        else:
            print("暂无日志文件")
    elif args.command == 'login':
        # 手动登录 LinkedIn 并保存会话
        from monitor import LinkedInMonitor
        monitor = LinkedInMonitor()
        try:
            monitor.start_browser()
            monitor.login()
        finally:
            monitor.close()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
