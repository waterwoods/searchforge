#!/usr/bin/env python3
"""
Test script for demo pack bundle functionality.
"""

import os
import sys
import json
import zipfile
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_bundle_creation():
    """Test that bundle creation works correctly."""
    print("🧪 Testing demo pack bundle creation...")
    
    # Import the bundle script
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
    from build_demo_bundle import find_latest_demo_pack, create_presenter_notes, copy_necessary_files
    
    try:
        # Test finding latest demo pack
        latest_pack = find_latest_demo_pack()
        print(f"✅ Found latest demo pack: {latest_pack}")
        
        # Test presenter notes creation
        notes = create_presenter_notes()
        assert "AutoTuner Demo Pack" in notes
        assert "打开 AutoTuner 就更快" in notes
        assert "不牺牲召回" in notes
        assert "可上线" in notes
        print("✅ Presenter notes generated correctly")
        
        # Test file copying (if demo pack exists)
        if latest_pack.exists():
            with tempfile.TemporaryDirectory() as temp_dir:
                copy_necessary_files(latest_pack, temp_dir)
                
                # Check that key files were copied
                temp_path = Path(temp_dir)
                assert (temp_path / "index.html").exists(), "index.html not found"
                assert (temp_path / "metadata.json").exists(), "metadata.json not found"
                assert (temp_path / "README_PRESENTATION.md").exists(), "README_PRESENTATION.md not found"
                print("✅ File copying works correctly")
        
        print("🎉 All bundle tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Bundle test failed: {e}")
        return False

def test_zip_structure(zip_path):
    """Test that ZIP bundle has correct structure."""
    print(f"🧪 Testing ZIP structure: {zip_path}")
    
    if not os.path.exists(zip_path):
        print(f"❌ ZIP file not found: {zip_path}")
        return False
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            files = zipf.namelist()
            
            # Check for required files
            required_files = [
                "index.html",
                "metadata.json", 
                "README_PRESENTATION.md"
            ]
            
            for req_file in required_files:
                if req_file not in files:
                    print(f"❌ Missing required file: {req_file}")
                    return False
            
            # Check for plots directory
            plot_files = [f for f in files if f.startswith("plots/")]
            if not plot_files:
                print("⚠️  No plot files found in ZIP")
            
            # Check for scenario directories
            scenario_dirs = [f for f in files if f.startswith("scenario_")]
            if not scenario_dirs:
                print("⚠️  No scenario directories found in ZIP")
            
            print(f"✅ ZIP structure valid ({len(files)} files)")
            return True
            
    except Exception as e:
        print(f"❌ ZIP test failed: {e}")
        return False

def test_global_comparison_table():
    """Test that Global Comparison table has required metrics."""
    print("🧪 Testing Global Comparison table...")
    
    # Find latest demo pack
    demo_pack_dir = Path("demo_pack")
    if not demo_pack_dir.exists():
        print("❌ demo_pack directory not found")
        return False
    
    # Look for latest pack
    pattern_dirs = []
    for pattern in ["SIM_BATTERY_*", "LOCAL_*", "LIVE_*"]:
        import glob
        pattern_dirs.extend(glob.glob(str(demo_pack_dir / pattern)))
    
    if not pattern_dirs:
        print("❌ No demo pack directories found")
        return False
    
    latest_dir = max(pattern_dirs, key=os.path.getmtime)
    latest_path = Path(latest_dir)
    
    # Check nested directory
    nested_dirs = [d for d in latest_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if nested_dirs:
        latest_path = nested_dirs[0]
    
    index_file = latest_path / "index.html"
    if not index_file.exists():
        print("❌ index.html not found")
        return False
    
    # Read and check for Global Comparison content
    with open(index_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required metrics in the JavaScript
    required_metrics = [
        "deltaP95",
        "pValue", 
        "deltaRecall",
        "safetyRate",
        "applyRate"
    ]
    
    for metric in required_metrics:
        if metric not in content:
            print(f"❌ Missing metric in Global Comparison: {metric}")
            return False
    
    print("✅ Global Comparison table has all required metrics")
    return True

def main():
    """Run all bundle tests."""
    print("🚀 Running AutoTuner Demo Pack Bundle Tests\n")
    
    # Test bundle creation
    bundle_test = test_bundle_creation()
    
    # Test global comparison table
    table_test = test_global_comparison_table()
    
    # Test ZIP structure if bundle was created
    zip_test = True
    if bundle_test:
        # Look for the most recent ZIP file
        demo_pack_dir = Path("demo_pack")
        zip_files = list(demo_pack_dir.glob("AutoTuner_Demo_*.zip"))
        if zip_files:
            latest_zip = max(zip_files, key=os.path.getmtime)
            zip_test = test_zip_structure(latest_zip)
        else:
            print("⚠️  No ZIP bundle found to test")
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"   Bundle Creation: {'✅ PASS' if bundle_test else '❌ FAIL'}")
    print(f"   Global Table: {'✅ PASS' if table_test else '❌ FAIL'}")
    print(f"   ZIP Structure: {'✅ PASS' if zip_test else '❌ FAIL'}")
    
    all_passed = bundle_test and table_test and zip_test
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    main()
