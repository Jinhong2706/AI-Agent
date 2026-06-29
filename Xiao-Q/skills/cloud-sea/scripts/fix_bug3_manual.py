#!/usr/bin/env python3
"""
问题4 Bug #3 手动修复辅助脚本

BUG根因：
  build_12factors() 中因子11计算缺少 dict 处理分支
  transparency_score 可能是 {"value": 6.0, "level": "GOOD"} 格式
  但代码只处理了 int/float/None，没处理 dict

修复内容：
  在 L535 (if vis_score is not None...) 和 L537 (elif s.get("max_visibility_km")...) 之间
  插入2行 dict 处理分支

使用方法：
  1. 运行此脚本（自动备份+插入）
  2. 或根据输出的代码片段手动编辑
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ANALYZER_PY = SCRIPT_DIR / "analyzer.py"

def find_target_lines(lines):
    """查找目标行：if vis_score is not None 和 elif s.get("max_visibility_km")"""
    target_line_1 = '    if vis_score is not None and isinstance(vis_score, (int, float)):'
    target_line_2 = '    elif s.get("max_visibility_km") is not None:'
    
    idx1 = None
    idx2 = None
    
    for i, line in enumerate(lines):
        if target_line_1 in line:
            idx1 = i
        if target_line_2 in line:
            idx2 = i
            break
    
    return idx1, idx2

def insert_fix(lines, idx1, idx2):
    """在 idx1 和 idx2 之间插入2行"""
    if idx1 is None or idx2 is None:
        print("[FAIL] 找不到目标行！")
        print("  请手动检查 analyzer.py L533-540")
        return None
    
    # 检查是否已经修复过
    if 'elif isinstance(vis_score, dict)' in lines[idx1 + 1]:
        print("[SKIP] Bug #3 似乎已修复（已有 dict 处理分支）")
        return lines
    
    # 插入2行
    insert_lines = [
        '    elif isinstance(vis_score, dict) and "value" in vis_score:\n',
        '        f11 = min(10, vis_score["value"])\n',
    ]
    
    # 在 idx1+1 位置插入（ after the if block's f11 = ... line）
    # 实际应该是 after line idx1+1 (f11 = min(10, vis_score))
    # 但我们需要确保插入在 elif s.get(...) 之前
    
    # 找到 if 块的结束位置（f11 = ... 那行）
    insert_pos = None
    for i in range(idx1, idx2):
        if 'f11 = min(10, vis_score)' in lines[i]:
            insert_pos = i + 1  # 在这行之后插入
            break
    
    if insert_pos is None:
        print("[FAIL] 找不到插入位置！")
        print("  请手动在 if vis_score... 和 elif s.get(...) 之间添加:")
        print('    elif isinstance(vis_score, dict) and "value" in vis_score:')
        print('        f11 = min(10, vis_score["value"])')
        return None
    
    print(f"[INFO] 插入位置: L{insert_pos+1}")
    print(f"[INFO] 插入内容:")
    for il in insert_lines:
        print(f"  {il.rstrip()}")
    
    # 插入
    lines_with_insert = lines[:insert_pos] + insert_lines + lines[insert_pos:]
    print(f"\n[OK] 已插入2行到 L{insert_pos+1}-{insert_pos+2}")
    
    return lines_with_insert

def main():
    print("=" * 60)
    print("问题4 Bug #3 手动修复辅助脚本")
    print("=" * 60)
    
    if not ANALYZER_PY.exists():
        print(f"[FAIL] 错误: {ANALYZER_PY} 不存在")
        sys.exit(1)
    
    # 读取文件
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n[INFO] 已读取: {ANALYZER_PY} ({len(lines)} 行)")
    print("\n[SEARCH] 查找目标行...")
    
    # 查找目标行
    idx1, idx2 = find_target_lines(lines)
    
    if idx1 is None:
        print("[FAIL] 找不到目标行1: if vis_score is not None...")
        print("  请手动检查 analyzer.py L533-540")
        sys.exit(1)
    
    if idx2 is None:
        print("[FAIL] 找不到目标行2: elif s.get('max_visibility_km')...")
        print("  请手动检查 analyzer.py L533-540")
        sys.exit(1)
    
    print(f"[OK] 找到目标行1: L{idx1+1}")
    print(f"[OK] 找到目标行2: L{idx2+1}")
    print(f"\n[INFO] 准备在 L{idx1+2}-L{idx2+1} 之间插入2行...")
    
    # 插入修复
    fixed_lines = insert_fix(lines, idx1, idx2)
    
    if fixed_lines is None:
        sys.exit(1)
    
    # 备份原文件
    backup = ANALYZER_PY.with_suffix('.py.bak2')
    if backup.exists():
        backup = ANALYZER_PY.with_suffix(f'.py.bak_{len(list(ANALYZER_PY.parent.glob("*.bak*"))+1}')
    
    ANALYZER_PY.rename(backup)
    print(f"\n[BACKUP] 已备份原文件到: {backup}")
    
    # 保存修复后的文件
    with open(ANALYZER_PY, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    print(f"[OK] 已保存修复后的文件: {ANALYZER_PY}")
    
    # 验证修复
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        verified_content = f.read()
    
    if 'elif isinstance(vis_score, dict)' in verified_content:
        print(f"\n[VERIFY] 验证通过: dict 处理分支已存在")
        print(f"\n[SUMMARY] Bug #3 修复完成！")
        print("=" * 60)
        print("现在可以运行测试验证修复效果:")
        print("  cd C:\\Users\\86139\\.qclaw\\skills\\cloud-sea\\scripts")
        print("  python weather_fetch.py --date 2026-05-30")
        print("  python analyzer.py --date 2026-05-30")
        print("=" * 60)
        return 0
    else:
        print(f"\n[WARN] 验证失败: dict 处理分支未找到")
        print("  请手动检查 analyzer.py L533-540")
        return 1

if __name__ == "__main__":
    sys.exit(main())
