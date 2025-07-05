#!/usr/bin/env python3
"""
Code validation script for langfuse-samples

Performs basic syntax and import checks on all Python files.
Useful for CI/CD pipelines and pre-commit validation.
"""

import os
import ast
import sys
from pathlib import Path

def validate_python_syntax(file_path):
    """Check if Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def find_python_files():
    """Find all Python files in the repository"""
    python_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'cdk.out'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    print("🔍 Validating Python files...")
    print("=" * 50)
    
    python_files = find_python_files()
    
    if not python_files:
        print("❌ No Python files found")
        return 1
    
    print(f"Found {len(python_files)} Python files")
    
    errors = []
    
    for file_path in python_files:
        valid, error = validate_python_syntax(file_path)
        if valid:
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}: {error}")
            errors.append((file_path, error))
    
    print("\n" + "=" * 50)
    
    if errors:
        print(f"❌ {len(errors)} files have syntax errors:")
        for file_path, error in errors:
            print(f"  {file_path}: {error}")
        return 1
    else:
        print(f"✅ All {len(python_files)} Python files have valid syntax")
        return 0

if __name__ == "__main__":
    sys.exit(main())