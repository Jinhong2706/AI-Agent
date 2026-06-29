#!/usr/bin/env python3
"""Clean '[已修正]' suffix from fog_type in all JSON data and fix the source in analyzer.py"""
import json, os, re

# STEP 1: Clean all report_config JSON files
data_dir = '../data'
fixed_files = 0
for fname in os.listdir(data_dir):
    if not fname.startswith('report_config_') or not fname.endswith('.json'):
        continue
    fpath = os.path.join(data_dir, fname)
    data = json.load(open(fpath, encoding='utf-8'))
    modified = False
    for peak in data.get('ranked', []):
        ft = peak.get('fog_type', '')
        if isinstance(ft, str) and '[已修正]' in ft:
            peak['fog_type'] = ft.replace('[已修正]', '')
            modified = True
            print(f'  Cleaned {fname}: {ft} -> {peak["fog_type"]}')
        # Also check fog_type_raw (might be a tuple/list stored as list in JSON)
        ftr = peak.get('fog_type_raw')
        if isinstance(ftr, list) and len(ftr) >= 2:
            if isinstance(ftr[1], str) and '[已修正]' in ftr[1]:
                ftr[1] = ftr[1].replace('[已修正]', '')
                modified = True
                print(f'  Cleaned fog_type_raw in {fname}')
    if modified:
        json.dump(data, open(fpath, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'  Saved {fname}')
        fixed_files += 1
    else:
        print(f'  No change: {fname}')
print(f'\nDone. Fixed {fixed_files} files.')

# STEP 2: Find and fix the source in analyzer.py
print('\n--- Searching analyzer.py for [已修正] source ---')
content = open('analyzer.py', encoding='utf-8').read()
# Check if it's in the file
if '[已修正]' in content:
    print('FOUND in analyzer.py! Locating...')
    pos = content.find('[已修正]')
    line_num = content[:pos].count('\n') + 1
    print(f'  Line {line_num}: ...{repr(content[max(0,pos-60):pos+20])}...')
    print('  Will fix this line.')
else:
    print('NOT FOUND in analyzer.py source code.')
    print('  The [已修正] suffix may be added dynamically or in a different file.')
    # Check cloud_sea_shared.py
    if os.path.exists('../cloud_sea_shared.py'):
        shared = open('../cloud_sea_shared.py', encoding='utf-8').read()
        if '[已修正]' in shared:
            print('  FOUND in cloud_sea_shared.py!')
        else:
            print('  NOT in cloud_sea_shared.py either.')
