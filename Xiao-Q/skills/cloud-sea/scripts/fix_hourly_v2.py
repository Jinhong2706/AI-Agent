#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 build_hourly_tables() 中的逻辑错误：
当整体预测为'无雾'时，逐小时数据不应显示'❌ 在雾中'
"""

with open('report_gen.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复1: 在 rows = [] 之后添加整体 fog_type 检查
old1 = "    rows = []\n\n    for row in sunrise_rows:"

new1 = """    rows = []

    # 修复: 检查整体 fog_type，如果无雾则所有小时都显示"无雾，无云海"
    overall_fog_type = config.get('ranked', [{}])[0].get('fog_type', '')
    ft_str = ""
    if isinstance(overall_fog_type, (list, tuple)) and len(overall_fog_type) >= 2:
        ft_str = str(overall_fog_type[1])  # 取雾型中文名
    else:
        ft_str = str(overall_fog_type) if overall_fog_type else ""
    overall_no_fog = any(k in ft_str for k in ('none', '无雾', '无云', '晴空雾'))

    for row in sunrise_rows:"""

if old1 in content:
    content = content.replace(old1, new1)
    print('修复1成功: 添加整体fog_type检查')
else:
    print('修复1失败: 未找到匹配文本')
    # 调试: 打印附近文本
    idx = content.find('rows = []')
    if idx >= 0:
        print(f'Found rows = [] at position {idx}')
        print(f'Context: {repr(content[idx:idx+100])}')

# 修复2: 在云海判断逻辑前添加整体无雾检查
old2 = "        # 云海判断\n        if diff > 200:"

new2 = """        # 云海判断
        # 修复: 如果整体无雾，所有小时都显示"无雾，无云海"
        if overall_no_fog:
            cloud_judge = "无雾，无云海"
            judge_cls = "judge-none"
        elif diff > 200:"""

if old2 in content:
    content = content.replace(old2, new2)
    print('修复2成功: 添加整体无雾检查')
else:
    print('修复2失败: 未找到匹配文本')
    # 调试: 打印附近文本
    idx = content.find('# 云海判断')
    if idx >= 0:
        print(f'Found # 云海判断 at position {idx}')
        print(f'Context: {repr(content[idx:idx+200])}')

with open('report_gen.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('修复完成！')
