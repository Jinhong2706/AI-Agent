#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

pk_data = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\references\peaks.json', 'r', encoding='utf-8'))
peaks = pk_data.get('peaks', [])
wd = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-06.json', 'r', encoding='utf-8'))

# 从weather_data获取API格点海拔
peak_entries = wd.get('peaks', {})

print("=" * 90)
print("16峰 API格点海拔 vs 山顶海拔 vs cc_low可靠性分析")
print("=" * 90)
print(f"{'峰名':8s} {'山顶m':>6s} {'API格点m':>8s} {'差值m':>6s} {'cc_low凌晨均值%':>14s} {'可靠性':>6s}")
print("-" * 70)

for pk in peaks:
    name = pk['name']
    summit = pk.get('summit_elev', 0)
    
    pd = peak_entries.get(name, {})
    api_elev = pd.get('elevation', 0)
    diff = summit - api_elev
    
    hourly = pd.get('hourly', [])
    cc_lows = [h.get('cloud_cover_low', 0) or 0 for h in hourly 
               if h.get('time','').startswith('2026-06-06') and 0 <= int(h.get('time','T00:00')[11:13]) <= 8]
    cc_low_avg = sum(cc_lows) / len(cc_lows) if cc_lows else -1
    
    if diff < 300:
        rel = "OK"
    elif diff < 600:
        rel = "WARN"
    else:
        rel = "BAD"
    
    print(f"{name:8s} {summit:>6d} {api_elev:>8.0f} {diff:>6d} {cc_low_avg:>14.1f} {rel:>6s}")
