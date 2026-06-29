#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量生成云海预测报告（05-25 ~ 05-31）"""
import subprocess, pathlib, sys

scripts_dir = pathlib.Path(__file__).parent
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
    result = subprocess.run(
        [sys.executable, "analyzer.py", "--date", date],
        cwd=scripts_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60
    )
    if result.returncode == 0:
        # 提取关键信息
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if any(kw in line for kw in ['TOP', '目标日', '峰', '✅', '⚠️', '❌']):
                print(f"  {line.strip()}")
    else:
        print(f"  ❌ 分析失败:")
        print(f"  {result.stderr[-200:]}")
        continue
    
    # Step 3: report_gen.py
    print(f"\n[Step 3] 生成 HTML: {date}")
    result = subprocess.run(
        [sys.executable, "report_gen.py", date],
        cwd=scripts_dir,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60
    )
    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if any(kw in line for kw in ['OK:', '✅', '❌', '配置', '模板']):
                print(f"  {line.strip()}")
    else:
        print(f"  ❌ HTML 生成失败:")
        print(f"  {result.stderr[-200:]}")
        continue
    
    print(f"✅ {date} 完成")

print(f"\n{'='*60}")
print("批量生成完成")
print(f"{'='*60}")
