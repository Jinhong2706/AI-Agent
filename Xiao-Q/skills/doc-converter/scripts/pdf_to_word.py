#!/usr/bin/env python3
"""
PDF to Word Converter
Converts PDF files to Word (.docx) format using pdf2docx library.
"""

import sys
import os

def pdf_to_word(pdf_path, docx_path):
    """Convert PDF to Word document"""
    try:
        from pdf2docx import Converter
        
        # Check if input file exists
        if not os.path.exists(pdf_path):
            print(f"Error: Input file '{pdf_path}' not found.")
            return False
        
        # Convert PDF to Word
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        
        print(f"Successfully converted '{pdf_path}' to '{docx_path}'")
        return True
        
    except ImportError:
        print("Error: pdf2docx library not installed.")
        print("Please install it with: pip install pdf2docx")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 pdf_to_word.py <input.pdf> <output.docx>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    docx_path = sys.argv[2]
    
    success = pdf_to_word(pdf_path, docx_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
