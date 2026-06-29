#!/usr/bin/env python3
"""
Excel to CSV Converter
Converts Excel (.xlsx) files to CSV format using pandas.
"""

import sys
import os

def excel_to_csv(excel_path, csv_path):
    """Convert Excel file to CSV"""
    try:
        import pandas as pd
        
        # Check if input file exists
        if not os.path.exists(excel_path):
            print(f"Error: Input file '{excel_path}' not found.")
            return False
        
        # Read Excel file (first sheet by default)
        df = pd.read_excel(excel_path, sheet_name=0)
        
        # Write to CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        print(f"Successfully converted '{excel_path}' to '{csv_path}'")
        print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
        return True
        
    except ImportError:
        print("Error: pandas library not installed.")
        print("Please install it with: pip install pandas openpyxl")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 excel_to_csv.py <input.xlsx> <output.csv>")
        sys.exit(1)
    
    excel_path = sys.argv[1]
    csv_path = sys.argv[2]
    
    success = excel_to_csv(excel_path, csv_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
