#!/usr/bin/env python3
"""
简化版 Notion to Hexo 发布工具
支持从配置文件读取设置

使用方法:
    python publish_notion.py <notion_url>
    python publish_notion.py --test <notion_url>
"""

import os
import sys
import json
from pathlib import Path

# Import from the package
from notion_to_hexo import config, main as run_main


def load_config():
    """加载配置文件"""
    config_file = Path(__file__).parent / 'config.json'

    if not config_file.exists():
        print("警告: 未找到config.json配置文件")
        print("请复制config.example.json为config.json并填入配置信息")
        return None

    with open(config_file, 'r', encoding='utf-8') as f:
        file_config = json.load(f)

    return file_config


def main():
    # Load configuration
    file_config = load_config()

    if file_config:
        # Set Hexo blog path - only if not already set via environment
        if file_config.get('hexo', {}).get('blog_path'):
            if not os.environ.get('HEXO_ROOT'):
                blog_path = Path(file_config['hexo']['blog_path'])
                if blog_path.exists():
                    config.hexo_root = blog_path
                else:
                    print(f"警告: 配置的blog_path不存在: {blog_path}")

        # Set Notion token - only if not already set via environment
        if file_config.get('notion', {}).get('token'):
            if not os.environ.get('NOTION_TOKEN'):
                config.notion_token = file_config['notion']['token']
                os.environ['NOTION_TOKEN'] = file_config['notion']['token']

        # Set OSS configuration - only if not already set via environment
        if file_config.get('oss'):
            oss_config = file_config['oss']
            if not os.environ.get('NOTION_OSS_ACCESS_KEY_ID'):
                config.oss_config['access_key_id'] = oss_config.get('access_key_id', '')
            if not os.environ.get('NOTION_OSS_ACCESS_KEY_SECRET'):
                config.oss_config['access_key_secret'] = oss_config.get('access_key_secret', '')
            if not os.environ.get('NOTION_OSS_BUCKET_NAME'):
                config.oss_config['bucket_name'] = oss_config.get('bucket_name', '')
            if not os.environ.get('NOTION_OSS_ENDPOINT'):
                config.oss_config['endpoint'] = oss_config.get('endpoint', '')
            if not os.environ.get('NOTION_OSS_CDN_DOMAIN'):
                config.oss_config['cdn_domain'] = oss_config.get('cdn_domain', '')

        print("✓ 已从配置文件加载设置\n")

    # Run the main workflow
    run_main()


if __name__ == '__main__':
    main()
