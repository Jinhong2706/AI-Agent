#!/usr/bin/env python3
"""
问题4 Bug #3 简化修复脚本

直接在 analyzer.py L535 后插入2行 dict 处理分支
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ANALYZER_PY = SCRIPT_DIR / "analyzer.py"

def main():
    print("=" * 60)
    print("问题4 Bug #3 简化修复脚本")
    print("=" * 60)
    
    if not ANALYZER_PY.exists():
        print(f"[FAIL] 错误: {ANALYZER_PY} 不存在")
        sys.exit(1)
    
    # 读取文件
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n[INFO] 已读取: {ANALYZER_PY} ({len(lines)} 行)")
    print("\n[SEARCH] 查找目标位置...")
    
    # 查找目标行
    target_idx = None
    insert_idx = None
    
    for i, line in enumerate(lines):
        # 找到: if vis_score is not None and isinstance(vis_score, (int, float)):
        if 'if vis_score is not None and isinstance(vis_score, (int, float)):' in line:
            target_idx = i
            # 下一行应该是 f11 = min(10, vis_score)
            if i + 1 < len(lines) and 'f11 = min(10, vis_score)' in lines[i + 1]:
                insert_idx = i + 2  # 在这行之后插入
                break
    
    if target_idx is None:
        print("\n[FAIL] 找不到目标行!")
        print("  请手动检查 analyzer.py L533-537")
        sys.exit(1)
    
    if insert_idx is None:
        print("\n[FAIL] 找不到插入位置!")
        print("  请手动在 f11 = min(10, vis_score) 之后添加:")
        print('    elif isinstance(vis_score, dict) and "value" in vis_score:')
        print('        f11 = min(10, vis_score["value"])')
        sys.exit(1)
    
    print(f"[OK] 找到目标位置: L{insert_idx+1}")
    print(f"\n[INSERT] 准备插入2行到 L{insert_idx+1}-{insert_idx+2}...")
    
    # 检查是否已修复
    if insert_idx < len(lines) and 'elif isinstance(vis_score, dict)' in lines[insert_idx]:
        print("\n[SKIP] Bug #3 似乎已修复 (L{} 已有 dict 处理)".format(insert_idx+1))
        sys.exit(0)
    
    # 插入2行
    insert_lines = [
        '    elif isinstance(vis_score, dict) and "value" in vis_score:\n',
        '        f11 = min(10, vis_score["value"])\n',
    ]
    
    lines_with_insert = lines[:insert_idx] + insert_lines + lines[insert_idx:]
    
    print(f"\n[INFO] 插入内容:")
    for il in insert_lines:
        print(f"  {il.rstrip()}")
    
    # 备份原文件
    bak_files = list(ANALYZER_PY.parent.glob("analyzer.py.bak*"))
    bak_num = len(bak_files) + 1
    backup = ANALYZER_PY.with_suffix(f'.py.bak{bak_num}')
    
    ANALYZER_PY.rename(backup)
    print(f"\n[BACKUP] 已备份原文件到: {backup}")
    
    # 保存修复后的文件
    with open(ANALYZER_PY, 'w', encoding='utf-8') as f:
        f.writelines(lines_with_insert)
    print(f"[OK] 已保存修复后的文件: {ANALYZER_PY}")
    
    # 验证修复
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        verified_lines = f.readlines()
    
    # 检查插入是否成功
    success = False
    for i, line in enumerate(verified_lines):
        if 'elif isinstance(vis_score, dict)' in line:
            print(f"\n[VERIFY] 验证通过: L{i+1} 已有 dict 处理分支")
            success = True
            break
    
    if not success:
        print("\n[WARN] 验证失败: dict 处理分支未找到")
        print("  请手动检查 analyzer.py L533-540")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Bug #3 修复完成!")
    print("=" * 60)
    print("\n[TEST] 建议运行测试:")
    print("  cd C:\\Users\\86139\\.qclaw\\skills\\cloud-sea\\scripts")
    print("  python weather_fetch.py --date 2026-05-30")
    print("  python analyzer.py --date 2026-05-30")
    print("\n[CHECK] 检查项:")
    print("  1. transparency_score 存储的是数值 (非 dict)")
    print("  2. 因子11 (能见度) 评分正常")
    print("  3. wind_direction 字段不再为 None")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
