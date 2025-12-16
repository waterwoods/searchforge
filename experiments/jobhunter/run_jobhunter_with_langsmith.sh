#!/usr/bin/env bash
# Helper script to run JobHunter CLI with LangSmith tracing enabled
# and a dedicated LANGCHAIN_PROJECT=searchforge-jobhunter.

set -euo pipefail

# Set LangSmith environment variables
# LANGCHAIN_API_KEY should be set in .env or external environment
export LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2:-true}
export LANGCHAIN_PROJECT=${LANGCHAIN_PROJECT:-searchforge-jobhunter}

# Run JD chat coach CLI with text file input
# Usage: ./run_jobhunter_with_langsmith.sh [path/to/jd.txt]
python3 -m experiments.jobhunter.jd_chat_coach_cli \
  --jd-file "${1:-tmp/sample_jd.txt}" \
  --use-default-profile

# Note: To use jd_explainer_cli instead, replace the command above with:
# python3 -m experiments.jobhunter.jd_explainer_cli \
#   --from-text-file "${1:-tmp/sample_jd.txt}" \
#   --use-default-profile
