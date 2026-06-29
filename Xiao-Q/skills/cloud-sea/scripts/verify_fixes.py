#!/usr/bin/env python3
"""验证AUDIT-007和无雾显示修复"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

# 1. 检查report_config中是否有"无雾"峰，验证显示逻辑
data_dir = r'C:\Users\86139\.qclaw\skills\cloud-sea\data'
config_files = [f for f in os.listdir(data_dir) if f.startswith('report_config')]
print(f"=== Report config files: {len(config_files)} ===")

# 找一个无雾日期的report_config验证
for cf in sorted(config_files)[-3:]:
    fpath = os.path.join(data_dir, cf)
    with open(fpath, 'r', encoding='utf-8') as f:
        config = json.load(f)
    ranked = config.get('ranked', [])
    no_fog_count = sum(1 for r in ranked if '无雾' in str(r.get('fog_type', '')))
    print(f"  {cf}: {len(ranked)} peaks, {no_fog_count} no-fog")

# 2. 检查妙峰山在peaks.json中的坐标
peaks_path = os.path.join(os.path.dirname(data_dir), 'references', 'peaks.json')
if os.path.exists(peaks_path):
    with open(peaks_path, 'r', encoding='utf-8') as f:
        peaks = json.load(f)
    for p in peaks:
        if '妙峰' in p.get('name', ''):
            print(f"\n=== 妙峰山坐标 ===")
            print(f"  name: {p['name']}")
            print(f"  lat: {p['lat']}, lon: {p['lon']}")
            print(f"  summit_elev: {p.get('summit_elev', '?')}")

# 3. 直接API验证妙峰山坐标对应的格点海拔
import urllib.request
lat, lon = 40.03, 116.0
url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,dew_point_2m,relative_humidity_2m,cloud_cover_low&start_date=2026-06-06&end_date=2026-06-06&timezone=Asia/Shanghai'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
api_data = json.load(resp)
elev = api_data.get('elevation')
h = api_data['hourly']
print(f"\n=== API直接调用 妙峰山(40.03,116.0) 海拔={elev}m ===")
print(f"{'时间':>8s} | {'T':>5s} | {'Td':>5s} | {'RH':>4s} | cc_low")
for i, t in enumerate(h['time']):
    hr = t[11:16]
    if hr in ['05:00','06:00','07:00','08:00']:
        T = h['temperature_2m'][i]
        Td = h['dew_point_2m'][i]
        RH = h['relative_humidity_2m'][i]
        ccl = h['cloud_cover_low'][i]
        print(f"{hr:>8s} | {T:>5.1f} | {Td:>5.1f} | {RH:>4.0f}% | {ccl}")

# 4. 对比weather_data JSON中的妙峰山数据
wd_path = os.path.join(data_dir, 'weather_data_2026-06-06.json')
if os.path.exists(wd_path):
    with open(wd_path, 'r', encoding='utf-8') as f:
        wd = json.load(f)
    peaks_data = wd.get('peaks', {})
    for pk, pv in peaks_data.items():
        if '妙峰' in str(pv.get('name', '')):
            print(f"\n=== weather_data JSON 妙峰山 ===")
            print(f"  station_elev: {pv.get('station_elev')}")
            hourly = pv.get('hourly', [])
            print(f"  hourly records: {len(hourly)}")
            for hr_data in hourly:
                t = hr_data.get('time', '')
                if any(t.endswith(x) for x in ['05:00','06:00','07:00','08:00']):
                    T = hr_data.get('temperature_2m')
                    Td = hr_data.get('dew_point_2m')
                    RH = hr_data.get('relative_humidity_2m')
                    ccl = hr_data.get('cloud_cover_low', hr_data.get('cc_low'))
                    print(f"  {t[11:16]} | T={T} Td={Td} RH={RH}% cc_low={ccl}")
