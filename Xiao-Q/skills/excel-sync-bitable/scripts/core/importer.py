"""导入模块 - 使用新版 lark-cli 命令"""
import os
import subprocess
import sys
import pandas as pd
import json
from typing import Dict, Tuple
import re

from .converter import infer_field_type
from .parser import extract_token_from_url


def convert_excel_to_json(excel_path: str) -> Tuple[list, Dict[str, str]]:
    """将Excel转换为符合新版lark-cli要求的格式
    
    Args:
        excel_path: Excel文件路径
    
    Returns:
        tuple: (记录列表, 字段类型映射)
    
    Raises:
        FileNotFoundError: 文件不存在
        Exception: 读取Excel失败
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"❌ 文件不存在: {excel_path}")
    
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        raise Exception(f"❌ 读取Excel文件失败: {str(e)}")
    
    # 推断字段类型
    field_types = {}
    for col in df.columns:
        field_types[col] = infer_field_type(df[col])
    
    # 转换数据为记录列表
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            value = row[col]
            typ = field_types[col]
            
            # 处理空值
            if pd.isna(value):
                record[col] = None
            elif typ == 'datetime':
                # 转换日期格式
                record[col] = pd.to_datetime(value).strftime('%Y-%m-%d %H:%M:%S')
            elif typ == 'number':
                # 数字保持原样
                record[col] = float(value) if not pd.isna(value) else None
            else:
                # 文本等
                record[col] = str(value)
        
        records.append(record)
    
    print(f"✅ 已转换 {len(records)} 条记录")
    print(f"📋 字段类型推断结果: {field_types}")
    return records, field_types


def create_new_bitable(excel_path: str, app_name: str, table_name: str) -> Dict[str, str]:
    """创建新的多维表格并导入数据
    
    Args:
        excel_path: Excel文件路径
        app_name: 应用名称
        table_name: 数据表名称
    
    Returns:
        dict: 包含 base_token 和 table_id 的信息
    
    Raises:
        Exception: 创建失败
    """
    # 1. 转换数据
    records, field_types = convert_excel_to_json(excel_path)
    
    # 2. 创建 Base
    print(f"\n📦 创建多维表格: {app_name}")
    cmd = ['lark-cli', 'base', '+create', '--name', app_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 创建 Base 失败: {result.stderr}")
        sys.exit(1)
    
    # 提取 base_token
    output = result.stdout
    # 从输出中解析 base_token（格式可能是 app_xxx）
    match = re.search(r'"token"\s*:\s*"([^"]+)"', output)
    if not match:
        match = re.search(r'app_[a-zA-Z0-9]+', output)
    
    if not match:
        print(f"❌ 无法解析 base_token，原始输出:\n{output}")
        sys.exit(1)
    
    base_token = match.group(0) if match.group(0).startswith('app_') else match.group(1)
    print(f"✅ Base 创建成功，token: {base_token}")
    
    # 3. 创建数据表
    print(f"\n📋 创建数据表: {table_name}")
    cmd = ['lark-cli', 'base', '+table-create', '--base-token', base_token, '--name', table_name]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ 创建数据表失败: {result.stderr}")
        sys.exit(1)
    
    # 提取 table_id
    output = result.stdout
    match = re.search(r'"table_id"\s*:\s*"([^"]+)"', output)
    if not match:
        match = re.search(r'tbl_[a-zA-Z0-9]+', output)
    
    if not match:
        print(f"❌ 无法解析 table_id，原始输出:\n{output}")
        sys.exit(1)
    
    table_id = match.group(0) if match.group(0).startswith('tbl_') else match.group(1)
    print(f"✅ 数据表创建成功，table_id: {table_id}")
    
    # 4. 创建字段
    print(f"\n🔧 创建字段...")
    for field_name, field_type in field_types.items():
        # 映射字段类型
        lark_type = {
            'text': 'text',
            'number': 'number',
            'datetime': 'date',
            'bool': 'checkbox'
        }.get(field_type, 'text')
        
        cmd = [
            'lark-cli', 'base', '+field-create',
            '--base-token', base_token,
            '--table-id', table_id,
            '--name', field_name,
            '--type', lark_type
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ 字段 '{field_name}' ({lark_type})")
        else:
            print(f"  ⚠️  字段 '{field_name}' 创建失败: {result.stderr}")
    
    # 5. 批量插入记录
    print(f"\n📝 插入 {len(records)} 条记录...")
    success_count = 0
    for i, record in enumerate(records):
        # 批量插入，每次最多10条
        batch = records[i:i+10]
        if len(batch) == 0:
            break
        
        # 新版命令一次只能插入一条记录，需要逐条插入
        json_str = json.dumps(record, ensure_ascii=False)
        cmd = [
            'lark-cli', 'base', '+record-upsert',
            '--base-token', base_token,
            '--table-id', table_id,
            '--json', json_str
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            success_count += 1
        else:
            print(f"  ⚠️  记录 {i+1} 插入失败: {result.stderr}")
    
    print(f"✅ 成功插入 {success_count}/{len(records)} 条记录")
    
    return {
        'base_token': base_token,
        'table_id': table_id,
        'records_count': success_count
    }


def sync_to_existing_bitable(excel_path: str, base_url: str, table_name: str = None, 
                             key_field: str = None, create_missing: bool = True) -> Dict[str, str]:
    """同步到现有多维表格
    
    Args:
        excel_path: Excel文件路径
        base_url: 多维表格URL
        table_name: 数据表名称（可选，URL中包含时可不传）
        key_field: 主键字段名（用于更新匹配）
        create_missing: 是否创建缺失的记录
    
    Returns:
        dict: 同步结果信息
    
    Raises:
        Exception: 同步失败
    """
    # 1. 解析URL获取 base_token 和 table_id
    parsed = extract_token_from_url(base_url)
    base_token = parsed.get('token')
    table_id = parsed.get('table_id')
    
    # 确保是多维表格
    if parsed.get('type') != 'bitable':
        raise Exception(f"❌ URL 不是多维表格: {base_url}")
    
    if not base_token:
        raise Exception(f"❌ 无法从URL解析 base_token: {base_url}")
    
    print(f"📋 Base Token: {base_token}")
    print(f"📋 Table ID: {table_id}")
    
    # 2. 转换数据
    records, field_types = convert_excel_to_json(excel_path)
    
    # 3. 如果没有 table_id，需要通过 table_name 查找或创建
    if not table_id and table_name:
        print(f"\n🔍 查找数据表: {table_name}")
        cmd = ['lark-cli', 'base', '+table-list', '--base-token', base_token]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # 从输出中查找匹配的表
            output = result.stdout
            match = re.search(rf'"name"\s*:\s*"{table_name}"[^}}]*"table_id"\s*:\s*"([^"]+)"', output)
            if match:
                table_id = match.group(1)
                print(f"✅ 找到数据表: {table_id}")
            else:
                # 创建新表
                print(f"⚠️  未找到数据表，创建新表...")
                cmd = ['lark-cli', 'base', '+table-create', '--base-token', base_token, '--name', table_name]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    match = re.search(r'tbl_[a-zA-Z0-9]+', result.stdout)
                    if match:
                        table_id = match.group(0)
                        print(f"✅ 创建数据表成功: {table_id}")
    
    if not table_id:
        raise Exception("❌ 无法确定 table_id，请提供完整的 URL 或 table_name")
    
    # 4. 同步记录
    print(f"\n📝 同步 {len(records)} 条记录...")
    success_count = 0
    update_count = 0
    
    for i, record in enumerate(records):
        json_str = json.dumps(record, ensure_ascii=False)
        cmd = [
            'lark-cli', 'base', '+record-upsert',
            '--base-token', base_token,
            '--table-id', table_id,
            '--json', json_str
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            success_count += 1
            # 判断是创建还是更新
            if 'created' in result.stdout:
                update_count += 0
            elif 'updated' in result.stdout:
                update_count += 1
        else:
            print(f"  ⚠️  记录 {i+1} 同步失败: {result.stderr}")
        
        # 进度提示
        if (i + 1) % 10 == 0:
            print(f"  📊 进度: {i+1}/{len(records)}")
    
    print(f"\n✅ 同步完成: 成功 {success_count}/{len(records)} 条")
    
    return {
        'base_token': base_token,
        'table_id': table_id,
        'records_count': success_count,
        'updated_count': update_count
    }


def import_from_excel(excel_path: str, target_url: str = None, app_name: str = None, 
                      table_name: str = "导入数据", key_field: str = None) -> Dict[str, str]:
    """统一的导入入口
    
    Args:
        excel_path: Excel文件路径
        target_url: 目标多维表格URL（可选，有则同步，无则创建新表）
        app_name: 新建时的应用名称
        table_name: 数据表名称
        key_field: 主键字段名
    
    Returns:
        dict: 导入结果信息
    """
    if target_url:
        # 同步到现有表格
        return sync_to_existing_bitable(excel_path, target_url, table_name, key_field)
    else:
        # 创建新表格
        if not app_name:
            # 使用文件名作为应用名称
            app_name = os.path.splitext(os.path.basename(excel_path))[0]
        return create_new_bitable(excel_path, app_name, table_name)
