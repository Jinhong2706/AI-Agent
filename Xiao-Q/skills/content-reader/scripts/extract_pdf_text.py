#!/usr/bin/env python3
"""
PDF Text Extractor
Extracts text content from PDF files using pdfplumber.
"""

import sys
import os

def extract_pdf_text(pdf_path, output_path=None):
    """Extract text from PDF file"""
    try:
        import pdfplumber
        
        # Check if input file exists
        if not os.path.exists(pdf_path):
            print(f"Error: Input file '{pdf_path}' not found.")
            return False
        
        # Extract text from PDF
        text_content = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
        
        full_text = '\n\n'.join(text_content)
        
        # Output
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"Successfully extracted text from '{pdf_path}' to '{output_path}'")
            print(f"Total characters: {len(full_text)}")
        else:
            print(full_text)
        
        return True
        
    except ImportError:
        print("Error: pdfplumber library not installed.")
        print("Please install it with: pip install pdfplumber")
        return False
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 extract_pdf_text.py <input.pdf> [output.txt]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = extract_pdf_text(pdf_path, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
