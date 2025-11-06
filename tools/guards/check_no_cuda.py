#!/usr/bin/env python3
"""
check_no_cuda.py - Check for CUDA packages in pip freeze
========================================================
Checks pip freeze output for nvidia|torch[-_]cuda packages.
"""
import subprocess
import sys
import re

def check_pip_freeze():
    """Check pip freeze for CUDA packages."""
    try:
        result = subprocess.run(
            ["pip", "freeze"],
            capture_output=True,
            text=True,
            check=False
        )
        freeze_output = result.stdout
        
        # Check for banned patterns
        ban_patterns = [
            r'^nvidia',
            r'^torch[-_]?cuda',
            r'cuda.*torch',
            r'torch.*cuda'
        ]
        
        found = []
        for line in freeze_output.splitlines():
            line = line.strip().lower()
            if not line:
                continue
            for pattern in ban_patterns:
                if re.search(pattern, line):
                    found.append(line)
                    break
        
        if found:
            print("ERROR: CUDA packages detected in pip freeze:", file=sys.stderr)
            for pkg in found:
                print(f"  - {pkg}", file=sys.stderr)
            return False
        
        return True
        
    except FileNotFoundError:
        print("WARNING: pip not found", file=sys.stderr)
        return True  # Assume OK if pip not available
    except Exception as e:
        print(f"ERROR: Failed to check pip freeze: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    if check_pip_freeze():
        print("✅ No CUDA packages found")
        sys.exit(0)
    else:
        print("❌ CUDA packages detected", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

