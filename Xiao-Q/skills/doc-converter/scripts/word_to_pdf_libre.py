#!/usr/bin/env python3
"""
Word to PDF Converter (LibreOffice version)
Converts Word (.docx) files to PDF format using LibreOffice.
Works on Linux/macOS without Microsoft Word.
"""

import sys
import os
import subprocess

def word_to_pdf(docx_path, pdf_path):
    """Convert Word document to PDF using LibreOffice"""
    try:
        # Check if input file exists
        if not os.path.exists(docx_path):
            print(f"Error: Input file '{docx_path}' not found.")
            return False
        
        # Get absolute paths
        docx_abs = os.path.abspath(docx_path)
        output_dir = os.path.dirname(os.path.abspath(pdf_path))
        pdf_filename = os.path.basename(pdf_path)
        
        # Use LibreOffice to convert
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_dir,
            docx_abs
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error during conversion: {result.stderr}")
            return False
        
        # LibreOffice creates PDF with same name as input
        # Rename if necessary
        generated_pdf = os.path.join(output_dir, 
                                     os.path.splitext(os.path.basename(docx_path))[0] + '.pdf')
        
        if os.path.exists(generated_pdf) and generated_pdf != os.path.abspath(pdf_path):
            os.rename(generated_pdf, os.path.abspath(pdf_path))
        
        print(f"Successfully converted '{docx_path}' to '{pdf_path}'")
        return True
        
    except FileNotFoundError:
        print("Error: LibreOffice not installed.")
        print("Please install it with: sudo apt-get install libreoffice")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 word_to_pdf_libre.py <input.docx> <output.pdf>")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    pdf_path = sys.argv[2]
    
    success = word_to_pdf(docx_path, pdf_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
