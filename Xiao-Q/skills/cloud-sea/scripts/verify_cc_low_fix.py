#!/usr/bin/env python3
"""验证cc_low地形修正的效果对比"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

# 06-07 修正前后对比
print("=== 06-07 cc_low地形修正效果 ===")
print(f"{'峰名':8s} {'cc_low原始':>10s} {'cc_low修正':>10s} {'触发条件':>20s}")
print("-" * 55)

# 手动模拟修正逻辑
wd = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-07.json', 'r', encoding='utf-8'))
pk_data = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\references\peaks.json', 'r', encoding='utf-8'))
peaks_config = pk_data.get('peaks', [])
peak_entries = wd.get('peaks', {})

# PEAK_ELEVATIONS (from shared)
from cloud_sea_shared import PEAK_ELEVATIONS

for pk in peaks_config:
    name = pk['name']
    pd = peak_entries.get(name, {})
    api_elev = pd.get('elevation', 0)
    summit = PEAK_ELEVATIONS.get(name, api_elev)
    hourly = pd.get('hourly', [])
    
    cc_lows = [h.get('cloud_cover_low', 0) or 0 for h in hourly 
               if h.get('time', '').startswith('2026-06-07') and 0 <= int(h.get('time', 'T00:00')[11:13]) <= 8]
    cc_low_avg = sum(cc_lows) / len(cc_lows) if cc_lows else -1
    
    rh_vals = [h.get('RH_pct', 0) or 0 for h in hourly 
               if h.get('time', '').startswith('2026-06-07') and 0 <= int(h.get('time', 'T00:00')[11:13]) <= 6]
    rh_avg = sum(rh_vals) / len(rh_vals) if rh_vals else 0
    
    original = cc_low_avg
    adjusted = cc_low_avg
    trigger = ""
    
    if summit - api_elev > 500 and cc_low_avg >= 0 and cc_low_avg < 10:
        if rh_avg >= 90:
            adjusted = max(cc_low_avg, min(50, rh_avg - 50))
            trigger = f"RH替代(RH={rh_avg:.0f}%)"
        elif api_elev < 600:
            adjusted = max(cc_low_avg, 20)
            trigger = f"API海拔下限({api_elev:.0f}m)"
        elif api_elev < 1000 and rh_avg >= 85:
            adjusted = max(cc_low_avg, 15)
            trigger = f"中海拔+RH({api_elev:.0f}m,RH={rh_avg:.0f}%)"
    
    if adjusted != original:
        print(f"{name:8s} {original:>10.1f}% {adjusted:>10.1f}% {trigger:>20s}")
