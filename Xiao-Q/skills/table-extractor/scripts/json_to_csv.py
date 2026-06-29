#!/usr/bin/env python3
"""
JSON to CSV Converter
Converts JSON files to CSV format using pandas.
Supports multiple JSON formats (array, nested with data field, JSON Lines).
"""

import sys
import os
import json

def json_to_csv(json_path, csv_path):
    """Convert JSON file to CSV"""
    try:
        import pandas as pd
        
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
        
        # Handle different JSON structures
        if isinstance(data, dict):
            # Check if it has a 'data' or similar field containing an array
            array_fields = ['data', 'items', 'results', 'rows', 'records']
            for field in array_fields:
                if field in data and isinstance(data[field], list):
                    data = data[field]
                    break
            else:
                # Use the first array value found
                for value in data.values():
                    if isinstance(value, list) and len(value) > 0:
                        data = value
                        break
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"Successfully converted '{json_path}' to '{csv_path}'")
        print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        return True
        
    except ImportError:
        print("Error: pandas library not installed.")
        print("Please install it with: pip install pandas")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 json_to_csv.py <input.json> <output.csv>")
        sys.exit(1)
    
    json_path = sys.argv[1]
    csv_path = sys.argv[2]
    
    success = json_to_csv(json_path, csv_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
