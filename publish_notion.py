#!/usr/bin/env python3
"""
简化版 Notion to Hexo 发布工具
支持从配置文件读取设置

使用方法:
    python publish_notion.py <notion_url>
    python publish_notion.py --test <notion_url>
    python publish_notion.py --yes <notion_url>
"""

from notion_to_hexo.cli import main

if __name__ == '__main__':
    main()
