#!/usr/bin/env python3
import os
import sys
import argparse
import pandas as pd
import subprocess
from datetime import datetime
import json

def infer_field_type(series):
    """自动推断字段类型"""
    # 检查是否全为空值
    if series.dropna().empty:
        return 'text'  # 空值列默认为文本类型
    
    dtype = str(series.dtype)
    if 'int' in dtype or 'float' in dtype:
        # 检查是否实际为空值列（dtype为float64但全为NaN）
        if series.isna().all():
            return 'text'
        return 'number'
    elif 'datetime' in dtype:
        return 'datetime'
    else:
        # 尝试判断是否为日期字符串（抽样更多行提高准确性）
        sample_size = min(100, len(series.dropna()))
        if sample_size > 0:
            try:
                sample = series.dropna().sample(sample_size, random_state=42)
                pd.to_datetime(sample)
                return 'datetime'
            except:
                pass
        return 'text'

def check_lark_cli():
    """检查 lark-cli 是否已安装"""
    try:
        result = subprocess.run(['lark-cli', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            return True
    except FileNotFoundError:
        pass
    
    print("❌ 错误：未安装 lark-cli（飞书CLI）")
    print("\n📥 安装步骤：")
    print("  1. 确保已安装 Node.js 16.0+")
    print("  2. 运行：npm install -g @larksuite/cli")
    print("  3. 初始化：lark-cli config init")
    print("\n📖 详细文档：https://github.com/larksuite/cli")
    sys.exit(1)

def convert_excel_to_csv(excel_path, output_csv_path):
    """将Excel转换为符合lark-cli要求的CSV格式"""
    # 检查文件是否存在
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"❌ 文件不存在: {excel_path}")
    
    # 读取Excel
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        raise Exception(f"❌ 读取Excel文件失败: {str(e)}")
    
    # 推断每个字段的类型
    field_types = {}
    for col in df.columns:
        field_types[col] = infer_field_type(df[col])
    
    # 处理日期格式
    for col, typ in field_types.items():
        if typ == 'datetime':
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
    # 生成带类型的表头
    new_columns = [f"{col}:{field_types[col]}" for col in df.columns]
    df.columns = new_columns
    
    # 保存为CSV
    df.to_csv(output_csv_path, index=False, encoding='utf-8')
    print(f"✅ 已生成CSV文件: {output_csv_path}")
    print(f"📋 字段类型推断结果: {field_types}")
    return field_types

def create_new_bitable(csv_path, app_name, table_name):
    """创建新的多维表格"""
    cmd = [
        'lark-cli', 'create',
        '--csv',
        '--from', csv_path,
        '--app-name', app_name,
        '--table-name', table_name
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ 新多维表格创建成功！")
        print(result.stdout)
    else:
        print("❌ 创建失败:")
        print(result.stderr)
        sys.exit(1)

def sync_to_existing_bitable(csv_path, base_url, table_name, key_field, create_missing=True):
    """同步到现有多维表格"""
    cmd = [
        'lark-cli', 'sync',
        '--csv',
        '--from', csv_path,
        '--url', base_url,
        '--table-name', table_name,
        '--key', key_field
    ]
    if create_missing:
        cmd.append('--create-missing')
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ 数据同步成功！")
        print(result.stdout)
    else:
        print("❌ 同步失败:")
        print(result.stderr)
        sys.exit(1)

def extract_token_from_url(url):
    """从URL中提取token信息，支持多维表格和电子表格"""
    import re
    
    token_info = {
        'type': None,  # 'bitable' 或 'sheet'
        'token': None,
        'table_id': None,
        'sheet_id': None
    }
    
    # 尝试匹配 /base/TOKEN
    base_match = re.search(r'/base/([a-zA-Z0-9]+)', url)
    if base_match:
        token_info['type'] = 'bitable'
        token_info['token'] = base_match.group(1)
    
    # 尝试匹配 /sheets/TOKEN
    sheet_match = re.search(r'/sheets/([a-zA-Z0-9]+)', url)
    if sheet_match:
        token_info['type'] = 'sheet'
        token_info['token'] = sheet_match.group(1)
    
    # 尝试匹配 /wiki/TOKEN
    wiki_match = re.search(r'/wiki/([a-zA-Z0-9]+)', url)
    if wiki_match:
        wiki_token = wiki_match.group(1)
        cmd = ['lark-cli', 'wiki', 'spaces', 'get_node', '--params', json.dumps({"token": wiki_token})]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if data.get('code') == 0:
                    node = data.get('data', {}).get('node', {})
                    obj_type = node.get('obj_type')
                    token_info['token'] = node.get('obj_token')
                    if obj_type == 'bitable':
                        token_info['type'] = 'bitable'
                    elif obj_type == 'sheet':
                        token_info['type'] = 'sheet'
            except:
                pass
    
    # 尝试匹配 table=TABLE_ID 或 sheet=SHEET_ID
    table_match = re.search(r'table=([a-zA-Z0-9]+)', url)
    if table_match:
        token_info['table_id'] = table_match.group(1)
    
    sheet_id_match = re.search(r'sheet=([a-zA-Z0-9]+)', url)
    if sheet_id_match:
        token_info['sheet_id'] = sheet_id_match.group(1)
    
    return token_info

def extract_base_token_from_url(url):
    """从URL中提取base_token和table_id（兼容旧版）"""
    token_info = extract_token_from_url(url)
    if token_info['type'] == 'bitable':
        return token_info['token'], token_info['table_id']
    return None, None

def export_from_spreadsheet(url, sheet_names, output_path, no_record_id=False):
    """从电子表格导出数据"""
    print(f"📤 正在导出电子表格数据...")
    print(f"📋 工作表: {', '.join(sheet_names) if sheet_names else '全部'}")
    
    # 提取token
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
    
    # 如果没有指定工作表，导出所有
    if not sheet_names:
        sheet_names = list(sheet_map.keys())
    
    # 导出数据
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
            # 列号转换为字母（A, B, ..., Z, AA, AB, ...）
            def col_to_letter(n):
                result = ''
                while n > 0:
                    n, remainder = divmod(n - 1, 26)
                    result = chr(65 + remainder) + result
                return result
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
                processed_row = []
                for cell in row:
                    if cell is None:
                        processed_row.append('')
                    elif isinstance(cell, list):
                        # 富文本格式，提取纯文本
                        text = ''.join([seg.get('text', '') for seg in cell if isinstance(seg, dict)])
                        processed_row.append(text)
                    else:
                        processed_row.append(cell)
                processed_values.append(processed_row)
            
            # 转换为DataFrame
            if len(processed_values) > 1:
                df = pd.DataFrame(processed_values[1:], columns=processed_values[0])
            else:
                df = pd.DataFrame(processed_values)
            
            dfs.append({
                'name': sheet_name,
                'data': df
            })
            print(f"✅ 已获取工作表 [{sheet_name}]: {len(df)} 行")
        except Exception as e:
            print(f"⚠️ 解析数据失败: {sheet_name}: {str(e)}")
            continue
    
    if not dfs:
        print("❌ 没有数据可导出")
        sys.exit(1)
    
    print("✅ 数据导出成功！")
    return {'tables': [{'meta': {'tableName': d['name']}, 'rows': d['data'].to_dict('records')} for d in dfs]}

def export_from_bitable(base_url, table_names, output_path, no_record_id=False):
    """从多维表格导出数据（使用新版lark-cli命令）"""
    print(f"📤 正在导出多维表格数据...")
    print(f"📋 表名: {', '.join(table_names)}")
    
    # 提取base_token
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
    
    # 导出数据
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
            
            # 转换为DataFrame
            df = pd.DataFrame(rows, columns=fields_from_response)
            
            # 删除_record_id列（如果存在）
            if '_record_id' in df.columns:
                df = df.drop(columns=['_record_id'])
            if no_record_id and 'record_id' in df.columns:
                df = df.drop(columns=['record_id'])
            
            dfs.append({
                'name': table_name,
                'data': df
            })
            print(f"✅ 已获取表 [{table_name}]: {len(df)} 行")
        except Exception as e:
            print(f"⚠️ 解析数据失败: {table_name}: {str(e)}")
            continue
    
    if not dfs:
        print("❌ 没有数据可导出")
        sys.exit(1)
    
    print("✅ 数据导出成功！")
    return {'tables': [{'meta': {'tableName': d['name']}, 'rows': d['data'].to_dict('records')} for d in dfs]}

def parse_exported_json(data):
    """解析导出的JSON数据，返回DataFrame列表"""
    try:
        dfs = []
        for table in data.get('tables', []):
            table_name = table['meta']['tableName']
            
            # rows数据在table['rows']中，不在meta里
            rows = table.get('rows', [])
            
            if not rows:
                print(f"⚠️ 表 [{table_name}] 没有数据")
                continue
            
            # 将行数据转换为DataFrame
            df = pd.DataFrame(rows)
            
            # 删除_record_id列（如果存在）
            if '_record_id' in df.columns:
                df = df.drop(columns=['_record_id'])
            
            dfs.append({
                'name': table_name,
                'data': df
            })
        
        return dfs
    except Exception as e:
        print(f"❌ 解析JSON失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def save_as_csv(dfs, output_path):
    """将DataFrame保存为CSV"""
    if len(dfs) == 0:
        print("❌ 没有数据可保存")
        return False
    
    # 如果只有一个表，直接保存
    if len(dfs) == 1:
        dfs[0]['data'].to_csv(output_path, index=False, encoding='utf-8')
        print(f"✅ 已保存为CSV: {output_path}")
        print(f"📊 数据行数: {len(dfs[0]['data'])}")
        print(f"📋 字段数量: {len(dfs[0]['data'].columns)}")
        return True
    
    # 如果有多个表，分别保存
    for i, df_info in enumerate(dfs):
        table_path = output_path.replace('.csv', f'_{df_info["name"]}.csv')
        df_info['data'].to_csv(table_path, index=False, encoding='utf-8')
        print(f"✅ 已保存表 [{df_info['name']}] 为CSV: {table_path}")
        print(f"   数据行数: {len(df_info['data'])}")
    
    return True

def save_as_excel(dfs, output_path, sheet_name=None):
    """将DataFrame保存为Excel"""
    if len(dfs) == 0:
        print("❌ 没有数据可保存")
        return False
    
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for i, df_info in enumerate(dfs):
                # 如果只有一个表且有指定sheet名称，使用指定的；否则用表名
                sheet = sheet_name if (len(dfs) == 1 and sheet_name) else df_info['name']
                # Excel sheet名称最长31个字符
                sheet = sheet[:31]
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

def main():
    parser = argparse.ArgumentParser(
        description='Excel与飞书多维表格互转工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导入：创建新表
  python excel_to_bitable.py --input data.xlsx --mode create --app-name "员工表" --table-name "员工列表"
  
  # 导入：同步到现有表
  python excel_to_bitable.py --input data.xlsx --mode sync --url "https://xxx.feishu.cn/base/xxx" --table-name "员工列表" --key "员工编号"
  
  # 导出：导出为CSV
  python excel_to_bitable.py --mode export --url "https://xxx.feishu.cn/base/xxx" --table-name "员工列表" --output employees.csv
  
  # 导出：导出为Excel
  python excel_to_bitable.py --mode export --url "https://xxx.feishu.cn/base/xxx" --table-name "员工列表" --output employees.xlsx --format excel
  
  # 导出：导出多个表
  python excel_to_bitable.py --mode export --url "https://xxx.feishu.cn/base/xxx" --table-name "表1" "表2" --output data.xlsx --format excel
        """
    )
    
    # 模式选择
    parser.add_argument('--mode', choices=['create', 'sync', 'export'], required=True, 
                        help='操作模式：create=创建新表，sync=同步到现有表，export=导出数据')
    
    # 导入相关参数
    parser.add_argument('--input', help='输入Excel/CSV文件路径（create/sync模式）')
    parser.add_argument('--app-name', help='新表的应用名称（create模式必填）')
    parser.add_argument('--key', help='主键字段名（sync模式必填）')
    parser.add_argument('--no-create-missing', action='store_true', help='同步时不自动插入新行')
    
    # 通用参数
    parser.add_argument('--table-name', nargs='+', help='数据表名称（export模式支持多个）')
    parser.add_argument('--url', help='目标多维表格URL（sync/export模式）')
    
    # 导出相关参数
    parser.add_argument('--output', help='输出文件路径（export模式必填）')
    parser.add_argument('--format', choices=['csv', 'excel'], default='csv', help='导出格式：csv或excel（默认csv）')
    parser.add_argument('--no-record-id', action='store_true', help='导出时不包含_record_id字段')
    parser.add_argument('--sheet-name', help='Excel工作表名称（仅format=excel时有效）')
    
    args = parser.parse_args()
    
    # 检查 lark-cli 是否已安装
    check_lark_cli()
    
    # 参数校验
    if args.mode in ['create', 'sync'] and not args.input:
        print("❌ create/sync模式必须提供--input参数")
        sys.exit(1)
    
    if args.mode == 'create' and not args.app_name:
        print("❌ create模式必须提供--app-name参数")
        sys.exit(1)
    
    if args.mode == 'sync' and (not args.url or not args.key):
        print("❌ sync模式必须提供--url和--key参数")
        sys.exit(1)
    
    if args.mode == 'export' and (not args.url or not args.output):
        print("❌ export模式必须提供--url和--output参数")
        sys.exit(1)
    
    # 执行操作
    if args.mode == 'create':
        # 创建新表
        temp_csv = f"/tmp/excel_to_bitable_{int(datetime.now().timestamp())}.csv"
        try:
            convert_excel_to_csv(args.input, temp_csv)
            create_new_bitable(temp_csv, args.app_name, args.table_name[0] if isinstance(args.table_name, list) else args.table_name)
        except FileNotFoundError as e:
            print(str(e))
            sys.exit(1)
        except Exception as e:
            print(f"❌ 创建多维表格失败: {str(e)}")
            sys.exit(1)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
    
    elif args.mode == 'sync':
        # 同步到现有表
        temp_csv = f"/tmp/excel_to_bitable_{int(datetime.now().timestamp())}.csv"
        try:
            convert_excel_to_csv(args.input, temp_csv)
            sync_to_existing_bitable(
                temp_csv, 
                args.url, 
                args.table_name[0] if isinstance(args.table_name, list) else args.table_name, 
                args.key, 
                not args.no_create_missing
            )
        except FileNotFoundError as e:
            print(str(e))
            sys.exit(1)
        except Exception as e:
            print(f"❌ 同步数据失败: {str(e)}")
            sys.exit(1)
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
    
    elif args.mode == 'export':
        # 导出数据 - 自动识别电子表格或多维表格
        token_info = extract_token_from_url(args.url)
        
        if token_info['type'] == 'sheet':
            # 电子表格导出
            data = export_from_spreadsheet(args.url, args.table_name, args.output, args.no_record_id)
        elif token_info['type'] == 'bitable':
            # 多维表格导出
            data = export_from_bitable(args.url, args.table_name, args.output, args.no_record_id)
        else:
            print("❌ 无法识别URL类型，请检查URL是否正确")
            sys.exit(1)
        
        # 2. 解析JSON
        dfs = parse_exported_json(data)
        
        if not dfs:
            print("❌ 没有解析到数据")
            sys.exit(1)
        
        # 3. 根据格式保存
        if args.format == 'excel':
            success = save_as_excel(dfs, args.output, args.sheet_name)
        else:
            success = save_as_csv(dfs, args.output)
        
        if not success:
            sys.exit(1)

if __name__ == "__main__":
    main()
