#!/usr/bin/env python3
"""验证妙峰山数据一致性 + AUDIT-007修复验证"""
import json, sys, urllib.request
sys.stdout.reconfigure(encoding='utf-8')

data_dir = r'C:\Users\86139\.qclaw\skills\cloud-sea\data'

# 1. 直接API调用妙峰山
lat, lon = 40.03, 116.0
url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,dew_point_2m,relative_humidity_2m,cloud_cover_low,weather_code,wind_speed_10m&start_date=2026-06-06&end_date=2026-06-06&timezone=Asia/Shanghai'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
api_data = json.load(resp)
elev = api_data.get('elevation')
h = api_data['hourly']
print(f"=== API direct: lat={lat} lon={lon} elevation={elev}m ===")
for i, t in enumerate(h['time']):
    hr = t[11:16]
    if hr in ['05:00','06:00','07:00','08:00']:
        print(f"  {hr} | T={h['temperature_2m'][i]:.1f} | Td={h['dew_point_2m'][i]:.1f} | RH={h['relative_humidity_2m'][i]:.0f} | cc_low={h['cloud_cover_low'][i]} | wmo={h['weather_code'][i]} | wind={h['wind_speed_10m'][i]}")

# 2. weather_data JSON
wd_path = f'{data_dir}\\weather_data_2026-06-06.json'
with open(wd_path, 'r', encoding='utf-8') as f:
    wd = json.load(f)
peaks_data = wd.get('peaks', {})
for pk, pv in peaks_data.items():
    name = pv.get('name', '')
    if '妙峰' in name:
        print(f"\n=== weather_data JSON: {name} station_elev={pv.get('station_elev')} ===")
        hourly = pv.get('hourly', [])
        for hr_data in hourly:
            t = str(hr_data.get('time', ''))
            if any(t.endswith(x) for x in ['05:00','06:00','07:00','08:00']):
                T = hr_data.get('temperature_2m')
                Td = hr_data.get('dew_point_2m')
                RH = hr_data.get('relative_humidity_2m')
                ccl = hr_data.get('cloud_cover_low', hr_data.get('cc_low'))
                wmo = hr_data.get('weather_code')
                wind = hr_data.get('wind_speed_10m')
                print(f"  {t[11:16]} | T={T} | Td={Td} | RH={RH} | cc_low={ccl} | wmo={wmo} | wind={wind}")

# 3. AUDIT-007: 检查无雾峰的report_config
rc_path = f'{data_dir}\\report_config_2026-06-06.json'
with open(rc_path, 'r', encoding='utf-8') as f:
    rc = json.load(f)
ranked = rc.get('ranked', [])
print(f"\n=== Report config 06-06: {len(ranked)} peaks ===")
for r in ranked:
    ft = r.get('fog_type', '')
    if isinstance(ft, (list, tuple)):
        ft = ft[1] if len(ft) > 1 else str(ft)
    prob = r.get('prob_pct', 0)
    diff = r.get('diff', r.get('summit_diff_m', 0))
    print(f"  {r.get('name','?'):8s} | prob={prob:3d}% | fog_type={ft} | diff={diff}")
