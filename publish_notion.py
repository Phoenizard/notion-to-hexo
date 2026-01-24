#!/usr/bin/env python3
"""
简化版 Notion to Hexo 发布工具
支持从配置文件读取设置

使用方法:
    python publish_notion.py <notion_url>
"""

import os
import sys
import json
from pathlib import Path

# 导入主脚本
sys.path.insert(0, str(Path(__file__).parent))
import notion_to_hexo

def load_config():
    """加载配置文件"""
    config_file = Path(__file__).parent / 'config.json'

    if not config_file.exists():
        print("警告: 未找到config.json配置文件")
        print("请复制config.example.json为config.json并填入配置信息")
        return None

    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config

def main():
    # 加载配置
    config = load_config()

    if config:
        # 设置Hexo博客路径
        if config.get('hexo', {}).get('blog_path'):
            blog_path = Path(config['hexo']['blog_path'])
            if blog_path.exists():
                notion_to_hexo.HEXO_ROOT = blog_path
            else:
                print(f"警告: 配置的blog_path不存在: {blog_path}")

        # 设置Notion token
        if config.get('notion', {}).get('token'):
            notion_to_hexo.NOTION_TOKEN = config['notion']['token']
            os.environ['NOTION_TOKEN'] = config['notion']['token']

        # 设置OSS配置
        if config.get('oss'):
            oss_config = config['oss']
            notion_to_hexo.OSS_CONFIG['access_key_id'] = oss_config.get('access_key_id', '')
            notion_to_hexo.OSS_CONFIG['access_key_secret'] = oss_config.get('access_key_secret', '')
            notion_to_hexo.OSS_CONFIG['bucket_name'] = oss_config.get('bucket_name', '')
            notion_to_hexo.OSS_CONFIG['endpoint'] = oss_config.get('endpoint', '')
            notion_to_hexo.OSS_CONFIG['cdn_domain'] = oss_config.get('cdn_domain', '')

        print("✓ 已从配置文件加载设置\n")

    # 运行主程序
    notion_to_hexo.main()

if __name__ == '__main__':
    main()
