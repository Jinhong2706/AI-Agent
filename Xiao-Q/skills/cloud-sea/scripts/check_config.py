"""Check report_config_2026-06-07.json"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

data_path = r'C:\Users\86139\.qclaw\skills\cloud-sea\data\report_config_2026-06-07.json'
if os.path.exists(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    ranked = d.get('ranked', [])
    print('=== report_config 06-07 ===')
    print(f'Target: {d.get("target_date", "?")}')
    for i, r in enumerate(ranked[:10], 1):
        name = r.get('peak_name', '?')
        score = r.get('score', '?')
        diff = r.get('diff_m', '?')
        fog = r.get('fog_type', '?')
        print(f'{i:2d}. {name:12s}| {str(score):3s}% | diff={diff}m | {fog}')
else:
    print('File not found')