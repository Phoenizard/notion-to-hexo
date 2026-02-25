"""
Network utilities for Notion to Hexo.

Provides HTTP request functionality with timeout and retry support.
"""

import time
import logging
import requests

from .config import TIMEOUT_API, TIMEOUT_IMAGE, MAX_RETRIES, RETRY_BACKOFF

logger = logging.getLogger(__name__)


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
    timeout_type = kwargs.pop('timeout_type', 'api')
    timeout = TIMEOUT_IMAGE if timeout_type == 'image' else TIMEOUT_API
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
            logger.warning("请求超时 (尝试 %d/%d), %d秒后重试...",
                           attempt + 1, MAX_RETRIES, wait_time)
            time.sleep(wait_time)
        except requests.exceptions.ConnectionError as e:
            last_exception = e
            wait_time = RETRY_BACKOFF ** attempt
            logger.warning("连接错误 (尝试 %d/%d), %d秒后重试...",
                           attempt + 1, MAX_RETRIES, wait_time)
            time.sleep(wait_time)
        except requests.exceptions.HTTPError as e:
            if e.response is not None and 400 <= e.response.status_code < 500:
                raise
            last_exception = e
            wait_time = RETRY_BACKOFF ** attempt
            logger.warning("服务器错误 (尝试 %d/%d), %d秒后重试...",
                           attempt + 1, MAX_RETRIES, wait_time)
            time.sleep(wait_time)

    if last_exception is not None:
        raise last_exception
    raise requests.exceptions.RequestException(f"Request failed after {MAX_RETRIES} retries")
