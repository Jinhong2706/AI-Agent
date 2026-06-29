#!/usr/bin/env python3
"""
HTML to Markdown Converter
Converts HTML files to Markdown format using html2text library.
"""

import sys
import os

def html_to_md(html_path, md_path):
    """Convert HTML to Markdown"""
    try:
        import html2text
        
        # Check if input file exists
        if not os.path.exists(html_path):
            print(f"Error: Input file '{html_path}' not found.")
            return False
        
        # Read HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Convert to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.body_width = 0  # Don't wrap lines
        md_content = h.handle(html_content)
        
        # Write Markdown file
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"Successfully converted '{html_path}' to '{md_path}'")
        return True
        
    except ImportError:
        print("Error: html2text library not installed.")
        print("Please install it with: pip install html2text")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 html_to_md.py <input.html> <output.md>")
        sys.exit(1)
    
    html_path = sys.argv[1]
    md_path = sys.argv[2]
    
    success = html_to_md(html_path, md_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
