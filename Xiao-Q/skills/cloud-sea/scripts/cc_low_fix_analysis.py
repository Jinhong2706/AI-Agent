#!/usr/bin/env python3
"""分析cc_low修正方案：海拔加权插值 + RH替代法"""
import json, sys, math
sys.stdout.reconfigure(encoding='utf-8')

wd = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-07.json', 'r', encoding='utf-8'))
pk_data = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\references\peaks.json', 'r', encoding='utf-8'))
peaks = pk_data.get('peaks', [])
peak_entries = wd.get('peaks', {})

# 构建分析数据
entries = []
for pk in peaks:
    name = pk['name']
    pd = peak_entries.get(name, {})
    hourly = pd.get('hourly', [])
    api_elev = pd.get('elevation', 0)
    summit = pk.get('summit_elev', 0)
    
    cc_lows = [h.get('cloud_cover_low', 0) or 0 for h in hourly 
               if h.get('time', '').startswith('2026-06-07') and 0 <= int(h.get('time', 'T00:00')[11:13]) <= 8]
    cc_low_avg = sum(cc_lows) / len(cc_lows) if cc_lows else -1
    
    rh_vals = [h.get('RH_pct', h.get('relative_humidity_2m', 0)) or 0 for h in hourly 
               if h.get('time', '').startswith('2026-06-07') and 0 <= int(h.get('time', 'T00:00')[11:13]) <= 8]
    rh_avg = sum(rh_vals) / len(rh_vals) if rh_vals else 0
    
    entries.append({
        'name': name, 'lat': pk.get('latitude', 0), 'lon': pk.get('longitude', 0),
        'api_elev': api_elev, 'summit': summit, 'cc_low_avg': cc_low_avg, 'rh_avg': rh_avg
    })

good = [e for e in entries if e['cc_low_avg'] >= 10]
bad = [e for e in entries if e['cc_low_avg'] < 10]

print("=== 方案1: 邻近高海拔站cc_low插值 ===")
for e in bad:
    best = None
    best_dist = 999
    for g in good:
        dist = math.sqrt((e['lat']-g['lat'])**2 + (e['lon']-g['lon'])**2) * 111
        if dist < best_dist:
            best_dist = dist
            best = g
    
    # 海拔修正因子：如果目标站API海拔更高，cc_low应该更高
    elev_ratio = e['api_elev'] / best['api_elev'] if best['api_elev'] > 0 else 1
    estimated_cc_low = best['cc_low_avg'] * min(elev_ratio, 1.5)  # 上限1.5倍
    
    print(f"  {e['name']:8s} api={e['api_elev']:.0f}m cc_low_real={e['cc_low_avg']:.1f}% "
          f"-> 参考: {best['name']}(cc_low={best['cc_low_avg']:.1f}%, api={best['api_elev']:.0f}m, "
          f"距{best_dist:.0f}km) -> 估算cc_low={estimated_cc_low:.1f}%")

print()
print("=== 方案2: RH替代法 (RH>=90%时强制cc_low=30%) ===")
for e in entries:
    if e['cc_low_avg'] < 10 and e['rh_avg'] >= 85:
        suggested = min(50, max(20, e['rh_avg'] - 50))  # RH 90%->40%, RH 95%->45%, RH 100%->50%
        print(f"  {e['name']:8s} cc_low={e['cc_low_avg']:.1f}% rh_avg={e['rh_avg']:.0f}% "
              f"-> RH>=85%强制cc_low={suggested:.0f}%")

print()
print("=== 方案3: 基于API海拔的cc_low下限 ===")
for e in entries:
    if e['api_elev'] < 600:
        floor = 20  # 平原站cc_low下限20%
    elif e['api_elev'] < 1000:
        floor = 15
    else:
        floor = 0   # 高海拔站数据可信
    adjusted = max(e['cc_low_avg'], floor)
    if adjusted != e['cc_low_avg']:
        print(f"  {e['name']:8s} cc_low={e['cc_low_avg']:.1f}% -> 下限修正={adjusted:.1f}% (api_elev={e['api_elev']:.0f}m)")
