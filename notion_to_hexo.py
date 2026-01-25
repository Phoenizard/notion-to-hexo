#!/usr/bin/env python3
"""
Notion to Hexo Blog Publisher
自动将Notion页面转换为Hexo博客文章

使用方法:
    python notion_to_hexo.py <notion_page_url>

功能:
1. 从Notion获取页面内容
2. 创建Hexo文章模板 (hexo new [name])
3. 转换Notion内容为Markdown
4. 上传图片到阿里云OSS
5. 生成Hexo静态文件 (hexo generate)

This is a backwards-compatible wrapper that imports from the notion_to_hexo package.
For new code, prefer importing directly from the package:
    from notion_to_hexo import fetch_notion_page, upload_to_oss
"""

# Re-export everything from the package for backwards compatibility
from notion_to_hexo import (
    # Config
    config,
    load_config,
    TIMEOUT_API,
    TIMEOUT_IMAGE,
    MAX_RETRIES,
    RETRY_BACKOFF,
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
# These are mutable references to the config object's attributes
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

# Default blog path constant
from pathlib import Path
DEFAULT_BLOG_PATH = Path.home() / 'Documents' / 'Blog'

if __name__ == '__main__':
    main()
