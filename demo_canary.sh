#!/bin/bash

# Canary Deployment Demo Script
# This script provides a one-click demonstration of the canary deployment system

echo "🚀 Canary Deployment System - Quick Demo"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "modules/canary/__init__.py" ]; then
    echo "❌ Please run this script from the project root directory."
    exit 1
fi

echo "📋 Demo Options:"
echo "1. Quick Demo (30 seconds)"
echo "2. Complete Demo (3 minutes)"
echo "3. A/B Testing Demo"
echo "4. SLO Strategy Demo"
echo "5. Observability Package Demo"
echo

read -p "Select demo option (1-5): " choice

case $choice in
    1)
        echo "🚀 Running Quick Demo..."
        echo "n" | python3 scripts/canary_cli.py start candidate_high_recall
        echo "⏳ Waiting 30 seconds for demo..."
        sleep 30
        echo "n" | python3 scripts/canary_cli.py stop
        echo "📊 Generating reports..."
        python3 -c "
from modules.canary import generate_observability_package
package = generate_observability_package(output_prefix='quick_demo')
print(f'Generated {len(package.generated_files)} files')
for f in package.generated_files:
    print(f'  - {f}')
"
        ;;
    2)
        echo "🚀 Running Complete Demo..."
        python3 scripts/demo_canary_complete.py
        ;;
    3)
        echo "🧪 Running A/B Testing Demo..."
        python3 scripts/test_ab_evaluator.py
        ;;
    4)
        echo "📊 Running SLO Strategy Demo..."
        python3 scripts/test_slo_strategy.py
        ;;
    5)
        echo "📈 Running Observability Package Demo..."
        python3 scripts/test_observability_package.py
        ;;
    *)
        echo "❌ Invalid option. Please select 1-5."
        exit 1
        ;;
esac

echo
echo "🎉 Demo completed!"
echo
echo "Generated files are in: reports/canary/"
echo "View HTML reports in your browser to see the results."
echo


