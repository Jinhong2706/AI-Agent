#!/usr/bin/env python3
"""
Word to PDF Converter
Converts Word (.docx) files to PDF format using docx2pdf library.
"""

import sys
import os

def word_to_pdf(docx_path, pdf_path):
    """Convert Word document to PDF"""
    try:
        from docx2pdf import convert
        
        # Check if input file exists
        if not os.path.exists(docx_path):
            print(f"Error: Input file '{docx_path}' not found.")
            return False
        
        # Convert Word to PDF
        convert(docx_path, pdf_path)
        
        print(f"Successfully converted '{docx_path}' to '{pdf_path}'")
        return True
        
    except ImportError:
        print("Error: docx2pdf library not installed.")
        print("Please install it with: pip install docx2pdf")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 word_to_pdf.py <input.docx> <output.pdf>")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    pdf_path = sys.argv[2]
    
    success = word_to_pdf(docx_path, pdf_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
