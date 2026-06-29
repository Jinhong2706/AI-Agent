#!/usr/bin/env python3
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
rc = json.load(open(r'C:\Users\86139\.qclaw\skills\cloud-sea\data\report_config_2026-06-03.json', 'r', encoding='utf-8'))
ranked = rc.get('ranked', [])
print(f"=== 2026-06-03 云海预测排名 ({len(ranked)}峰) ===")
for i, r in enumerate(ranked):
    name = r.get('name', '?')
    score = r.get('score', 0)
    diff = r.get('diff', 0)
    fog_type = r.get('fog_type', '')
    print(f"  {i+1:2d}. {name:8s} | {score:3d}% | diff={diff}m | {fog_type}")
