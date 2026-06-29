#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dual_trend_selector import DualTrendSelector
from data_loader import TdxDataLoader, CSVDataLoader, generate_test_data


def _analyze_single(code: str, tdx_path: str = None, data_dir: str = None,
                    liquidity: float = 1e8, adx_threshold: float = 20) -> Dict[str, Any]:
    selector = DualTrendSelector(liquidity=liquidity, adx_th=adx_threshold)

    stock_data = None
    if data_dir and os.path.isdir(data_dir):
        loader = CSVDataLoader(data_dir)
        stock_data = loader.load_stock(code)
    elif tdx_path:
        loader = TdxDataLoader(tdx_path)
        stock_data = loader.load_stock(code)
    else:
        loader = TdxDataLoader()
        stock_data = loader.load_stock(code)
        if stock_data is None:
            csv_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
            if os.path.isdir(csv_dir):
                csv_loader = CSVDataLoader(csv_dir)
                stock_data = csv_loader.load_stock(code)

    if stock_data is None:
        return {
            "success": False,
            "data": None,
            "count": 0,
            "message": f"未找到股票 {code} 的数据，请检查代码或数据路径"
        }

    result = selector.analyze(stock_data)
    return {
        "success": True,
        "data": result,
        "count": 1,
        "message": f"分析完成: {code} {result.get('signal', 'UNKNOWN')}"
    }


def _batch_analyze(codes: List[str], tdx_path: str = None, data_dir: str = None,
                   liquidity: float = 1e8, adx_threshold: float = 20) -> Dict[str, Any]:
    selector = DualTrendSelector(liquidity=liquidity, adx_th=adx_threshold)
    stock_list = []

    if data_dir and os.path.isdir(data_dir):
        loader = CSVDataLoader(data_dir)
        for code in codes:
            data = loader.load_stock(code)
            if data is not None:
                stock_list.append(data)
    else:
        loader = TdxDataLoader(tdx_path)
        if loader.tdx_path is None:
            return {
                "success": False,
                "data": [],
                "count": 0,
                "message": "未找到通达信安装目录，请使用 tdx_path 参数指定路径"
            }
        for code in codes:
            data = loader.load_stock(code)
            if data is not None:
                stock_list.append(data)

    if not stock_list:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": "未找到任何有效股票数据"
        }

    results = selector.batch_analyze(stock_list)
    return {
        "success": True,
        "data": results,
        "count": len(results),
        "message": f"批量分析完成，共 {len(results)} 只股票"
    }


def _scan_tdx(tdx_path: str = None, max_count: int = 0,
              liquidity: float = 1e8, adx_threshold: float = 20) -> Dict[str, Any]:
    loader = TdxDataLoader(tdx_path)
    if loader.tdx_path is None:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": "未找到通达信安装目录，请使用 tdx_path 参数指定路径"
        }

    codes = loader.scan_all(max_count)
    if not codes:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": "未找到股票数据文件"
        }

    selector = DualTrendSelector(liquidity=liquidity, adx_th=adx_threshold)
    stock_list = []
    for code in codes:
        data = loader.load_stock(code)
        if data is not None:
            stock_list.append(data)

    if not stock_list:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": "有效数据为0"
        }

    results = selector.batch_analyze(stock_list)
    report = selector.format_report(results)

    return {
        "success": True,
        "data": results,
        "report": report,
        "count": len(results),
        "scanned": len(codes),
        "valid": len(stock_list),
        "message": f"扫描完成: 扫描{len(codes)}只, 有效{len(stock_list)}只"
    }


def _scan_csv(data_dir: str = None, liquidity: float = 1e8,
              adx_threshold: float = 20) -> Dict[str, Any]:
    if data_dir is None:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

    loader = CSVDataLoader(data_dir)
    codes = loader.scan_all()
    if not codes:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": f"未找到CSV数据文件，请将CSV文件放入 {data_dir} 目录"
        }

    selector = DualTrendSelector(liquidity=liquidity, adx_th=adx_threshold)
    stock_list = []
    for code in codes:
        data = loader.load_stock(code)
        if data is not None:
            stock_list.append(data)

    if not stock_list:
        return {
            "success": False,
            "data": [],
            "count": 0,
            "message": "有效数据为0"
        }

    results = selector.batch_analyze(stock_list)
    report = selector.format_report(results)

    return {
        "success": True,
        "data": results,
        "report": report,
        "count": len(results),
        "scanned": len(codes),
        "valid": len(stock_list),
        "message": f"CSV扫描完成: 扫描{len(codes)}只, 有效{len(stock_list)}只"
    }


def _test(liquidity: float = 1e8, adx_threshold: float = 20) -> Dict[str, Any]:
    selector = DualTrendSelector(liquidity=liquidity, adx_th=adx_threshold)

    test_stocks = [
        generate_test_data('600519', '贵州茅台', 120, 'bull'),
        generate_test_data('000858', '五粮液', 120, 'bull'),
        generate_test_data('601318', '中国平安', 120, 'range'),
        generate_test_data('000001', '平安银行', 120, 'bear'),
        generate_test_data('600036', '招商银行', 120, 'bull'),
    ]

    results = selector.batch_analyze(test_stocks)
    report = selector.format_report(results)

    return {
        "success": True,
        "data": results,
        "report": report,
        "count": len(results),
        "message": f"测试完成，共 {len(results)} 只模拟股票"
    }


def skill_handler(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action", "test")

    liquidity = float(params.get("liquidity", 1e8))
    adx_threshold = float(params.get("adx_threshold", 20))
    tdx_path = params.get("tdx_path")
    data_dir = params.get("data_dir")

    if action == "analyze":
        code = params.get("code")
        if not code:
            return {
                "success": False,
                "data": None,
                "count": 0,
                "message": "缺少必要参数: code (股票代码)"
            }
        return _analyze_single(code, tdx_path, data_dir, liquidity, adx_threshold)

    elif action == "batch_analyze":
        codes = params.get("codes", [])
        if not codes:
            return {
                "success": False,
                "data": [],
                "count": 0,
                "message": "缺少必要参数: codes (股票代码列表)"
            }
        if isinstance(codes, str):
            codes = [c.strip() for c in codes.split(",")]
        return _batch_analyze(codes, tdx_path, data_dir, liquidity, adx_threshold)

    elif action == "scan_tdx":
        max_count = int(params.get("max_count", 0))
        return _scan_tdx(tdx_path, max_count, liquidity, adx_threshold)

    elif action == "scan_csv":
        return _scan_csv(data_dir, liquidity, adx_threshold)

    elif action == "test":
        return _test(liquidity, adx_threshold)

    else:
        return {
            "success": False,
            "data": None,
            "count": 0,
            "message": f"未知的action: {action}，支持: analyze, batch_analyze, scan_tdx, scan_csv, test"
        }


if __name__ == "__main__":
    print("=== 双趋势共振量化选股系统 Skill 测试 ===\n")

    result = skill_handler({"action": "test"})
    print(f"成功: {result['success']}")
    print(f"数量: {result['count']}")
    print(f"消息: {result['message']}")
    if result.get("report"):
        print("\n" + result["report"])
