"""Tests for converter module."""

import pytest
from notion_to_hexo.converter import rich_text_to_markdown, blocks_to_markdown


class TestRichTextToMarkdown:
    def test_plain_text(self):
        rich_text = [{'type': 'text', 'plain_text': 'hello', 'annotations': {}}]
        assert rich_text_to_markdown(rich_text) == 'hello'

    def test_bold(self):
        rich_text = [{'type': 'text', 'plain_text': 'bold', 'annotations': {'bold': True}}]
        assert rich_text_to_markdown(rich_text) == '**bold**'

    def test_italic(self):
        rich_text = [{'type': 'text', 'plain_text': 'italic', 'annotations': {'italic': True}}]
        assert rich_text_to_markdown(rich_text) == '*italic*'

    def test_code(self):
        rich_text = [{'type': 'text', 'plain_text': 'code', 'annotations': {'code': True}}]
        assert rich_text_to_markdown(rich_text) == '`code`'

    def test_strikethrough(self):
        rich_text = [{'type': 'text', 'plain_text': 'strike', 'annotations': {'strikethrough': True}}]
        assert rich_text_to_markdown(rich_text) == '~~strike~~'

    def test_link(self):
        rich_text = [{'type': 'text', 'plain_text': 'link', 'annotations': {}, 'href': 'https://example.com'}]
        assert rich_text_to_markdown(rich_text) == '[link](https://example.com)'

    def test_inline_equation(self):
        rich_text = [{'type': 'equation', 'equation': {'expression': 'E=mc^2'}}]
        assert rich_text_to_markdown(rich_text) == '$E=mc^2$'

    def test_empty(self):
        assert rich_text_to_markdown([]) == ''

    def test_multiple_segments(self):
        rich_text = [
            {'type': 'text', 'plain_text': 'Hello ', 'annotations': {}},
            {'type': 'text', 'plain_text': 'World', 'annotations': {'bold': True}},
        ]
        assert rich_text_to_markdown(rich_text) == 'Hello **World**'


class TestBlocksToMarkdown:
    def _make_block(self, block_type, rich_text=None, **extra):
        content = {}
        if rich_text is not None:
            content['rich_text'] = [{'type': 'text', 'plain_text': rich_text, 'annotations': {}}]
        content.update(extra)
        return {
            'id': 'test-id',
            'type': block_type,
            block_type: content,
            'has_children': False,
        }

    def test_paragraph(self):
        blocks = [self._make_block('paragraph', 'Hello')]
        result = blocks_to_markdown(blocks)
        assert 'Hello' in result

    def test_headings(self):
        for i, prefix in [(1, '# '), (2, '## '), (3, '### ')]:
            blocks = [self._make_block(f'heading_{i}', 'Title')]
            result = blocks_to_markdown(blocks)
            assert f'{prefix}Title' in result

    def test_bulleted_list(self):
        blocks = [self._make_block('bulleted_list_item', 'item')]
        result = blocks_to_markdown(blocks)
        assert '- item' in result

    def test_numbered_list(self):
        blocks = [self._make_block('numbered_list_item', 'item')]
        result = blocks_to_markdown(blocks)
        assert '1. item' in result

    def test_to_do_unchecked(self):
        blocks = [self._make_block('to_do', 'task', checked=False)]
        result = blocks_to_markdown(blocks)
        assert '- [ ] task' in result

    def test_to_do_checked(self):
        blocks = [self._make_block('to_do', 'done', checked=True)]
        result = blocks_to_markdown(blocks)
        assert '- [x] done' in result

    def test_code_block(self):
        blocks = [self._make_block('code', 'print("hi")', language='python')]
        result = blocks_to_markdown(blocks)
        assert '```python' in result
        assert 'print("hi")' in result
        assert '```' in result

    def test_equation_block(self):
        blocks = [self._make_block('equation', expression='E=mc^2')]
        # equation block doesn't use rich_text; override
        blocks[0]['equation'] = {'expression': 'E=mc^2'}
        result = blocks_to_markdown(blocks)
        assert '$$' in result
        assert 'E=mc^2' in result

    def test_image_file(self):
        block = {
            'id': 'test-id',
            'type': 'image',
            'image': {
                'type': 'file',
                'file': {'url': 'https://example.com/img.png'},
                'caption': [],
            },
            'has_children': False,
        }
        result = blocks_to_markdown([block])
        assert '![](https://example.com/img.png)' in result

    def test_image_external(self):
        block = {
            'id': 'test-id',
            'type': 'image',
            'image': {
                'type': 'external',
                'external': {'url': 'https://cdn.example.com/img.jpg'},
                'caption': [{'type': 'text', 'plain_text': 'caption', 'annotations': {}}],
            },
            'has_children': False,
        }
        result = blocks_to_markdown([block])
        assert '![caption](https://cdn.example.com/img.jpg)' in result

    def test_quote(self):
        blocks = [self._make_block('quote', 'quoted text')]
        result = blocks_to_markdown(blocks)
        assert '> quoted text' in result

    def test_callout(self):
        block = {
            'id': 'test-id',
            'type': 'callout',
            'callout': {
                'rich_text': [{'type': 'text', 'plain_text': 'important', 'annotations': {}}],
                'icon': {'emoji': '⚠️'},
            },
            'has_children': False,
        }
        result = blocks_to_markdown([block])
        assert '> ⚠️ important' in result

    def test_divider(self):
        blocks = [self._make_block('divider')]
        # divider doesn't use rich_text
        blocks[0]['divider'] = {}
        result = blocks_to_markdown(blocks)
        assert '---' in result

    def test_toggle(self):
        block = self._make_block('toggle', 'Click me')
        result = blocks_to_markdown([block])
        assert '<details><summary>Click me</summary>' in result
        assert '</details>' in result

    def test_nested_list_with_children(self):
        parent = self._make_block('bulleted_list_item', 'parent')
        parent['has_children'] = True

        child = self._make_block('bulleted_list_item', 'child')

        def fetch_children(block_id):
            return [child]

        result = blocks_to_markdown([parent], fetch_children=fetch_children)
        assert '- parent' in result
        assert '  - child' in result

    def test_table(self):
        table_block = {
            'id': 'table-id',
            'type': 'table',
            'table': {'table_width': 2, 'has_column_header': True},
            'has_children': True,
        }

        row1 = {
            'id': 'row1',
            'type': 'table_row',
            'table_row': {
                'cells': [
                    [{'type': 'text', 'plain_text': 'Header 1', 'annotations': {}}],
                    [{'type': 'text', 'plain_text': 'Header 2', 'annotations': {}}],
                ]
            },
            'has_children': False,
        }
        row2 = {
            'id': 'row2',
            'type': 'table_row',
            'table_row': {
                'cells': [
                    [{'type': 'text', 'plain_text': 'Cell 1', 'annotations': {}}],
                    [{'type': 'text', 'plain_text': 'Cell 2', 'annotations': {}}],
                ]
            },
            'has_children': False,
        }

        def fetch_children(block_id):
            return [row1, row2]

        result = blocks_to_markdown([table_block], fetch_children=fetch_children)
        assert '| Header 1 | Header 2 |' in result
        assert '| --- | --- |' in result
        assert '| Cell 1 | Cell 2 |' in result
