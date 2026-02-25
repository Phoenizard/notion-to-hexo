"""Tests for hexo module."""

import pytest
from unittest.mock import patch, MagicMock

from notion_to_hexo.hexo import sanitize_filename, find_hexo_executable


class TestSanitizeFilename:
    def test_basic(self):
        assert sanitize_filename('Hello World') == 'Hello-World'

    def test_special_chars(self):
        assert sanitize_filename('Title: A <Guide>') == 'Title-A-Guide'

    def test_quotes(self):
        assert sanitize_filename('She said "hello"') == 'She-said-hello'

    def test_question_mark(self):
        assert sanitize_filename('What is Python?') == 'What-is-Python'

    def test_pipe(self):
        assert sanitize_filename('A | B') == 'A-B'

    def test_backslash(self):
        assert sanitize_filename('path\\to\\file') == 'path-to-file'

    def test_multiple_spaces(self):
        assert sanitize_filename('too   many   spaces') == 'too-many-spaces'

    def test_leading_trailing_hyphens(self):
        assert sanitize_filename('-title-') == 'title'
        assert sanitize_filename('---title---') == 'title'

    def test_consecutive_hyphens(self):
        assert sanitize_filename('a---b') == 'a-b'

    def test_chinese(self):
        assert sanitize_filename('中文标题') == '中文标题'

    def test_mixed(self):
        assert sanitize_filename('React: 入门指南 [2025]') == 'React-入门指南-[2025]'

    def test_asterisk(self):
        assert sanitize_filename('C* Language') == 'C-Language'


class TestFindHexoExecutable:
    @patch('notion_to_hexo.hexo.shutil.which')
    def test_found_in_path(self, mock_which):
        mock_which.return_value = '/usr/local/bin/hexo'
        assert find_hexo_executable() == '/usr/local/bin/hexo'

    @patch('notion_to_hexo.hexo.shutil.which')
    @patch('notion_to_hexo.hexo.glob.glob')
    def test_found_via_nvm(self, mock_glob, mock_which):
        mock_which.return_value = None  # Not in PATH
        mock_glob.return_value = [
            '/Users/test/.nvm/versions/node/v18.0.0/bin/hexo',
            '/Users/test/.nvm/versions/node/v20.0.0/bin/hexo',
        ]
        # Also need to ensure npm_paths don't match
        with patch('notion_to_hexo.hexo.Path') as mock_path_cls:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path_instance.is_file.return_value = False
            mock_path_instance.__truediv__ = lambda s, o: mock_path_instance
            mock_path_cls.return_value = mock_path_instance
            mock_path_cls.home.return_value = mock_path_instance

            result = find_hexo_executable()
            assert result == '/Users/test/.nvm/versions/node/v20.0.0/bin/hexo'

    @patch('notion_to_hexo.hexo.shutil.which')
    @patch('notion_to_hexo.hexo.glob.glob')
    def test_not_found_has_npx(self, mock_glob, mock_which):
        # First call for hexo: not found. Second call for npx: found.
        mock_which.side_effect = [None, '/usr/local/bin/npx']
        mock_glob.return_value = []

        # Mock Path.exists() for npm_paths to return False
        with patch('notion_to_hexo.hexo.Path') as mock_path_cls:
            mock_path_instance = MagicMock()
            mock_path_instance.exists.return_value = False
            mock_path_instance.is_file.return_value = False
            mock_path_instance.__truediv__ = lambda s, o: mock_path_instance
            mock_path_cls.return_value = mock_path_instance
            mock_path_cls.home.return_value = mock_path_instance

            result = find_hexo_executable()
            assert result is None  # Signals to use npx
