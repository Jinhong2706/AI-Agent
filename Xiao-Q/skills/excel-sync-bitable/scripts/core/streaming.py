"""流式处理模块 - 大数据量支持"""
import json
import subprocess
from typing import Iterator, List, Dict, Any, Optional
import pandas as pd


def stream_records_from_bitable(
    base_token: str,
    table_id: str,
    batch_size: int = 500,
    max_records: Optional[int] = None
) -> Iterator[List[Dict]]:
    """流式读取多维表格记录
    
    Args:
        base_token: 多维表格token
        table_id: 数据表ID
        batch_size: 每批记录数（默认500）
        max_records: 最大记录数（None表示无限制）
    
    Yields:
        list: 每批记录数据
    
    Example:
        >>> for batch in stream_records_from_bitable(token, table_id):
        ...     process_batch(batch)
    """
    # 先获取字段信息
    cmd = ['lark-cli', 'base', '+field-list', '--base-token', base_token, '--table-id', table_id]
    field_result = subprocess.run(cmd, capture_output=True, text=True)
    
    fields = []
    if field_result.returncode == 0:
        try:
            field_data = json.loads(field_result.stdout)
            fields = [f['field_name'] for f in field_data.get('data', {}).get('items', [])]
        except:
            pass
    
    total_yielded = 0
    page_token = None
    
    while True:
        # 构建查询命令
        cmd = ['lark-cli', 'base', '+record-list', '--base-token', base_token, '--table-id', table_id]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            break
        
        try:
            data = json.loads(result.stdout)
            rows = data.get('data', {}).get('data', [])
            fields_from_response = data.get('data', {}).get('fields', fields)
            
            if not rows:
                break
            
            # 转换为字典列表
            batch = []
            for row in rows:
                record = dict(zip(fields_from_response, row))
                batch.append(record)
            
            yield batch
            
            total_yielded += len(batch)
            
            if max_records and total_yielded >= max_records:
                break
            
            # 如果返回的记录数小于批次大小，说明已经读完
            if len(rows) < batch_size:
                break
            
            # TODO: 使用 page_token 实现分页（当 lark-cli 支持时）
            break
            
        except Exception as e:
            print(f"⚠️ 解析记录失败: {str(e)}")
            break


def stream_records_from_sheet(
    spreadsheet_token: str,
    sheet_id: str,
    batch_rows: int = 1000,
    max_rows: Optional[int] = None
) -> Iterator[pd.DataFrame]:
    """流式读取电子表格记录
    
    Args:
        spreadsheet_token: 电子表格token
        sheet_id: 工作表ID
        batch_rows: 每批行数（默认1000）
        max_rows: 最大行数（None表示无限制）
    
    Yields:
        DataFrame: 每批数据
    
    Example:
        >>> for df in stream_records_from_sheet(token, sheet_id):
        ...     process_batch(df)
    """
    start_row = 1
    total_yielded = 0
    
    # 先读取表头
    cmd = ['lark-cli', 'sheets', '+read', 
           '--spreadsheet-token', spreadsheet_token, 
           '--range', f'{sheet_id}!A1:Z1']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    headers = []
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            values = data.get('data', {}).get('valueRange', {}).get('values', [])
            if values:
                headers = values[0]
        except:
            pass
    
    while True:
        if max_rows and total_yielded >= max_rows:
            break
        
        end_row = start_row + batch_rows - 1
        range_str = f'{sheet_id}!A{start_row}:Z{end_row}'
        
        cmd = ['lark-cli', 'sheets', '+read', 
               '--spreadsheet-token', spreadsheet_token, 
               '--range', range_str]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            break
        
        try:
            data = json.loads(result.stdout)
            values = data.get('data', {}).get('valueRange', {}).get('values', [])
            
            if not values or (len(values) == 1 and start_row > 1):
                break
            
            # 第一批包含表头，后续批次不包含
            if start_row == 1:
                df = pd.DataFrame(values[1:], columns=values[0] if values else headers)
            else:
                df = pd.DataFrame(values, columns=headers)
            
            if len(df) == 0:
                break
            
            yield df
            
            total_yielded += len(df)
            start_row = end_row + 1
            
        except Exception as e:
            print(f"⚠️ 解析数据失败: {str(e)}")
            break


def export_large_bitable_to_csv(
    base_token: str,
    table_id: str,
    output_path: str,
    batch_size: int = 500
) -> int:
    """流式导出大多维表格到CSV
    
    Args:
        base_token: 多维表格token
        table_id: 数据表ID
        output_path: 输出文件路径
        batch_size: 每批记录数
    
    Returns:
        int: 总导出记录数
    """
    total_records = 0
    first_batch = True
    
    print(f"📤 开始流式导出到 {output_path}...")
    
    for batch in stream_records_from_bitable(base_token, table_id, batch_size):
        df = pd.DataFrame(batch)
        
        if first_batch:
            df.to_csv(output_path, index=False, encoding='utf-8')
            first_batch = False
        else:
            df.to_csv(output_path, mode='a', header=False, index=False, encoding='utf-8')
        
        total_records += len(batch)
        print(f"  📊 已导出 {total_records} 条记录...")
    
    print(f"✅ 导出完成：共 {total_records} 条记录")
    return total_records


def export_large_sheet_to_csv(
    spreadsheet_token: str,
    sheet_id: str,
    output_path: str,
    batch_rows: int = 1000
) -> int:
    """流式导出大电子表格到CSV
    
    Args:
        spreadsheet_token: 电子表格token
        sheet_id: 工作表ID
        output_path: 输出文件路径
        batch_rows: 每批行数
    
    Returns:
        int: 总导出行数
    """
    total_rows = 0
    first_batch = True
    
    print(f"📤 开始流式导出到 {output_path}...")
    
    for df in stream_records_from_sheet(spreadsheet_token, sheet_id, batch_rows):
        if first_batch:
            df.to_csv(output_path, index=False, encoding='utf-8')
            first_batch = False
        else:
            df.to_csv(output_path, mode='a', header=False, index=False, encoding='utf-8')
        
        total_rows += len(df)
        print(f"  📊 已导出 {total_rows} 行...")
    
    print(f"✅ 导出完成：共 {total_rows} 行")
    return total_rows
