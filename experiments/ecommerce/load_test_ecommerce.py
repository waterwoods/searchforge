#!/usr/bin/env python3
"""
load_test_ecommerce.py - Simple Load Test for Ecommerce Agent API

A lightweight load testing script for the ecommerce refund agent HTTP endpoint.
Measures latency, success/error rates, and generates percentile statistics.

Usage:
    python -m experiments.ecommerce.load_test_ecommerce \
        --url http://localhost:8080/api/ecommerce-agent/run \
        --concurrency 5 \
        --requests 50

This script sends concurrent POST requests to the ecommerce agent endpoint
and collects latency and error metrics for SLO validation.
"""

import asyncio
import argparse
import time
from typing import List, Tuple
from statistics import mean

import httpx


async def send_request(
    client: httpx.AsyncClient,
    url: str,
    order_id: str,
    user_message: str,
) -> Tuple[bool, float, int]:
    """
    Send a single POST request to the ecommerce agent endpoint.

    Args:
        client: httpx async client
        url: Target endpoint URL
        order_id: Order ID for the request
        user_message: User message for the request

    Returns:
        Tuple of (success: bool, latency_ms: float, status_code: int)
    """
    payload = {
        "order_id": order_id,
        "user_message": user_message,
    }

    start_time = time.time()
    try:
        response = await client.post(url, json=payload, timeout=30.0)
        latency_ms = (time.time() - start_time) * 1000
        success = response.status_code == 200
        return success, latency_ms, response.status_code
    except httpx.RequestError as e:
        latency_ms = (time.time() - start_time) * 1000
        return False, latency_ms, 0


async def run_load_test(
    url: str,
    concurrency: int,
    total_requests: int,
    order_id: str = "A10001",
    user_message: str = "I want a refund because the product was damaged.",
) -> None:
    """
    Run the load test with specified concurrency and total requests.

    Args:
        url: Target endpoint URL
        concurrency: Number of concurrent requests
        total_requests: Total number of requests to send
        order_id: Order ID to use in requests
        user_message: User message to use in requests
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
            async with httpx.AsyncClient() as client:
                success, latency_ms, status_code = await send_request(
                    client, url, order_id, user_message
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
    success_count = sum(1 for success, _, _ in results if success)
    error_count = total_requests - success_count
    success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0.0

    latencies = [latency for _, latency, _ in results]
    avg_latency = mean(latencies) if latencies else 0.0

    # Calculate percentiles
    sorted_latencies = sorted(latencies)
    p50 = sorted_latencies[int(len(sorted_latencies) * 0.5)] if sorted_latencies else 0.0
    p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0.0

    # Print summary
    print()
    print("=" * 50)
    print("Load Test Summary")
    print("=" * 50)
    print(f"URL: {url}")
    print(f"Requests: {total_requests}, Concurrency: {concurrency}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Success: {success_count}, Errors: {error_count} (success rate: {success_rate:.1f}%)")
    print(f"Latency (ms): avg={avg_latency:.1f}, p50={p50:.1f}, p95={p95:.1f}")
    print("=" * 50)


def main() -> None:
    """Main entry point for the load test script."""
    parser = argparse.ArgumentParser(
        description="Load test script for ecommerce agent API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with defaults
  python -m experiments.ecommerce.load_test_ecommerce

  # Custom URL and parameters
  python -m experiments.ecommerce.load_test_ecommerce \\
    --url http://localhost:8080/api/ecommerce-agent/run \\
    --concurrency 10 \\
    --requests 100
        """,
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://localhost:8080/api/ecommerce-agent/run",
        help="Target endpoint URL (default: http://localhost:8080/api/ecommerce-agent/run)",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent requests (default: 5)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=50,
        help="Total number of requests to send (default: 50)",
    )
    parser.add_argument(
        "--order-id",
        type=str,
        default="A10001",
        help="Order ID to use in requests (default: A10001)",
    )
    parser.add_argument(
        "--user-message",
        type=str,
        default="I want a refund because the product was damaged.",
        help="User message to use in requests",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.concurrency < 1:
        parser.error("--concurrency must be >= 1")
    if args.requests < 1:
        parser.error("--requests must be >= 1")
    if args.concurrency > args.requests:
        parser.error("--concurrency cannot be greater than --requests")

    # Run the load test
    asyncio.run(
        run_load_test(
            url=args.url,
            concurrency=args.concurrency,
            total_requests=args.requests,
            order_id=args.order_id,
            user_message=args.user_message,
        )
    )


if __name__ == "__main__":
    main()
