"""Tests for notion module."""

import pytest
from unittest.mock import patch, MagicMock

from notion_to_hexo.notion import extract_notion_page_id, _has_math_content, _fetch_all_blocks


class TestExtractNotionPageId:
    def test_32_hex_at_end(self):
        url = 'https://www.notion.so/Test-Page-abcdef1234567890abcdef1234567890'
        result = extract_notion_page_id(url)
        assert result == 'abcdef12-3456-7890-abcd-ef1234567890'

    def test_uuid_with_dashes(self):
        url = 'https://www.notion.so/abcdef12-3456-7890-abcd-ef1234567890'
        result = extract_notion_page_id(url)
        assert result == 'abcdef12-3456-7890-abcd-ef1234567890'

    def test_with_query_params(self):
        url = 'https://www.notion.so/Test-abcdef1234567890abcdef1234567890?v=123'
        result = extract_notion_page_id(url)
        assert result == 'abcdef12-3456-7890-abcd-ef1234567890'

    def test_workspace_url(self):
        url = 'https://www.notion.so/workspace/Page-Title-abcdef1234567890abcdef1234567890'
        result = extract_notion_page_id(url)
        assert result == 'abcdef12-3456-7890-abcd-ef1234567890'

    def test_invalid_url(self):
        assert extract_notion_page_id('https://www.notion.so/') is None
        assert extract_notion_page_id('https://google.com') is None
        assert extract_notion_page_id('not-a-url') is None

    def test_case_insensitive(self):
        url = 'https://www.notion.so/ABCDEF1234567890ABCDEF1234567890'
        result = extract_notion_page_id(url)
        assert result == 'abcdef12-3456-7890-abcd-ef1234567890'

    def test_page_with_dashes_in_title(self):
        url = 'https://www.notion.so/My-Page-With-Dashes-abcdef1234567890abcdef1234567890'
        result = extract_notion_page_id(url)
        assert result == 'abcdef12-3456-7890-abcd-ef1234567890'


class TestHasMathContent:
    def test_display_math(self):
        assert _has_math_content('Some text $$E=mc^2$$ more text') is True

    def test_inline_math(self):
        assert _has_math_content('The value $x^2$ is positive') is True

    def test_dollar_sign_not_math(self):
        # Price-like usage should not trigger
        assert _has_math_content('The price is $100') is False
        assert _has_math_content('$100 per item') is False

    def test_backslash_bracket(self):
        assert _has_math_content('Formula: \\[x^2 + y^2\\]') is True

    def test_no_math(self):
        assert _has_math_content('Just regular text') is False

    def test_empty_string(self):
        assert _has_math_content('') is False

    def test_multiline_display_math(self):
        content = "Before\n$$\nx^2 + y^2 = z^2\n$$\nAfter"
        assert _has_math_content(content) is True


class TestFetchAllBlocks:
    @patch('notion_to_hexo.notion.request_with_retry')
    def test_single_page(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [{'id': 'block1', 'type': 'paragraph'}],
            'has_more': False,
            'next_cursor': None,
        }
        mock_request.return_value = mock_response

        headers = {'Authorization': 'Bearer test'}
        result = _fetch_all_blocks('page-id', headers)

        assert len(result) == 1
        assert result[0]['id'] == 'block1'
        mock_request.assert_called_once()

    @patch('notion_to_hexo.notion.request_with_retry')
    def test_pagination(self, mock_request):
        """Verify that pagination fetches all blocks across multiple pages."""
        response1 = MagicMock()
        response1.json.return_value = {
            'results': [{'id': f'block{i}', 'type': 'paragraph'} for i in range(100)],
            'has_more': True,
            'next_cursor': 'cursor1',
        }

        response2 = MagicMock()
        response2.json.return_value = {
            'results': [{'id': f'block{i}', 'type': 'paragraph'} for i in range(100, 150)],
            'has_more': False,
            'next_cursor': None,
        }

        mock_request.side_effect = [response1, response2]

        headers = {'Authorization': 'Bearer test'}
        result = _fetch_all_blocks('page-id', headers)

        assert len(result) == 150
        assert mock_request.call_count == 2

        # Verify second call includes start_cursor
        second_call_kwargs = mock_request.call_args_list[1]
        assert second_call_kwargs[1]['params'] == {'start_cursor': 'cursor1'}
