"""文件保存模块"""
import pandas as pd
from typing import List, Dict, Optional


def save_as_csv(dfs: List[Dict], output_path: str) -> bool:
    """将DataFrame保存为CSV
    
    Args:
        dfs: DataFrame列表 [{'name': 表名, 'data': DataFrame}, ...]
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功
    """
    if len(dfs) == 0:
        print("❌ 没有数据可保存")
        return False
    
    if len(dfs) == 1:
        dfs[0]['data'].to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ 已保存为CSV: {output_path}")
        print(f"📊 数据行数: {len(dfs[0]['data'])}")
        print(f"📋 字段数量: {len(dfs[0]['data'].columns)}")
        return True
    
    for df_info in dfs:
        table_path = output_path.replace('.csv', f'_{df_info["name"]}.csv')
        df_info['data'].to_csv(table_path, index=False, encoding='utf-8')
        print(f"✅ 已保存表 [{df_info['name']}] 为CSV: {table_path}")
        print(f"   数据行数: {len(df_info['data'])}")
    
    return True


def save_as_excel(dfs: List[Dict], output_path: str, sheet_name: Optional[str] = None) -> bool:
    """将DataFrame保存为Excel
    
    Args:
        dfs: DataFrame列表 [{'name': 表名, 'data': DataFrame}, ...]
        output_path: 输出文件路径
        sheet_name: 工作表名称（仅单个表时有效）
    
    Returns:
        bool: 是否成功
    """
    if len(dfs) == 0:
        print("❌ 没有数据可保存")
        return False
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for df_info in dfs:
                sheet = sheet_name if (len(dfs) == 1 and sheet_name) else df_info['name']
                sheet = sheet[:31]  # Excel sheet名称最长31个字符
                df_info['data'].to_excel(writer, sheet_name=sheet, index=False)
        
        print(f"✅ 已保存为Excel: {output_path}")
        if len(dfs) == 1:
            print(f"📊 数据行数: {len(dfs[0]['data'])}")
            print(f"📋 字段数量: {len(dfs[0]['data'].columns)}")
        else:
            print(f"📊 包含 {len(dfs)} 个工作表:")
            for df_info in dfs:
                print(f"   - {df_info['name']}: {len(df_info['data'])} 行")
        
        return True
    except Exception as e:
        print(f"❌ 保存Excel失败: {str(e)}")
        return False
