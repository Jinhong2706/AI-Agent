#!/usr/bin/env python3
"""
Word Text Extractor
Extracts text content from Word (.docx) files using python-docx.
"""

import sys
import os

def extract_word_text(docx_path, output_path=None):
    """Extract text from Word document"""
    try:
        from docx import Document
        
        # Check if input file exists
        if not os.path.exists(docx_path):
            print(f"Error: Input file '{docx_path}' not found.")
            return False
        
        # Open Word document
        doc = Document(docx_path)
        
        # Extract text from all paragraphs
        text_content = []
        for para in doc.paragraphs:
            if para.text.strip():  # Skip empty paragraphs
                text_content.append(para.text)
        
        full_text = '\n'.join(text_content)
        
        # Output
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"Successfully extracted text from '{docx_path}' to '{output_path}'")
            print(f"Total characters: {len(full_text)}")
            print(f"Total paragraphs: {len(text_content)}")
        else:
            print(full_text)
        
        return True
        
    except ImportError:
        print("Error: python-docx library not installed.")
        print("Please install it with: pip install python-docx")
        return False
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 extract_word_text.py <input.docx> [output.txt]")
        sys.exit(1)
    
    docx_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = extract_word_text(docx_path, output_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
