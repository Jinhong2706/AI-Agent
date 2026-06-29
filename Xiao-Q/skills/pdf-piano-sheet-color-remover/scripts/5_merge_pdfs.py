#!/usr/bin/env python3
"""
Step 5: Merge multiple PDF files into a single PDF
Usage: python3 5_merge_pdfs.py <input_dir> <output_pdf>
"""

from pypdf import PdfWriter, PdfReader
import os
import sys


def merge_pdfs(input_dir, output_pdf):
    """Merge all PDF files in input directory into a single PDF"""
    # Get all PDF files and sort
    pdf_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.pdf')])
    
    print(f"Found {len(pdf_files)} PDF files, merging...")
    
    writer = PdfWriter()
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        reader = PdfReader(pdf_path)
        
        for page in reader.pages:
            writer.add_page(page)
        
        print(f"  Added: {pdf_file}")
    
    # Save merged PDF
    with open(output_pdf, "wb") as output:
        writer.write(output)
    
    print(f"\nMerge complete!")
    print(f"Output: {output_pdf}")
    print(f"Total pages: {len(writer.pages)}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 5_merge_pdfs.py <input_dir> <output_pdf>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_pdf = sys.argv[2]
    merge_pdfs(input_dir, output_pdf)
