#!/usr/bin/env python3
"""
Markdown to PDF Converter
Converts Markdown files to PDF format using markdown and weasyprint libraries.
"""

import sys
import os

def md_to_pdf(md_path, pdf_path):
    """Convert Markdown to PDF"""
    try:
        import markdown
        from weasyprint import HTML, CSS
        
        # Check if input file exists
        if not os.path.exists(md_path):
            print(f"Error: Input file '{md_path}' not found.")
            return False
        
        # Read Markdown file
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert to HTML
        html_content = markdown.markdown(md_content)
        
        # Add basic HTML structure with CSS
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted from Markdown</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
        
        # Convert HTML to PDF
        HTML(string=full_html).write_pdf(pdf_path)
        
        print(f"Successfully converted '{md_path}' to '{pdf_path}'")
        return True
        
    except ImportError as e:
        if 'weasyprint' in str(e):
            print("Error: weasyprint library not installed.")
            print("Please install it with: pip install weasyprint")
        elif 'markdown' in str(e):
            print("Error: markdown library not installed.")
            print("Please install it with: pip install markdown")
        else:
            print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 md_to_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    
    md_path = sys.argv[1]
    pdf_path = sys.argv[2]
    
    success = md_to_pdf(md_path, pdf_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
