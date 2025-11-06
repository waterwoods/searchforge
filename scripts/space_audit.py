#!/usr/bin/env python3
"""
Space Audit Script - Analyzes disk space usage for Poetry venv, caches, and project files.
Outputs a detailed report to space_report.md.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def get_human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_size(path: Path) -> int:
    """Get total size of a path in bytes. Returns 0 if path doesn't exist."""
    if not path.exists():
        return 0
    try:
        result = subprocess.run(
            ['du', '-sb', str(path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return int(result.stdout.split()[0])
    except (subprocess.TimeoutExpired, ValueError, IndexError):
        pass
    return 0


def get_poetry_venv_path() -> Optional[str]:
    """Get the Poetry virtual environment path."""
    try:
        result = subprocess.run(
            ['poetry', 'env', 'info', '-p'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    return None


def get_site_packages_sizes(venv_path: Optional[str], top_n: int = 30) -> List[Tuple[str, int]]:
    """Get sizes of top N packages in site-packages."""
    if not venv_path:
        return []
    
    site_packages = Path(venv_path) / 'lib' / 'python3.*' / 'site-packages'
    # Try to find the actual site-packages directory
    site_packages_glob = list(Path(venv_path).glob('lib/python*/site-packages'))
    if not site_packages_glob:
        return []
    
    site_packages_dir = site_packages_glob[0]
    
    packages = []
    # Important packages to highlight
    important_packages = {
        'torch', 'torchvision', 'transformers', 'sentence_transformers',
        'numpy', 'pandas', 'scipy', 'sklearn', 'Pillow', 'accelerate'
    }
    
    try:
        for item in site_packages_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                size = get_size(item)
                if size > 0:
                    packages.append((item.name, size))
    except (OSError, PermissionError):
        pass
    
    # Sort by size descending
    packages.sort(key=lambda x: x[1], reverse=True)
    
    # Highlight important packages by putting them first
    important_list = [(name, size) for name, size in packages if name in important_packages]
    other_list = [(name, size) for name, size in packages if name not in important_packages]
    
    # Return top N, with important packages prioritized
    result = important_list + other_list
    return result[:top_n]


def find_project_root() -> Path:
    """Find the project root directory (where pyproject.toml or Makefile exists)."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / 'pyproject.toml').exists() or (parent / 'Makefile').exists():
            return parent
    return current


def scan_cache_directories() -> Dict[str, int]:
    """Scan various cache directories and return their sizes."""
    home = Path.home()
    caches = {}
    
    # HuggingFace cache
    hf_cache = home / '.cache' / 'huggingface' / 'hub'
    caches['HuggingFace Hub'] = get_size(hf_cache)
    
    # Poetry cache
    poetry_cache1 = home / '.cache' / 'pypoetry'
    poetry_cache2 = home / 'Library' / 'Caches' / 'pypoetry'
    caches['Poetry Cache (Linux)'] = get_size(poetry_cache1)
    caches['Poetry Cache (macOS)'] = get_size(poetry_cache2)
    
    # Pip cache
    pip_cache1 = home / '.cache' / 'pip'
    pip_cache2 = home / 'Library' / 'Caches' / 'pip'
    caches['Pip Cache (Linux)'] = get_size(pip_cache1)
    caches['Pip Cache (macOS)'] = get_size(pip_cache2)
    
    # Project node_modules
    project_root = find_project_root()
    node_modules = project_root / 'frontend' / 'node_modules'
    caches['Frontend node_modules'] = get_size(node_modules)
    
    # Frontend node_modules/.cache
    frontend_cache = project_root / 'frontend' / 'node_modules' / '.cache'
    caches['Frontend node_modules/.cache'] = get_size(frontend_cache)
    
    # /tmp/raglab* directories
    tmp_dirs = list(Path('/tmp').glob('raglab*'))
    tmp_total = sum(get_size(d) for d in tmp_dirs)
    caches['/tmp/raglab* (all)'] = tmp_total
    
    return {k: v for k, v in caches.items() if v > 0}


def scan_pycache_directories(project_root: Path) -> int:
    """Scan __pycache__ directories in the project."""
    total_size = 0
    try:
        for pycache in project_root.rglob('__pycache__'):
            if pycache.is_dir():
                total_size += get_size(pycache)
    except (OSError, PermissionError):
        pass
    return total_size


def check_torchvision_usage(project_root: Path) -> Tuple[bool, List[str]]:
    """Check if torchvision is used in the codebase."""
    usage_files = []
    import re
    
    # Patterns for actual imports (more precise)
    import_patterns = [
        r'^\s*import\s+torchvision',
        r'^\s*from\s+torchvision\s+import',
        r'^\s*from\s+torchvision\.',
    ]
    
    # Exclude common directories that shouldn't be scanned
    exclude_dirs = {'.venv', 'venv', 'env', '.env', '__pycache__', 'node_modules', 
                    '.git', 'build', 'dist', '.tox', '.pytest_cache', 'site-packages'}
    
    # Exclude the space_audit script itself
    script_name = Path(__file__).name
    
    try:
        for py_file in project_root.rglob('*.py'):
            # Skip if file is in an excluded directory
            parts = py_file.parts
            if any(excluded in parts for excluded in exclude_dirs):
                continue
            
            # Skip the audit script itself
            if py_file.name == script_name:
                continue
            
            if py_file.is_file():
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    lines = content.split('\n')
                    for line in lines:
                        # Skip comments
                        stripped = line.strip()
                        if stripped.startswith('#'):
                            continue
                        # Check for actual import statements
                        for pattern in import_patterns:
                            if re.match(pattern, line):
                                usage_files.append(str(py_file.relative_to(project_root)))
                                break
                        if usage_files and usage_files[-1] == str(py_file.relative_to(project_root)):
                            break
                except (OSError, UnicodeDecodeError):
                    pass
    except (OSError, PermissionError):
        pass
    
    return len(usage_files) > 0, usage_files


def generate_report(output_file: Path):
    """Generate the space audit report."""
    project_root = find_project_root()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Get Poetry venv path
    venv_path = get_poetry_venv_path()
    venv_size = get_size(Path(venv_path)) if venv_path else 0
    
    # Get site-packages sizes
    site_packages = get_site_packages_sizes(venv_path, top_n=30)
    
    # Scan cache directories
    caches = scan_cache_directories()
    
    # Scan __pycache__
    pycache_size = scan_pycache_directories(project_root)
    
    # Check torchvision usage
    torchvision_used, torchvision_files = check_torchvision_usage(project_root)
    torchvision_removed = False
    
    # Check if torchvision is already removed from pyproject.toml
    pyproject_path = project_root / 'pyproject.toml'
    if pyproject_path.exists():
        pyproject_content = pyproject_path.read_text(encoding='utf-8')
        # Check if torchvision assignment line exists
        if 'torchvision = "*"' not in pyproject_content and 'torchvision =' not in pyproject_content:
            torchvision_removed = True
    
    # Generate markdown report
    lines = [
        f"# Space Audit Report",
        f"",
        f"**Generated:** {timestamp}",
        f"**Project Root:** {project_root}",
        f"",
        "---",
        "",
        "## Summary",
        "",
        f"| Item | Size |",
        f"|------|------|",
    ]
    
    # Poetry venv
    if venv_path:
        lines.append(f"| Poetry Virtual Environment | {get_human_readable_size(venv_size)} |")
        lines.append(f"| Venv Path | `{venv_path}` |")
    
    # Cache totals
    cache_total = sum(caches.values())
    if cache_total > 0:
        lines.append(f"| **Total Cache Size** | **{get_human_readable_size(cache_total)}** |")
    
    # __pycache__ total
    if pycache_size > 0:
        lines.append(f"| Project __pycache__ directories | {get_human_readable_size(pycache_size)} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Top 30 Site-Packages by Size",
        "",
        "| Package | Size |",
        "|---------|------|",
    ])
    
    for pkg_name, pkg_size in site_packages:
        lines.append(f"| `{pkg_name}` | {get_human_readable_size(pkg_size)} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## Cache Directories",
        "",
        "| Cache Location | Size |",
        "|----------------|------|",
    ])
    
    for cache_name, cache_size in sorted(caches.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| {cache_name} | {get_human_readable_size(cache_size)} |")
    
    if pycache_size > 0:
        lines.append(f"| Project `__pycache__` directories | {get_human_readable_size(pycache_size)} |")
    
    lines.extend([
        "",
        "---",
        "",
        "## torchvision Usage Check",
        "",
    ])
    
    if torchvision_used:
        lines.extend([
            f"⚠️ **torchvision is used in the codebase**",
            "",
            "Files using torchvision:",
            "",
        ])
        for file in torchvision_files[:20]:  # Limit to first 20 files
            lines.append(f"- `{file}`")
        if len(torchvision_files) > 20:
            lines.append(f"- ... and {len(torchvision_files) - 20} more files")
        lines.append("")
        lines.append("**Recommendation:** Keep torchvision in dependencies.")
        lines.append("**Status:** Keeping torchvision (actively used).")
    elif torchvision_removed:
        lines.extend([
            "✅ **torchvision is NOT used in the codebase**",
            "",
            "**Status:** ✅ torchvision has been removed from dependencies.",
            "",
            "> Run `poetry install --no-cache` to sync the environment if needed.",
        ])
    else:
        lines.extend([
            "✅ **torchvision is NOT used in the codebase**",
            "",
            "**Recommendation:** Can be safely removed with `poetry remove torchvision`",
            "",
        ])
        # Try to remove torchvision
        try:
            result = subprocess.run(
                ['poetry', 'remove', 'torchvision', '--no-interaction'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                torchvision_removed = True
                lines.append("> ✅ **Status:** torchvision has been removed from dependencies.")
                lines.append("")
                lines.append("> Run `poetry install --no-cache` to sync the environment.")
            else:
                # If poetry remove fails, try manually editing pyproject.toml
                pyproject_path = project_root / 'pyproject.toml'
                if pyproject_path.exists():
                    try:
                        content = pyproject_path.read_text(encoding='utf-8')
                        # Remove torchvision line
                        original_lines = content.splitlines(keepends=True) if '\n' in content or '\r' in content else content.split('\n')
                        new_lines = []
                        found_torchvision = False
                        for line in original_lines:
                            # Skip lines that contain torchvision assignment
                            stripped = line.strip()
                            if stripped.startswith('torchvision') and '=' in stripped:
                                found_torchvision = True
                                continue
                            new_lines.append(line)
                        
                        if found_torchvision:
                            # Join lines back, preserving original line endings
                            if '\r\n' in content:
                                new_content = ''.join(new_lines)
                            elif '\n' in content:
                                new_content = ''.join(new_lines)
                            else:
                                new_content = '\n'.join(new_lines) + '\n' if new_lines else ''
                            
                            if new_content != content:
                                pyproject_path.write_text(new_content, encoding='utf-8')
                                torchvision_removed = True
                                lines.append("> ✅ **Status:** torchvision has been removed from pyproject.toml.")
                                lines.append("")
                                lines.append("> Run `poetry install --no-cache` to sync the environment.")
                        else:
                            lines.append(f"> ⚠️ **Status:** Failed to remove torchvision automatically.")
                            lines.append(f"> Poetry error: {result.stderr[:200]}")
                            lines.append("")
                            lines.append("> You can manually remove 'torchvision = \"*\"' from pyproject.toml")
                    except Exception as e2:
                        lines.append(f"> ⚠️ **Status:** Failed to remove torchvision automatically.")
                        lines.append(f"> Poetry error: {result.stderr[:200]}")
                        lines.append(f"> Manual removal error: {e2}")
                        lines.append("")
                        lines.append("> You can manually remove 'torchvision = \"*\"' from pyproject.toml")
                else:
                    lines.append(f"> ⚠️ **Status:** Failed to remove torchvision automatically.")
                    lines.append(f"> Error: {result.stderr[:200]}")
                    lines.append("")
                    lines.append("> You can manually run: `poetry remove torchvision`")
        except Exception as e:
            lines.append(f"> ⚠️ **Status:** Error attempting to remove torchvision: {e}")
            lines.append("")
            lines.append("> You can manually remove 'torchvision = \"*\"' from pyproject.toml")
    
    lines.extend([
        "",
        "---",
        "",
        "## Estimated Reclaimable Space",
        "",
        "The following caches can be safely cleaned:",
        "",
        "| Cache | Estimated Reclaimable |",
        "|-------|----------------------|",
    ])
    
    reclaimable_total = cache_total + pycache_size
    for cache_name, cache_size in sorted(caches.items(), key=lambda x: x[1], reverse=True):
        if cache_size > 10 * 1024 * 1024:  # Only show if > 10MB
            lines.append(f"| {cache_name} | {get_human_readable_size(cache_size)} |")
    
    if pycache_size > 10 * 1024 * 1024:
        lines.append(f"| Project `__pycache__` | {get_human_readable_size(pycache_size)} |")
    
    lines.extend([
        "",
        f"**Total Estimated Reclaimable:** {get_human_readable_size(reclaimable_total)}",
        "",
        "---",
        "",
        "## Notes",
        "",
        "- Use `make space-report` to regenerate this report",
        "- Use `make clean-space` (dry-run) to preview cleanup",
        "- Use `make clean-space RUN=1` to execute cleanup",
        "- HuggingFace cache can be moved to external drive by setting `HF_HOME`",
        "",
    ])
    
    # Write report
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text('\n'.join(lines))
    
    print(f"✅ Space audit report generated: {output_file}")
    print(f"   Total cache size: {get_human_readable_size(cache_total)}")
    print(f"   Estimated reclaimable: {get_human_readable_size(reclaimable_total)}")
    
    if torchvision_used:
        print(f"⚠️  torchvision is used in {len(torchvision_files)} file(s) - keeping it")
    else:
        if torchvision_removed:
            print(f"✅ torchvision not used - removed from dependencies")
            print(f"   Run 'poetry install --no-cache' to sync the environment")
        else:
            print(f"⚠️  torchvision not used but removal failed - check report for details")


if __name__ == '__main__':
    project_root = find_project_root()
    output_file = project_root / 'space_report.md'
    
    try:
        generate_report(output_file)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

