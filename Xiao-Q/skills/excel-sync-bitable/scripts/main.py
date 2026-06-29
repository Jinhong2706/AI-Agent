#!/usr/bin/env python3
"""Excel与飞书表格互转工具 - 主入口"""
import os
import sys
import argparse
from datetime import datetime

from core.parser import extract_token_from_url
from core.exporter import export_from_bitable, export_from_spreadsheet
from core.importer import convert_excel_to_csv, create_new_bitable, sync_to_existing_bitable
from core.converter import parse_exported_json
from core.saver import save_as_csv, save_as_excel


def check_lark_cli():
    """检查 lark-cli 是否已安装"""
    import subprocess
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


def main():
    parser = argparse.ArgumentParser(
        description='Excel与飞书表格互转工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 导入：创建新表
  python main.py --input data.xlsx --mode create --app-name "员工表" --table-name "员工列表"
  
  # 导入：同步到现有表
  python main.py --input data.xlsx --mode sync --url "https://xxx.feishu.cn/base/xxx" --table-name "员工列表" --key "员工编号"
  
  # 导出：导出多维表格
  python main.py --mode export --url "https://xxx.feishu.cn/base/xxx" --table-name "员工列表" --output employees.xlsx --format excel
  
  # 导出：导出电子表格（所有工作表）
  python main.py --mode export --url "https://xxx.feishu.cn/sheets/xxx" --output spreadsheet.xlsx --format excel
        """
    )
    
    parser.add_argument('--mode', choices=['create', 'sync', 'export'], required=True, 
                        help='操作模式：create=创建新表，sync=同步到现有表，export=导出数据')
    parser.add_argument('--input', help='输入Excel/CSV文件路径（create/sync模式）')
    parser.add_argument('--app-name', help='新表的应用名称（create模式必填）')
    parser.add_argument('--key', help='主键字段名（sync模式必填）')
    parser.add_argument('--no-create-missing', action='store_true', help='同步时不自动插入新行')
    parser.add_argument('--table-name', nargs='+', help='数据表/工作表名称（export模式可选）')
    parser.add_argument('--url', help='目标表格URL（sync/export模式）')
    parser.add_argument('--output', help='输出文件路径（export模式必填）')
    parser.add_argument('--format', choices=['csv', 'excel'], default='csv', help='导出格式')
    parser.add_argument('--no-record-id', action='store_true', help='导出时不包含record_id')
    parser.add_argument('--sheet-name', help='Excel工作表名称')
    
    args = parser.parse_args()
    
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
        temp_csv = f"/tmp/excel_to_bitable_{int(datetime.now().timestamp())}.csv"
        try:
            convert_excel_to_csv(args.input, temp_csv)
            create_new_bitable(temp_csv, args.app_name, args.table_name[0] if args.table_name else '数据表')
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
        temp_csv = f"/tmp/excel_to_bitable_{int(datetime.now().timestamp())}.csv"
        try:
            convert_excel_to_csv(args.input, temp_csv)
            sync_to_existing_bitable(
                temp_csv, args.url, 
                args.table_name[0] if args.table_name else '数据表', 
                args.key, not args.no_create_missing
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
        token_info = extract_token_from_url(args.url)
        
        if token_info['type'] == 'sheet':
            data = export_from_spreadsheet(args.url, args.table_name, args.output, args.no_record_id)
        elif token_info['type'] == 'bitable':
            if not args.table_name:
                print("❌ 多维表格导出需要指定 --table-name")
                sys.exit(1)
            data = export_from_bitable(args.url, args.table_name, args.output, args.no_record_id)
        else:
            print("❌ 无法识别URL类型，请检查URL是否正确")
            sys.exit(1)
        
        dfs = parse_exported_json(data)
        
        if not dfs:
            print("❌ 没有解析到数据")
            sys.exit(1)
        
        if args.format == 'excel':
            success = save_as_excel(dfs, args.output, args.sheet_name)
        else:
            success = save_as_csv(dfs, args.output)
        
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
