#!/usr/bin/env python3
"""
JSON Data Reader
Reads and displays JSON data with optional summary.
"""

import sys
import os
import json
import pandas as pd

def read_json(json_path, summary=False):
    """Read and display JSON data"""
    try:
        # Check if input file exists
        if not os.path.exists(json_path):
            print(f"Error: Input file '{json_path}' not found.")
            return False
        
        # Read JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                # Try JSON Lines format
                f.seek(0)
                data = [json.loads(line) for line in f if line.strip()]
        
        # Convert to DataFrame for easier handling
        if isinstance(data, dict):
            # Check if it has a data field
            array_fields = ['data', 'items', 'results', 'rows', 'records']
            for field in array_fields:
                if field in data and isinstance(data[field], list):
                    data = data[field]
                    break
            else:
                # Use first array value
                for value in data.values():
                    if isinstance(value, list) and len(value) > 0:
                        data = value
                        break
        
        df = pd.DataFrame(data)
        
        # Output
        if summary:
            print(f"File: {json_path}")
            print(f"Rows: {len(df)}")
            print(f"Columns: {len(df.columns)}")
            print(f"Column names: {', '.join(df.columns.tolist())}")
            print(f"\nData types:")
            print(df.dtypes)
            print(f"\nFirst 5 rows:")
            print(df.head())
        else:
            print(df.to_string())
        
        return True
        
    except ImportError:
        print("Error: pandas library not installed.")
        print("Please install it with: pip install pandas")
        return False
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 read_json.py <input.json> [--summary]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    summary = '--summary' in sys.argv
    
    success = read_json(json_path, summary)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
