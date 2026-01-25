"""
Network utilities for Notion to Hexo.

Provides HTTP request functionality with timeout and retry support.
"""

import time
import requests

from .config import TIMEOUT_API, TIMEOUT_IMAGE, MAX_RETRIES, RETRY_BACKOFF


def request_with_retry(method, url, **kwargs):
    """
    Make HTTP request with timeout and exponential backoff retry.

    Args:
        method: 'get', 'post', etc.
        url: Target URL
        **kwargs: Additional arguments passed to requests (headers, stream, etc.)
                  Special kwarg 'timeout_type' can be 'api' or 'image'

    Returns:
        Response object

    Raises:
        requests.RequestException: After all retries exhausted
    """
    # Determine timeout based on request type
    timeout_type = kwargs.pop('timeout_type', 'api')
    timeout = TIMEOUT_IMAGE if timeout_type == 'image' else TIMEOUT_API

    # Ensure timeout is always set
    kwargs.setdefault('timeout', timeout)

    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            response = getattr(requests, method)(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            last_exception = e
            wait_time = RETRY_BACKOFF ** attempt
            print(f"请求超时 (尝试 {attempt + 1}/{MAX_RETRIES}), {wait_time}秒后重试...")
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            last_exception = e
            wait_time = RETRY_BACKOFF ** attempt
            print(f"连接错误 (尝试 {attempt + 1}/{MAX_RETRIES}), {wait_time}秒后重试...")
            time.sleep(wait_time)
        except requests.exceptions.HTTPError as e:
            # Don't retry client errors (4xx), only server errors (5xx)
            if e.response is not None and 400 <= e.response.status_code < 500:
                raise  # Re-raise immediately for client errors
            last_exception = e
            wait_time = RETRY_BACKOFF ** attempt
            print(f"服务器错误 (尝试 {attempt + 1}/{MAX_RETRIES}), {wait_time}秒后重试...")
            time.sleep(wait_time)

    # All retries exhausted
    if last_exception is not None:
        raise last_exception
    raise requests.exceptions.RequestException(f"Request failed after {MAX_RETRIES} retries")
