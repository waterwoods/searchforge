#!/usr/bin/env python3
"""
Fix HTML file by removing duplicate plot sections and properly embedding plots
"""

import re
from pathlib import Path

def fix_html_file(html_path: str) -> bool:
    """Fix HTML file by removing duplicates and properly embedding plots."""
    
    html_file = Path(html_path)
    if not html_file.exists():
        print(f"❌ HTML file not found: {html_path}")
        return False
    
    try:
        with open(html_file, 'r') as f:
            content = f.read()
        
        # Remove all existing plot sections
        plot_pattern = r'<div class="scenario-plots"[^>]*>.*?</div>\s*<p style="font-size: 12px; color: #888[^"]*"[^>]*>.*?</p>\s*</div>'
        content = re.sub(plot_pattern, '', content, flags=re.DOTALL)
        
        # Also remove any incomplete plot sections
        incomplete_pattern = r'<div class="scenario-plots"[^>]*>.*?(?=<div class="scenario-plots"|</body>)'
        content = re.sub(incomplete_pattern, '', content, flags=re.DOTALL)
        
        # Find insertion point (after KPI section)
        kpi_end = content.find('</div>', content.find('Hero KPIs'))
        if kpi_end == -1:
            print("❌ Could not find KPI section end")
            return False
        
        # Create clean plot section
        plots_html = '''
        <div class="scenario-plots" style="margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 8px;">
            <h3 style="margin-bottom: 15px; color: #333;">Scenario A Time Series</h3>
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px;">
                    <img src="plots/scenario_a_p95.png" alt="P95 Latency" style="width: 100%; max-width: 600px; height: auto;">
                    <p style="font-size: 12px; color: #666; margin-top: 5px;">P95 Latency (ms) over time</p>
                </div>
                <div style="flex: 1; min-width: 300px;">
                    <img src="plots/scenario_a_recall.png" alt="Recall@10" style="width: 100%; max-width: 600px; height: auto;">
                    <p style="font-size: 12px; color: #666; margin-top: 5px;">Recall@10 over time</p>
                </div>
            </div>
            <p style="font-size: 12px; color: #888; margin-top: 10px; font-style: italic;">
                P95(ms) and Recall@10 trends over experiment time. Single-knob (dashed gray) vs Multi-knob (solid blue) with EWMA smoothing.
            </p>
        </div>
        '''
        
        # Insert clean plots HTML
        new_content = content[:kpi_end] + plots_html + content[kpi_end:]
        
        # Write back to file
        with open(html_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Fixed HTML file: {html_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing HTML: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python fix_html.py <html_file>")
        sys.exit(1)
    
    html_path = sys.argv[1]
    fix_html_file(html_path)
