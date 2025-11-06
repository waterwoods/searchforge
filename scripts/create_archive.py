#!/usr/bin/env python3
"""
Archive non-essential files while keeping the minimal 4-file surface
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
ARCHIVE_ROOT = PROJECT_ROOT / "_archive" / "20251009"

# Core files to KEEP (all others will be archived)
KEEP_FILES = {
    "launch.sh",
    "services/fiqa_api/app.py",
    "services/fiqa_api/settings.py",
    "logs/metrics_logger.py",
    # Also keep new freeze infrastructure
    "scripts/contract_check.py",
    "scripts/freeze_check.sh",
    "scripts/generate_openapi.py",
    "scripts/smoke_load.py",
    "docs/openapi_snapshot.json",
}

# Directories to keep (will be created/preserved)
KEEP_DIRS = {
    "services/fiqa_api",
    "services/fiqa_api/logs",
    "services/fiqa_api/reports",
    "logs",
    "scripts",
    "docs",
    "_archive",
}

def should_archive(path: Path) -> bool:
    """Determine if a file should be archived"""
    # Convert to relative path from project root
    try:
        rel_path = path.relative_to(PROJECT_ROOT)
    except ValueError:
        return False
    
    rel_path_str = str(rel_path)
    
    # Skip if in keep list
    if rel_path_str in KEEP_FILES:
        return False
    
    # Skip if it's the archive directory itself
    if rel_path_str.startswith("_archive"):
        return False
    
    # Skip hidden files and __pycache__
    if any(part.startswith('.') or part == '__pycache__' for part in rel_path.parts):
        return False
    
    # Archive everything else in services/fiqa_api/
    if rel_path_str.startswith("services/fiqa_api/") and path.is_file():
        return True
    
    return False

def create_archive_manifest(archived_files: list):
    """Generate ARCHIVE_MANIFEST.md"""
    manifest_path = PROJECT_ROOT / "ARCHIVE_MANIFEST.md"
    
    with open(manifest_path, 'w') as f:
        f.write("# Archive Manifest\n\n")
        f.write(f"**Archive Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Files Archived:** {len(archived_files)}\n\n")
        f.write("## Archived Files\n\n")
        f.write("Files moved to `_archive/20251009/` with preserved directory structure:\n\n")
        
        for src_file in sorted(archived_files):
            f.write(f"- `{src_file}`\n")
        
        f.write("\n## Retained Files (Minimal Surface)\n\n")
        for keep_file in sorted(KEEP_FILES):
            f.write(f"- `{keep_file}`\n")
        
        f.write("\n## Rollback\n\n")
        f.write("To restore archived files:\n\n")
        f.write("```bash\n")
        f.write("# Restore all archived files\n")
        f.write("cp -r _archive/20251009/* .\n\n")
        f.write("# Or restore specific file\n")
        f.write("cp _archive/20251009/services/fiqa_api/<filename> services/fiqa_api/\n")
        f.write("```\n")
    
    print(f"✓ Generated ARCHIVE_MANIFEST.md")
    return str(manifest_path)

def main():
    print("📦 Creating Archive Structure")
    print("=" * 60)
    
    # Create archive root
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    
    archived_files = []
    
    # Find and archive files in services/fiqa_api/
    fiqa_api_dir = PROJECT_ROOT / "services" / "fiqa_api"
    if fiqa_api_dir.exists():
        for item in fiqa_api_dir.rglob('*'):
            if item.is_file() and should_archive(item):
                # Calculate relative path from project root
                rel_path = item.relative_to(PROJECT_ROOT)
                
                # Create destination path in archive
                dest_path = ARCHIVE_ROOT / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.copy2(item, dest_path)
                archived_files.append(str(rel_path))
                print(f"  Archived: {rel_path}")
    
    print(f"\n✓ Archived {len(archived_files)} files to _archive/20251009/")
    
    # Generate manifest
    manifest_path = create_archive_manifest(archived_files)
    
    # Now delete the archived files from source
    print("\n🗑️  Removing archived files from source...")
    for archived in archived_files:
        source_file = PROJECT_ROOT / archived
        if source_file.exists():
            source_file.unlink()
            print(f"  Removed: {archived}")
    
    print("\n" + "=" * 60)
    print(f"✅ Archive complete!")
    print(f"   Archived: {len(archived_files)} files")
    print(f"   Manifest: {manifest_path}")
    print(f"   Location: _archive/20251009/")
    
    return 0

if __name__ == "__main__":
    exit(main())

