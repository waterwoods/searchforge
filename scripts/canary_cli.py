#!/usr/bin/env python3
"""
Canary Deployment CLI Tool

This script provides command-line interface for managing canary deployments,
configuration versions, and monitoring system status.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.canary import (
    get_config_manager, get_canary_executor, get_audit_logger,
    get_metrics_collector, get_slo_monitor
)


def list_presets():
    """List all available configuration presets."""
    config_manager = get_config_manager()
    presets = config_manager.list_presets()
    
    print("Available Configuration Presets:")
    print("=" * 50)
    
    for preset in presets:
        try:
            config = config_manager.load_preset(preset)
            print(f"• {preset}")
            print(f"  Description: {config.description}")
            print(f"  Version: {config.version}")
            print(f"  Tags: {', '.join(config.tags)}")
            print(f"  Macro Knobs: latency_guard={config.macro_knobs['latency_guard']:.2f}, recall_bias={config.macro_knobs['recall_bias']:.2f}")
            print()
        except Exception as e:
            print(f"• {preset} (ERROR: {e})")
            print()


def show_status():
    """Show current canary deployment status."""
    from modules.canary import get_global_instances
    instances = get_global_instances()
    config_manager = instances['config_manager']
    canary_executor = instances['canary_executor']
    
    print("Canary Deployment Status:")
    print("=" * 50)
    
    # Configuration state
    state = config_manager.get_canary_status()
    print(f"Status: {state['status']}")
    print(f"Active Config: {state['active_config']}")
    print(f"Last Good Config: {state['last_good_config']}")
    print(f"Candidate Config: {state['candidate_config'] or 'None'}")
    
    if state['canary_start_time']:
        print(f"Canary Start Time: {state['canary_start_time']}")
    
    print()
    
    # Canary executor status
    executor_status = canary_executor.get_current_status()
    if executor_status['is_running']:
        print("Canary Deployment Details:")
        print(f"  Deployment ID: {executor_status['deployment_id']}")
        print(f"  Status: {executor_status['status']}")
        print(f"  Traffic Split: {executor_status['traffic_split']}")
        print(f"  Total Requests: {executor_status['total_requests']}")
        if executor_status['duration_seconds']:
            print(f"  Duration: {executor_status['duration_seconds']:.1f} seconds")
    else:
        print("No canary deployment currently running.")


def start_canary(candidate_config: str):
    """Start a canary deployment with the specified candidate configuration."""
    from modules.canary import get_global_instances
    instances = get_global_instances()
    config_manager = instances['config_manager']
    canary_executor = instances['canary_executor']
    audit_logger = instances['audit_logger']
    
    print(f"Starting canary deployment with candidate: {candidate_config}")
    
    try:
        # Validate candidate configuration exists
        config_manager.load_preset(candidate_config)
        
        # Start canary deployment
        result = canary_executor.start_canary(candidate_config)
        
        # Log audit event
        audit_logger.log_canary_start(
            deployment_id=result.deployment_id,
            candidate_config=candidate_config,
            traffic_split=result.traffic_split
        )
        
        print(f"✓ Canary deployment started successfully!")
        print(f"  Deployment ID: {result.deployment_id}")
        print(f"  Traffic Split: {result.traffic_split}")
        print(f"  Start Time: {result.start_time}")
        
    except Exception as e:
        print(f"✗ Failed to start canary deployment: {e}")
        sys.exit(1)


def stop_canary(promote: bool = False):
    """Stop the current canary deployment."""
    from modules.canary import get_global_instances
    instances = get_global_instances()
    canary_executor = instances['canary_executor']
    audit_logger = instances['audit_logger']
    
    action = "promote" if promote else "rollback"
    print(f"Stopping canary deployment with {action}...")
    
    try:
        result = canary_executor.stop_canary(promote=promote)
        
        if promote:
            audit_logger.log_canary_promote(
                deployment_id=result.deployment_id,
                candidate_config=result.candidate_config,
                metrics_summary=result.metrics_summary
            )
            print(f"✓ Canary deployment promoted successfully!")
        else:
            audit_logger.log_canary_rollback(
                deployment_id=result.deployment_id,
                candidate_config=result.candidate_config,
                reason=result.rollback_reason or "Manual rollback",
                metrics_summary=result.metrics_summary
            )
            print(f"✓ Canary deployment rolled back successfully!")
            if result.rollback_reason:
                print(f"  Reason: {result.rollback_reason}")
        
        print(f"  Final Status: {result.status}")
        print(f"  Total Requests: {result.total_requests}")
        if result.duration_seconds:
            print(f"  Duration: {result.duration_seconds:.1f} seconds")
        
    except Exception as e:
        print(f"✗ Failed to stop canary deployment: {e}")
        sys.exit(1)


def create_config(name: str, description: str = ""):
    """Create a new configuration from current parameters."""
    config_manager = get_config_manager()
    audit_logger = get_audit_logger()
    
    print(f"Creating new configuration: {name}")
    
    try:
        # Create configuration from current parameters
        config = config_manager.create_config_from_current(name, description)
        
        # Save the configuration
        config_manager.save_preset(config)
        
        # Log audit event
        audit_logger.log_config_operation(
            operation_type=audit_logger.AuditEventType.CONFIG_CREATE,
            config_name=name,
            config_details={
                "macro_knobs": config.macro_knobs,
                "derived_params": config.derived_params,
                "description": config.description
            }
        )
        
        print(f"✓ Configuration created successfully!")
        print(f"  Name: {config.name}")
        print(f"  Description: {config.description}")
        print(f"  Macro Knobs: latency_guard={config.macro_knobs['latency_guard']:.2f}, recall_bias={config.macro_knobs['recall_bias']:.2f}")
        
    except Exception as e:
        print(f"✗ Failed to create configuration: {e}")
        sys.exit(1)


def show_metrics(config_name: str = None, window_minutes: int = 10):
    """Show metrics for a configuration or all configurations."""
    metrics_collector = get_metrics_collector()
    
    print(f"Metrics Summary (Last {window_minutes} minutes):")
    print("=" * 60)
    
    if config_name:
        # Show metrics for specific configuration
        summary = metrics_collector.get_summary_stats(config_name, window_minutes)
        _print_metrics_summary(summary)
    else:
        # Show metrics for all configurations
        config_manager = get_config_manager()
        presets = config_manager.list_presets()
        
        for preset in presets:
            try:
                summary = metrics_collector.get_summary_stats(preset, window_minutes)
                if summary['total_responses'] > 0:
                    print(f"\nConfiguration: {preset}")
                    _print_metrics_summary(summary)
            except Exception as e:
                print(f"\nConfiguration: {preset} (ERROR: {e})")


def _print_metrics_summary(summary: Dict[str, Any]):
    """Print a metrics summary in a formatted way."""
    print(f"  Total Responses: {summary['total_responses']}")
    print(f"  Buckets: {summary['bucket_count']}")
    print(f"  Avg P95 Latency: {summary['avg_p95_ms']:.2f} ms")
    print(f"  Avg Recall@10: {summary['avg_recall_at_10']:.3f}")
    print(f"  SLO Violations: {summary['total_slo_violations']}")
    print(f"  SLO Violation Rate: {summary['slo_violation_rate']:.2%}")


def export_results(output_dir: str = "reports/canary"):
    """Export canary results and metrics to JSON files."""
    canary_executor = get_canary_executor()
    audit_logger = get_audit_logger()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    print(f"Exporting results to {output_path}...")
    
    try:
        # Export canary result
        result_file = output_path / f"canary_result_{timestamp}.json"
        canary_executor.export_result_to_json(str(result_file))
        print(f"✓ Canary result exported to: {result_file}")
        
        # Export metrics
        metrics_file = output_path / f"metrics_{timestamp}.json"
        canary_executor.get_metrics_export(str(metrics_file))
        print(f"✓ Metrics exported to: {metrics_file}")
        
        # Export SLO violations
        violations_file = output_path / f"violations_{timestamp}.json"
        canary_executor.get_violations_export(str(violations_file))
        print(f"✓ SLO violations exported to: {violations_file}")
        
        # Export audit events
        audit_file = output_path / f"audit_{timestamp}.json"
        audit_logger.export_audit_events(str(audit_file))
        print(f"✓ Audit events exported to: {audit_file}")
        
    except Exception as e:
        print(f"✗ Failed to export results: {e}")
        sys.exit(1)


def show_audit_trail(deployment_id: str = None, hours: int = 24):
    """Show audit trail for a deployment or recent events."""
    audit_logger = get_audit_logger()
    
    if deployment_id:
        print(f"Audit Trail for Deployment: {deployment_id}")
        print("=" * 60)
        events = audit_logger.get_deployment_audit_trail(deployment_id)
    else:
        print(f"Recent Audit Events (Last {hours} hours):")
        print("=" * 60)
        events = audit_logger.get_recent_events(hours=hours, limit=50)
    
    if not events:
        print("No audit events found.")
        return
    
    for event in events:
        status = "✓" if event.success else "✗"
        print(f"{status} [{event.timestamp}] {event.event_type.value}")
        print(f"    Deployment: {event.deployment_id or 'N/A'}")
        print(f"    Config: {event.config_name or 'N/A'}")
        print(f"    User: {event.user_id or 'system'}")
        
        if event.error_message:
            print(f"    Error: {event.error_message}")
        
        if event.details:
            action = event.details.get('action', '')
            if action:
                print(f"    Action: {action}")
        
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Canary Deployment CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List presets command
    subparsers.add_parser('list', help='List available configuration presets')
    
    # Status command
    subparsers.add_parser('status', help='Show current canary deployment status')
    
    # Start canary command
    start_parser = subparsers.add_parser('start', help='Start a canary deployment')
    start_parser.add_argument('candidate', help='Candidate configuration name')
    
    # Stop canary command
    stop_parser = subparsers.add_parser('stop', help='Stop current canary deployment')
    stop_group = stop_parser.add_mutually_exclusive_group()
    stop_group.add_argument('--promote', action='store_true', help='Promote candidate configuration')
    stop_group.add_argument('--rollback', action='store_true', help='Rollback to last good configuration')
    
    # Create config command
    create_parser = subparsers.add_parser('create', help='Create a new configuration')
    create_parser.add_argument('name', help='Configuration name')
    create_parser.add_argument('--description', help='Configuration description')
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show metrics')
    metrics_parser.add_argument('--config', help='Specific configuration name')
    metrics_parser.add_argument('--window', type=int, default=10, help='Time window in minutes')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export results to JSON files')
    export_parser.add_argument('--output', default='reports/canary', help='Output directory')
    
    # Audit command
    audit_parser = subparsers.add_parser('audit', help='Show audit trail')
    audit_parser.add_argument('--deployment', help='Specific deployment ID')
    audit_parser.add_argument('--hours', type=int, default=24, help='Hours to look back')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'list':
            list_presets()
        elif args.command == 'status':
            show_status()
        elif args.command == 'start':
            start_canary(args.candidate)
        elif args.command == 'stop':
            promote = args.promote or (not args.rollback and input("Promote candidate? (y/N): ").lower().startswith('y'))
            stop_canary(promote=promote)
        elif args.command == 'create':
            create_config(args.name, args.description or "")
        elif args.command == 'metrics':
            show_metrics(args.config, args.window)
        elif args.command == 'export':
            export_results(args.output)
        elif args.command == 'audit':
            show_audit_trail(args.deployment, args.hours)
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
