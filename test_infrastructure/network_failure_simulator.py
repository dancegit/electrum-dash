"""
Network Failure Simulation Framework
Simulates various network conditions and failures for robust testing
"""

import time
import random
import socket
import threading
from typing import Optional, Callable, Dict, Any, List
from unittest.mock import MagicMock, patch
import requests
import requests.exceptions
import pytest


class NetworkFailureSimulator:
    """Simulate various network failure scenarios"""
    
    @staticmethod
    def timeout_response(delay: float = 30.0):
        """Simulate a request timeout"""
        def side_effect(*args, **kwargs):
            time.sleep(delay)
            raise requests.exceptions.Timeout(f"Request timed out after {delay}s")
        return side_effect
    
    @staticmethod
    def connection_error():
        """Simulate connection refused/failed"""
        def side_effect(*args, **kwargs):
            raise requests.exceptions.ConnectionError(
                "Failed to establish a new connection: [Errno 111] Connection refused"
            )
        return side_effect
    
    @staticmethod
    def dns_failure():
        """Simulate DNS resolution failure"""
        def side_effect(*args, **kwargs):
            raise requests.exceptions.ConnectionError(
                "Failed to resolve hostname: [Errno -2] Name or service not known"
            )
        return side_effect
    
    @staticmethod
    def ssl_error():
        """Simulate SSL/TLS errors"""
        def side_effect(*args, **kwargs):
            raise requests.exceptions.SSLError(
                "SSL: CERTIFICATE_VERIFY_FAILED certificate verify failed"
            )
        return side_effect
    
    @staticmethod
    def intermittent_failure(failure_rate: float = 0.5,
                           failure_type: str = "connection"):
        """Simulate intermittent network failures"""
        def side_effect(*args, **kwargs):
            if random.random() < failure_rate:
                if failure_type == "connection":
                    raise requests.exceptions.ConnectionError("Intermittent connection failure")
                elif failure_type == "timeout":
                    raise requests.exceptions.Timeout("Intermittent timeout")
                elif failure_type == "500":
                    response = MagicMock()
                    response.status_code = 500
                    response.text = "Internal Server Error"
                    response.raise_for_status = MagicMock(
                        side_effect=requests.exceptions.HTTPError("500 Server Error")
                    )
                    return response
            else:
                # Success case - return mock success response
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {"status": "ok"}
                response.text = '{"status": "ok"}'
                return response
        
        return side_effect
    
    @staticmethod
    def slow_network(min_delay: float = 0.5, max_delay: float = 3.0):
        """Simulate slow network with variable latency"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def packet_loss(loss_rate: float = 0.1):
        """Simulate packet loss by dropping responses"""
        def side_effect(*args, **kwargs):
            if random.random() < loss_rate:
                # Simulate packet loss with connection reset
                raise requests.exceptions.ConnectionError(
                    "Connection reset by peer"
                )
            else:
                # Normal response
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {"status": "ok"}
                return response
        return side_effect
    
    @staticmethod
    def bandwidth_limit(bytes_per_second: int = 1024):
        """Simulate bandwidth limitations"""
        class BandwidthLimitedResponse:
            def __init__(self, content: bytes, bps: int):
                self.content = content
                self.bps = bps
                self.status_code = 200
                
            def iter_content(self, chunk_size: int = 1024):
                """Yield content with bandwidth limitation"""
                for i in range(0, len(self.content), chunk_size):
                    chunk = self.content[i:i + chunk_size]
                    # Calculate sleep time based on bandwidth
                    sleep_time = len(chunk) / self.bps
                    time.sleep(sleep_time)
                    yield chunk
        
        def side_effect(*args, **kwargs):
            # Return bandwidth-limited response
            mock_content = b"x" * 10240  # 10KB of data
            return BandwidthLimitedResponse(mock_content, bytes_per_second)
        
        return side_effect
    
    @staticmethod
    def retry_with_backoff(max_retries: int = 3,
                          initial_delay: float = 1.0,
                          backoff_factor: float = 2.0):
        """Simulate retries with exponential backoff"""
        attempt_count = 0
        
        def side_effect(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count < max_retries:
                # Fail with retriable error
                delay = initial_delay * (backoff_factor ** (attempt_count - 1))
                time.sleep(delay)
                raise requests.exceptions.ConnectionError(
                    f"Attempt {attempt_count} failed"
                )
            else:
                # Success on final attempt
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {"status": "ok", "attempts": attempt_count}
                return response
        
        return side_effect
    
    @staticmethod
    def network_partition(partition_duration: float = 5.0):
        """Simulate network partition (split-brain scenario)"""
        partition_start = time.time()
        
        def side_effect(*args, **kwargs):
            if time.time() - partition_start < partition_duration:
                raise requests.exceptions.ConnectionError(
                    "Network is unreachable (partitioned)"
                )
            else:
                # Network recovered
                response = MagicMock()
                response.status_code = 200
                response.json.return_value = {"status": "recovered"}
                return response
        
        return side_effect


class NetworkConditionContext:
    """Context manager for applying network conditions"""
    
    def __init__(self, condition: Callable, target: str = 'requests.request'):
        self.condition = condition
        self.target = target
        self.patcher = None
    
    def __enter__(self):
        self.patcher = patch(self.target, side_effect=self.condition)
        self.mock = self.patcher.__enter__()
        return self.mock
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.patcher:
            self.patcher.__exit__(exc_type, exc_val, exc_tb)


# Pytest fixtures for network testing
@pytest.fixture
def network_simulator():
    """Provide network failure simulator"""
    return NetworkFailureSimulator()


@pytest.fixture
def timeout_network():
    """Simulate network timeout"""
    with NetworkConditionContext(NetworkFailureSimulator.timeout_response(1.0)):
        yield


@pytest.fixture
def flaky_network():
    """Simulate flaky network with 50% failure rate"""
    with NetworkConditionContext(
        NetworkFailureSimulator.intermittent_failure(0.5)
    ):
        yield


@pytest.fixture
def slow_network():
    """Simulate slow network"""
    def make_slow(func):
        return NetworkFailureSimulator.slow_network(0.5, 2.0)(func)
    return make_slow


# Test utilities
class NetworkTestScenarios:
    """Pre-defined network test scenarios"""
    
    @staticmethod
    def get_scenarios() -> List[Dict[str, Any]]:
        """Get list of network failure scenarios to test"""
        return [
            {
                "name": "timeout",
                "condition": NetworkFailureSimulator.timeout_response(0.5),
                "expected_error": requests.exceptions.Timeout
            },
            {
                "name": "connection_refused", 
                "condition": NetworkFailureSimulator.connection_error(),
                "expected_error": requests.exceptions.ConnectionError
            },
            {
                "name": "dns_failure",
                "condition": NetworkFailureSimulator.dns_failure(),
                "expected_error": requests.exceptions.ConnectionError
            },
            {
                "name": "ssl_error",
                "condition": NetworkFailureSimulator.ssl_error(),
                "expected_error": requests.exceptions.SSLError
            },
            {
                "name": "intermittent_failure",
                "condition": NetworkFailureSimulator.intermittent_failure(0.7),
                "expected_error": (requests.exceptions.ConnectionError, 
                                 requests.exceptions.HTTPError)
            },
            {
                "name": "packet_loss",
                "condition": NetworkFailureSimulator.packet_loss(0.3),
                "expected_error": requests.exceptions.ConnectionError
            }
        ]