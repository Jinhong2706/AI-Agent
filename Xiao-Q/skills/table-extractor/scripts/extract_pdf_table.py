#!/usr/bin/env python3
"""
PDF Table Extractor
Extracts tables from PDF files and saves to Excel using pdfplumber.
"""

import sys
import os

def extract_pdf_table(pdf_path, excel_path):
    """Extract tables from PDF and save to Excel"""
    try:
        import pdfplumber
        import pandas as pd
        
        # Check if input file exists
        if not os.path.exists(pdf_path):
            print(f"Error: Input file '{pdf_path}' not found.")
            return False
        
        # Extract tables from PDF
        tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_tables = page.extract_tables()
                for j, table in enumerate(page_tables):
                    if table:  # Only add non-empty tables
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables.append({
                            'page': i + 1,
                            'table': j + 1,
                            'data': df
                        })
        
        if not tables:
            print("No tables found in the PDF.")
            return False
        
        # Save to Excel with multiple sheets if multiple tables
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for idx, table_info in enumerate(tables):
                sheet_name = f"Table_{idx + 1}" if len(tables) > 1 else "Sheet1"
                table_info['data'].to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"Successfully extracted {len(tables)} table(s) from '{pdf_path}' to '{excel_path}'")
        for table_info in tables:
            print(f"  - Page {table_info['page']}, Table {table_info['table']}: {len(table_info['data'])} rows")
        return True
        
    except ImportError as e:
        if 'pdfplumber' in str(e):
            print("Error: pdfplumber library not installed.")
            print("Please install it with: pip install pdfplumber")
        elif 'pandas' in str(e) or 'openpyxl' in str(e):
            print("Error: pandas or openpyxl library not installed.")
            print("Please install it with: pip install pandas openpyxl")
        else:
            print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 extract_pdf_table.py <input.pdf> <output.xlsx>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    excel_path = sys.argv[2]
    
    success = extract_pdf_table(pdf_path, excel_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
