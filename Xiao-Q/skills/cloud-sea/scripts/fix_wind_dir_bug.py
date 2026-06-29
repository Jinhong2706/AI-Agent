#!/usr/bin/env python3
"""
修复 wind_dir 键名不匹配 bug（问题1）

BUG根因：
weather_fetch.py L525 存储键名 "wind_direction"
analyzer.py L863/865/866/872/873 用 "wind_dir" 读取
→ 键名不匹配 → wind_dir 永远为 None

修复：统一为 "wind_direction"（更安全，避免与变量名混淆）
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
ANALYZER_PY = SCRIPT_DIR / "analyzer.py"

def main():
    print("=" * 60)
    print("wind_dir 键名不匹配 bug 修复脚本")
    print("=" * 60)
    
    if not ANALYZER_PY.exists():
        print(f"[FAIL] 错误: {ANALYZER_PY} 不存在")
        sys.exit(1)
    
    # 读取文件
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n[INFO] 已读取: {ANALYZER_PY} ({len(content)} 字符)")
    print("\n[SEARCH] 开始修复...")
    
    # 统计需要修复的次数
    count_before = content.count('"wind_dir"')
    print(f"  [INFO] 发现 {count_before} 处 \"wind_dir\" 字典键引用")
    
    if count_before == 0:
        print("\n[WARN] 未找到 \"wind_dir\" 引用，可能已修复")
        resp = input("  是否继续检查? (y/N): ")
        if resp.lower() != 'y':
            sys.exit(0)
    
    # 修复：替换字典键名 "wind_dir" → "wind_direction"
    # 注意：只替换字符串键名，不替换变量名 wind_dir
    content_fixed = content.replace('"wind_dir"', '"wind_direction"')
    
    count_after = content_fixed.count('"wind_dir"')
    count_replaced = count_before - count_after
    
    if count_replaced == 0:
        print("\n[WARN] 没有需要修复的内容")
        print("  可能：1) 已修复  2) 键名已经是 wind_direction")
        sys.exit(0)
    
    print(f"  [OK] 已替换 {count_replaced} 处字典键名")
    
    # 备份原文件
    backup = ANALYZER_PY.with_suffix('.py.bak')
    ANALYZER_PY.rename(backup)
    print(f"\n[BACKUP] 已备份原文件到: {backup}")
    
    # 保存修复后的文件
    with open(ANALYZER_PY, 'w', encoding='utf-8') as f:
        f.write(content_fixed)
    print(f"[OK] 已保存修复后的文件: {ANALYZER_PY}")
    
    # 验证修复
    with open(ANALYZER_PY, 'r', encoding='utf-8') as f:
        verified = f.read()
    
    verify_count = verified.count('"wind_direction"')
    print(f"\n[VERIFY] 验证: 文件现在包含 {verify_count} 处 \"wind_direction\" 引用")
    
    if verified.count('"wind_dir"') > 0:
        print("[WARN] 警告: 文件中仍有 \"wind_dir\" 残留!")
        print("  请手动检查...")
    else:
        print("[OK] 验证通过: 无 \"wind_dir\" 残留")
    
    print("\n" + "=" * 60)
    print(f"修复完成: {count_replaced} 处字典键名已修复")
    print("=" * 60)
    
    # 提示需要同时修复 weather_fetch.py（如果有必要）
    print("\n[INFO] 可选步骤:")
    print("  如果需要保持键名一致，请同时检查 weather_fetch.py")
    print("  当前 weather_fetch.py 使用键名: wind_direction")
    print("  如果 analyzer.py 现在也用 wind_direction，则无需修改")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
