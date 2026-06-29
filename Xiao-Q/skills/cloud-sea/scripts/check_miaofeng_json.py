#!/usr/bin/env python3
"""检查weather_data JSON中妙峰山的原始数据"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\weather_data_2026-06-06.json','r',encoding='utf-8') as f:
    data = json.load(f)

print("=== weather_data JSON keys ===")
for k, v in data.items():
    if isinstance(v, dict):
        name = v.get('name', '?')
        pid = v.get('id', '?')
        print(f"  key='{k}' -> name={name}, id={pid}")
        # 检查妙峰山
        if '妙峰' in str(name) or 'miaofeng' in str(pid).lower():
            print(f"\n=== FOUND: {name} (key={k}) ===")
            print(f"  station_elev = {v.get('station_elev')}")
            if 'hourly' in v:
                print(f"  hourly count = {len(v['hourly'])}")
                for h in v['hourly']:
                    t = h.get('time', '')
                    if '05:' in t or '06:' in t or '07:' in t or '08:' in t:
                        T = h.get('temperature_2m')
                        Td = h.get('dew_point_2m')
                        RH = h.get('relative_humidity_2m')
                        ccl = h.get('cloud_cover_low', h.get('cc_low'))
                        wmo = h.get('weather_code')
                        print(f"  {t[11:16]} | T={T} Td={Td} RH={RH} cc_low={ccl} wmo={wmo}")
            if 'summary' in v:
                s = v['summary']
                print(f"  summary: RH_max={s.get('rh_morning_max')} cc_low_avg={s.get('cc_low_avg','?')}")
