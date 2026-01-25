"""
Notion API client for Notion to Hexo.

Provides functions for fetching content from the Notion API.
"""

import re

from .config import config
from .network import request_with_retry
from .converter import blocks_to_markdown


def extract_notion_page_id(url):
    """
    Extract page ID from a Notion URL.

    Args:
        url: Notion page URL

    Returns:
        UUID formatted page ID, or None if extraction fails
    """
    # Remove query parameters first
    url_path = url.split('?')[0]

    # Try to match 32 hex chars at the end of the path (most reliable)
    match = re.search(r'([a-f0-9]{32})$', url_path, re.IGNORECASE)
    if match:
        page_id = match.group(1).lower()
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"

    # Try UUID format with dashes at the end
    match = re.search(
        r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$',
        url_path,
        re.IGNORECASE
    )
    if match:
        return match.group(1).lower()

    # Fallback: remove dashes from end segment only and look for 32 hex chars
    last_segment = url_path.split('/')[-1].replace('-', '')
    match = re.search(r'([a-f0-9]{32})$', last_segment, re.IGNORECASE)
    if match:
        page_id = match.group(1).lower()
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"

    return None


def fetch_notion_page(page_id, notion_token=None):
    """
    Fetch page content using the Notion API.

    Note: Requires a Notion Integration Token.

    Args:
        page_id: The Notion page ID (UUID format)
        notion_token: Optional token override (uses config.notion_token if not provided)

    Returns:
        Tuple of (title, content_markdown, tags, category, description, mathjax)

    Raises:
        ValueError: If no Notion token is configured
    """
    token = notion_token or config.notion_token

    if not token:
        raise ValueError("未设置NOTION_TOKEN。请设置环境变量或在脚本中配置。")

    headers = {
        'Authorization': f'Bearer {token}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }

    # Fetch page properties
    page_url = f'https://api.notion.com/v1/pages/{page_id}'
    page_response = request_with_retry('get', page_url, headers=headers, timeout_type='api')
    page_data = page_response.json()

    # Extract title and properties
    properties = page_data.get('properties', {})

    # Extract title
    title = ''
    if 'title' in properties:
        title_property = properties['title']
        if title_property.get('title'):
            title = ''.join([t['plain_text'] for t in title_property['title']])

    # Extract other properties (adjust based on your Notion database structure)
    tags = []
    category = '学习笔记'  # Default category
    description = ''
    mathjax = False

    # Try to extract tags
    if 'Tags' in properties or 'tags' in properties:
        tag_property = properties.get('Tags') or properties.get('tags')
        if tag_property.get('type') == 'multi_select':
            tags = [tag['name'] for tag in tag_property.get('multi_select', [])]

    # Try to extract category
    if 'Category' in properties or 'category' in properties:
        cat_property = properties.get('Category') or properties.get('category')
        if cat_property.get('type') == 'select' and cat_property.get('select'):
            category = cat_property['select']['name']

    # Try to extract description
    if 'Description' in properties or 'description' in properties:
        desc_property = properties.get('Description') or properties.get('description')
        if desc_property.get('type') == 'rich_text':
            description = ''.join([t['plain_text'] for t in desc_property.get('rich_text', [])])

    # Check if mathjax is needed
    if 'MathJax' in properties or 'mathjax' in properties:
        math_property = properties.get('MathJax') or properties.get('mathjax')
        if math_property.get('type') == 'checkbox':
            mathjax = math_property.get('checkbox', False)

    # Fetch page content blocks
    blocks_url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    blocks_response = request_with_retry('get', blocks_url, headers=headers, timeout_type='api')
    blocks_data = blocks_response.json()

    # Convert to Markdown
    markdown_content = blocks_to_markdown(blocks_data.get('results', []), headers)

    # Check content for math formulas
    if '$' in markdown_content or '\\[' in markdown_content:
        mathjax = True

    return title, markdown_content, tags, category, description, mathjax
