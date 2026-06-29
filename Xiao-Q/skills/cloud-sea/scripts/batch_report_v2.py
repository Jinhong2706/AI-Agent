#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成云海预测报告（05-25 ~ 05-31）"""
import subprocess, pathlib, sys, os

# 强制 UTF-8 输出（修复 PowerShell GBK 编码问题）
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

SCRIPTS_DIR = pathlib.Path(__file__).parent
dates = [f"2026-05-{d:02d}" for d in range(25, 32)]  # 05-25 ~ 05-31

print("="*60)
print("批量生成云海预测报告")
print("="*60)

for date in dates:
    print(f"\n{'='*60}")
    print(f"处理日期: {date}")
    print(f"{'='*60}")
    
    # Step 2: analyzer.py（默认行为 = --config）
    print(f"\n[Step 2] 分析数据: {date}")
    try:
        subprocess.run(
            [sys.executable, "analyzer.py", "--date", date],
            cwd=SCRIPTS_DIR,
            check=True,
            timeout=60
        )
    except subprocess.CalledProcessError as e:
        print(f"  ❌ 分析失败 (returncode={e.returncode})")
        continue
    except subprocess.TimeoutExpired:
        print(f"  ❌ 分析超时（>60秒）")
        continue
    
    # Step 3: report_gen.py
    print(f"\n[Step 3] 生成 HTML: {date}")
    try:
        subprocess.run(
            [sys.executable, "report_gen.py", date],
            cwd=SCRIPTS_DIR,
            check=True,
            timeout=60
        )
    except subprocess.CalledProcessError as e:
        print(f"  ❌ HTML 生成失败 (returncode={e.returncode})")
        continue
    except subprocess.TimeoutExpired:
        print(f"  ❌ HTML 生成超时（>60秒）")
        continue
    
    print(f"✅ {date} 完成")

print(f"\n{'='*60}")
print("批量生成完成")
print(f"{'='*60}")
