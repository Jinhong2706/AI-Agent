#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn 潜客监控 - 配置检查工具
"""

import os
import sys
import io
from pathlib import Path
from dotenv import load_dotenv

# 修复 Windows 中文输出问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DB_PATH = Path(__file__).parent.parent / 'data' / 'leads.db'

def check_env():
    """检查配置文件"""
    print("\n📋 检查配置文件...")
    
    if not env_path.exists():
        print("  ✗ .env 文件不存在")
        print("  → 运行：python scripts/cli.py setup")
        return False
    
    print("  ✓ .env 文件存在")
    
    # 检查必填项
    required = ['FEISHU_USER_ID']
    missing = []
    
    for key in required:
        if not os.getenv(key):
            missing.append(key)
            print(f"  ✗ {key} 未配置")
        else:
            print(f"  ✓ {key} 已配置")
    
    # 检查可选项
    if os.getenv('LINKEDIN_EMAIL'):
        print(f"  ✓ LinkedIn 账号已配置")
    else:
        print(f"  ℹ LinkedIn 账号未配置（首次登录需要）")
    
    if os.getenv('CHROME_USER_DATA'):
        print(f"  ✓ Chrome 用户数据目录已配置")
    
    return len(missing) == 0

def check_database():
    """检查数据库"""
    print("\n📊 检查数据库...")
    
    if not DB_PATH.exists():
        print("  ✗ 数据库文件不存在")
        print("  → 运行：python scripts/cli.py setup")
        return False
    
    print("  ✓ 数据库文件存在")
    
    # 检查潜客数量
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM leads')
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"  ✓ 潜客数量：{count} 个")
    else:
        print(f"  ⚠ 暂无潜客")
        print(f"  → 运行：python scripts/cli.py add --url <URL> --name <姓名>")
    
    conn.close()
    return True

def check_browser():
    """检查浏览器"""
    print("\n🌐 检查浏览器...")
    
    try:
        from playwright.sync_api import sync_playwright
        print("  ✓ Playwright 已安装")
    except ImportError:
        print("  ✗ Playwright 未安装")
        print("  → 运行：pip install playwright")
        print("  → 运行：playwright install chromium")
        return False
    
    # 检查 Chromium
    state_dir = Path(__file__).parent.parent / 'data' / 'state'
    profile_dir = state_dir / 'linkedin-profile'
    
    if profile_dir.exists():
        print(f"  ✓ LinkedIn 浏览器配置文件存在")
        
        # 检查登录状态
        storage_file = state_dir / 'storage.json'
        if storage_file.exists():
            print(f"  ✓ 登录会话已保存")
        else:
            print(f"  ⚠ 登录会话未保存")
            print(f"  → 运行：python scripts/cli.py login")
    else:
        print(f"  ⚠ 浏览器配置文件未创建")
        print(f"  → 运行：python scripts/cli.py login")
    
    return True

def check_dependencies():
    """检查依赖"""
    print("\n📦 检查依赖...")
    
    deps = {
        'playwright': 'playwright',
        'sqlite3': 'sqlite3',
        'requests': 'requests',
        'dotenv': 'python-dotenv'
    }
    
    missing = []
    for module, pip_name in deps.items():
        try:
            __import__(module)
            print(f"  ✓ {pip_name}")
        except ImportError:
            print(f"  ✗ {pip_name}")
            missing.append(pip_name)
    
    if missing:
        print(f"\n  → 运行：pip install {' '.join(missing)}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 LinkedIn 潜客监控 - 配置检查")
    print("=" * 60)
    
    results = []
    
    results.append(("依赖检查", check_dependencies()))
    results.append(("配置文件", check_env()))
    results.append(("数据库", check_database()))
    results.append(("浏览器", check_browser()))
    
    print("\n" + "=" * 60)
    print("📊 检查结果")
    print("=" * 60)
    
    all_ok = True
    for name, ok in results:
        status = "✓" if ok else "✗"
        print(f"{status} {name}")
        if not ok:
            all_ok = False
    
    print("=" * 60)
    
    if all_ok:
        print("\n✅ 所有检查通过！可以开始监控了")
        print("\n下一步：")
        print("  1. python scripts/cli.py check          # 检查潜客")
        print("  2. python scripts/cli.py watch --interval 30  # 持续监控")
    else:
        print("\n⚠️  部分检查未通过，请先修复上述问题")
    
    print()

if __name__ == '__main__':
    main()
