#!/usr/bin/env python3
"""Test batch API"""
import requests, sys, json
sys.stdout.reconfigure(encoding='utf-8')

params = {
    'latitude': '40.03,40.57',
    'longitude': '116.0,115.78',
    'hourly': 'temperature_2m,dew_point_2m',
    'models': 'ecmwf_ifs025',
    'forecast_days': 7,
    'timezone': 'Asia/Shanghai',
}
try:
    r = requests.get('https://api.open-meteo.com/v1/forecast', params=params, timeout=60)
    print(f'Status: {r.status_code}')
    if r.status_code != 200:
        print(f'Error: {r.text[:500]}')
    else:
        data = r.json()
        if isinstance(data, list):
            print(f'Response is list, len={len(data)}')
            for i, d in enumerate(data):
                print(f'  [{i}] elev={d.get("elevation")}, hourly_count={len(d.get("hourly",{}).get("time",[]))}')
        else:
            print(f'Response is dict, keys={list(data.keys())[:5]}')
except Exception as e:
    print(f'Exception: {e}')
