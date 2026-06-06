#!/usr/bin/env bash
# Founder wrapper — forwards to scripts/founder_pre_trial_checklist.sh
# For first broker trial launch prefer: bash scripts/trial_launch_check.sh
exec bash "$(dirname "$0")/../founder_pre_trial_checklist.sh" "$@"
