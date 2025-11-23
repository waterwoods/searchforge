"""HTTP utility with retry logic for connection errors and timeouts."""

import json as json_module
import random
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen


def fetch_json(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout: float = 10.0,
    max_retry: int = 6,
    backoff_base: float = 0.5,
) -> Dict[str, Any]:
    """
    Fetch JSON from URL with exponential backoff retry for connection errors.
    
    Retries on:
    - ConnectionError (network issues)
    - ProtocolError (broken connection)
    - ReadTimeout (timeout)
    - 5xx server errors
    
    Does NOT retry on:
    - 4xx client errors (bad request, unauthorized, etc.)
    
    Args:
        url: URL to fetch
        method: HTTP method (default: GET)
        headers: Optional HTTP headers dict
        json: Optional JSON data to send (for POST/PUT)
        timeout: Request timeout in seconds (default: 10)
        max_retry: Maximum number of retries (default: 6)
        backoff_base: Base backoff delay in seconds (default: 0.5)
        
    Returns:
        Parsed JSON response as dict
        
    Raises:
        HTTPError: For 4xx errors (not retried)
        URLError: For connection errors after all retries exhausted
    """
    last_exception = None
    request_headers = headers.copy() if headers else {}
    
    for attempt in range(max_retry + 1):
        try:
            payload = None
            
            if json is not None:
                payload = json_module.dumps(json).encode("utf-8")
                request_headers["Content-Type"] = "application/json"
            
            req = Request(url, data=payload, headers=request_headers, method=method)
            
            with urlopen(req, timeout=timeout) as resp:
                if resp.status >= 500:
                    # 5xx server error - retry
                    status = resp.status
                    print(f"[http_util] Attempt {attempt + 1}/{max_retry + 1}: Server error {status}, will retry")
                    raise HTTPError(
                        url, status, f"Server error {status}",
                        resp.headers, resp
                    )
                elif resp.status >= 400:
                    # 4xx client error - don't retry
                    print(f"[http_util] Attempt {attempt + 1}/{max_retry + 1}: Client error {resp.status}, no retry")
                    raise HTTPError(
                        url, resp.status, f"Client error {resp.status}",
                        resp.headers, resp
                    )
                
                response_data = resp.read().decode("utf-8")
                if attempt > 0:
                    print(f"[http_util] Request succeeded after {attempt + 1} attempts")
                return json_module.loads(response_data)
                
        except HTTPError as e:
            if e.code >= 400 and e.code < 500:
                # 4xx client errors - don't retry
                print(f"[http_util] Client error {e.code}, not retrying")
                raise
            # 5xx server errors - retry
            last_exception = e
            if attempt < max_retry:
                delay = backoff_base * (2 ** attempt)
                # Cap delay at ~30 seconds (total duration ~30s)
                delay = min(delay, 30.0)
                print(f"[http_util] Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retry + 1})")
                time.sleep(delay)
                continue
            print(f"[http_util] All retries exhausted for {url}")
            raise
            
        except (URLError, OSError) as e:
            # Connection errors, timeouts, etc. - retry
            error_str = str(e).lower()
            is_retryable = any(
                keyword in error_str
                for keyword in ["connection", "timeout", "timed out", "network", "temporarily unavailable"]
            )
            
            if not is_retryable:
                # Non-retryable error
                print(f"[http_util] Non-retryable error: {e}")
                raise
            
            last_exception = e
            if attempt < max_retry:
                delay = backoff_base * (2 ** attempt)
                # Cap delay at ~30 seconds
                delay = min(delay, 30.0)
                print(f"[http_util] Connection error, retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retry + 1}): {e}")
                time.sleep(delay)
                continue
            
            # All retries exhausted
            print(f"[http_util] All retries exhausted for {url}: {e}")
            raise URLError(f"Failed after {max_retry} retries: {e}") from e
    
    # Should not reach here, but just in case
    if last_exception:
        raise last_exception
    raise URLError("Unexpected error in fetch_json")


def wait_ready(base: str, timeout: int = 300, consecutive: int = 3) -> bool:
    """
    Wait for backend readiness by polling /readyz endpoint.
    
    Requires consecutive successful checks where clients_ready==true.
    Resets counter on connection errors.
    
    Args:
        base: Base URL (e.g., "http://localhost:8000")
        timeout: Maximum time to wait in seconds (default: 300)
        consecutive: Number of consecutive successful checks required (default: 3)
        
    Returns:
        True if ready, False if timeout
        
    Raises:
        URLError: If connection fails after all retries
    """
    readyz_url = f"{base.rstrip('/')}/readyz"
    deadline = time.time() + timeout
    success_count = 0
    
    print(f"[http_util] Waiting for readiness at {readyz_url} (timeout={timeout}s, consecutive={consecutive})")
    
    while time.time() < deadline:
        try:
            response = fetch_json(readyz_url, timeout=5.0, max_retry=2, backoff_base=0.5)
            clients_ready = response.get("clients_ready", False)
            
            if clients_ready:
                success_count += 1
                print(f"[http_util] Readiness check {success_count}/{consecutive} passed")
                if success_count >= consecutive:
                    print(f"[http_util] Backend ready after {consecutive} consecutive checks")
                    return True
            else:
                success_count = 0
                print(f"[http_util] Readiness check failed (clients_ready=false), reset counter")
                
        except (URLError, HTTPError, Exception) as e:
            # Connection error resets counter
            success_count = 0
            error_msg = str(e)
            if "404" in error_msg or "Connection refused" in error_msg:
                print(f"[http_util] Readiness check failed (connection error), reset counter: {e}")
            else:
                print(f"[http_util] Readiness check error, reset counter: {e}")
        
        # Wait a bit before next check
        time.sleep(1.0)
    
    print(f"[http_util] Readiness timeout after {timeout}s (got {success_count}/{consecutive} consecutive)")
    return False

