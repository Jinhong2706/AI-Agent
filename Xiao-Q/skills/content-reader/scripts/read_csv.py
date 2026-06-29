#!/usr/bin/env python3
"""
CSV Data Reader
Reads and displays CSV data with optional summary and head.
"""

import sys
import os
import pandas as pd

def read_csv(csv_path, summary=False, head=10):
    """Read and display CSV data"""
    try:
        # Check if input file exists
        if not os.path.exists(csv_path):
            print(f"Error: Input file '{csv_path}' not found.")
            return False
        
        # Read CSV file
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # Output
        if summary:
            print(f"File: {csv_path}")
            print(f"Rows: {len(df)}")
            print(f"Columns: {len(df.columns)}")
            print(f"Column names: {', '.join(df.columns.tolist())}")
            print(f"\nData types:")
            print(df.dtypes)
            print(f"\nFirst {min(head, len(df))} rows:")
            print(df.head(head))
        else:
            print(df.head(head).to_string())
        
        return True
        
    except ImportError:
        print("Error: pandas library not installed.")
        print("Please install it with: pip install pandas")
        return False
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 read_csv.py <input.csv> [--summary] [--head N]")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    summary = '--summary' in sys.argv
    
    head = 10  # default
    if '--head' in sys.argv:
        idx = sys.argv.index('--head')
        if idx + 1 < len(sys.argv):
            try:
                head = int(sys.argv[idx + 1])
            except ValueError:
                print("Error: --head requires a number")
                sys.exit(1)
    
    success = read_csv(csv_path, summary, head)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
