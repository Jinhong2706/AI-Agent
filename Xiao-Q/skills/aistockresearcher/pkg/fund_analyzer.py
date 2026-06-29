#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基金分析器 v1.0 — 风格漂移/持仓穿透/超额收益归因"""
from __future__ import annotations
import sys, json, time, re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "pkg"))
from crawl_utils import safe_request

def safe_float(val, default=0.0):
    "_safe float conversion_"
    try:
        f = float(val)
        return f if __import__("math").isfinite(f) else default
    except (TypeError, ValueError):
        return default

# ─────────────────────────────────────────────────────
# 数据获取
# ─────────────────────────────────────────────────────
def fetch_fund_nav(fund_code: str) -> dict:
    """获取基金实时估值/净值
    返回: {code, name, nav, nav_date, est_nav, est_change_pct, d7_return, d1_return}
    """
    url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt=1700000000"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
    try:
        raw = safe_request(url, headers=headers, timeout=8)
        if isinstance(raw, tuple):
            raw = raw[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        # JSONP: jsonpgz(...)
        m = re.search(r'jsonpgz\((.*)\)', raw, re.S)
        if m:
            data = json.loads(m.group(1))
            return {
                "code": data.get("fundcode", ""),
                "name": data.get("name", ""),
                "nav": data.get("dwjz", ""),
                "nav_date": data.get("jzrq", ""),
                "est_nav": data.get("gsz", ""),
                "est_change_pct": data.get("gszzl", ""),
                "d7_return": data.get("dwjz7d", ""),
            }
    except Exception:
        pass
    return {}

def fetch_fund_info(fund_code: str) -> dict:
    """获取基金基本信息（从东方财富）"""
    url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt=1700000000"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
    try:
        raw = safe_request(url, headers=headers, timeout=8)
        if isinstance(raw, tuple):
            raw = raw[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        m = re.search(r'jsonpgz\((.*)\)', raw, re.S)
        if m:
            data = json.loads(m.group(1))
            return {"code": data.get("fundcode", ""), "name": data.get("name", "")}
    except Exception:
        pass

    # 降级：用东财搜索页
    search_url = f"https://fund.eastmoney.com/pingzhong/{fund_code}.html"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://fund.eastmoney.com/",
    }
    try:
        raw = safe_request(search_url, headers=headers, timeout=8)
        if isinstance(raw, tuple):
            raw = raw[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        name_m = re.search(r'<h4 class="title">([^<]+)</h4>', raw)
        manager_m = re.search(r'基金经理：<a[^>]+>([^<]+)</a>', raw)
        scale_m = re.search(r'基金规模：([^<]+)</', raw)
        type_m = re.search(r'基金类型：([^<]+)</', raw)
        return {
            "name": name_m.group(1) if name_m else "",
            "manager": manager_m.group(1) if manager_m else "",
            "scale": scale_m.group(1).strip() if scale_m else "",
            "type": type_m.group(1).strip() if type_m else "",
        }
    except Exception:
        return {}

def _safe_http(url, headers=None, timeout=8):
    """HTTP GET, return str or None"""
    import urllib.request
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception:
        return None

def fetch_fund_history(fund_code: str, days: int = 90) -> list[dict]:
    """获取基金历史净值（用于计算波动率/回撤）
    EastMoney API 每次最多100条，多页请求确保足够数据
    """
    from datetime import date, timedelta
    end_d = date.today().strftime("%Y-%m-%d")
    start_d = (date.today() - timedelta(days=days * 5)).strftime("%Y-%m-%d")

    all_records = []
    page = 1
    api_max = 100

    while True:
        url_api = (f"https://api.fund.eastmoney.com/f10/lsjz?callback=jQuery"
                   f"&fundCode={fund_code}&pageIndex={page}&pageSize={api_max}"
                   f"&startDate={start_d}&endDate={end_d}")
        headers_api = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://fund.eastmoney.com/",
            "Accept": "application/json, text/javascript",
        }
        raw = _safe_http(url_api, headers_api)
        if not raw:
            break
        try:
            m = re.search(r'jQuery\((.*)\)$', raw, re.DOTALL)
            if not m:
                break
            data = json.loads(m.group(1))
            lsjz = data.get("Data", {}).get("LSJZList", [])
            if not lsjz:
                break
            for item in lsjz:
                all_records.append({
                    "date": item.get("FSRQ", "")[:10],
                    "nav": safe_float(item.get("DWJZ")),
                    "add_nav": safe_float(item.get("LJJZ")),
                    "change_pct": safe_float(item.get("JZZZL")),
                })
            total = data.get("Data", {}).get("TotalCount", 0)
            if len(lsjz) < api_max or page > 3:
                break
            page += 1
            if page > 5:
                break
        except Exception:
            break

    all_records.reverse()

    # 方式2: HTML table 备用
    if len(all_records) < max(days // 2, 5):
        url_html = (f"https://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz"
                    f"&code={fund_code}&page=1&pageSize={days}&start={start_d}&end={end_d}")
        raw2 = _safe_http(url_html, {"User-Agent": "Mozilla/5.0"})
        if raw2:
            try:
                rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw2, re.DOTALL)
                for row in rows[1:]:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    if len(cells) >= 4:
                        ds = re.sub(r'<[^>]+>', '', cells[0]).strip()[:10]
                        ns = re.sub(r'<[^>]+>', '', cells[1]).strip()
                        ans = re.sub(r'<[^>]+>', '', cells[2]).strip()
                        ps = re.sub(r'<[^>]+>', '', cells[3]).strip().replace('%', '')
                        all_records.append({
                            "date": ds,
                            "nav": safe_float(ns),
                            "add_nav": safe_float(ans),
                            "change_pct": safe_float(ps),
                        })
                all_records.sort(key=lambda x: x["date"])
            except Exception:
                pass

    return all_records[-days:] if len(all_records) > days else all_records

STYLE_BENCHMARKS = {
    "大盘价值":   {"pe_range": (8, 15), "pb_range": (1, 3), "market_cap": "large"},
    "大盘成长":   {"pe_range": (20, 50), "pb_range": (4, 15), "market_cap": "large"},
    "中盘均衡":   {"pe_range": (15, 30), "pb_range": (2, 6), "market_cap": "mid"},
    "小盘成长":   {"pe_range": (30, 80), "pb_range": (3, 10), "market_cap": "small"},
    "小盘价值":   {"pe_range": (10, 20), "pb_range": (1, 2.5), "market_cap": "small"},
    "行业均衡":   {"pe_range": (15, 40), "pb_range": (2, 8), "market_cap": "mixed"},
}

def detect_style_drift(fund_code: str, target_style: str = "") -> dict:
    """检测风格漂移
    target_style: 招募说明书中描述的目标风格
    返回: {is_drifted, current_style, target_style, drift_pct, evidence}
    """
    # 获取基金近期持仓风格（通过东财持仓数据）
    url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt=1700000000"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://fund.eastmoney.com/"}
    info = fetch_fund_info(fund_code)

    # 简化：通过基金名称关键词判断目标风格
    name = info.get("name", "")
    if not target_style:
        if "价值" in name:
            target_style = "大盘价值" if "大盘" in name else "中盘价值"
        elif "成长" in name:
            target_style = "大盘成长" if "大盘" in name else "小盘成长"
        elif "均衡" in name or "平衡" in name:
            target_style = "中盘均衡"
        elif "小盘" in name:
            target_style = "小盘成长"
        else:
            target_style = "大盘价值"  # 默认

    # 获取近期行情（判断实际风格）
    history = fetch_fund_history(fund_code, days=30)
    if len(history) < 5:
        return {
            "is_drifted": False,
            "current_style": "数据不足",
            "target_style": target_style,
            "drift_pct": 0,
            "evidence": "历史净值数据不足",
        }

    returns = [h["change_pct"] / 100 for h in history]  # change_pct 是百分数如0.54，转小数0.0054
    # 计算波动率
    import math
    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
    vol = math.sqrt(variance * 252) if variance > 0 else 0

    # 计算最大回撤
    navs = [h["nav"] for h in history]
    peak = navs[0]
    max_drawdown = 0.0
    for nav in navs:
        if nav > peak:
            peak = nav
        dd = (peak - nav) / peak if peak > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd

    # 通过波动率反推风格
    # 高波动(>30%) → 小盘成长/小盘价值
    # 中波动(15-30%) → 中盘均衡/大盘成长
    # 低波动(<15%) → 大盘价值
    if vol < 0.15:
        inferred = "大盘价值"
    elif vol < 0.25:
        inferred = "大盘成长" if mean_ret > 0.5 else "中盘均衡"
    elif vol < 0.35:
        inferred = "中盘均衡" if mean_ret > 0 else "小盘成长"
    else:
        inferred = "小盘成长"

    is_drifted = inferred != target_style

    return {
        "is_drifted": is_drifted,
        "current_style": inferred,
        "target_style": target_style,
        "drift_pct": 0 if not is_drifted else 50,  # 简化：漂移则50%偏离
        "volatility_annual": round(vol * 100, 1),
        "max_drawdown": round(max_drawdown * 100, 1),
        "evidence": f"年化波动率{vol*100:.1f}%→推断为{inferred}（目标{target_style}）",
    }

# ─────────────────────────────────────────────────────
# 超额收益归因（简化版）
# ─────────────────────────────────────────────────────
def attribute_excess_return(fund_code: str, benchmark_code: str = "sh000300") -> dict:
    """超额收益归因
    fund_code: 基金代码
    benchmark_code: 基准指数代码（沪深300=sh000300）
    """
    fund_hist = fetch_fund_history(fund_code, days=90)
    benchmark_hist = fetch_kline_simple(benchmark_code, days=90)

    if len(fund_hist) < 10 or len(benchmark_hist) < 10:
        return {"error": "数据不足"}

    # 对齐日期
    fund_dict = {h["date"]: h["nav"] for h in fund_hist}
    bm_dict = {h["date"]: h["close"] for h in benchmark_hist}
    common_dates = sorted(set(fund_dict.keys()) & set(bm_dict.keys()))

    fund_rets, bm_rets = [], []
    for i in range(1, len(common_dates)):
        d = common_dates[i]
        prev = common_dates[i-1]
        if d in fund_dict and prev in fund_dict and fund_dict[prev] > 0:
            fund_rets.append((fund_dict[d] - fund_dict[prev]) / fund_dict[prev])
        if d in bm_dict and prev in bm_dict and bm_dict[prev] > 0:
            bm_rets.append((bm_dict[d] - bm_dict[prev]) / bm_dict[prev])

    if not fund_rets or not bm_rets:
        return {"error": "无重叠交易日"}

    import math
    fund_cum = (1 + sum(fund_rets) / len(fund_rets)) ** len(fund_rets) - 1
    bm_cum = (1 + sum(bm_rets) / len(bm_rets)) ** len(bm_rets) - 1
    alpha = fund_cum - bm_cum

    # 波动率
    fund_vol = math.sqrt(sum((r - sum(fund_rets)/len(fund_rets))**2 for r in fund_rets) / len(fund_rets) * 252)
    bm_vol = math.sqrt(sum((r - sum(bm_rets)/len(bm_rets))**2 for r in bm_rets) / len(bm_rets) * 252)
    beta = (sum((r - sum(fund_rets)/len(fund_rets)) * (b - sum(bm_rets)/len(bm_rets))
             for r, b in zip(fund_rets, bm_rets)) / len(fund_rets)) / (sum((b - sum(bm_rets)/len(bm_rets))**2 for b in bm_rets) / len(bm_rets)) if bm_vol > 0 else 1.0

    sharpe = ((fund_cum * 252 / len(fund_rets) * len(fund_rets)) - 0.03) / fund_vol if fund_vol > 0 else 0

    attribution = {
        "period": f"近{len(fund_rets)}交易日",
        "fund_return": round(fund_cum * 100, 2),
        "benchmark_return": round(bm_cum * 100, 2),
        "alpha": round(alpha * 100, 2),
        "beta": round(beta, 2),
        "sharpe_ratio": round(sharpe, 2),
        "fund_volatility": round(fund_vol * 100, 1),
        "benchmark_volatility": round(bm_vol * 100, 1),
        "verdict": "跑赢基准" if alpha > 0 else "跑输基准",
    }
    return attribution

def fetch_kline_simple(code: str, days: int = 90) -> list[dict]:
    """简化K线获取"""
    url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayhfq&param={code},day,,,{days},qfq"
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://gu.qq.com"}
    try:
        raw = safe_request(url, headers=headers, timeout=8)
        if isinstance(raw, tuple):
            raw = raw[0]
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        raw = re.sub(r"^[^=]+=", "", raw.strip())
        data = json.loads(raw)
        day_data = data.get("data", {}).get(code, {}).get("day", [])
        return [{"date": item[0], "close": float(item[2]) if item[2] else 0}
                for item in day_data[-days:] if len(item) >= 3]
    except Exception:
        return []

# ─────────────────────────────────────────────────────
# 综合基金评分
# ─────────────────────────────────────────────────────
def score_fund(fund_code: str) -> dict:
    """综合评分（0-100）"""
    nav_data = fetch_fund_nav(fund_code)
    style = detect_style_drift(fund_code)
    nav_hist = fetch_fund_history(fund_code, days=90)
    attribution = attribute_excess_return(fund_code)

    score = 50
    details = []

    # 近期表现（30%）
    if len(nav_hist) >= 7:
        w7 = (nav_hist[-1]["nav"] - nav_hist[-7]["nav"]) / nav_hist[-7]["nav"] * 100 if nav_hist[-7]["nav"] > 0 else 0
        if w7 > 5: score += 15; details.append(f"周涨幅{w7:.1f}%(+15)")
        elif w7 > 0: score += 8; details.append(f"周涨幅{w7:.1f}%(+8)")
        elif w7 < -5: score -= 15; details.append(f"周跌幅{w7:.1f}%(-15)")

    if len(nav_hist) >= 30:
        m1 = (nav_hist[-1]["nav"] - nav_hist[-30]["nav"]) / nav_hist[-30]["nav"] * 100 if nav_hist[-30]["nav"] > 0 else 0
        if m1 > 10: score += 15; details.append(f"月涨幅{m1:.1f}%(+15)")
        elif m1 < -10: score -= 15; details.append(f"月跌幅{m1:.1f}%(-15)")

    # 风格稳定性（20%）
    if style["is_drifted"]:
        score -= 20
        details.append(f"风格漂移(-20): {style['evidence']}")
    else:
        score += 10
        details.append("风格稳定(+10)")

    # 阿尔法（25%）
    if "alpha" in attribution:
        alpha_val = attribution["alpha"]
        if alpha_val > 3: score += 20; details.append(f"超额收益{alpha_val:.1f}%(+20)")
        elif alpha_val > 0: score += 10; details.append(f"超额收益{alpha_val:.1f}%(+10)")
        elif alpha_val < -3: score -= 20; details.append(f"跑输基准{alpha_val:.1f}%(-20)")

    # 夏普比率（25%）
    if "sharpe_ratio" in attribution:
        sr = attribution["sharpe_ratio"]
        if sr > 1: score += 15; details.append(f"夏普比率{sr:.2f}(+15)")
        elif sr > 0.3: score += 8; details.append(f"夏普比率{sr:.2f}(+8)")
        elif sr < 0: score -= 10; details.append(f"夏普比率{sr:.2f}(-10)")

    final_score = max(0, min(100, score))

    return {
        "code": fund_code,
        "name": nav_data.get("name", ""),
        "score": final_score,
        "grade": "A" if final_score > 75 else "B" if final_score > 55 else "C" if final_score > 40 else "D",
        "details": details,
        "style": style,
        "attribution": attribution,
        "nav": nav_data,
    }

def print_fund_analysis(result: dict):
    s = result["score"]
    g = result["grade"]
    print(f"\n{'='*55}")
    print(f"  基金分析报告: {result['code']} {result['name']}")
    print(f"  综合评分: {s}/100  等级: {g}")
    print(f"{'='*55}")
    print(f"  风格: {result['style']['current_style']} "
          f"({'漂移' if result['style']['is_drifted'] else '正常'})")
    if "alpha" in result["attribution"]:
        a = result["attribution"]
        print(f"  超额收益: {a['alpha']:+.2f}% | β:{a['beta']} | 夏普:{a['sharpe_ratio']:.2f}")
        print(f"  基准涨跌: {a['benchmark_return']:+.2f}% | 基金涨跌: {a['fund_return']:+.2f}%")
    print(f"  最新净值: {result['nav'].get('nav','N/A')} ("
          f"{result['nav'].get('est_change_pct','N/A')}%)")
    print(f"  依据:")
    for d in result["details"]:
        print(f"    · {d}")
    print(f"{'='*55}\n")

# ─────────────────────────────────────────────────────
# 基金对比
# ─────────────────────────────────────────────────────
def compare_funds(codes: list[str]) -> list[dict]:
    """对比多只基金"""
    results = []
    for code in codes:
        r = score_fund(code)
        results.append(r)
        time.sleep(0.3)
    return sorted(results, key=lambda x: x["score"], reverse=True)

if __name__ == "__main__":
    print("=== 基金分析测试：易方达消费行业(110022) ===")
    r = score_fund("110022")
    print_fund_analysis(r)
    print("\n=== 基金对比：110022 vs 000083 ===")
    comparison = compare_funds(["110022", "000083"])
    for i, fund in enumerate(comparison, 1):
        print(f"  #{i} {fund['code']} {fund['name']}: {fund['score']}分 {fund['grade']}级")


def get_fund_nav(fund_code: str) -> dict:
    """获取基金净值（等同于 fetch_fund_nav）"""
    return fetch_fund_nav(fund_code)

def get_fund_industry(fund_code: str) -> str:
    """获取基金行业/类型"""
    info = fetch_fund_info(fund_code)
    return info.get("type", "混合型")
