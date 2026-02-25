"""
Notion API client for Notion to Hexo.

Provides functions for fetching content from the Notion API.
"""

import re
import logging

from .config import config
from .network import request_with_retry
from .converter import blocks_to_markdown
from .exceptions import NotionAPIError

logger = logging.getLogger(__name__)


def extract_notion_page_id(url):
    """
    Extract page ID from a Notion URL.

    Args:
        url: Notion page URL

    Returns:
        UUID formatted page ID, or None if extraction fails
    """
    url_path = url.split('?')[0]

    match = re.search(r'([a-f0-9]{32})$', url_path, re.IGNORECASE)
    if match:
        page_id = match.group(1).lower()
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"

    match = re.search(
        r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$',
        url_path,
        re.IGNORECASE
    )
    if match:
        return match.group(1).lower()

    last_segment = url_path.split('/')[-1].replace('-', '')
    match = re.search(r'([a-f0-9]{32})$', last_segment, re.IGNORECASE)
    if match:
        page_id = match.group(1).lower()
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"

    return None


def _fetch_all_blocks(parent_id, headers):
    """
    Fetch all child blocks with pagination.

    The Notion API returns at most 100 blocks per request.
    This function handles pagination to fetch all blocks.

    Args:
        parent_id: Parent block or page ID
        headers: HTTP headers for Notion API

    Returns:
        List of all child block objects
    """
    all_blocks = []
    url = f'https://api.notion.com/v1/blocks/{parent_id}/children'
    has_more = True
    start_cursor = None

    while has_more:
        params = {}
        if start_cursor:
            params['start_cursor'] = start_cursor

        response = request_with_retry(
            'get', url, headers=headers, params=params, timeout_type='api'
        )
        data = response.json()
        all_blocks.extend(data.get('results', []))
        has_more = data.get('has_more', False)
        start_cursor = data.get('next_cursor')

    logger.debug("Fetched %d blocks from %s", len(all_blocks), parent_id)
    return all_blocks


def _has_math_content(content):
    """
    Check if content contains LaTeX math formulas.

    Uses proper regex to avoid false positives from dollar signs
    in prices or other non-math contexts.

    Args:
        content: Markdown content string

    Returns:
        True if math formulas are detected
    """
    # Match display math: $$...$$
    if re.search(r'\$\$.+?\$\$', content, re.DOTALL):
        return True

    # Match inline math: $...$  (not preceded/followed by space adjacent to $)
    # Excludes: "$ 100" or "100 $" (price-like patterns)
    if re.search(r'(?<!\$)\$(?!\s)(?!\$).+?(?<!\s)(?<!\$)\$(?!\$)', content):
        return True

    # Match \[...\] display math
    if '\\[' in content:
        return True

    return False


def fetch_notion_page(page_id, notion_token=None):
    """
    Fetch page content using the Notion API.

    Handles pagination to fetch all blocks (not limited to 100).

    Args:
        page_id: The Notion page ID (UUID format)
        notion_token: Optional token override

    Returns:
        Tuple of (title, content_markdown, tags, category, description, mathjax)

    Raises:
        NotionAPIError: If Notion API request fails
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
    try:
        page_response = request_with_retry('get', page_url, headers=headers, timeout_type='api')
    except Exception as e:
        raise NotionAPIError(f"获取页面属性失败: {e}") from e

    page_data = page_response.json()
    properties = page_data.get('properties', {})

    # Extract title
    title = ''
    if 'title' in properties:
        title_property = properties['title']
        if title_property.get('title'):
            title = ''.join([t['plain_text'] for t in title_property['title']])

    # Extract other properties
    tags = []
    category = '学习笔记'
    description = ''
    mathjax = False

    if 'Tags' in properties or 'tags' in properties:
        tag_property = properties.get('Tags') or properties.get('tags')
        if tag_property.get('type') == 'multi_select':
            tags = [tag['name'] for tag in tag_property.get('multi_select', [])]

    if 'Category' in properties or 'category' in properties:
        cat_property = properties.get('Category') or properties.get('category')
        if cat_property.get('type') == 'select' and cat_property.get('select'):
            category = cat_property['select']['name']

    if 'Description' in properties or 'description' in properties:
        desc_property = properties.get('Description') or properties.get('description')
        if desc_property.get('type') == 'rich_text':
            description = ''.join([t['plain_text'] for t in desc_property.get('rich_text', [])])

    # MathJax checkbox property takes priority
    mathjax_from_property = False
    if 'MathJax' in properties or 'mathjax' in properties:
        math_property = properties.get('MathJax') or properties.get('mathjax')
        if math_property.get('type') == 'checkbox':
            mathjax = math_property.get('checkbox', False)
            mathjax_from_property = True

    # Fetch all page content blocks (with pagination)
    all_blocks = _fetch_all_blocks(page_id, headers)

    # Create fetch_children callback for converter (also handles pagination)
    def fetch_children(block_id):
        return _fetch_all_blocks(block_id, headers)

    # Convert to Markdown
    markdown_content = blocks_to_markdown(all_blocks, fetch_children=fetch_children)

    # Auto-detect math from content only if not explicitly set by property
    if not mathjax_from_property and _has_math_content(markdown_content):
        mathjax = True

    return title, markdown_content, tags, category, description, mathjax
