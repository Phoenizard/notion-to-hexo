"""Tests for cli module."""

import pytest
import yaml

from notion_to_hexo.cli import _build_front_matter, build_parser


class TestBuildFrontMatter:
    def test_basic(self):
        fm = {
            'title': 'Hello World',
            'date': '2025-01-24 12:00:00',
            'tags': ['python', 'hexo'],
            'categories': '学习笔记',
            'mathjax': False,
        }
        result = _build_front_matter(fm)
        assert result.startswith('---\n')
        assert result.endswith('---\n\n')

        # Parse back to verify valid YAML
        content = result.strip('- \n')
        parsed = yaml.safe_load(content)
        assert parsed['title'] == 'Hello World'
        assert parsed['tags'] == ['python', 'hexo']
        assert parsed['categories'] == '学习笔记'
        assert parsed['mathjax'] is False

    def test_special_chars_in_title(self):
        """Titles with YAML special characters should be properly escaped."""
        fm = {
            'title': 'Title: with colon',
            'date': '2025-01-24 12:00:00',
            'tags': [],
            'categories': 'test',
            'mathjax': False,
        }
        result = _build_front_matter(fm)
        # Should be valid YAML
        content = result.replace('---\n', '', 1).rsplit('---', 1)[0]
        parsed = yaml.safe_load(content)
        assert parsed['title'] == 'Title: with colon'

    def test_title_with_brackets(self):
        fm = {
            'title': '[React] Hooks Guide',
            'date': '2025-01-24 12:00:00',
            'tags': [],
            'categories': 'test',
            'mathjax': False,
        }
        result = _build_front_matter(fm)
        content = result.replace('---\n', '', 1).rsplit('---', 1)[0]
        parsed = yaml.safe_load(content)
        assert parsed['title'] == '[React] Hooks Guide'

    def test_title_with_hash(self):
        fm = {
            'title': 'C# Programming',
            'date': '2025-01-24 12:00:00',
            'tags': [],
            'categories': 'test',
            'mathjax': False,
        }
        result = _build_front_matter(fm)
        content = result.replace('---\n', '', 1).rsplit('---', 1)[0]
        parsed = yaml.safe_load(content)
        assert parsed['title'] == 'C# Programming'

    def test_with_description(self):
        fm = {
            'title': 'Test',
            'date': '2025-01-24 12:00:00',
            'tags': ['a'],
            'categories': 'cat',
            'mathjax': True,
            'description': 'A multi-line\ndescription',
        }
        result = _build_front_matter(fm)
        content = result.replace('---\n', '', 1).rsplit('---', 1)[0]
        parsed = yaml.safe_load(content)
        assert parsed['description'] == 'A multi-line\ndescription'
        assert parsed['mathjax'] is True

    def test_unicode_title(self):
        fm = {
            'title': '中文标题：测试',
            'date': '2025-01-24 12:00:00',
            'tags': ['标签'],
            'categories': '分类',
            'mathjax': False,
        }
        result = _build_front_matter(fm)
        content = result.replace('---\n', '', 1).rsplit('---', 1)[0]
        parsed = yaml.safe_load(content)
        assert parsed['title'] == '中文标题：测试'


class TestBuildParser:
    def test_basic_url(self):
        parser = build_parser()
        args = parser.parse_args(['https://notion.so/page-id'])
        assert args.url == 'https://notion.so/page-id'

    def test_test_mode(self):
        parser = build_parser()
        args = parser.parse_args(['--test', 'https://notion.so/page-id'])
        assert args.test is True

    def test_yes_mode(self):
        parser = build_parser()
        args = parser.parse_args(['-y', 'https://notion.so/page-id'])
        assert args.yes is True

    def test_all_options(self):
        parser = build_parser()
        args = parser.parse_args([
            '--title', 'My Title',
            '--front-title', 'Display Title',
            '--category', 'Tech',
            '--tags', 'python', 'hexo',
            '--description', 'A description',
            '--yes',
            '--no-serve',
            '--deploy',
            '--llm-summary',
            '--verbose',
            '--config', '/path/to/config.json',
            'https://notion.so/page-id',
        ])
        assert args.title == 'My Title'
        assert args.front_title == 'Display Title'
        assert args.category == 'Tech'
        assert args.tags == ['python', 'hexo']
        assert args.description == 'A description'
        assert args.yes is True
        assert args.no_serve is True
        assert args.deploy is True
        assert args.llm_summary is True
        assert args.verbose is True
        assert args.config_path == '/path/to/config.json'

    def test_dry_run(self):
        parser = build_parser()
        args = parser.parse_args(['--dry-run', 'https://notion.so/page-id'])
        assert args.dry_run is True

    def test_ui_mode(self):
        parser = build_parser()
        args = parser.parse_args(['--ui'])
        assert args.ui is True
