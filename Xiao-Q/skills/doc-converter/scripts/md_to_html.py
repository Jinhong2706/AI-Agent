#!/usr/bin/env python3
"""
Markdown to HTML Converter
Converts Markdown files to HTML format using markdown library.
"""

import sys
import os

def md_to_html(md_path, html_path):
    """Convert Markdown to HTML"""
    try:
        import markdown
        
        # Check if input file exists
        if not os.path.exists(md_path):
            print(f"Error: Input file '{md_path}' not found.")
            return False
        
        # Read Markdown file
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert to HTML
        html_content = markdown.markdown(md_content)
        
        # Add basic HTML structure
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted from Markdown</title>
</head>
<body>
{html_content}
</body>
</html>"""
        
        # Write HTML file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"Successfully converted '{md_path}' to '{html_path}'")
        return True
        
    except ImportError:
        print("Error: markdown library not installed.")
        print("Please install it with: pip install markdown")
        return False
    except Exception as e:
        print(f"Error during conversion: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 md_to_html.py <input.md> <output.html>")
        sys.exit(1)
    
    md_path = sys.argv[1]
    html_path = sys.argv[2]
    
    success = md_to_html(md_path, html_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
