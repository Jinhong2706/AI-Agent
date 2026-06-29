#!/usr/bin/env python3
"""
CLI Tool Example
"""
import argparse
import sys
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def greet(name: str, verbose: bool = False) -> None:
    """Greet someone."""
    if verbose:
        logger.info(f"Greeting {name}")
    print(f"Hello, {name}!")

def calculate(operation: str, a: float, b: float) -> float:
    """Simple calculator."""
    if operation == "add":
        return a + b
    elif operation == "sub":
        return a - b
    elif operation == "mul":
        return a * b
    elif operation == "div":
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description="A powerful CLI tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Greet command
    greet_parser = subparsers.add_parser("greet", help="Greet someone")
    greet_parser.add_argument("name", help="Name to greet")
    greet_parser.add_argument("-v", "--verbose", action="store_true")
    
    # Calculate command
    calc_parser = subparsers.add_parser("calc", help="Calculator")
    calc_parser.add_argument("operation", choices=["add", "sub", "mul", "div"])
    calc_parser.add_argument("a", type=float)
    calc_parser.add_argument("b", type=float)
    
    args = parser.parse_args()
    
    if args.command == "greet":
        greet(args.name, args.verbose)
    elif args.command == "calc":
        try:
            result = calculate(args.operation, args.a, args.b)
            print(f"Result: {result}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()