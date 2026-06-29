#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动化爬取调度器 v2.0
- 自动判断是否为交易日（工作日 9:00-15:30）
- 支持手动触发和定时任务
- 优化股票/基金量化估计逻辑
"""

import sys, json, time, subprocess
from pathlib import Path
from datetime import datetime, time as dtime
from dateutil import parser as dateparser

# 工作日配置文件
TRADING_CONFIG = {
    "check_time": (9, 0),   # 开始检查时间（时, 分）
    "end_time": (15, 30),   # 交易结束时间
    "retry_interval": 1800, # 非交易时段重试间隔（秒）
    "market_close_check": True,
}

def is_trading_day() -> bool:
    """判断今天是否为交易日（简单判断：工作日）"""
    today = datetime.now()
    # 0=周一...6=周日
    return today.weekday() < 5

def is_within_trading_hours() -> bool:
    """判断当前是否在交易时间内"""
    now = datetime.now()
    current_time = dtime(now.hour, now.minute)
    start = dtime(*TRADING_CONFIG["check_time"])
    end = dtime(*TRADING_CONFIG["end_time"])
    return start <= current_time <= end

def should_run_daily() -> bool:
    """判断是否应该执行每日任务"""
    if not is_trading_day():
        return False
    if not is_within_trading_hours():
        return False
    return True

def get_next_run_time() -> str:
    """获取下次运行时间"""
    now = datetime.now()
    h, m = TRADING_CONFIG["check_time"]
    # 如果已经过了开始时间，返回下一个工作日9点
    if now.hour > h or (now.hour == h and now.minute > m):
        from datetime import timedelta
        next_day = now + timedelta(days=1)
        while next_day.weekday() >= 5:  # 跳过周末
            next_day += timedelta(days=1)
        return next_day.replace(hour=h, minute=m, second=0).strftime("%Y-%m-%d %H:%M")
    return now.replace(hour=h, minute=m, second=0).strftime("%Y-%m-%d %H:%M")

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "pkg"))

def run_step(name, script_path, timeout=300):
    """执行单个脚本步骤"""
    print(f"\n{'='*60}")
    print(f"  >> {name}")
    print('='*60)
    t0 = time.time()
    try:
        r = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True,
            cwd=str(SKILL_DIR), timeout=timeout
        )
        elapsed = time.time() - t0
        ok = r.returncode == 0
        status = "OK" if ok else f"FAIL({r.returncode})"
        lines = r.stdout.strip().split("\n")
        # 只打印前8行
        print("\n".join(lines[:8]))
        if len(lines) > 8:
            print(f"  ... ({len(lines)} 行)")
        print(f"[{status}] 耗时 {elapsed:.1f}s")
        if not ok and r.stderr:
            print(f"STDERR: {r.stderr[:200]}")
        return ok
    except subprocess.TimeoutExpired:
        print(f"[超时] {script_path.name} 执行超过 {timeout}s")
        return False
    except Exception as e:
        print(f"[错误] {e}")
        return False

def run_full_daily(stocks=None, funds=None):
    """执行每日全量流程"""
    today = datetime.now().strftime("%Y-%m-%d")
    today_short = today.replace("-", "")
    print(f"\n{'#'*60}")
    print(f"  每日自动化爬取 {today}")
    print(f"{'#'*60}")

    results = {}
    scripts_dir = SKILL_DIR / "scripts"

    # Step 0: 财经新闻抓取
    results["新闻抓取"] = run_step(
        "财经新闻抓取",
        scripts_dir / "crawl_news.py",
        timeout=60
    )

    # Step 1: 板块投资时机
    results["板块分析"] = run_step(
        "板块投资时机分析",
        scripts_dir / "sector_forecast.py",
        timeout=180
    )

    # Step 2: 股票突破分析
    results["股票分析"] = run_step(
        "突破/跌破股票分析",
        scripts_dir / "analyze_breakthrough.py",
        timeout=180
    )

    # Step 3: 基金产品综合分析
    results["基金分析"] = run_step(
        "基金产品综合分析",
        scripts_dir / "fund_universe_analyzer.py",
        timeout=300
    )

    # Step 4: 量化信号分析
    results["量化信号"] = run_step(
        "量化信号分析",
        scripts_dir / "quantitative_analysis.py",
        timeout=120
    )

    # Step 5: 追踪报告
    results["追踪报告"] = run_step(
        "定向追踪每日报告",
        scripts_dir / "tracker_daily_report.py",
        timeout=120
    )

    # Step 6: 基金净值预测
    results["净值预测"] = run_step(
        "基金净值预测",
        scripts_dir / "fund_forecast.py",
        timeout=180
    )

    # Step 7: 注册预测
    print(f"\n{'='*60}")
    print(f"  >> 注册今日预测")
    print('='*60)
    try:
        from prediction_tracker import register_todays_predictions
        cnt = register_todays_predictions()
        results["注册预测"] = True
        print(f"[OK] 注册 {cnt} 条预测")
    except Exception as e:
        print(f"[错误] {e}")
        results["注册预测"] = False

    # 汇总
    print(f"\n{'='*60}")
    print(f"  执行完成 {today}")
    print('='*60)
    ok_list = [k for k, v in results.items() if v]
    fail_list = [k for k, v in results.items() if not v]
    print(f"  成功: {', '.join(ok_list) if ok_list else '无'}")
    if fail_list:
        print(f"  失败: {', '.join(fail_list)}")

    return results

# ── CLI入口 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="每日自动化爬取调度器")
    parser.add_argument("--force", action="store_true", help="强制执行（忽略时间检查）")
    parser.add_argument("--check", action="store_true", help="只检查是否应该执行")
    parser.add_argument("--stocks", nargs="*", default=[], help="股票代码列表")
    parser.add_argument("--funds", nargs="*", default=[], help="基金代码列表")
    args = parser.parse_args()

    if args.check:
        print(f"是否为交易日: {is_trading_day()}")
        print(f"是否在交易时间: {is_within_trading_hours()}")
        print(f"是否应该执行: {should_run_daily()}")
        print(f"下次运行时间: {get_next_run_time()}")
    elif args.force or should_run_daily():
        run_full_daily(stocks=args.stocks, funds=args.funds)
    else:
        print(f"[跳过] 非交易时段，上次运行检查: {datetime.now().strftime('%H:%M:%S')}")
        print(f"下次运行时间: {get_next_run_time()}")