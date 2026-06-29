"""导出模块"""
import json
import subprocess
import sys
import pandas as pd
from typing import List, Dict, Optional

from .parser import extract_token_from_url, extract_base_token_from_url, col_to_letter
from .converter import process_rich_text_cell


def export_from_spreadsheet(url: str, sheet_names: Optional[List[str]], 
                           output_path: str, no_record_id: bool = False) -> Dict:
    """从电子表格导出数据
    
    Args:
        url: 电子表格URL
        sheet_names: 工作表名称列表，None表示导出所有
        output_path: 输出文件路径
        no_record_id: 是否不包含record_id
    
    Returns:
        dict: 导出的数据
    """
    print(f"📤 正在导出电子表格数据...")
    print(f"📋 工作表: {', '.join(sheet_names) if sheet_names else '全部'}")
    
    token_info = extract_token_from_url(url)
    spreadsheet_token = token_info['token']
    
    if not spreadsheet_token or token_info['type'] != 'sheet':
        print("❌ 无法从URL中提取电子表格token")
        sys.exit(1)
    
    print(f"📦 Spreadsheet Token: {spreadsheet_token}")
    
    # 获取工作表列表
    cmd = ['lark-cli', 'sheets', '+info', '--spreadsheet-token', spreadsheet_token]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ 获取工作表列表失败:")
        print(result.stderr)
        sys.exit(1)
    
    try:
        sheet_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ 解析工作表信息失败")
        sys.exit(1)
    
    sheets = sheet_data.get('data', {}).get('sheets', {}).get('sheets', [])
    sheet_map = {s['title']: s['sheet_id'] for s in sheets if s.get('resource_type') == 'sheet'}
    
    if not sheet_names:
        sheet_names = list(sheet_map.keys())
    
    dfs = []
    for sheet_name in sheet_names:
        sheet_id = sheet_map.get(sheet_name)
        if not sheet_id:
            print(f"⚠️ 未找到工作表: {sheet_name}")
            continue
        
        # 动态获取工作表行列范围
        sheet_info = next((s for s in sheets if s['sheet_id'] == sheet_id), None)
        if sheet_info and 'grid_properties' in sheet_info:
            grid = sheet_info['grid_properties']
            max_row = grid.get('row_count', 1000)
            max_col = grid.get('column_count', 26)
            col_letter = col_to_letter(max_col)
            range_str = f'{sheet_id}!A1:{col_letter}{max_row}'
        else:
            range_str = f'{sheet_id}!A1:Z1000'
        
        cmd = ['lark-cli', 'sheets', '+read', '--spreadsheet-token', spreadsheet_token, '--range', range_str]
        read_result = subprocess.run(cmd, capture_output=True, text=True)
        
        if read_result.returncode != 0:
            print(f"⚠️ 读取工作表失败: {sheet_name}")
            continue
        
        try:
            read_data = json.loads(read_result.stdout)
            values = read_data.get('data', {}).get('valueRange', {}).get('values', [])
            
            if not values:
                print(f"⚠️ 工作表 [{sheet_name}] 没有数据")
                continue
            
            # 处理富文本格式的单元格
            processed_values = []
            for row in values:
                processed_row = [process_rich_text_cell(cell) for cell in row]
                processed_values.append(processed_row)
            
            if len(processed_values) > 1:
                df = pd.DataFrame(processed_values[1:], columns=processed_values[0])
            else:
                df = pd.DataFrame(processed_values)
            
            dfs.append({'name': sheet_name, 'data': df})
            print(f"✅ 已获取工作表 [{sheet_name}]: {len(df)} 行")
        except Exception as e:
            print(f"⚠️ 解析数据失败: {sheet_name}: {str(e)}")
            continue
    
    if not dfs:
        print("❌ 没有数据可导出")
        sys.exit(1)
    
    print("✅ 数据导出成功！")
    return {'tables': [{'meta': {'tableName': d['name']}, 'rows': d['data'].to_dict('records')} for d in dfs]}


def export_from_bitable(base_url: str, table_names: List[str], 
                       output_path: str, no_record_id: bool = False) -> Dict:
    """从多维表格导出数据
    
    Args:
        base_url: 多维表格URL
        table_names: 数据表名称列表
        output_path: 输出文件路径
        no_record_id: 是否不包含record_id
    
    Returns:
        dict: 导出的数据
    """
    print(f"📤 正在导出多维表格数据...")
    print(f"📋 表名: {', '.join(table_names)}")
    
    base_token, table_id = extract_base_token_from_url(base_url)
    
    if not base_token:
        print("❌ 无法从URL中提取base_token")
        sys.exit(1)
    
    print(f"📦 Base Token: {base_token}")
    
    # 获取表列表
    cmd = ['lark-cli', 'base', '+table-list', '--base-token', base_token]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ 获取表列表失败:")
        print(result.stderr)
        sys.exit(1)
    
    try:
        table_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ 解析表列表失败")
        sys.exit(1)
    
    tables = table_data.get('data', {}).get('items', [])
    table_id_map = {t['table_name']: t['table_id'] for t in tables}
    
    dfs = []
    for table_name in table_names:
        tid = table_id_map.get(table_name) or table_id
        if not tid:
            print(f"⚠️ 未找到表: {table_name}")
            continue
        
        # 获取字段列表
        cmd = ['lark-cli', 'base', '+field-list', '--base-token', base_token, '--table-id', tid]
        field_result = subprocess.run(cmd, capture_output=True, text=True)
        
        if field_result.returncode != 0:
            print(f"⚠️ 获取字段列表失败: {table_name}")
            continue
        
        try:
            field_data = json.loads(field_result.stdout)
            fields = field_data.get('data', {}).get('items', [])
            field_names = [f['field_name'] for f in fields]
        except:
            field_names = []
        
        # 获取记录列表
        cmd = ['lark-cli', 'base', '+record-list', '--base-token', base_token, '--table-id', tid]
        record_result = subprocess.run(cmd, capture_output=True, text=True)
        
        if record_result.returncode != 0:
            print(f"⚠️ 获取记录失败: {table_name}")
            continue
        
        try:
            record_data = json.loads(record_result.stdout)
            rows = record_data.get('data', {}).get('data', [])
            fields_from_response = record_data.get('data', {}).get('fields', field_names)
            
            df = pd.DataFrame(rows, columns=fields_from_response)
            
            if '_record_id' in df.columns:
                df = df.drop(columns=['_record_id'])
            if no_record_id and 'record_id' in df.columns:
                df = df.drop(columns=['record_id'])
            
            dfs.append({'name': table_name, 'data': df})
            print(f"✅ 已获取表 [{table_name}]: {len(df)} 行")
        except Exception as e:
            print(f"⚠️ 解析数据失败: {table_name}: {str(e)}")
            continue
    
    if not dfs:
        print("❌ 没有数据可导出")
        sys.exit(1)
    
    print("✅ 数据导出成功！")
    return {'tables': [{'meta': {'tableName': d['name']}, 'rows': d['data'].to_dict('records')} for d in dfs]}
