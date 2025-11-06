#!/usr/bin/env python3
"""
Check and finalize all scenario charts in the AutoTuner Demo Pack.

This script:
1. Detects the latest demo pack
2. Checks for all required chart files (A,B,C scenarios, p95 and recall charts)
3. Generates missing charts if needed
4. Provides a concise summary table
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import glob

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def find_latest_demo_pack():
    """Find the latest demo pack directory."""
    demo_pack_dir = Path("demo_pack")
    if not demo_pack_dir.exists():
        return None
    
    # Get all demo pack directories with timestamps
    packs = []
    for item in demo_pack_dir.iterdir():
        if item.is_dir():
            # Try to extract timestamp from directory name
            name = item.name
            if name.startswith("SIM_BATTERY") or name.startswith("LOCAL") or name.startswith("2025"):
                packs.append((item, item.stat().st_mtime))
    
    if not packs:
        return None
    
    # Sort by modification time (newest first)
    packs.sort(key=lambda x: x[1], reverse=True)
    return packs[0][0]

def check_chart_files(pack_root):
    """Check if all required chart files exist."""
    required_files = [
        "plots/scenario_A_p95.png",
        "plots/scenario_A_recall.png", 
        "plots/scenario_B_p95.png",
        "plots/scenario_B_recall.png",
        "plots/scenario_C_p95.png",
        "plots/scenario_C_recall.png"
    ]
    
    status = {}
    missing_files = []
    
    for file_path in required_files:
        full_path = pack_root / file_path
        scenario = file_path.split("_")[1]  # A, B, or C
        chart_type = file_path.split("_")[2].split(".")[0]  # p95 or recall
        
        exists = full_path.exists()
        status[(scenario, chart_type)] = exists
        
        if not exists:
            missing_files.append(file_path)
    
    return status, missing_files

def generate_missing_charts(pack_root):
    """Generate missing charts using the plot_time_series script."""
    print("🔧 Generating missing charts...")
    
    # Determine which scenarios need charts
    status, missing_files = check_chart_files(pack_root)
    scenarios_needed = set()
    
    for scenario, chart_type in status:
        if not status[(scenario, chart_type)]:
            scenarios_needed.add(scenario)
    
    if not scenarios_needed:
        return True
    
    scenarios_str = ",".join(sorted(scenarios_needed))
    
    # Run the plot generation script
    cmd = [
        sys.executable, "scripts/plot_time_series.py",
        "--pack-root", str(pack_root),
        "--scenarios", scenarios_str,
        "--alpha", "0.3"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())
        if result.returncode == 0:
            print("✅ Charts generated successfully")
            return True
        else:
            print(f"❌ Error generating charts: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running chart generation: {e}")
        return False

def print_summary_table(status, pack_root):
    """Print a concise summary table."""
    print(f"\n📊 Chart Status Summary for {pack_root.name}:")
    print("=" * 60)
    print(f"{'Scenario':<10} {'p95.png':<12} {'recall.png':<12} {'Status':<12}")
    print("-" * 60)
    
    all_ok = True
    
    for scenario in ['A', 'B', 'C']:
        p95_exists = status.get((scenario, 'p95'), False)
        recall_exists = status.get((scenario, 'recall'), False)
        
        p95_status = "✅ OK" if p95_exists else "❌ Missing"
        recall_status = "✅ OK" if recall_exists else "❌ Missing"
        
        if p95_exists and recall_exists:
            overall_status = "✅ OK"
        elif p95_exists or recall_exists:
            overall_status = "⚠️  Partial"
            all_ok = False
        else:
            overall_status = "❌ Missing"
            all_ok = False
        
        print(f"{scenario:<10} {p95_status:<12} {recall_status:<12} {overall_status:<12}")
    
    print("-" * 60)
    return all_ok

def main():
    """Main function to check and finalize all scenario charts."""
    print("🔍 Checking AutoTuner Demo Pack charts...")
    
    # Find the latest demo pack
    latest_pack = find_latest_demo_pack()
    if not latest_pack:
        print("❌ No demo packs found in demo_pack/ directory")
        return False
    
    print(f"📁 Latest demo pack: {latest_pack}")
    
    # Check current chart status
    status, missing_files = check_chart_files(latest_pack)
    
    # Print initial status
    all_ok = print_summary_table(status, latest_pack)
    
    if all_ok:
        print("\n✅ All charts ready - no generation needed!")
        print("已检查完毕，曲线已生成")
        return True
    
    # Generate missing charts
    if missing_files:
        print(f"\n⚠️  Found {len(missing_files)} missing chart files:")
        for file in missing_files:
            print(f"   - {file}")
        
        success = generate_missing_charts(latest_pack)
        if not success:
            print("❌ Failed to generate missing charts")
            return False
        
        # Re-check status after generation
        status, _ = check_chart_files(latest_pack)
        print_summary_table(status, latest_pack)
        
        if all(status.values()):
            print("\n✅ All charts ready - generation complete!")
            print("已检查完毕，曲线已生成")
        else:
            print("\n⚠️  Some charts still missing after generation")
            print("已检查完毕，部分曲线生成失败")
    else:
        print("\n✅ All charts ready!")
        print("已检查完毕，曲线已生成")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
