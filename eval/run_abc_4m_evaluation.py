#!/usr/bin/env python3
"""
A/B/C 4-minute evaluation runner

Run:
  PYTHONPATH="$(pwd)" python eval/run_abc_4m_evaluation.py \
    --config eval/configs/evaluation_config_4m_abc.json \
    --output reports/abc_4m --seed 42
"""

import argparse
import json
import os
import sys
import time
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from evaluation.enhanced_ab_evaluator import EnhancedABEvaluator
from evaluation.enhanced_ab_analyzer import EnhancedABAnalyzer
from modules.evaluation import enhanced_ab_analyzer as analyzer


def create_output_dirs(output_dir: str) -> None:
    """Create necessary output directories."""
    dirs_to_create = [
        output_dir,
        f"{output_dir}/charts",
        f"{output_dir}/timeline",
        f"{output_dir}/recovery"
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")


def run_single_evaluation(config: Dict[str, Any], run_config: Dict[str, Any], 
                         run_name: str, output_dir: str, seed: int) -> str:
    """Run a single evaluation and return the results file path."""
    print(f"\n🚀 Starting {run_name}...")
    print(f"   Configuration: {run_config.get('name', run_name)}")
    
    # Create a temporary config file for this specific run
    temp_config = {
        "duration_seconds": run_config.get("duration_seconds", 240),
        "common": config.get("common", {}),
        "baseline": run_config if run_name == "baseline" else {},
        "high_stress": run_config if run_name in ["stress_off", "stress_on"] else {}
    }
    
    temp_config_file = f"/tmp/temp_config_{run_name}.json"
    with open(temp_config_file, 'w') as f:
        json.dump(temp_config, f)
    
    try:
        # Create evaluator with temp config
        evaluator = EnhancedABEvaluator(temp_config_file)
        
        # Set random seed
        evaluator.random_seed = seed
        
        # Determine run name and output file
        run_name_for_evaluator = "baseline" if run_name == "baseline" else "high_stress"
        output_filename = run_config.get('output_filename', f'{run_name}_results.json')
        final_results_file = f"{output_dir}/{output_filename}"
        
        # Run evaluation (async)
        import asyncio
        asyncio.run(evaluator.run_evaluation(run_name_for_evaluator, final_results_file))
        
        print(f"✅ {run_name} completed")
        print(f"   Results saved to: {final_results_file}")
        
        return final_results_file
        
    finally:
        # Clean up temp config file
        if os.path.exists(temp_config_file):
            os.remove(temp_config_file)


def extract_timeline_data(results_file: str, chaos_config: Dict[str, Any]) -> str:
    """Extract timeline data from results and save as CSV."""
    try:
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        timeline_data = results.get('timeline_data', [])
        if not timeline_data:
            print(f"⚠️ No timeline data found in {results_file}")
            return ""
        
        # Extract base filename and create timeline CSV
        base_name = Path(results_file).stem
        timeline_file = f"{Path(results_file).parent}/timeline/{base_name}_timeline.csv"
        
        with open(timeline_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ts_sec', 'p95_ms', 'recall_at_10', 'hnsw_ef', 'tuner_actions', 'chaos_active'])
            
            for entry in timeline_data:
                ts_sec = entry.get('timestamp', 0)
                p95_ms = entry.get('p95_ms', 0)
                recall_at_10 = entry.get('recall_at_10', None)
                hnsw_ef = entry.get('hnsw_ef', 64)  # Default value
                tuner_actions = entry.get('tuner_actions', 0)
                
                # Determine if chaos is active at this timestamp
                chaos_active = False
                if chaos_config.get('enabled', False):
                    disconnect_times = chaos_config.get('disconnect_times', [])
                    disconnect_duration = chaos_config.get('disconnect_duration', 0)
                    for disconnect_time in disconnect_times:
                        if disconnect_time <= ts_sec <= disconnect_time + disconnect_duration:
                            chaos_active = True
                            break
                
                writer.writerow([ts_sec, p95_ms, recall_at_10, hnsw_ef, tuner_actions, chaos_active])
        
        print(f"✅ Timeline data saved to: {timeline_file}")
        return timeline_file
        
    except Exception as e:
        print(f"⚠️ Failed to extract timeline data from {results_file}: {e}")
        return ""


def main():
    parser = argparse.ArgumentParser(description='A/B/C 4-minute evaluation runner')
    parser.add_argument('--config', required=True, help='Configuration file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    print("🎬 SmartSearchX A/B/C 4-minute Evaluation")
    print("=" * 40)
    print(f"Configuration: {args.config}")
    print(f"Output directory: {args.output}")
    print(f"Random seed: {args.seed}")
    
    # Load configuration
    try:
        with open(args.config, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1
    
    # Create output directories
    create_output_dirs(args.output)
    
    # Run three evaluations
    runs = [
        ('baseline', 'baseline_results.json'),
        ('stress_off', 'stress_off_results.json'),
        ('stress_on', 'stress_on_results.json')
    ]
    
    results_files = {}
    timeline_files = {}
    
    for run_key, output_filename in runs:
        if run_key not in config:
            print(f"⚠️ Skipping {run_key} - not found in config")
            continue
        
        run_config = config[run_key]
        run_config['output_filename'] = output_filename
        
        # Run evaluation
        results_file = run_single_evaluation(config, run_config, run_key, args.output, args.seed)
        results_files[run_key] = results_file
        
        # Extract timeline data
        chaos_config = run_config.get('chaos', {})
        timeline_file = extract_timeline_data(results_file, chaos_config)
        if timeline_file:
            timeline_files[run_key] = timeline_file
        
        # Small delay between runs
        time.sleep(2)
    
    # Generate charts
    print("\n📊 Generating A/B/C charts...")
    try:
        from evaluation.enhanced_ab_analyzer import (
            plot_abc_latency_timeline_from_json,
            plot_abc_summary_bars
        )
        
        charts_dir = f"{args.output}/charts"
        slo_ms = config.get('common', {}).get('slo_p95_ms', 250.0)
        
        # 1. Latency timeline
        if all(key in results_files for key in ['baseline', 'stress_off', 'stress_on']):
            chaos_windows = []
            for run_key in ['baseline', 'stress_off', 'stress_on']:
                run_config = config.get(run_key, {})
                chaos_config = run_config.get('chaos', {})
                if chaos_config.get('enabled', False):
                    disconnect_times = chaos_config.get('disconnect_times', [])
                    disconnect_duration = chaos_config.get('disconnect_duration', 0)
                    for disconnect_time in disconnect_times:
                        chaos_windows.append((disconnect_time, disconnect_time + disconnect_duration))
            
            plot_abc_latency_timeline_from_json(
                results_files['baseline'],
                results_files['stress_off'],
                results_files['stress_on'],
                f"{charts_dir}/latency_timeline_abc.png",
                slo_ms,
                chaos_windows
            )
            print("✅ Generated latency_timeline_abc.png")
        
        # 2. EF/Recall timeline (all three scenarios)
        if all(key in results_files for key in ['baseline', 'stress_off', 'stress_on']):
            analyzer.plot_ef_recall_timeline_from_json(
                results_files['baseline'],
                results_files['stress_off'],
                results_files['stress_on'],
                f"{charts_dir}/ef_recall_timeline.png"
            )
            print("✅ Generated ef_recall_timeline.png")
        
        # 3. Summary bars
        if all(key in results_files for key in ['baseline', 'stress_off', 'stress_on']):
            plot_abc_summary_bars(
                results_files['baseline'],
                results_files['stress_off'],
                results_files['stress_on'],
                f"{charts_dir}/summary_bars.png",
                slo_ms
            )
            print("✅ Generated summary_bars.png")
            
    except ImportError as e:
        print(f"⚠️ Chart generation failed (import error): {e}")
    except Exception as e:
        print(f"⚠️ Chart generation failed: {e}")
    
    # Create README
    readme_file = f"{args.output}/README.txt"
    try:
        with open(readme_file, 'w') as f:
            f.write("A/B/C 4-minute Evaluation Results\n")
            f.write("=" * 40 + "\n\n")
            f.write("Generated Charts:\n")
            f.write("1. latency_timeline_abc.png - P95 latency timeline showing baseline vs stress_off vs stress_on\n")
            f.write("   - Shows chaos windows as shaded regions\n")
            f.write("   - Includes SLO line at 250ms\n")
            f.write("   - Three colored lines for each scenario\n\n")
            f.write("2. ef_recall_timeline.png - HNSW ef_search parameter and Recall@10 over time\n")
            f.write("   - Left axis: Recall@10 (blue line)\n")
            f.write("   - Right axis: hnsw_ef (red line)\n")
            f.write("   - Dots indicate AutoTuner actions\n\n")
            f.write("3. summary_bars.png - Summary comparison across A/B/C scenarios\n")
            f.write("   - Peak P95 latency\n")
            f.write("   - SLO violation minutes\n")
            f.write("   - Average Recall@10\n")
            f.write("   - Grouped bars for easy comparison\n\n")
            f.write("Data Files:\n")
            f.write("- *_results.json: Detailed results for each scenario\n")
            f.write("- timeline/*_timeline.csv: Time-series data for plotting\n")
        
        print(f"✅ Created README: {readme_file}")
    except Exception as e:
        print(f"⚠️ Failed to create README: {e}")
    
    print("\n🎯 A/B/C evaluation completed!")
    print(f"📁 Results saved to: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
