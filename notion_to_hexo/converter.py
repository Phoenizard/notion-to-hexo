"""
Markdown conversion utilities for Notion to Hexo.

Provides functions to convert Notion blocks to Markdown format.
"""

import requests

from .network import request_with_retry


def rich_text_to_markdown(rich_text_array):
    """
    Convert Notion rich text to Markdown.

    Args:
        rich_text_array: List of Notion rich text objects

    Returns:
        Markdown formatted string
    """
    result = []

    for text_obj in rich_text_array:
        text_type = text_obj.get('type', 'text')

        # Handle inline equations
        if text_type == 'equation':
            expression = text_obj.get('equation', {}).get('expression', '')
            result.append(f"${expression}$")
            continue

        text = text_obj.get('plain_text', '')
        annotations = text_obj.get('annotations', {})
        href = text_obj.get('href')

        # Apply formatting
        if annotations.get('bold'):
            text = f"**{text}**"
        if annotations.get('italic'):
            text = f"*{text}*"
        if annotations.get('code'):
            text = f"`{text}`"
        if annotations.get('strikethrough'):
            text = f"~~{text}~~"

        # Handle links
        if href:
            text = f"[{text}]({href})"

        result.append(text)

    return ''.join(result)


def blocks_to_markdown(blocks, headers, level=0):
    """
    Convert Notion blocks to Markdown.

    This is a simplified version that handles common block types.
    May need extension for specific use cases.

    Args:
        blocks: List of Notion block objects
        headers: HTTP headers for Notion API (needed for child block fetches)
        level: Current nesting level for indentation

    Returns:
        Markdown formatted string
    """
    markdown = []

    for block in blocks:
        block_type = block.get('type')
        block_content = block.get(block_type, {})

        if block_type == 'paragraph':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            markdown.append(text)
            markdown.append('')  # Empty line

        elif block_type == 'heading_1':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            markdown.append(f"# {text}")
            markdown.append('')

        elif block_type == 'heading_2':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            markdown.append(f"## {text}")
            markdown.append('')

        elif block_type == 'heading_3':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            markdown.append(f"### {text}")
            markdown.append('')

        elif block_type == 'bulleted_list_item':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            indent = '  ' * level
            markdown.append(f"{indent}- {text}")

        elif block_type == 'numbered_list_item':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            indent = '  ' * level
            markdown.append(f"{indent}1. {text}")

        elif block_type == 'code':
            code_text = rich_text_to_markdown(block_content.get('rich_text', []))
            language = block_content.get('language', '')
            markdown.append(f"```{language}")
            markdown.append(code_text)
            markdown.append("```")
            markdown.append('')

        elif block_type == 'equation':
            expression = block_content.get('expression', '')
            markdown.append("$$")
            markdown.append(expression)
            markdown.append("$$")
            markdown.append('')

        elif block_type == 'image':
            image_url = ''
            if block_content.get('type') == 'file':
                image_url = block_content.get('file', {}).get('url', '')
            elif block_content.get('type') == 'external':
                image_url = block_content.get('external', {}).get('url', '')

            caption = rich_text_to_markdown(block_content.get('caption', []))
            markdown.append(f"![{caption}]({image_url})")
            markdown.append('')

        elif block_type == 'quote':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            lines = text.split('\n')
            for line in lines:
                markdown.append(f"> {line}")
            markdown.append('')

        elif block_type == 'divider':
            markdown.append('---')
            markdown.append('')

        # Handle child blocks
        if block.get('has_children'):
            children_url = f"https://api.notion.com/v1/blocks/{block['id']}/children"
            try:
                children_response = request_with_retry(
                    'get', children_url, headers=headers, timeout_type='api'
                )
                children_data = children_response.json()
                child_markdown = blocks_to_markdown(
                    children_data.get('results', []),
                    headers,
                    level + 1
                )
                markdown.append(child_markdown)
            except requests.RequestException as e:
                print(f"警告: 获取子块失败: {e}")
                # Continue processing other blocks

    return '\n'.join(markdown)
