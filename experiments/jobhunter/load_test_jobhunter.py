#!/usr/bin/env python3
"""
load_test_jobhunter.py - Simple Load Test for JobHunter Agent API

A lightweight load testing script for the JobHunter analyze HTTP endpoint.
Measures latency, success/error rates, and generates percentile statistics.
Includes a simple SLO evaluation (99% success rate, p95 <= 1000ms).

Usage:
    python -m experiments.jobhunter.load_test_jobhunter \
        --url http://localhost:8082/api/jobhunter/analyze \
        --concurrency 2 \
        --requests 20

This script sends concurrent POST requests to the JobHunter analyze endpoint
and collects latency and error metrics for SLO validation.
"""

import asyncio
import argparse
import time
from typing import List, Tuple
from statistics import mean
from pathlib import Path

import httpx


# Built-in JD text used when --jd-file is not provided
DEFAULT_JD_TEXT = """
We are looking for a Senior LLM / AI Agent Engineer to join our team.

Requirements:
- 5+ years of experience in LLM applications and agent frameworks
- Strong background in Python, FastAPI, and async programming
- Experience with LangChain, LangGraph, or similar agent orchestration frameworks
- Deep understanding of RAG systems and vector databases (Qdrant, Pinecone)
- Experience with GCP services including BigQuery and Cloud Run
- Proven track record building data pipelines and observability systems
- Experience with Kubernetes and containerized deployments

Nice to have:
- Experience with evaluation frameworks and SLO monitoring
- Understanding of agentic workflows and multi-agent systems

This role involves designing and implementing AI agent systems, optimizing RAG pipelines,
and building observability tooling for production AI systems.
"""


async def send_request(
    client: httpx.AsyncClient,
    url: str,
    jd_description: str,
    timeout: float = 120.0,
) -> Tuple[bool, float, int]:
    """
    Send a single POST request to the JobHunter analyze endpoint.

    Args:
        client: httpx async client
        url: Target endpoint URL
        jd_description: Job description text
        timeout: Request timeout in seconds (default: 120.0)

    Returns:
        Tuple of (success: bool, latency_ms: float, status_code: int)
        status_code: HTTP status code if success, -1 for timeout, -2 for connection error, -3 for other error
    """
    payload = {
        "jd_input": {
            "job_id": "TEST-JOB",
            "company": "TestCo",
            "title": "Senior Data / LLM Engineer",
            "location": "Remote",
            "description": jd_description,
        },
        "use_default_profile": True,
    }

    start_time = time.time()
    try:
        response = await client.post(url, json=payload, timeout=timeout)
        latency_ms = (time.time() - start_time) * 1000
        success = response.status_code == 200
        return success, latency_ms, response.status_code
    except httpx.TimeoutException as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, latency_ms, -1  # -1 indicates timeout
    except httpx.ConnectError as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, latency_ms, -2  # -2 indicates connection error
    except httpx.RequestError as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, latency_ms, -3  # -3 indicates other request error


async def health_check(url: str, timeout: float = 3.0) -> bool:
    """
    Perform a health check by sending a simple request to the endpoint.
    
    Args:
        url: Target endpoint URL
        timeout: Health check timeout in seconds (default: 3.0)
        
    Returns:
        True if health check passes, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Try to connect to the endpoint (we'll send a minimal request)
            # Extract base URL for healthz check
            if "/api/jobhunter/analyze" in url:
                healthz_url = url.replace("/api/jobhunter/analyze", "/healthz")
            else:
                healthz_url = url.rsplit("/", 1)[0] + "/healthz" if "/" in url else url + "/healthz"
            
            response = await client.get(healthz_url)
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    except Exception:
        return False


async def run_load_test(
    url: str,
    concurrency: int,
    total_requests: int,
    jd_description: str,
    timeout: float = 120.0,
) -> None:
    """
    Run the load test with specified concurrency and total requests.

    Args:
        url: Target endpoint URL
        concurrency: Number of concurrent requests
        total_requests: Total number of requests to send
        jd_description: Job description text to use in requests
    """
    print(f"Starting load test...")
    print(f"URL: {url}")
    print(f"Concurrency: {concurrency}, Total requests: {total_requests}")
    print()

    # Semaphore to limit concurrency
    semaphore = asyncio.Semaphore(concurrency)
    results: List[Tuple[bool, float, int]] = []

    async def bounded_request(request_id: int) -> None:
        """Send a single request with concurrency control."""
        async with semaphore:
            async with httpx.AsyncClient(timeout=timeout) as client:
                success, latency_ms, status_code = await send_request(
                    client, url, jd_description, timeout=timeout
                )
                results.append((success, latency_ms, status_code))
                if request_id % 10 == 0:
                    print(f"Progress: {request_id + 1}/{total_requests} requests completed")

    # Create all tasks
    tasks = [bounded_request(i) for i in range(total_requests)]

    # Run all tasks concurrently
    start_time = time.time()
    await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    # Calculate statistics
    # Separate infra errors (connection/timeout) from application-level requests
    infra_errors = sum(1 for _, _, status in results if status in (-1, -2))  # timeout or connection error
    app_requests = [r for r in results if r[2] not in (-1, -2)]  # requests that reached the server
    
    success_count = sum(1 for success, _, _ in app_requests if success)
    app_error_count = len(app_requests) - success_count
    total_app_requests = len(app_requests)
    
    # SLO is calculated only based on application-level requests
    success_rate = (success_count / total_app_requests * 100) if total_app_requests > 0 else 0.0

    # Count error types for display
    timeout_count = sum(1 for _, _, status in results if status == -1)
    connect_error_count = sum(1 for _, _, status in results if status == -2)
    other_error_count = sum(1 for _, _, status in results if status == -3)
    http_error_count = sum(1 for success, _, status in app_requests if not success and status > 0)

    # Only calculate latency stats for successful requests
    success_latencies = [latency for success, latency, _ in app_requests if success]
    avg_latency = mean(success_latencies) if success_latencies else 0.0

    # Calculate percentiles for successful requests
    sorted_success_latencies = sorted(success_latencies)
    p50 = sorted_success_latencies[int(len(sorted_success_latencies) * 0.5)] if sorted_success_latencies else 0.0
    p95 = sorted_success_latencies[int(len(sorted_success_latencies) * 0.95)] if sorted_success_latencies else 0.0

    # Calculate QPS (requests per second)
    qps = total_requests / total_time if total_time > 0 else 0.0

    # Print summary
    print()
    print("=" * 50)
    print("Load Test Summary")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Requests: {total_requests}, Concurrency: {concurrency}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Application requests: {total_app_requests} (reached server)")
    print(f"Success: {success_count}, Application errors: {app_error_count}")
    if infra_errors > 0:
        print(f"Infra errors: {infra_errors} (connection/timeout issues not counted against SLO)")
    if total_app_requests > 0:
        print(f"Success rate: {success_rate:.1f}% (based on {total_app_requests} app requests)")
    error_count = timeout_count + connect_error_count + other_error_count + http_error_count
    if error_count > 0:
        print(f"Error breakdown: {timeout_count} timeouts, {connect_error_count} connection errors, {other_error_count} other errors, {http_error_count} HTTP errors")
    if success_latencies:
        print(f"Latency (ms): avg={avg_latency:.1f}, p50={p50:.1f}, p95={p95:.1f}")
    else:
        print(f"Latency (ms): No successful requests to calculate")
    print(f"Throughput: {qps:.2f} QPS")
    print("=" * 50)

    # SLO evaluation
    print()
    print("=" * 50)
    print("SLO Evaluation")
    print("=" * 50)
    
    # SLO thresholds
    SLO_SUCCESS_RATE = 99.0  # >= 99%
    SLO_P95_LATENCY_MS = 1000.0  # <= 1000ms
    
    slo_pass = success_rate >= SLO_SUCCESS_RATE and p95 <= SLO_P95_LATENCY_MS
    
    if slo_pass:
        print("SLO RESULT: PASS ✅")
        print(f"- success_rate >= {SLO_SUCCESS_RATE}% and p95 <= {SLO_P95_LATENCY_MS}ms")
    else:
        print("SLO RESULT: FAIL ❌")
        if success_rate < SLO_SUCCESS_RATE:
            print(f"- success_rate {success_rate:.1f}% < {SLO_SUCCESS_RATE}% (target)")
        if p95 > SLO_P95_LATENCY_MS:
            print(f"- p95 latency {p95:.1f}ms > {SLO_P95_LATENCY_MS}ms (target)")
    
    print("=" * 50)


def load_jd_from_file(file_path: str) -> str:
    """
    Load job description text from a file.
    
    Args:
        file_path: Path to the JD text file
        
    Returns:
        Job description text as string
    """
    jd_path = Path(file_path)
    if not jd_path.exists():
        raise FileNotFoundError(f"JD file not found: {file_path}")
    
    with open(jd_path, "r", encoding="utf-8") as f:
        return f.read().strip()


def main() -> None:
    """Main entry point for the load test script."""
    parser = argparse.ArgumentParser(
        description="Load test script for JobHunter analyze API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults (uses built-in JD)
  python -m experiments.jobhunter.load_test_jobhunter

  # Custom URL and parameters
  python -m experiments.jobhunter.load_test_jobhunter \\
    --url http://localhost:8082/api/jobhunter/analyze \\
    --concurrency 2 \\
    --requests 20

  # Use a custom JD file
  python -m experiments.jobhunter.load_test_jobhunter \\
    --url http://localhost:8082/api/jobhunter/analyze \\
    --concurrency 2 \\
    --requests 20 \\
    --jd-file /path/to/job_description.txt
        """,
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8082/api/jobhunter/analyze",
        help="Target endpoint URL (default: http://localhost:8082/api/jobhunter/analyze)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=2,
        help="Number of concurrent requests (default: 2)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=50,
        help="Total number of requests to send (default: 50)",
    )
    parser.add_argument(
        "--jd-file",
        type=str,
        default=None,
        help="Path to a text file containing job description. If not provided, uses built-in JD text.",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.concurrency < 1:
        parser.error("--concurrency must be >= 1")
    if args.requests < 1:
        parser.error("--requests must be >= 1")
    if args.concurrency > args.requests:
        parser.error("--concurrency cannot be greater than --requests")

    # Load JD text
    if args.jd_file:
        try:
            jd_description = load_jd_from_file(args.jd_file)
            print(f"Loaded JD from file: {args.jd_file}")
        except Exception as e:
            print(f"Error loading JD file: {e}")
            return
    else:
        jd_description = DEFAULT_JD_TEXT.strip()
        print("Using built-in JD text")

    # Health check before running load test
    print("Performing health check...")
    try:
        health_check_passed = asyncio.run(health_check(args.url, timeout=3.0))
        if not health_check_passed:
            print("❌ Health check failed: port-forward may be down or service not ready")
            print("Please ensure:")
            print("  1. kubectl port-forward deployment/jobhunter-api 8082:8000 is running")
            print("  2. JobHunter API is deployed and ready in K8S")
            return
        print("✅ Health check passed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("Please ensure port-forward is active and service is ready")
        return

    # Run the load test
    timeout_seconds = 120.0
    print(f"Starting load test with timeout={timeout_seconds}s...")
    try:
        asyncio.run(
            run_load_test(
                url=args.url,
                concurrency=args.concurrency,
                total_requests=args.requests,
                jd_description=jd_description,
                timeout=timeout_seconds,
            )
        )
    except KeyboardInterrupt:
        print("\nLoad test interrupted by user")
    except Exception as e:
        print(f"Error running load test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


