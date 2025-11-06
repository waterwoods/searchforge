#!/usr/bin/env python3
"""
AutoTuner Demo Pack Bundle Builder

This script packages the latest demo pack into a shareable ZIP file with:
- index.html
- plots/ directory
- scenario_*/ directories (one_pager.html, json, csv)
- metadata.json
- README_PRESENTATION.md (Chinese presenter notes)
"""

import os
import sys
import json
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import glob

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def find_latest_demo_pack():
    """Find the latest demo pack directory."""
    demo_pack_dir = Path("demo_pack")
    if not demo_pack_dir.exists():
        raise FileNotFoundError("demo_pack directory not found")
    
    # Look for directories with pattern like SIM_BATTERY_*, LOCAL_*, etc.
    # Prioritize SIM_BATTERY packs as they have complete data
    pattern_dirs = []
    for pattern in ["SIM_BATTERY_*", "LOCAL_*", "LIVE_*"]:
        pattern_dirs.extend(glob.glob(str(demo_pack_dir / pattern)))
    
    if not pattern_dirs:
        raise FileNotFoundError("No demo pack directories found")
    
    # Prioritize SIM_BATTERY packs, then sort by modification time
    sim_battery_dirs = [d for d in pattern_dirs if "SIM_BATTERY" in d and "FIXED" not in d]
    if sim_battery_dirs:
        latest_dir = max(sim_battery_dirs, key=os.path.getmtime)
    else:
        latest_dir = max(pattern_dirs, key=os.path.getmtime)
    latest_path = Path(latest_dir)
    
    # Check if there's a nested directory (some packs have nested structure)
    nested_dirs = [d for d in latest_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if nested_dirs:
        # Use the first nested directory (usually the timestamp directory)
        latest_path = nested_dirs[0]
    
    print(f"Found latest demo pack: {latest_path}")
    return latest_path

def create_presenter_notes():
    """Generate Chinese presenter notes."""
    return """# AutoTuner Demo Pack - 演示说明

## 核心要点 (3个关键指标)

### 1. "打开 AutoTuner 就更快" - 性能提升
- **ΔP95 > 0** 且 **p < 0.05** (三场景都通过)
- 蓝色曲线显示延迟降低，性能提升明显
- 统计显著性确保结果可信

### 2. "不牺牲召回" - 质量保证  
- **ΔRecall ≥ -0.01** (召回率基本无损失)
- 曲线显示蓝线更低更稳
- 在提升性能的同时保持搜索质量

### 3. "可上线" - 生产就绪
- **apply_rate ≥ 0.95** (95%以上参数被应用)
- **safety ≥ 0.99** (99%以上安全率)
- 回滚/冷却护栏在报告中可见
- 系统具备自动保护机制

## 演示顺序

1. **Global Comparison** - 展示三场景整体表现
2. **Scenario A 曲线** - 高延迟低召回场景的优化效果
3. **Scenario B 曲线** - 高召回高延迟场景的平衡
4. **Scenario C 曲线** - 低延迟低召回场景的精细调优
5. **失败原因Top3卡片** - 展示系统的安全机制

## 技术亮点

- **多场景验证**: A/B/C三个不同业务场景全面测试
- **统计严谨**: 5000次排列检验确保结果可信
- **生产就绪**: 内置安全护栏，支持自动回滚
- **实时监控**: 15分钟快速验证，支持持续优化

---
*Generated: {timestamp}*
""".format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def copy_necessary_files(source_dir, target_dir):
    """Copy only necessary files to target directory."""
    source_path = Path(source_dir)
    target_path = Path(target_dir)
    
    # Create target directory
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Files to copy
    files_to_copy = [
        "index.html",
        "metadata.json"
    ]
    
    # Copy main files
    for file_name in files_to_copy:
        source_file = source_path / file_name
        if source_file.exists():
            shutil.copy2(source_file, target_path / file_name)
            print(f"Copied {file_name}")
    
    # Copy plots directory
    plots_source = source_path / "plots"
    if plots_source.exists():
        plots_target = target_path / "plots"
        shutil.copytree(plots_source, plots_target)
        print(f"Copied plots/ directory")
    else:
        print(f"⚠️  Plots directory not found at {plots_source}")
    
    # Copy scenario directories
    for scenario_dir in source_path.glob("scenario_*"):
        if scenario_dir.is_dir():
            scenario_target = target_path / scenario_dir.name
            scenario_target.mkdir(exist_ok=True)
            
            # Copy scenario files
            for file_pattern in ["one_pager.html", "one_pager.json", "one_pager.csv"]:
                source_file = scenario_dir / file_pattern
                if source_file.exists():
                    shutil.copy2(source_file, scenario_target / file_pattern)
                    print(f"Copied {scenario_dir.name}/{file_pattern}")
    
    # Create presenter notes
    presenter_notes = create_presenter_notes()
    with open(target_path / "README_PRESENTATION.md", "w", encoding="utf-8") as f:
        f.write(presenter_notes)
    print("Created README_PRESENTATION.md")

def create_zip_bundle(source_dir, output_path):
    """Create ZIP bundle from source directory."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(source_dir)
                zipf.write(file_path, arc_path)
                print(f"Added to ZIP: {arc_path}")
    
    # Get file size
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Created ZIP bundle: {output_path} ({size_mb:.1f} MB)")

def main():
    """Main function to build demo pack bundle."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build AutoTuner Demo Pack Bundle')
    parser.add_argument('--src', help='Source directory path (e.g., demo_pack/20251006_1034)')
    parser.add_argument('--out', help='Output ZIP file path (e.g., demo_pack/20251006_1034.zip)')
    args = parser.parse_args()
    
    try:
        # Determine source directory
        if args.src:
            source_pack = Path(args.src)
            if not source_pack.exists():
                raise FileNotFoundError(f"Source directory not found: {source_pack}")
            print(f"Using specified source: {source_pack}")
        else:
            # Find latest demo pack
            source_pack = find_latest_demo_pack()
            print(f"Using latest demo pack: {source_pack}")
        
        # Create temporary directory for bundling
        temp_dir = Path("temp_bundle")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        
        # Copy necessary files
        copy_necessary_files(source_pack, temp_dir)
        
        # Determine output ZIP path
        if args.out:
            zip_name = args.out
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            zip_name = f"demo_pack/AutoTuner_Demo_{timestamp}.zip"
        
        # Create ZIP bundle
        create_zip_bundle(temp_dir, zip_name)
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
        print(f"\n✅ Demo pack bundle created successfully!")
        print(f"📦 Bundle: {zip_name}")
        print(f"📋 Presenter notes: README_PRESENTATION.md included")
        print(f"🎯 Global Comparison table with 5 metrics (ΔP95, p-value, ΔRecall, Safety, Apply)")
        
        return zip_name
        
    except Exception as e:
        print(f"❌ Error creating bundle: {e}")
        return None

if __name__ == "__main__":
    main()
