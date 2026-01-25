"""
Notion to Hexo Blog Publisher Package

This package provides tools to convert Notion pages to Hexo blog posts
with automatic image upload to Aliyun OSS.

Usage:
    from notion_to_hexo import fetch_notion_page, upload_to_oss, create_hexo_post
"""

from .config import (
    config,
    load_config,
    TIMEOUT_API,
    TIMEOUT_IMAGE,
    MAX_RETRIES,
    RETRY_BACKOFF,
)

from .network import request_with_retry

from .hexo import (
    run_hexo_command,
    sanitize_filename,
    find_hexo_executable,
)

from .notion import (
    fetch_notion_page,
    extract_notion_page_id,
)

from .converter import (
    blocks_to_markdown,
    rich_text_to_markdown,
)

from .oss import (
    upload_to_oss,
    download_notion_image,
    process_images_in_markdown,
)

from .cli import (
    main,
    create_hexo_post,
    test_mode_export,
    print_step,
)

__all__ = [
    # Config
    'config',
    'load_config',
    'TIMEOUT_API',
    'TIMEOUT_IMAGE',
    'MAX_RETRIES',
    'RETRY_BACKOFF',
    # Network
    'request_with_retry',
    # Hexo
    'run_hexo_command',
    'sanitize_filename',
    'find_hexo_executable',
    # Notion
    'fetch_notion_page',
    'extract_notion_page_id',
    # Converter
    'blocks_to_markdown',
    'rich_text_to_markdown',
    # OSS
    'upload_to_oss',
    'download_notion_image',
    'process_images_in_markdown',
    # CLI
    'main',
    'create_hexo_post',
    'test_mode_export',
    'print_step',
]

__version__ = '2.0.0'
