"""
Markdown conversion utilities for Notion to Hexo.

Provides functions to convert Notion blocks to Markdown format.
"""

import logging

logger = logging.getLogger(__name__)


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


def blocks_to_markdown(blocks, fetch_children=None, level=0):
    """
    Convert Notion blocks to Markdown.

    Args:
        blocks: List of Notion block objects
        fetch_children: Callable(block_id) -> list of child blocks.
                        Used for fetching nested blocks with pagination.
                        If None, children are skipped.
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
            markdown.append('')

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

        elif block_type == 'to_do':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            checked = block_content.get('checked', False)
            indent = '  ' * level
            checkbox = '[x]' if checked else '[ ]'
            markdown.append(f"{indent}- {checkbox} {text}")

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

        elif block_type == 'callout':
            icon = block_content.get('icon', {}).get('emoji', '')
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            prefix = f"{icon} " if icon else ''
            markdown.append(f"> {prefix}{text}")
            markdown.append('')

        elif block_type == 'divider':
            markdown.append('---')
            markdown.append('')

        elif block_type == 'toggle':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            markdown.append(f"<details><summary>{text}</summary>")
            markdown.append('')

        elif block_type == 'table':
            # Table rendering is handled entirely in the has_children block below
            pass

        elif block_type == 'table_row':
            # Table rows at top level (shouldn't happen, but handle gracefully)
            cells = block_content.get('cells', [])
            row = ' | '.join(rich_text_to_markdown(cell) for cell in cells)
            markdown.append(f"| {row} |")

        # Handle child blocks
        if block.get('has_children') and fetch_children:
            try:
                children = fetch_children(block['id'])

                if block_type == 'table':
                    # Render complete GFM table from children
                    table_rows = [b for b in children if b.get('type') == 'table_row']
                    if table_rows:
                        # First row (header)
                        first_cells = table_rows[0].get('table_row', {}).get('cells', [])
                        header = ' | '.join(
                            rich_text_to_markdown(cell) for cell in first_cells
                        )
                        markdown.append(f"| {header} |")

                        # Separator
                        separator = ' | '.join(['---'] * len(first_cells))
                        markdown.append(f"| {separator} |")

                        # Data rows
                        for row_block in table_rows[1:]:
                            row_cells = row_block.get('table_row', {}).get('cells', [])
                            row = ' | '.join(
                                rich_text_to_markdown(cell) for cell in row_cells
                            )
                            markdown.append(f"| {row} |")

                    markdown.append('')
                else:
                    child_markdown = blocks_to_markdown(
                        children,
                        fetch_children,
                        level + 1
                    )
                    if child_markdown.strip():
                        markdown.append(child_markdown)

                    # Close toggle
                    if block_type == 'toggle':
                        markdown.append('</details>')
                        markdown.append('')
            except Exception as e:
                logger.warning("获取子块失败: %s", e)

        elif block_type == 'toggle' and not block.get('has_children'):
            # Close empty toggle
            markdown.append('</details>')
            markdown.append('')

    return '\n'.join(markdown)
