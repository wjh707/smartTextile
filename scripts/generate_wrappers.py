#!/usr/bin/env python3
"""
Generate JS wrapper files for each JSON data file in the data/ directory.
Output goes to dashboard/data_*.js for loading via <script> tags in static HTML.
"""
import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard')

# Map of JSON file -> JS variable name -> data property path
FILE_CONFIG = {
    'company_news.json': {
        'var': 'COMPANY_NEWS_DATA',
        'wrap': True,  # JSON is {"records": [...]}
    },
    'policy_data.json': {
        'var': 'POLICY_DATA',
        'wrap': True,  # JSON is {"records": [...]}
    },
    'smart_textile_data.json': {
        'var': 'SMART_TEXTILE_DATA',
        'wrap': True,  # JSON is {"records": [...]}
    },
    'papers.json': {
        'var': 'PAPERS_DATA',
        'wrap': False,  # JSON is just an array [...], wrap in {"records": [...]}
    },
    'standards.json': {
        'var': 'STANDARDS_DATA',
        'wrap': True,  # JSON is {"standards": [...]}
    },
}

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    for fname, config in FILE_CONFIG.items():
        src_path = os.path.join(DATA_DIR, fname)
        if not os.path.exists(src_path):
            print(f"WARNING: {src_path} not found, skipping.")
            continue

        with open(src_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle papers.json which is a raw array
        if not config['wrap'] and isinstance(data, list):
            data = {'records': data}

        out_name = f"data_{fname.replace('.json', '.js')}"
        out_path = os.path.join(OUT_DIR, out_name)

        var_name = config['var']
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        js_content = f"window.{var_name} = {json_str};\n"

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(js_content)

        # Count records
        if 'records' in data:
            count = len(data['records'])
        elif 'standards' in data:
            count = len(data['standards'])
        else:
            count = '?'
        print(f"✓ {out_name} (var={var_name}, {count} records)")

    print("\nDone! All JS wrappers generated.")

if __name__ == '__main__':
    main()
