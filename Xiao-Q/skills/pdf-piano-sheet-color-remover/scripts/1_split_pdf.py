#!/usr/bin/env python3
"""
Step 1: Split PDF into individual pages
Usage: python3 1_split_pdf.py <input_pdf> <output_dir>
"""

from pypdf import PdfReader, PdfWriter
import os
import sys


def split_pdf(input_pdf, output_dir):
    """Split a PDF into individual pages"""
    os.makedirs(output_dir, exist_ok=True)
    
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    print(f"PDF total pages: {total_pages}")
    
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        
        output_filename = f"page_{i+1:03d}.pdf"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, "wb") as output:
            writer.write(output)
        
        print(f"Saved: {output_filename}")
    
    print(f"\nSplit complete! {total_pages} pages saved to {output_dir}")
    return total_pages


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 1_split_pdf.py <input_pdf> <output_dir>")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_dir = sys.argv[2]
    split_pdf(input_pdf, output_dir)
