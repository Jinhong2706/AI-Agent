"""增量同步模块"""
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import pandas as pd

from .parser import extract_base_token_from_url


def get_last_sync_time(base_token: str, table_id: str, time_field: str = "更新时间") -> Optional[datetime]:
    """获取上次同步时间
    
    Args:
        base_token: 多维表格token
        table_id: 数据表ID
        time_field: 时间字段名
    
    Returns:
        datetime: 上次同步时间，如果没有则返回None
    """
    # 获取记录列表，按时间字段降序排序
    cmd = [
        'lark-cli', 'base', '+record-list',
        '--base-token', base_token,
        '--table-id', table_id
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return None
    
    try:
        data = json.loads(result.stdout)
        rows = data.get('data', {}).get('data', [])
        fields = data.get('data', {}).get('fields', [])
        
        if not rows:
            return None
        
        # 找到时间字段的索引
        time_idx = None
        for i, field in enumerate(fields):
            if field == time_field:
                time_idx = i
                break
        
        if time_idx is None:
            return None
        
        # 获取最新的时间值
        for row in rows:
            if row[time_idx]:
                try:
                    return datetime.fromisoformat(row[time_idx].replace('Z', '+00:00'))
                except:
                    continue
        
        return None
    except:
        return None


def filter_incremental_records(df: pd.DataFrame, time_field: str, 
                               last_sync_time: Optional[datetime],
                               lookback_hours: int = 24) -> pd.DataFrame:
    """过滤增量记录
    
    Args:
        df: 完整数据DataFrame
        time_field: 时间字段名
        last_sync_time: 上次同步时间
        lookback_hours: 回溯小时数（防止遗漏）
    
    Returns:
        DataFrame: 过滤后的增量数据
    """
    if last_sync_time is None:
        print("📋 首次同步，将同步全部数据")
        return df
    
    if time_field not in df.columns:
        print(f"⚠️ 未找到时间字段 {time_field}，将同步全部数据")
        return df
    
    # 回溯一段时间，防止遗漏
    cutoff_time = last_sync_time - timedelta(hours=lookback_hours)
    
    try:
        df['_sync_time'] = pd.to_datetime(df[time_field])
        incremental_df = df[df['_sync_time'] > cutoff_time].drop(columns=['_sync_time'])
        print(f"📋 增量同步：{len(incremental_df)} 条记录（上次同步: {last_sync_time}）")
        return incremental_df
    except Exception as e:
        print(f"⚠️ 时间字段解析失败: {str(e)}，将同步全部数据")
        return df


def get_existing_record_ids(base_token: str, table_id: str, key_field: str) -> Set[str]:
    """获取现有记录的主键集合
    
    Args:
        base_token: 多维表格token
        table_id: 数据表ID
        key_field: 主键字段名
    
    Returns:
        set: 现有记录的主键值集合
    """
    cmd = [
        'lark-cli', 'base', '+record-list',
        '--base-token', base_token,
        '--table-id', table_id
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        return set()
    
    try:
        data = json.loads(result.stdout)
        rows = data.get('data', {}).get('data', [])
        fields = data.get('data', {}).get('fields', [])
        
        # 找到主键字段的索引
        key_idx = None
        for i, field in enumerate(fields):
            if field == key_field:
                key_idx = i
                break
        
        if key_idx is None:
            return set()
        
        return {str(row[key_idx]) for row in rows if row[key_idx]}
    except:
        return set()


def smart_sync(csv_path: str, base_url: str, table_name: str, 
               key_field: str, incremental: bool = True,
               time_field: str = "更新时间") -> Dict[str, int]:
    """智能同步（增量/全量自动判断）
    
    Args:
        csv_path: CSV文件路径
        base_url: 多维表格URL
        table_name: 数据表名称
        key_field: 主键字段名
        incremental: 是否增量同步
        time_field: 时间字段名（用于增量判断）
    
    Returns:
        dict: {'created': 新增数, 'updated': 更新数}
    """
    base_token, table_id = extract_base_token_from_url(base_url)
    
    if not base_token:
        print("❌ 无法从URL中提取base_token")
        return {'created': 0, 'updated': 0}
    
    # 读取CSV数据
    df = pd.read_csv(csv_path)
    
    # 获取现有记录
    existing_ids = get_existing_record_ids(base_token, table_id or '', key_field)
    
    # 判断增量同步
    if incremental and time_field:
        df = filter_incremental_records(df, time_field, get_last_sync_time(base_token, table_id or '', time_field))
    
    # 分类：新增 vs 更新
    if key_field in df.columns:
        new_records = df[~df[key_field].astype(str).isin(existing_ids)]
        update_records = df[df[key_field].astype(str).isin(existing_ids)]
    else:
        new_records = df
        update_records = pd.DataFrame()
    
    stats = {'created': len(new_records), 'updated': len(update_records)}
    
    # 执行同步
    if len(new_records) > 0:
        print(f"📤 新增 {len(new_records)} 条记录...")
        # 这里调用实际的导入逻辑
    
    if len(update_records) > 0:
        print(f"📤 更新 {len(update_records)} 条记录...")
        # 这里调用实际的更新逻辑
    
    return stats
