#!/usr/bin/env python3
"""
Notion to Hexo Blog Publisher

This is a backwards-compatible wrapper that imports from the notion_to_hexo package.
For new code, prefer importing directly from the package:
    from notion_to_hexo import fetch_notion_page, upload_to_oss
"""

# Re-export everything from the package for backwards compatibility
from notion_to_hexo import (
    # Config
    config,
    load_config,
    get_config,
    TIMEOUT_API,
    TIMEOUT_IMAGE,
    MAX_RETRIES,
    RETRY_BACKOFF,
    # Exceptions
    NotionToHexoError,
    NotionAPIError,
    OSSUploadError,
    HexoCommandError,
    ConfigurationError,
    # Network
    request_with_retry,
    # Hexo
    run_hexo_command,
    sanitize_filename,
    find_hexo_executable,
    # Notion
    fetch_notion_page,
    extract_notion_page_id,
    # Converter
    blocks_to_markdown,
    rich_text_to_markdown,
    # OSS
    upload_to_oss,
    download_notion_image,
    process_images_in_markdown,
    # CLI
    main,
    create_hexo_post,
    test_mode_export,
    print_step,
)

# Backwards compatibility: expose config attributes as module-level globals
HEXO_ROOT = config.hexo_root
NOTION_TOKEN = config.notion_token
OSS_CONFIG = config.oss_config
HEXO_CONFIG = config.hexo_config

# Environment variable names (for reference)
ENV_VARS = {
    'notion_token': 'NOTION_TOKEN',
    'oss_access_key_id': 'NOTION_OSS_ACCESS_KEY_ID',
    'oss_access_key_secret': 'NOTION_OSS_ACCESS_KEY_SECRET',
    'oss_bucket_name': 'NOTION_OSS_BUCKET_NAME',
    'oss_endpoint': 'NOTION_OSS_ENDPOINT',
    'oss_cdn_domain': 'NOTION_OSS_CDN_DOMAIN',
    'hexo_root': 'HEXO_ROOT',
}

from pathlib import Path
DEFAULT_BLOG_PATH = Path.home() / 'Documents' / 'Blog'

if __name__ == '__main__':
    main()
