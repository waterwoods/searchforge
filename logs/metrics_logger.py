"""Lightweight metrics logger - pure Python with csv and datetime only."""
import csv
from datetime import datetime
from pathlib import Path


class MetricsLogger:
    """Simple CSV-based metrics logger with rolling average support."""
    
    HEADERS = ["timestamp", "p95_ms", "recall_at10", "tokens_in", "tokens_out", "est_cost", "success"]
    
    def __init__(self, log_dir="logs", filename="api_metrics.csv"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.filepath = self.log_dir / filename
        
        if not self.filepath.exists():
            with open(self.filepath, 'w', newline='') as f:
                csv.writer(f).writerow(self.HEADERS)
    
    def log(self, p95_ms, recall_at10, tokens_in, tokens_out, est_cost, success=True):
        """Append a single metrics entry with timestamp."""
        timestamp = datetime.now().isoformat()
        with open(self.filepath, 'a', newline='') as f:
            csv.writer(f).writerow([timestamp, p95_ms, recall_at10, tokens_in, tokens_out, est_cost, success])
    
    def get_recent_metrics(self, window=100):
        """Read recent metrics for rolling average computation."""
        if not self.filepath.exists():
            return []
        
        with open(self.filepath, 'r') as f:
            metrics = list(csv.DictReader(f))
        
        return metrics[-window:] if len(metrics) > window else metrics
    
    def compute_rolling_averages(self, window=100):
        """Compute rolling averages for /metrics endpoint."""
        recent = self.get_recent_metrics(window)
        
        if not recent:
            return {
                "count": 0, "avg_p95_ms": 0, "avg_recall": 0, 
                "avg_tokens_in": 0, "avg_tokens_out": 0, "avg_cost": 0
            }
        
        count = len(recent)
        total_p95 = sum(float(m["p95_ms"]) for m in recent)
        total_recall = sum(float(m["recall_at10"]) for m in recent)
        total_tokens_in = sum(float(m["tokens_in"]) for m in recent)
        total_tokens_out = sum(float(m["tokens_out"]) for m in recent)
        total_cost = sum(float(m["est_cost"]) for m in recent)
        
        return {
            "count": count,
            "avg_p95_ms": round(total_p95 / count, 2),
            "avg_recall": round(total_recall / count, 4),
            "avg_tokens_in": round(total_tokens_in / count, 2),
            "avg_tokens_out": round(total_tokens_out / count, 2),
            "avg_cost": round(total_cost / count, 6)
        }

