#!/usr/bin/env python3
"""
generate_vitals_stream.py - Continuous Fake Vitals Data Generator

Generates realistic vitals data (HR, SpO2) with smooth drift and optional spikes.
Supports two modes:
  - stdout: Print newline-delimited JSON to stdout
  - post: HTTP POST each reading to ingest endpoint

Usage:
    python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 5
    python3 scripts/generate_vitals_stream.py --mode post --duration-sec 60 --endpoint http://localhost:8000/api/vitals/ingest
"""

import argparse
import json
import random
import signal
import sys
import time
from datetime import datetime
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class VitalsGenerator:
    """Generates realistic vitals data with smooth drift."""
    
    def __init__(self, seed: Optional[int] = None, spike_prob: float = 0.01):
        """
        Initialize the generator.
        
        Args:
            seed: Optional random seed for reproducibility
            spike_prob: Probability of generating a spike (0.0-1.0)
        """
        if seed is not None:
            random.seed(seed)
        
        self.spike_prob = spike_prob
        
        # Initialize baseline values with some randomness
        self.hr_baseline = random.uniform(60.0, 95.0)
        self.spo2_baseline = random.uniform(94.0, 99.0)
        
        # Track time for smooth drift
        self.start_time = time.time()
        self.last_update_time = self.start_time
        
        # Drift parameters (slow variation)
        self.hr_drift_rate = random.uniform(-0.5, 0.5)  # bpm per second
        self.spo2_drift_rate = random.uniform(-0.02, 0.02)  # % per second
        
        # Noise parameters
        self.hr_noise_std = 2.0  # bpm
        self.spo2_noise_std = 0.5  # %
    
    def generate(self) -> dict:
        """
        Generate a single vitals reading with realistic drift and noise.
        
        Returns:
            Dict with hr, spo2, time_ms, time_str fields
        """
        now = time.time()
        elapsed = now - self.last_update_time
        
        # Update baseline with slow drift
        self.hr_baseline += self.hr_drift_rate * elapsed
        self.spo2_baseline += self.spo2_drift_rate * elapsed
        
        # Clamp baselines to realistic ranges
        self.hr_baseline = max(60.0, min(95.0, self.hr_baseline))
        self.spo2_baseline = max(94.0, min(99.0, self.spo2_baseline))
        
        # Add small random noise
        hr_noise = random.gauss(0, self.hr_noise_std)
        spo2_noise = random.gauss(0, self.spo2_noise_std)
        
        # Optional spike (rare)
        spike_multiplier = 1.0
        if random.random() < self.spike_prob:
            # Spike: increase HR by 20-40 bpm temporarily
            spike_multiplier = random.uniform(1.3, 1.6)
        
        hr = self.hr_baseline * spike_multiplier + hr_noise
        spo2 = self.spo2_baseline + spo2_noise
        
        # Clamp final values to realistic ranges
        hr = max(50.0, min(120.0, hr))
        spo2 = max(90.0, min(100.0, spo2))
        
        # Generate timestamps
        time_ms = int(now * 1000)
        time_str = datetime.fromtimestamp(now).strftime("%Y-%m-%d %H:%M:%S")
        
        self.last_update_time = now
        
        return {
            "hr": round(hr, 1),
            "spo2": round(spo2, 1),
            "time_ms": time_ms,
            "time_str": time_str,
        }


class VitalsStream:
    """Manages the vitals data stream generation and output."""
    
    def __init__(
        self,
        interval_sec: float = 2.0,
        duration_sec: float = 60.0,
        source: str = "esp32-livingroom",
        mode: str = "stdout",
        endpoint: str = "http://localhost:8000/api/vitals/ingest",
        jitter: float = 0.2,
        seed: Optional[int] = None,
        spike_prob: float = 0.01,
    ):
        """
        Initialize the stream.
        
        Args:
            interval_sec: Base interval between readings (seconds)
            duration_sec: Total duration (0 = run forever)
            source: Device source identifier
            mode: Output mode ('stdout' or 'post')
            endpoint: HTTP endpoint for post mode
            jitter: Random jitter factor (0.0-1.0)
            seed: Optional random seed
            spike_prob: Probability of spike events
        """
        self.interval_sec = interval_sec
        self.duration_sec = duration_sec
        self.source = source
        self.mode = mode
        self.endpoint = endpoint
        self.jitter = jitter
        self.spike_prob = spike_prob
        
        self.generator = VitalsGenerator(seed=seed, spike_prob=spike_prob)
        self.total_sent = 0
        self.start_time = time.time()
        self.intervals = []
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self.should_stop = False
    
    def _signal_handler(self, signum, frame):
        """Handle SIGINT/SIGTERM for graceful shutdown."""
        self.should_stop = True
    
    def _calculate_interval(self) -> float:
        """Calculate next interval with jitter."""
        jitter_amount = self.interval_sec * self.jitter * (random.random() * 2 - 1)
        return max(0.1, self.interval_sec + jitter_amount)
    
    def _post_reading(self, reading: dict, max_retries: int = 3) -> bool:
        """
        POST a reading to the ingest endpoint with retry logic.
        
        Args:
            reading: Reading dict to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        payload = json.dumps(reading).encode('utf-8')
        req = Request(
            self.endpoint,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        for attempt in range(max_retries):
            try:
                with urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        return True
                    else:
                        if attempt < max_retries - 1:
                            time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                            continue
                        return False
            except HTTPError as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
                return False
            except URLError as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                print(f"URL error: {e.reason}", file=sys.stderr)
                return False
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                print(f"Unexpected error: {e}", file=sys.stderr)
                return False
        
        return False
    
    def _output_reading(self, reading: dict):
        """Output a reading based on mode."""
        reading['source'] = self.source
        
        if self.mode == 'stdout':
            print(json.dumps(reading))
            sys.stdout.flush()
        elif self.mode == 'post':
            if self._post_reading(reading):
                self.total_sent += 1
            else:
                print(f"Failed to POST reading: {reading}", file=sys.stderr)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")
    
    def run(self):
        """Run the stream generator."""
        try:
            while not self.should_stop:
                # Check duration limit
                if self.duration_sec > 0:
                    elapsed = time.time() - self.start_time
                    if elapsed >= self.duration_sec:
                        break
                
                # Generate and output reading
                reading = self.generator.generate()
                self._output_reading(reading)
                
                if self.mode == 'stdout':
                    self.total_sent += 1
                
                # Track interval for summary
                interval = self._calculate_interval()
                self.intervals.append(interval)
                
                # Sleep with jitter
                time.sleep(interval)
        
        except KeyboardInterrupt:
            self.should_stop = True
        
        finally:
            self._print_summary()
    
    def _print_summary(self):
        """Print final summary statistics."""
        elapsed = time.time() - self.start_time
        avg_interval = sum(self.intervals) / len(self.intervals) if self.intervals else 0.0
        
        print("\n" + "=" * 60, file=sys.stderr)
        print("Vitals Stream Summary", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"Total readings sent: {self.total_sent}", file=sys.stderr)
        print(f"Mode: {self.mode}", file=sys.stderr)
        if self.mode == 'post':
            print(f"Endpoint: {self.endpoint}", file=sys.stderr)
        print(f"Duration: {elapsed:.2f} seconds", file=sys.stderr)
        print(f"Average interval: {avg_interval:.2f} seconds", file=sys.stderr)
        print("=" * 60, file=sys.stderr)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate continuous fake vitals data stream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print JSON lines to stdout for 5 seconds
  python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 5

  # POST to API for 60 seconds
  python3 scripts/generate_vitals_stream.py --mode post --duration-sec 60

  # Run forever with custom interval
  python3 scripts/generate_vitals_stream.py --mode stdout --duration-sec 0 --interval-sec 1.0
        """
    )
    
    parser.add_argument(
        '--interval-sec',
        type=float,
        default=2.0,
        help='Base interval between readings in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--duration-sec',
        type=float,
        default=60.0,
        help='Total duration in seconds (0 = run forever, default: 60.0)'
    )
    parser.add_argument(
        '--source',
        type=str,
        default='esp32-livingroom',
        help='Device source identifier (default: esp32-livingroom)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['stdout', 'post'],
        default='stdout',
        help='Output mode: stdout (print JSON) or post (HTTP POST, default: stdout)'
    )
    parser.add_argument(
        '--endpoint',
        type=str,
        default='http://localhost:8000/api/vitals/ingest',
        help='HTTP endpoint for post mode (default: http://localhost:8000/api/vitals/ingest)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (optional)'
    )
    parser.add_argument(
        '--jitter',
        type=float,
        default=0.2,
        help='Random jitter factor 0.0-1.0 (default: 0.2)'
    )
    parser.add_argument(
        '--spike-prob',
        type=float,
        default=0.01,
        help='Probability of spike events 0.0-1.0 (default: 0.01)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.interval_sec <= 0:
        parser.error("--interval-sec must be > 0")
    if args.duration_sec < 0:
        parser.error("--duration-sec must be >= 0")
    if not (0.0 <= args.jitter <= 1.0):
        parser.error("--jitter must be between 0.0 and 1.0")
    if not (0.0 <= args.spike_prob <= 1.0):
        parser.error("--spike-prob must be between 0.0 and 1.0")
    
    # Create and run stream
    stream = VitalsStream(
        interval_sec=args.interval_sec,
        duration_sec=args.duration_sec,
        source=args.source,
        mode=args.mode,
        endpoint=args.endpoint,
        jitter=args.jitter,
        seed=args.seed,
        spike_prob=args.spike_prob,
    )
    
    stream.run()


if __name__ == '__main__':
    main()
