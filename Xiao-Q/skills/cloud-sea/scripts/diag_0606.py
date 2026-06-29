#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

wd = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-06.json', 'r', encoding='utf-8'))
peaks = wd.get('peaks', {})
summary = wd.get('summary', {})

print("=" * 70)
print("06-06 核心问题诊断")
print("=" * 70)

# 问题1: 雨天分析
print("\n### 06-06 凌晨(00-08h)雨天统计")
for name in ['长峪城', '妙峰山', '海坨山', '白草畔', '白石山', '雾灵山', '百花山', '东灵山', '北灵山', '云蒙山', '东指壶', '海坨山', '金山岭长城', '箭扣长城', '黄草梁', '西南灵山']:
    pk = peaks.get(name, {})
    hourly = pk.get('hourly', [])
    rain_hours = 0
    total_precip = 0
    for h in hourly:
        t = h.get('time', '')
        if t.startswith('2026-06-06'):
            hr = int(t[11:13])
            if 0 <= hr <= 8:
                wmo = h.get('weather_code', 0)
                precip = h.get('precipitation', 0) or 0
                total_precip += precip
                if wmo >= 51:
                    rain_hours += 1
    clear_ratio = max(0, 1 - rain_hours / 9)
    print(f"  {name:8s}: 雨时={rain_hours}/9h 降水={total_precip:.1f}mm clear_ratio={clear_ratio:.2f}")

# 问题2: 长峪城概率异常
print("\n### 长峪城 summary 关键字段")
s = summary.get('长峪城', {})
for k, v in sorted(s.items()):
    print(f"  {k}: {v}")

# 问题3: cc_low对比
print("\n### 长峪城 vs 白草畔 凌晨cc_low")
for name in ['长峪城', '白草畔', '妙峰山', '白石山']:
    pk = peaks.get(name, {})
    hourly = pk.get('hourly', [])
    cc_lows = []
    for h in hourly:
        t = h.get('time', '')
        if t.startswith('2026-06-06'):
            hr = int(t[11:13])
            if 0 <= hr <= 8:
                cc_low = h.get('cloud_cover_low', 0) or 0
                cc_lows.append(cc_low)
    avg = sum(cc_lows) / len(cc_lows) if cc_lows else 0
    print(f"  {name:8s}: cc_low逐时={cc_lows} avg={avg:.1f}%")
