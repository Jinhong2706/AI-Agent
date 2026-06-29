import argparse
import json
import sys
from datetime import datetime

from dual_trend_selector import DualTrendSelector
from data_loader import TdxDataLoader, CSVDataLoader, generate_test_data


def run_test():
    print("=" * 60)
    print("双趋势共振量化选股系统 — 测试模式")
    print("=" * 60)

    selector = DualTrendSelector()

    test_stocks = [
        generate_test_data('600519', '贵州茅台', 120, 'bull'),
        generate_test_data('000858', '五粮液', 120, 'bull'),
        generate_test_data('601318', '中国平安', 120, 'range'),
        generate_test_data('000001', '平安银行', 120, 'bear'),
        generate_test_data('600036', '招商银行', 120, 'bull'),
    ]

    results = selector.batch_analyze(test_stocks)
    report = selector.format_report(results)
    print(report)

    print("\n--- 详细JSON输出（S/A/B级）---")
    for r in results:
        if r.get('score', 0) >= 60:
            print(json.dumps(r, ensure_ascii=False, indent=2))

    return results


def run_tdx_scan(tdx_path=None, max_count=0, output_file=None):
    print("=" * 60)
    print("双趋势共振量化选股系统 — 通达信数据扫描")
    print("=" * 60)

    loader = TdxDataLoader(tdx_path)
    if loader.tdx_path is None:
        print("错误: 未找到通达信安装目录，请使用 --tdx_path 指定路径")
        print("常见路径: C:\\new_tdx, D:\\new_tdx")
        return None

    print(f"通达信路径: {loader.tdx_path}")
    codes = loader.scan_all(max_count)
    print(f"扫描股票数: {len(codes)}")

    if not codes:
        print("未找到股票数据文件")
        return None

    selector = DualTrendSelector()
    stock_list = []
    for i, code in enumerate(codes):
        if (i + 1) % 100 == 0:
            print(f"  已加载 {i + 1}/{len(codes)}...")
        data = loader.load_stock(code)
        if data is not None:
            stock_list.append(data)

    print(f"有效数据: {len(stock_list)} 只")

    results = selector.batch_analyze(stock_list)
    report = selector.format_report(results)
    print(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        json_file = output_file.replace('.txt', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n报告已保存: {output_file}")
        print(f"数据已保存: {json_file}")

    return results


def run_csv_scan(data_dir='data', output_file=None):
    print("=" * 60)
    print("双趋势共振量化选股系统 — CSV数据扫描")
    print("=" * 60)

    loader = CSVDataLoader(data_dir)
    codes = loader.scan_all()
    print(f"扫描股票数: {len(codes)}")

    if not codes:
        print(f"未找到CSV数据文件，请将CSV文件放入 {data_dir}/ 目录")
        return None

    selector = DualTrendSelector()
    stock_list = []
    for code in codes:
        data = loader.load_stock(code)
        if data is not None:
            stock_list.append(data)

    print(f"有效数据: {len(stock_list)} 只")

    results = selector.batch_analyze(stock_list)
    report = selector.format_report(results)
    print(report)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存: {output_file}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description='双趋势共振量化选股系统 (GMMA+Ichimoku+ADX+流动性过滤)'
    )
    parser.add_argument('--mode', choices=['test', 'tdx', 'csv'], default='test',
                        help='运行模式: test=测试数据, tdx=通达信数据, csv=CSV数据')
    parser.add_argument('--tdx_path', type=str, default=None,
                        help='通达信安装路径 (如: D:\\new_tdx)')
    parser.add_argument('--max_count', type=int, default=0,
                        help='最大扫描数量 (0=全部)')
    parser.add_argument('--data_dir', type=str, default='data',
                        help='CSV数据目录 (默认: data)')
    parser.add_argument('--output', type=str, default=None,
                        help='输出报告文件名 (如: report.txt)')
    parser.add_argument('--liquidity', type=float, default=1e8,
                        help='流动性门槛 (默认: 1亿)')
    parser.add_argument('--adx_threshold', type=float, default=20,
                        help='ADX趋势强度门槛 (默认: 20)')

    args = parser.parse_args()

    if args.mode == 'test':
        run_test()
    elif args.mode == 'tdx':
        run_tdx_scan(args.tdx_path, args.max_count, args.output)
    elif args.mode == 'csv':
        run_csv_scan(args.data_dir, args.output)


if __name__ == '__main__':
    main()
