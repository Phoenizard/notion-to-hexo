"""
Configuration management for Notion to Hexo.

This module handles loading configuration from:
1. Environment variables (highest priority)
2. config.json file
3. Default values
4. Interactive prompts (handled in cli.py)
"""

import os
import json
from pathlib import Path

# ==================== Network Configuration ====================
# Network configuration for timeouts and retries

TIMEOUT_API = 15      # Notion API calls (seconds)
TIMEOUT_IMAGE = 30    # Image downloads (seconds)
MAX_RETRIES = 3       # Number of retry attempts
RETRY_BACKOFF = 2     # Exponential backoff multiplier

# ==================== Environment Variable Names ====================
# Security warning: Never commit secrets to version control!
# Use environment variables or .env file for sensitive data.

ENV_VARS = {
    'notion_token': 'NOTION_TOKEN',
    'oss_access_key_id': 'NOTION_OSS_ACCESS_KEY_ID',
    'oss_access_key_secret': 'NOTION_OSS_ACCESS_KEY_SECRET',
    'oss_bucket_name': 'NOTION_OSS_BUCKET_NAME',
    'oss_endpoint': 'NOTION_OSS_ENDPOINT',
    'oss_cdn_domain': 'NOTION_OSS_CDN_DOMAIN',
    'hexo_root': 'HEXO_ROOT',
    'dashscope_api_key': 'DASHSCOPE_API_KEY',
}


class Config:
    """
    Configuration holder class.

    Provides mutable configuration that can be modified at runtime
    while maintaining a clean interface.
    """

    def __init__(self):
        # Default Hexo blog path
        self.default_blog_path = Path.home() / 'Documents' / 'Blog'
        self.hexo_root = Path(os.environ.get('HEXO_ROOT', self.default_blog_path))

        # Notion API token
        self.notion_token = os.environ.get('NOTION_TOKEN', '')

        # DashScope API key (for LLM summary generation)
        self.dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY', '')

        # Aliyun OSS configuration
        self.oss_config = {
            'access_key_id': '',
            'access_key_secret': '',
            'bucket_name': '',
            'endpoint': '',  # e.g., oss-cn-hangzhou.aliyuncs.com
            'cdn_domain': '',  # e.g., phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com
        }

        # Hexo article defaults
        self.hexo_config = {
            'default_title': '',
            'default_category': '学习笔记',
            'default_tags': [],
            'default_description': '',
            'default_mathjax': False,
        }

    def get_config_path(self):
        """Get the path to config.json relative to the package."""
        # First try package directory's parent (project root)
        package_dir = Path(__file__).parent.parent
        config_path = package_dir / 'config.json'
        if config_path.exists():
            return config_path

        # Fallback to current working directory
        cwd_config = Path.cwd() / 'config.json'
        if cwd_config.exists():
            return cwd_config

        return config_path  # Return project root path (may not exist)


# Global configuration instance
config = Config()


def load_config(config_path=None):
    """
    Load configuration from config file and environment variables.

    Priority (highest to lowest):
    1. Environment variables (including those from .env)
    2. config.json
    3. Default values
    4. Interactive prompts (handled in cli.py)

    Args:
        config_path: Optional path to config.json. If None, auto-detect.

    Returns:
        The global config instance
    """
    global config

    # Determine config file path
    if config_path is None:
        config_path = config.get_config_path()
    else:
        config_path = Path(config_path)

    file_config = {}

    # Step 1: Load config.json as base (if exists)
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            print(f"✓ 已从 {config_path} 加载配置")
        except json.JSONDecodeError as e:
            print(f"警告: config.json 格式错误: {e}")
    else:
        print(f"未找到配置文件: {config_path}")

    # Step 2: Apply config.json values (will be overridden by env vars)
    if 'notion' in file_config and file_config['notion'].get('token'):
        config.notion_token = file_config['notion']['token']

    if 'oss' in file_config:
        oss = file_config['oss']
        config.oss_config['access_key_id'] = oss.get('access_key_id', '')
        config.oss_config['access_key_secret'] = oss.get('access_key_secret', '')
        config.oss_config['bucket_name'] = oss.get('bucket_name', '')
        config.oss_config['endpoint'] = oss.get('endpoint', '')
        config.oss_config['cdn_domain'] = oss.get('cdn_domain', '')

    if 'hexo' in file_config:
        hexo = file_config['hexo']
        if hexo.get('blog_path'):
            config.hexo_root = Path(hexo['blog_path'])
        config.hexo_config['default_title'] = hexo.get('default_title', '')
        config.hexo_config['default_category'] = hexo.get('default_category', '学习笔记')
        config.hexo_config['default_tags'] = hexo.get('default_tags', [])
        config.hexo_config['default_description'] = hexo.get('default_description', '')
        config.hexo_config['default_mathjax'] = hexo.get('default_mathjax', False)

    # Step 3: Environment variables OVERRIDE config.json
    # This ensures secrets can be provided securely via env vars

    # Notion token
    env_token = os.environ.get(ENV_VARS['notion_token'])
    if env_token:
        config.notion_token = env_token
        print(f"✓ 使用环境变量 {ENV_VARS['notion_token']}")

    # OSS credentials
    env_oss_key = os.environ.get(ENV_VARS['oss_access_key_id'])
    if env_oss_key:
        config.oss_config['access_key_id'] = env_oss_key
        print(f"✓ 使用环境变量 {ENV_VARS['oss_access_key_id']}")

    env_oss_secret = os.environ.get(ENV_VARS['oss_access_key_secret'])
    if env_oss_secret:
        config.oss_config['access_key_secret'] = env_oss_secret
        print(f"✓ 使用环境变量 {ENV_VARS['oss_access_key_secret']}")

    env_bucket = os.environ.get(ENV_VARS['oss_bucket_name'])
    if env_bucket:
        config.oss_config['bucket_name'] = env_bucket

    env_endpoint = os.environ.get(ENV_VARS['oss_endpoint'])
    if env_endpoint:
        config.oss_config['endpoint'] = env_endpoint

    env_cdn = os.environ.get(ENV_VARS['oss_cdn_domain'])
    if env_cdn:
        config.oss_config['cdn_domain'] = env_cdn

    # Hexo root
    env_hexo_root = os.environ.get(ENV_VARS['hexo_root'])
    if env_hexo_root:
        config.hexo_root = Path(env_hexo_root)
        print(f"✓ 使用环境变量 {ENV_VARS['hexo_root']}")

    # DashScope API key
    env_dashscope = os.environ.get(ENV_VARS['dashscope_api_key'])
    if env_dashscope:
        config.dashscope_api_key = env_dashscope
        print(f"✓ 使用环境变量 {ENV_VARS['dashscope_api_key']}")

    return config


def try_load_dotenv():
    """
    Try to load .env file if python-dotenv is available.

    This is called automatically on module import.
    """
    try:
        from dotenv import load_dotenv
        package_dir = Path(__file__).parent.parent
        env_path = package_dir / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ 已从 {env_path} 加载环境变量")
    except ImportError:
        # python-dotenv not installed, skip .env loading
        pass


# Load .env on module import
try_load_dotenv()

# Load configuration on module import
load_config()
