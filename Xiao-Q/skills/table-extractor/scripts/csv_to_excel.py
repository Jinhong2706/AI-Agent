#!/usr/bin/env python3
"""
CSV to Excel Converter
Converts CSV files to Excel (.xlsx) format using pandas.
"""

import sys
import os

def csv_to_excel(csv_path, excel_path):
    """Convert CSV file to Excel"""
    try:
        import pandas as pd
        
        # Check if input file exists
        if not os.path.exists(csv_path):
            print(f"Error: Input file '{csv_path}' not found.")
            return False
        
        # Read CSV file
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # Write to Excel
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        print(f"Successfully converted '{csv_path}' to '{excel_path}'")
        print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        return True
        
    except ImportError:
        print("Error: pandas or openpyxl library not installed.")
        print("Please install it with: pip install pandas openpyxl")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 csv_to_excel.py <input.csv> <output.xlsx>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    excel_path = sys.argv[2]
    
    success = csv_to_excel(csv_path, excel_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
