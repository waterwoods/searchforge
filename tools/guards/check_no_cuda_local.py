#!/usr/bin/env python3
"""Check for CUDA packages in local environment."""
import pkgutil
import sys

ban = ('nvidia', 'cuda', 'torch_cuda')
# Exclude this script itself
found = [m.name for m in pkgutil.iter_modules() 
         if any(k in m.name for k in ban) 
         and 'check_no_cuda' not in m.name]

if found:
    print("CUDA_PACKAGES:", found)
    sys.exit(1)

print("✅ No CUDA packages found")
sys.exit(0)

