#!/usr/bin/env python3
"""
Clean duplicate plot sections from HTML files
"""

import re
from pathlib import Path

def clean_duplicate_plots(html_path: str) -> bool:
    """Remove duplicate plot sections from HTML file."""
    
    html_file = Path(html_path)
    if not html_file.exists():
        print(f"❌ HTML file not found: {html_path}")
        return False
    
    try:
        with open(html_file, 'r') as f:
            content = f.read()
        
        # Find all plot sections
        plot_pattern = r'<div class="scenario-plots"[^>]*>.*?</div>\s*<p style="font-size: 12px; color: #888[^"]*"[^>]*>.*?</p>\s*</div>'
        plot_sections = re.findall(plot_pattern, content, re.DOTALL)
        
        if len(plot_sections) <= 2:
            print("✅ No duplicate plots found")
            return True
        
        print(f"🔍 Found {len(plot_sections)} plot sections, keeping only the first 2")
        
        # Remove all plot sections
        content_without_plots = re.sub(plot_pattern, '', content, flags=re.DOTALL)
        
        # Find insertion point (after KPI cards)
        insertion_point = content_without_plots.find('</div>', content_without_plots.find('Hero KPIs'))
        if insertion_point == -1:
            insertion_point = content_without_plots.rfind('</body>')
        
        if insertion_point == -1:
            print("❌ Could not find insertion point")
            return False
        
        # Insert only the first 2 plot sections
        clean_plots = '\n'.join(plot_sections[:2])
        new_content = content_without_plots[:insertion_point] + clean_plots + content_without_plots[insertion_point:]
        
        # Write back to file
        with open(html_file, 'w') as f:
            f.write(new_content)
        
        print(f"✅ Cleaned duplicate plots from {html_file}")
        return True
        
    except Exception as e:
        print(f"❌ Error cleaning HTML: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python clean_duplicate_plots.py <html_file>")
        sys.exit(1)
    
    html_path = sys.argv[1]
    clean_duplicate_plots(html_path)
