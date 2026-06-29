#!/usr/bin/env python3
"""
RSDK Script Syntax Validator
Validates RSDK script syntax for common errors.
"""

import re
import sys
import os

def validate_rsdk_script(file_path):
    """Validate an RSDK script file for syntax errors."""
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    errors = []
    warnings = []
    
    # Check for required functions
    required_funcs = ['Create', 'Update']
    for func in required_funcs:
        if f"{func}:" not in content:
            warnings.append(f"Missing recommended function: {func}()")
    
    # Check for common syntax issues
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check for missing 'return' at end of functions
        if stripped and not stripped.startswith('//') and not stripped.startswith(';'):
            # Check if line ends function block (no return)
            if i < len(lines):
                next_line = lines[i].strip()
                if next_line and not next_line.startswith('//'):
                    if re.match(r'^[A-Za-z_]+\(\):', stripped):
                        # This is a function definition
                        pass
    
    # Check for unclosed conditionals
    conditional_stack = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track if/endif blocks
        if re.match(r'^\s*if\s+', stripped):
            conditional_stack.append(('if', i))
        elif re.match(r'^\s*elif\s+', stripped):
            if conditional_stack and conditional_stack[-1][0] == 'if':
                pass  # Valid
            else:
                errors.append(f"Line {i}: 'elif' without matching 'if'")
        elif stripped == 'endif':
            if conditional_stack:
                conditional_stack.pop()
            else:
                errors.append(f"Line {i}: 'endif' without matching 'if'")
    
    # Check for unclosed conditionals
    for cond_type, line_num in conditional_stack:
        errors.append(f"Line {line_num}: Unclosed '{cond_type}' block (missing 'endif')")
    
    # Check for common RSDK mistakes
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Check for = instead of == in conditions
        if re.search(r'\bif\s+\w+\s*=\s*\w+', stripped):
            warnings.append(f"Line {i}: Possible assignment (=) instead of comparison (==) in 'if' condition")
        
        # Check for missing self. prefix
        if re.search(r'\b(position|velocity|direction|active|visible)\s*=', stripped):
            if 'self.' not in stripped:
                warnings.append(f"Line {i}: Possible missing 'self.' prefix for object property")
    
    # Print results
    print(f"\n{'='*50}")
    print(f"Validation Results for: {file_path}")
    print(f"{'='*50}")
    
    if errors:
        print(f"\n❌ Errors ({len(errors)}):")
        for err in errors:
            print(f"  {err}")
    else:
        print("\n✅ No errors found")
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for warn in warnings:
            print(f"  {warn}")
    
    print(f"\n{'='*50}")
    if not errors:
        print("✅ Script validation PASSED")
        return True
    else:
        print("❌ Script validation FAILED")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_syntax.py <script_file>")
        print("\nExample:")
        print("  python validate_syntax.py Obj_NewEnemy.txt")
        sys.exit(1)
    
    script_file = sys.argv[1]
    success = validate_rsdk_script(script_file)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
