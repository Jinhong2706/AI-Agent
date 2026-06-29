#!/usr/bin/env python3
"""
修复通透度返回值格式bug（问题4）

BUG根因：
estimate_transparency() 返回 {"score": {"level": "GOOD", "value": 6.0}}
但调用处错误地用 .get("score") 取值（应为 .get("value")）

3处修复：
1. L789-790: s_enriched["transparency_score"] 存储了整个dict，应存储数值
2. L774: trans_score_val.get("score", None) 键名错误，应为 "value"
3. L535-537: build_12factors() 中 f11 计算缺少 dict 处理
"""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ANALYZER_PY = SCRIPT_DIR / "analyzer.py"

def fix_bug1(line_index, lines):
    """Bug #1: s_enriched["transparency_score"] 存储了整个dict"""
    target_line = "            s_enriched[\"transparency_score\"] = pt['score']"
    fixed_lines = [
        '            score_dict = pt[\'score\']',
        '            if isinstance(score_dict, dict) and "value" in score_dict:',
        '                s_enriched["transparency_score"] = score_dict["value"]',
        '            else:',
        '                s_enriched["transparency_score"] = None'
    ]
    
    if lines[line_index].strip() == target_line.strip():
        # 替换这一行
        lines[line_index] = fixed_lines[0] + '\n' + fixed_lines[1] + '\n' + fixed_lines[2] + '\n' + fixed_lines[3] + '\n' + fixed_lines[4] + '\n'
        print(f"[OK] Bug #1 修复成功 (L{line_index+1})")
        return True
    else:
        print(f"[FAIL] Bug #1 匹配失败 (L{line_index+1}): [{lines[line_index].strip()}]")
        return False

def fix_bug2(line_index, lines):
    """Bug #2: trans_score_val.get("score", None) 键名错误"""
    target_line = '        trans_score_val = trans_score_val.get("score", None)'
    fixed_line = '        trans_score_val = trans_score_val.get("value", None)'
    
    if lines[line_index].strip() == target_line.strip():
        lines[line_index] = fixed_line + '\n'
        print(f"[OK] Bug #2 修复成功 (L{line_index+1})")
        return True
    else:
        print(f"[FAIL] Bug #2 匹配失败 (L{line_index+1}): [{lines[line_index].strip()}]")
        return False

def fix_bug3(line_index, lines):
    """Bug #3: build_12factors() 中 f11 计算缺少 dict 处理"""
    # 在 L535 后插入 dict 处理分支
    target_line = '    if vis_score is not None and isinstance(vis_score, (int, float)):'
    
    # 检查当前代码是否已经包含 dict 处理
    if 'elif isinstance(vis_score, dict)' in lines[line_index + 2]:
        print(f"[SKIP] Bug #3 似乎已修复 (L{line_index+3} 已有 dict 处理)")
        return True
    
    # 实际插入修复
    insert_lines = [
        '    if vis_score is not None and isinstance(vis_score, (int, float)):',
        '        f11 = min(10, vis_score)',
        '    elif isinstance(vis_score, dict) and "value" in vis_score:',
        '        f11 = min(10, vis_score["value"])',
        '    elif s.get("max_visibility_km") is not None:'
    ]
    
    print(f"[MANUAL] Bug #3 需要手动修复 (L{line_index+1})")
    print("请手动在 build_12factors() 函数的 f11 计算部分添加:")
    print('    elif isinstance(vis_score, dict) and "value" in vis_score:')
    print('        f11 = min(10, vis_score["value"])')
    return False

def main():
    print("=" * 60)
    print("通透度返回值格式bug修复脚本")
    print("=" * 60)
    
    if not ANALYZER_PY.exists():
        print(f"[FAIL] 错误: {ANALYZER_PY} 不存在")
        sys.exit(1)
    
    # 读取文件
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n[INFO] 已读取: {ANALYZER_PY} ({len(lines)} 行)")
    print("\n[SEARCH] 开始修复...")
    
    # 查找并修复 3 个 Bug
    success_count = 0
    
    # Bug #1: L789-790
    for i, line in enumerate(lines):
        if 's_enriched["transparency_score"] = pt[\'score\']' in line:
            if fix_bug1(i, lines):
                success_count += 1
            break
    
    # Bug #2: L774
    for i, line in enumerate(lines):
        if 'trans_score_val = trans_score_val.get("score", None)' in line:
            if fix_bug2(i, lines):
                success_count += 1
            break
    
    # Bug #3: L535-537 (需要手动修复)
    for i, line in enumerate(lines):
        if 'if vis_score is not None and isinstance(vis_score, (int, float)):' in line:
            if fix_bug3(i, lines):
                success_count += 1
            break
    
    # 保存修复后的文件
    if success_count >= 2:  # 至少修复了 2 个 Bug
        backup = ANALYZER_PY.with_suffix('.py.bak')
        ANALYZER_PY.rename(backup)
        print(f"\n[BACKUP] 已备份原文件到: {backup}")
        
        with open(ANALYZER_PY, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"[OK] 已保存修复后的文件: {ANALYZER_PY}")
        
        print(f"\n[SUMMARY] 修复总结: {success_count}/3 个 Bug 已修复")
        print("\n[MANUAL] 请手动修复 Bug #3 (build_12factors() 函数)")
        print("   位置: analyzer.py L535-537")
        print("   添加 dict 处理分支...")
    else:
        print(f"\n[FAIL] 修复失败: 仅 {success_count}/3 个 Bug 匹配成功")
        print("   请手动检查 analyzer.py 中的代码...")
        sys.exit(1)

if __name__ == "__main__":
    main()
