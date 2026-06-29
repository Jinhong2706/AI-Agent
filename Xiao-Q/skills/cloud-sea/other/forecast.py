#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""6座张家口非官方峰 · 一周云海概率预测"""
import sys, os, json, math, datetime, urllib.request, urllib.parse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 6座非官方峰配置
CUSTOM_PEAKS = [
    {"name": "茶山",     "lat": 39.7808, "lon": 114.9470, "summit_elev": 2524,  "area": "蔚县"},
    {"name": "喜鹊梁",   "lat": 40.8306, "lon": 115.3673, "summit_elev": 2078,  "area": "崇礼区"},
    {"name": "麻田岭",   "lat": 39.7190, "lon": 114.8326, "summit_elev": 2122,  "area": "蔚县"},
    {"name": "白谷查山", "lat": 40.0033, "lon": 115.1123, "summit_elev": 2190,  "area": "涿鹿县"},
    {"name": "冰山梁",   "lat": 41.2638, "lon": 115.8045, "summit_elev": 2211,  "area": "赤城县"},
    {"name": "东猴顶",   "lat": 41.3558, "lon": 116.1469, "summit_elev": 2292.6,"area": "赤城县"},
]

# Open-Meteo API 参数
HOURLY_PARAMS = [
    "temperature_2m", "dew_point_2m", "relative_humidity_2m",
    "wind_speed_10m", "cloud_cover", "cloud_cover_low",
    "precipitation_probability",
]

def fetch_weather(peak, date_str):
    """Fetch weather from Open-Meteo API for a single peak."""
    params = {
        "latitude": peak["lat"],
        "longitude": peak["lon"],
        "hourly": ",".join(HOURLY_PARAMS),
        "timezone": "Asia/Shanghai",
        "forecast_days": "16",
    }
    url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def calc_lcl(t, td):
    """Calculate LCL using Magnus formula: LCL = 125 * (T - Td)."""
    spread = t - td
    if spread <= 0:
        return 10  # min 10m
    return 125 * spread

def calc_fog_type(td_spread, rh, ws, cc_low):
    """Determine fog type based on conditions."""
    if td_spread < 0.5 and rh >= 95:
        return "锋面雾"
    elif td_spread < 1.5 and rh >= 90:
        return "混合雾"
    elif td_spread < 3.0 and rh >= 85:
        return "上坡雾"
    elif ws < 3 and rh >= 90:
        return "辐射雾"
    else:
        return "无雾"

def calc_sunny_rating(lcl, cc_low, vis_km):
    """Sunrise quality rating (1-5 stars)."""
    if cc_low < 20 and vis_km >= 15:
        return 5
    elif cc_low < 30 and lcl < 150:
        return 4
    elif cc_low < 50:
        return 3
    elif cc_low < 75:
        return 2
    else:
        return 1

def calc_prob(peak, data, date_str):
    """Calculate cloud sea probability using simplified 12-factor model."""
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    station_elev = data.get("elevation", 1000)

    # Get morning hours (00-08 BJT)
    morning_data = []
    for i, t in enumerate(times):
        if not t.startswith(date_str):
            continue
        h = int(t[11:13])
        if h > 8:
            continue
        morning_data.append({
            "h": h, "T": hourly["temperature_2m"][i],
            "Td": hourly["dew_point_2m"][i],
            "RH": hourly["relative_humidity_2m"][i],
            "ws": hourly["wind_speed_10m"][i],
            "cc": hourly["cloud_cover"][i],
            "cc_low": hourly["cloud_cover_low"][i],
            "rain": hourly["precipitation_probability"][i],
        })

    if not morning_data:
        return None

    # Pre-dawn (01-06) for factor analysis
    pre_dawn = [d for d in morning_data if 1 <= d["h"] <= 6]
    # All morning for average
    all_morning = morning_data

    if not pre_dawn:
        return None

    # Factor 1: Radiative cooling (night sky cover)
    night_hours = [d for d in pre_dawn if d["h"] <= 3]
    avg_night_cc = sum(d["cc"] for d in night_hours) / len(night_hours) if night_hours else 50
    f1 = max(0, min(10, 10 - avg_night_cc * 0.1))

    # Factor 2: Stability (temp drop overnight)
    t_max = max(d["T"] for d in pre_dawn)
    t_min = min(d["T"] for d in pre_dawn)
    temp_drop = t_max - t_min
    f2 = min(10, max(0, temp_drop * 2))

    # Factor 3: Wind
    avg_ws = sum(d["ws"] for d in all_morning) / len(all_morning)
    if avg_ws < 1:
        f3 = avg_ws * 5
    elif avg_ws <= 8:
        f3 = 10
    elif avg_ws <= 12:
        f3 = 8
    elif avg_ws <= 20:
        f3 = 4
    else:
        f3 = 0

    # Factor 4: Moisture
    max_rh = max(d["RH"] for d in all_morning)
    avg_rh = sum(d["RH"] for d in all_morning) / len(all_morning)
    if max_rh >= 98:
        f4 = 10
    elif max_rh >= 95:
        f4 = 9
    elif max_rh >= 90:
        f4 = 8
    elif max_rh >= 85:
        f4 = 6
    elif max_rh >= 80:
        f4 = 4
    else:
        f4 = 2

    # Factor 5: Precipitation
    max_rain = max(d.get("rain", 0) for d in all_morning)
    if max_rain == 0:
        f5 = 10
    elif max_rain < 20:
        f5 = 8
    elif max_rain < 40:
        f5 = 5
    else:
        f5 = 1

    # Factor 6: LCL vs Altitude
    min_td_spread = min((d["T"] - d["Td"]) for d in pre_dawn)
    lcl_ag = calc_lcl(pre_dawn[0]["T"], pre_dawn[0]["Td"])  # Use first hour as proxy
    for d in pre_dawn:
        s = d["T"] - d["Td"]
        if s > 0:
            lcl_ag = min(lcl_ag, calc_lcl(d["T"], d["Td"]))
    fog_top = station_elev + lcl_ag + 150
    diff = peak["summit_elev"] - fog_top
    f6 = max(0, min(10, (diff + 100) / 80))

    # Factor 7: Sunrise timing
    f7 = 5  # neutral

    # Factor 8: Seasonal
    f8 = 5  # early June neutral

    # Factor 9: Terrain
    terrain_adv = peak["summit_elev"] - station_elev
    f9 = min(10, max(3, terrain_adv / 100))

    # Factor 10: Night clear sky
    clear_ratio = sum(1 for d in night_hours if d["cc"] < 30) / len(night_hours) if night_hours else 0.3
    f10 = clear_ratio * 8

    # Factor 11: Visibility
    avg_vis = max(5, 20 - avg_rh * 0.15)
    f11 = min(10, avg_vis / 2)

    # Factor 12: Uncertainty
    f12 = 5

    # Weighted score
    weights = [0.20, 0.15, 0.15, 0.15, 0.08, 0.13, 0.05, 0.05, 0.05, 0.03, 0.02, 0.05]
    factors = [f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12]
    score = sum(w * f for w, f in zip(weights, factors))

    # Convert to probability
    base_prob = score * 10

    # cc_low override
    avg_cc_low = sum(d["cc_low"] for d in all_morning) / len(all_morning)
    if avg_cc_low < 1:
        base_prob = min(base_prob, 3)
    elif avg_cc_low < 5:
        base_prob *= 0.6
    elif avg_cc_low < 20:
        base_prob *= 0.85

    # RH override
    if avg_rh < 80:
        base_prob = min(base_prob, 10)
    elif avg_rh < 85:
        base_prob *= 0.85

    prob = min(95, max(3, int(base_prob)))

    # Sunshine rating
    sr_stars = calc_sunny_rating(lcl_ag, avg_cc_low, avg_vis)

    # Fog type
    fog_type = calc_fog_type(min_td_spread, max_rh, avg_ws, avg_cc_low)

    return {
        "prob": prob,
        "lcl": int(lcl_ag),
        "diff": int(diff),
        "fog_top": int(fog_top),
        "rh": int(max_rh),
        "ws": round(avg_ws, 1),
        "cc_low": round(avg_cc_low, 1),
        "sunny": sr_stars,
        "fog_type": fog_type,
        "data": morning_data,
        "score": round(score, 2),
    }

def stars(n):
    return "⭐" * n + "★" * (5 - n)

def main():
    print()
    print("=" * 80)
    print("6座张家口非官方峰 · 一周云海概率预测".center(80))
    print("=" * 80)
    print()

    # Set date range: 06-07 (Sat) to 06-13 (Fri)
    today = datetime.date(2026, 6, 7)
    dates = [(today + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    print(f"预测日期: {dates[0]} ~ {dates[-1]}")
    print(f"数据源: Open-Meteo ECMWF IFS 0.25°")
    print(f"峰数: {len(CUSTOM_PEAKS)}")
    print()

    # Pre-fetch all weather data
    print("获取数据:")
    all_data = {}
    for peak in CUSTOM_PEAKS:
        print(f"  {peak['name']} ({peak['lat']}, {peak['lon']}) ...", end=" ", flush=True)
        data = fetch_weather(peak, dates[0])
        if data:
            print(f"OK (elev={data.get('elevation', '?')}m)")
            all_data[peak["name"]] = data
        else:
            print("FAIL")
    print()

    # Compute probabilities
    print("计算概率:")
    all_results = {}
    for peak in CUSTOM_PEAKS:
        print(f"  {peak['name']} ...", end=" ", flush=True)
        data = all_data.get(peak["name"])
        if not data:
            print("NO DATA")
            continue
        results = {}
        for date_str in dates:
            r = calc_prob(peak, data, date_str)
            results[date_str] = r
        all_results[peak["name"]] = results
        print("OK")
    print()

    # Print probability matrix
    print("=" * 80)
    print("云海概率矩阵（%）".center(80))
    print("=" * 80)
    date_hdr = f"{'日期':^12}"
    peak_cols = {p["name"]: f"{p['name']:^10}" for p in CUSTOM_PEAKS}
    print(date_hdr + "".join(peak_cols.values()))
    print("-" * (12 + 10 * len(CUSTOM_PEAKS)))

    for date_str in dates:
        weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.date.fromisoformat(date_str).weekday()]
        row = f"{date_str[5:]}({weekday})"
        for peak in CUSTOM_PEAKS:
            r = all_results.get(peak["name"], {}).get(date_str)
            if r:
                prob = r["prob"]
                diff = r["diff"]
                if prob >= 55 and diff > 200:
                    cell = f"🟢{prob:>3}%"
                elif prob >= 40 and diff > 100:
                    cell = f"🟡{prob:>3}%"
                elif diff < 0:
                    cell = f"🔴{prob:>3}%"
                else:
                    cell = f"  {prob:>3}%"
                row += f"{cell:^10}"
            else:
                row += f"{'--':^10}"
        print(row)

    print()

    # Detailed analysis
    print("=" * 80)
    print("详细分析（逐日逐峰）".center(80))
    print("=" * 80)

    for date_str in dates:
        weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.date.fromisoformat(date_str).weekday()]
        print()
        print(f"{'─' * 80}")
        print(f"  📅 {date_str} ({weekday})")
        print(f"{'─' * 80}")

        for peak in CUSTOM_PEAKS:
            r = all_results.get(peak["name"], {}).get(date_str)
            if not r:
                print(f"      {peak['name']}: ❌ 数据缺失")
                continue

            prob = r["prob"]
            diff = r["diff"]
            rh = r["rh"]
            ws = r["ws"]
            cc_low = r["cc_low"]
            lcl = r["lcl"]
            sr = r["sunny"]
            fog_type = r["fog_type"]
            score = r["score"]

            if prob >= 55 and diff > 200:
                mark = "🟢"
            elif prob >= 40 and diff > 100:
                mark = "🟡"
            elif diff < 0:
                mark = "🔴"
            else:
                mark = "  "

            diff_str = f"↑+{diff}m" if diff > 0 else f"↓{diff}m"
            print(f"  {mark} {peak['name']:10}: {prob:>3}% | 险差{diff_str} | {fog_type} | RH={rh}% | WS={ws}km/h | cc_low={cc_low:.0f}% | LCL={lcl}m | {stars(sr)}")

        # Show hourly detail for best peaks
        day_probs = [(peak["name"], r["prob"], r["diff"], r) for peak in CUSTOM_PEAKS
                     for r in [all_results.get(peak["name"], {}).get(date_str)] if r]
        day_probs.sort(key=lambda x: -x[1])
        best = [x for x in day_probs if x[1] >= 40][:2]
        for name, prob, diff, r in best:
            if r["data"]:
                print()
                print(f"    【{name} 逐时数据 03:00-08:00】")
                print(f"    {'时间':^6} {'T':^7} {'RH%':^6} {'Td差':^6} {'风速':^8} {'LCL':^6} {'雾顶':^7} {'险差':^8} {'状态':^8}")
                print(f"    {'-' * 68}")
                for d in sorted(r["data"], key=lambda x: x["h"]):
                    if d["h"] not in range(3, 9):
                        continue
                    spread = d["T"] - d["Td"]
                    lcl_h = calc_lcl(d["T"], d["Td"])
                    station = all_data.get(name, {}).get("elevation", 1000)
                    fog_top_h = station + lcl_h + 150
                    diff_h = peak.get("summit_elev", 2000) - fog_top_h
                    st = "雾上" if diff_h > 0 else "雾中"
                    ds = f"↑+{diff_h:.0f}m" if diff_h > 0 else f"↓{diff_h:.0f}m"
                    print(f"    {d['h']:02d}:00  {d['T']:>5.1f}° {d['RH']:>5.0f}% {spread:>5.1f}° {d['ws']:>5.1f}km {lcl_h:>5.0f}m {fog_top_h:>6.0f}m {ds:>8} {st:^8}")

    # Summary
    print()
    print("=" * 80)
    print("一周推荐总结".center(80))
    print("=" * 80)
    print()

    # Best per peak
    print("各峰一周最佳日:")
    for peak in CUSTOM_PEAKS:
        results = all_results.get(peak["name"], {})
        valid = [(d, r) for d, r in results.items() if r and r["diff"] > 100 and r["prob"] >= 30]
        if valid:
            best_d, best_r = max(valid, key=lambda x: x[1]["prob"])
            weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.date.fromisoformat(best_d).weekday()]
            diff_str = f"↑+{best_r['diff']}m"
            print(f"  {peak['name']} ({peak['summit_elev']}m): {best_d} {weekday} {best_r['prob']}% {diff_str} [{best_r['fog_type']}]")
        else:
            print(f"  {peak['name']} ({peak['summit_elev']}m): 本周无>=30%窗口")

    print()
    # Global best days
    all_valid = []
    for date_str in dates:
        for peak in CUSTOM_PEAKS:
            r = all_results.get(peak["name"], {}).get(date_str)
            if r and r["diff"] > 100 and r["prob"] >= 40:
                all_valid.append((date_str, peak["name"], r["prob"], r["diff"], r["score"]))

    if all_valid:
        all_valid.sort(key=lambda x: -x[2])
        print("全局最佳（>=40%且险差>100m）:")
        for date_str, name, prob, diff, score in all_valid[:5]:
            weekday = ["周一","周二","周三","周四","周五","周六","周日"][datetime.date.fromisoformat(date_str).weekday()]
            diff_str = f"↑+{diff}m"
            print(f"  🥇 {date_str} {weekday} {name} {prob}% {diff_str} (12因子={score})")
    else:
        print("  本周无>=40%且险差>100m的推荐日")

    print()
    print("=" * 80)
    print(f"📌 数据: Open-Meteo ECMWF IFS | 站点海拔来自API elevation字段")
    print(f"   ⚠️ 简化12因子模型，精度低于主系统 | 建议出发前再确认")
    print("=" * 80)

if __name__ == "__main__":
    main()
