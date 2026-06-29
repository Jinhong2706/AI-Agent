"""格式转换模块"""
import pandas as pd
from typing import List, Dict, Any


def infer_field_type(series: pd.Series) -> str:
    """自动推断字段类型
    
    Args:
        series: pandas Series
    
    Returns:
        str: 字段类型 'number' | 'datetime' | 'text'
    """
    if series.dropna().empty:
        return 'text'
    
    dtype = str(series.dtype)
    if 'int' in dtype or 'float' in dtype:
        if series.isna().all():
            return 'text'
        return 'number'
    elif 'datetime' in dtype:
        return 'datetime'
    else:
        sample_size = min(100, len(series.dropna()))
        if sample_size > 0:
            try:
                sample = series.dropna().sample(sample_size, random_state=42)
                pd.to_datetime(sample)
                return 'datetime'
            except:
                pass
        return 'text'


def process_rich_text_cell(cell: Any) -> str:
    """处理富文本格式的单元格，提取纯文本
    
    Args:
        cell: 单元格值，可能是 None、字符串或富文本列表
    
    Returns:
        str: 纯文本内容
    """
    if cell is None:
        return ''
    elif isinstance(cell, list):
        return ''.join([seg.get('text', '') for seg in cell if isinstance(seg, dict)])
    else:
        return str(cell)


def parse_exported_json(data: Dict) -> List[Dict]:
    """解析导出的JSON数据，返回DataFrame列表
    
    Args:
        data: 导出的JSON数据
    
    Returns:
        list: [{'name': 表名, 'data': DataFrame}, ...]
    """
    dfs = []
    for table in data.get('tables', []):
        table_name = table['meta']['tableName']
        rows = table.get('rows', [])
        
        if not rows:
            continue
        
        df = pd.DataFrame(rows)
        
        if '_record_id' in df.columns:
            df = df.drop(columns=['_record_id'])
        
        dfs.append({
            'name': table_name,
            'data': df
        })
    
    return dfs
