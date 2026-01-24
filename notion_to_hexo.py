#!/usr/bin/env python3
"""
Notion to Hexo Blog Publisher
自动将Notion页面转换为Hexo博客文章

使用方法:
    python notion_to_hexo.py <notion_page_url>

功能:
1. 从Notion获取页面内容
2. 创建Hexo文章模板 (hexo new [name])
3. 转换Notion内容为Markdown
4. 上传图片到阿里云OSS
5. 生成Hexo静态文件 (hexo generate)

"https://www.notion.so/Test-Page-2f25084901088002b209f3fc4f8c4a3c?source=copy_link"
"""

import os
import sys
import subprocess
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
import base64
import hashlib

# ==================== 配置区域 ====================

# Hexo博客根目录 (默认为用户Documents下的Blog文件夹)
# 可以通过环境变量 HEXO_ROOT 或命令行参数 --blog-path 覆盖
DEFAULT_BLOG_PATH = Path.home() / 'Documents' / 'Blog'
HEXO_ROOT = Path(os.environ.get('HEXO_ROOT', DEFAULT_BLOG_PATH))

# 阿里云OSS配置 (运行时输入)
OSS_CONFIG = {
    'access_key_id': '',
    'access_key_secret': '',
    'bucket_name': '',
    'endpoint': '',  # 例如: oss-cn-hangzhou.aliyuncs.com
    'cdn_domain': '',  # 例如: phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com
}

# Notion API配置 (将从环境变量或用户输入获取)
NOTION_TOKEN = os.environ.get('NOTION_TOKEN', '')

# Hexo文章默认配置
HEXO_CONFIG = {
    'default_title': '',
    'default_category': '学习笔记',
    'default_tags': [],
    'default_description': '',
    'default_mathjax': False,
}

# 加载配置文件
def load_config():
    """从config.json加载配置"""
    global HEXO_ROOT, NOTION_TOKEN, OSS_CONFIG, HEXO_CONFIG

    config_path = Path(__file__).parent / 'config.json'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 加载Notion配置
        if 'notion' in config and config['notion'].get('token'):
            NOTION_TOKEN = config['notion']['token']

        # 加载OSS配置
        if 'oss' in config:
            oss = config['oss']
            OSS_CONFIG['access_key_id'] = oss.get('access_key_id', '')
            OSS_CONFIG['access_key_secret'] = oss.get('access_key_secret', '')
            OSS_CONFIG['bucket_name'] = oss.get('bucket_name', '')
            OSS_CONFIG['endpoint'] = oss.get('endpoint', '')
            OSS_CONFIG['cdn_domain'] = oss.get('cdn_domain', '')

        # 加载Hexo配置
        if 'hexo' in config:
            hexo = config['hexo']
            if hexo.get('blog_path'):
                HEXO_ROOT = Path(hexo['blog_path'])
            HEXO_CONFIG['default_title'] = hexo.get('default_title', '')
            HEXO_CONFIG['default_category'] = hexo.get('default_category', '学习笔记')
            HEXO_CONFIG['default_tags'] = hexo.get('default_tags', [])
            HEXO_CONFIG['default_description'] = hexo.get('default_description', '')
            HEXO_CONFIG['default_mathjax'] = hexo.get('default_mathjax', False)

        print(f"✓ 已从 {config_path} 加载配置")
    else:
        print(f"未找到配置文件: {config_path}")

# 启动时加载配置
load_config()

# ==================== 工具函数 ====================

def print_step(step_num, message):
    """打印步骤信息"""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {message}")
    print(f"{'='*60}")


def run_hexo_command(command, cwd=None):
    """运行Hexo命令"""
    if cwd is None:
        cwd = HEXO_ROOT

    full_command = f"cd {cwd} && {command}"
    print(f"执行命令: {command}")

    result = subprocess.run(
        full_command,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False, result.stderr

    print(f"成功: {result.stdout}")
    return True, result.stdout


def sanitize_filename(filename):
    """清理文件名,移除非法字符"""
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    filename = re.sub(r'\s+', '-', filename)
    # 移除首尾的连字符，避免被解析为命令行参数
    filename = filename.strip('-')
    # 合并多个连续的连字符
    filename = re.sub(r'-+', '-', filename)
    return filename


def extract_notion_page_id(url):
    """从Notion URL中提取页面ID"""
    # Remove query parameters first
    url_path = url.split('?')[0]

    # Try to match 32 hex chars at the end of the path (most reliable)
    match = re.search(r'([a-f0-9]{32})$', url_path, re.IGNORECASE)
    if match:
        page_id = match.group(1).lower()
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"

    # Try UUID format with dashes at the end
    match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$', url_path, re.IGNORECASE)
    if match:
        return match.group(1).lower()

    # Fallback: remove dashes from end segment only and look for 32 hex chars
    last_segment = url_path.split('/')[-1].replace('-', '')
    match = re.search(r'([a-f0-9]{32})$', last_segment, re.IGNORECASE)
    if match:
        page_id = match.group(1).lower()
        return f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"

    return None


def upload_to_oss(file_path, object_name=None):
    """
    上传文件到阿里云OSS

    Args:
        file_path: 本地文件路径
        object_name: OSS中的对象名称,如果为None则使用文件名

    Returns:
        上传后的URL
    """
    try:
        import oss2
    except ImportError:
        print("正在安装阿里云OSS SDK...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'oss2', '--break-system-packages'],
                      capture_output=True)
        import oss2

    if object_name is None:
        object_name = os.path.basename(file_path)

    # 添加img/前缀以保持与现有图片路径一致
    object_name = f"img/{object_name}"

    auth = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    bucket = oss2.Bucket(auth, OSS_CONFIG['endpoint'], OSS_CONFIG['bucket_name'])

    # Check if object already exists in OSS
    if bucket.object_exists(object_name):
        cdn_url = f"https://{OSS_CONFIG['cdn_domain']}/{object_name}"
        print(f"图片已存在,跳过上传: {cdn_url}")
        return cdn_url

    # 上传文件
    bucket.put_object_from_file(object_name, file_path)

    # 返回CDN URL
    cdn_url = f"https://{OSS_CONFIG['cdn_domain']}/{object_name}"
    print(f"图片已上传: {cdn_url}")
    return cdn_url


def download_notion_image(image_url, save_dir):
    """
    下载Notion图片

    Args:
        image_url: 图片URL
        save_dir: 保存目录

    Returns:
        保存的文件路径
    """
    # Extract stable image UUID from Notion S3 URL
    # URL format: .../workspace-uuid/image-uuid/filename.png?params
    # Example: .../2d355810-.../c2dd9413-e1b4-4ee5-97b1-64b4292f82c3/Screenshot.png?...
    parsed = urlparse(image_url)
    path_parts = parsed.path.split('/')

    # Try to extract UUID and original filename from path
    if len(path_parts) >= 3:
        image_uuid = path_parts[-2]  # e.g., c2dd9413-e1b4-4ee5-97b1-64b4292f82c3
        original_name = path_parts[-1]  # e.g., Screenshot_2026-01-23.png
        ext = os.path.splitext(original_name)[1] or '.png'
        filename = f"notion_{image_uuid[:8]}{ext}"
    else:
        # Fallback to old behavior
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        ext = os.path.splitext(parsed.path)[1] or '.png'
        filename = f"notion_{url_hash}{ext}"

    filepath = os.path.join(save_dir, filename)

    # 下载图片
    # 注意: Notion S3签名URL已包含认证信息，不需要额外的Authorization头
    # 添加Authorization头会导致AWS返回400错误
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = requests.get(image_url, headers=headers, stream=True)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return filepath


def process_images_in_markdown(markdown_content, temp_dir):
    """
    处理Markdown中的图片,下载并上传到OSS

    Args:
        markdown_content: Markdown内容
        temp_dir: 临时目录用于保存下载的图片

    Returns:
        处理后的Markdown内容
    """
    # 匹配Markdown图片语法: ![alt](url)
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'

    def replace_image(match):
        alt_text = match.group(1)
        image_url = match.group(2)

        # 如果已经是OSS链接,不处理
        if OSS_CONFIG['cdn_domain'] in image_url:
            return match.group(0)

        try:
            print(f"处理图片: {image_url}")

            # 下载图片
            local_path = download_notion_image(image_url, temp_dir)

            # 上传到OSS
            oss_url = upload_to_oss(local_path)

            # 返回新的Markdown图片语法
            return f"![{alt_text}]({oss_url})"

        except Exception as e:
            print(f"图片处理失败: {image_url}, 错误: {str(e)}")
            # 保留原链接
            return match.group(0)

    return re.sub(image_pattern, replace_image, markdown_content)


def fetch_notion_page(page_id):
    """
    使用Notion API获取页面内容
    注意: 这需要Notion Integration Token

    Returns:
        (title, content_markdown, tags, category, description, mathjax)
    """
    if not NOTION_TOKEN:
        raise ValueError("未设置NOTION_TOKEN。请设置环境变量或在脚本中配置。")

    headers = {
        'Authorization': f'Bearer {NOTION_TOKEN}',
        'Notion-Version': '2022-06-28',
        'Content-Type': 'application/json',
    }

    # 获取页面属性
    page_url = f'https://api.notion.com/v1/pages/{page_id}'
    page_response = requests.get(page_url, headers=headers)
    page_response.raise_for_status()
    page_data = page_response.json()

    # 提取标题和属性
    properties = page_data.get('properties', {})

    # 提取标题
    title = ''
    if 'title' in properties:
        title_property = properties['title']
        if title_property.get('title'):
            title = ''.join([t['plain_text'] for t in title_property['title']])

    # 提取其他属性 (需要根据你的Notion数据库结构调整)
    tags = []
    category = '学习笔记'  # 默认分类
    description = ''
    mathjax = False

    # 尝试提取tags
    if 'Tags' in properties or 'tags' in properties:
        tag_property = properties.get('Tags') or properties.get('tags')
        if tag_property.get('type') == 'multi_select':
            tags = [tag['name'] for tag in tag_property.get('multi_select', [])]

    # 尝试提取分类
    if 'Category' in properties or 'category' in properties:
        cat_property = properties.get('Category') or properties.get('category')
        if cat_property.get('type') == 'select' and cat_property.get('select'):
            category = cat_property['select']['name']

    # 尝试提取描述
    if 'Description' in properties or 'description' in properties:
        desc_property = properties.get('Description') or properties.get('description')
        if desc_property.get('type') == 'rich_text':
            description = ''.join([t['plain_text'] for t in desc_property.get('rich_text', [])])

    # 检查是否需要mathjax
    if 'MathJax' in properties or 'mathjax' in properties:
        math_property = properties.get('MathJax') or properties.get('mathjax')
        if math_property.get('type') == 'checkbox':
            mathjax = math_property.get('checkbox', False)

    # 获取页面内容块
    blocks_url = f'https://api.notion.com/v1/blocks/{page_id}/children'
    blocks_response = requests.get(blocks_url, headers=headers)
    blocks_response.raise_for_status()
    blocks_data = blocks_response.json()

    # 转换为Markdown (简化版本)
    markdown_content = blocks_to_markdown(blocks_data.get('results', []), headers)

    # 检查内容中是否有数学公式
    if '$' in markdown_content or '\\[' in markdown_content:
        mathjax = True

    return title, markdown_content, tags, category, description, mathjax


def blocks_to_markdown(blocks, headers, level=0):
    """
    将Notion blocks转换为Markdown
    这是一个简化版本,可能需要根据实际情况扩展
    """
    markdown = []

    for block in blocks:
        block_type = block.get('type')
        block_content = block.get(block_type, {})

        if block_type == 'paragraph':
            text = rich_text_to_markdown(block_content.get('rich_text', []))
            markdown.append(text)
            markdown.append('')  # 空行

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
            markdown.append(f"$$")
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

        # 处理子块
        if block.get('has_children'):
            children_url = f"https://api.notion.com/v1/blocks/{block['id']}/children"
            children_response = requests.get(children_url, headers=headers)
            if children_response.status_code == 200:
                children_data = children_response.json()
                child_markdown = blocks_to_markdown(
                    children_data.get('results', []),
                    headers,
                    level + 1
                )
                markdown.append(child_markdown)

    return '\n'.join(markdown)


def rich_text_to_markdown(rich_text_array):
    """将Notion rich text转换为Markdown"""
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

        # 应用格式
        if annotations.get('bold'):
            text = f"**{text}**"
        if annotations.get('italic'):
            text = f"*{text}*"
        if annotations.get('code'):
            text = f"`{text}`"
        if annotations.get('strikethrough'):
            text = f"~~{text}~~"

        # 处理链接
        if href:
            text = f"[{text}]({href})"

        result.append(text)

    return ''.join(result)


def create_hexo_post(title, content, tags, category, description, mathjax):
    """
    创建Hexo博客文章

    Args:
        title: 文章标题
        content: Markdown内容
        tags: 标签列表
        category: 分类
        description: 描述
        mathjax: 是否启用mathjax
    """
    # 1. 使用hexo new创建文章
    print_step(1, f"创建Hexo文章: {title}")

    safe_title = sanitize_filename(title)
    # 使用双引号包裹标题，避免特殊字符问题
    success, output = run_hexo_command(f'hexo new "{safe_title}"')

    if not success:
        raise Exception(f"创建Hexo文章失败: {output}")

    # 2. 找到创建的文件
    post_file = HEXO_ROOT / 'source' / '_posts' / f'{safe_title}.md'

    if not post_file.exists():
        raise Exception(f"找不到创建的文章文件: {post_file}")

    # 3. 准备front matter
    front_matter = {
        'title': title,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tags': tags,
        'categories': category,
        'mathjax': mathjax,
    }

    if description:
        front_matter['description'] = description

    # 4. 处理图片
    print_step(2, "处理图片并上传到OSS")

    # 创建临时目录
    temp_dir = HEXO_ROOT / 'temp_images'
    temp_dir.mkdir(exist_ok=True)

    processed_content = process_images_in_markdown(content, temp_dir)

    # 5. 写入文件
    print_step(3, "写入Markdown文件")

    with open(post_file, 'w', encoding='utf-8') as f:
        # 写入front matter
        f.write('---\n')
        for key, value in front_matter.items():
            if isinstance(value, list):
                f.write(f'{key}: [{", ".join(value)}]\n')
            elif isinstance(value, bool):
                f.write(f'{key}: {str(value).lower()}\n')
            else:
                f.write(f'{key}: {value}\n')
        f.write('---\n\n')

        # 写入内容
        f.write(processed_content)

    print(f"文章已创建: {post_file}")

    # 清理临时目录
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    return post_file


def test_mode_export(title, content, tags, category, description, mathjax):
    """
    Test mode: Export markdown to test folder without running Hexo commands

    Args:
        title: Article title
        content: Markdown content
        tags: Tags list
        category: Category
        description: Description
        mathjax: Whether to enable mathjax

    Returns:
        Path to the created test file
    """
    # Create test folder
    test_dir = Path(__file__).parent / 'test'
    test_dir.mkdir(exist_ok=True)

    # Prepare front matter
    front_matter = {
        'title': title,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tags': tags,
        'categories': category,
        'mathjax': mathjax,
    }

    if description:
        front_matter['description'] = description

    # Generate filename
    safe_title = sanitize_filename(title)
    test_file = test_dir / f'{safe_title}.md'

    # Write file
    with open(test_file, 'w', encoding='utf-8') as f:
        # Write front matter
        f.write('---\n')
        for key, value in front_matter.items():
            if isinstance(value, list):
                f.write(f'{key}: [{", ".join(value)}]\n')
            elif isinstance(value, bool):
                f.write(f'{key}: {str(value).lower()}\n')
            else:
                f.write(f'{key}: {value}\n')
        f.write('---\n\n')

        # Write content (without image processing in test mode)
        f.write(content)

    print(f"测试文件已创建: {test_file}")
    return test_file


def main():
    """主函数"""
    global HEXO_ROOT

    # Check for test mode flag
    test_mode = '--test' in sys.argv
    if test_mode:
        sys.argv.remove('--test')

    print("="*60)
    if test_mode:
        print("Notion to Hexo Blog Publisher (TEST MODE)")
    else:
        print("Notion to Hexo Blog Publisher")
    print("="*60)

    # 0. 检查并设置Hexo路径 (skip in test mode)
    if not test_mode and not HEXO_ROOT.exists():
        print(f"\n警告: 默认Blog路径不存在: {HEXO_ROOT}")
        custom_path = input("请输入你的Hexo博客路径 (或按Enter跳过): ").strip()
        if custom_path:
            HEXO_ROOT = Path(custom_path)
            if not HEXO_ROOT.exists():
                print(f"错误: 路径不存在: {HEXO_ROOT}")
                sys.exit(1)

    if not test_mode:
        print(f"Blog路径: {HEXO_ROOT}\n")
    else:
        test_dir = Path(__file__).parent / 'test'
        print(f"测试输出目录: {test_dir}\n")

    # 1. 获取Notion页面URL
    if len(sys.argv) < 2:
        # Try to read from page_url.txt
        page_url_file = Path(__file__).parent / 'page_url.txt'
        if page_url_file.exists():
            with open(page_url_file, 'r', encoding='utf-8') as f:
                notion_url = f.read().strip()
            if notion_url:
                print(f"从 page_url.txt 读取URL: {notion_url}")
            else:
                notion_url = input("\n请输入Notion页面URL: ").strip()
        else:
            notion_url = input("\n请输入Notion页面URL: ").strip()
    else:
        notion_url = sys.argv[1]

    # 2. 提取页面ID
    page_id = extract_notion_page_id(notion_url)
    if not page_id:
        print("错误: 无法从URL中提取Notion页面ID")
        sys.exit(1)

    print(f"Notion页面ID: {page_id}")

    # 3. 检查Notion Token
    global NOTION_TOKEN
    if not NOTION_TOKEN:
        NOTION_TOKEN = input("\n请输入Notion Integration Token: ").strip()

    # 4. 配置阿里云OSS (skip in test mode)
    if not test_mode:
        # 检查OSS配置是否已经从配置文件加载
        if not OSS_CONFIG['access_key_id']:
            print("\n配置阿里云OSS")
            print("(留空则从PicGo配置读取,或跳过此步骤)")

            access_key = input("Access Key ID: ").strip()
            if access_key:
                OSS_CONFIG['access_key_id'] = access_key
                OSS_CONFIG['access_key_secret'] = input("Access Key Secret: ").strip()
                OSS_CONFIG['bucket_name'] = input("Bucket名称: ").strip()
                OSS_CONFIG['endpoint'] = input("Endpoint (如: oss-cn-hangzhou.aliyuncs.com): ").strip()
                OSS_CONFIG['cdn_domain'] = input("CDN域名 (如: your-bucket.oss-cn-hangzhou.aliyuncs.com): ").strip()
            else:
                # 尝试从示例文章中推断OSS配置
                OSS_CONFIG['cdn_domain'] = 'phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com'
                print(f"使用默认CDN域名: {OSS_CONFIG['cdn_domain']}")
                print("请手动配置OSS认证信息...")
                OSS_CONFIG['access_key_id'] = input("Access Key ID: ").strip()
                OSS_CONFIG['access_key_secret'] = input("Access Key Secret: ").strip()
                OSS_CONFIG['bucket_name'] = input("Bucket名称: ").strip()
                OSS_CONFIG['endpoint'] = input("Endpoint: ").strip()
        else:
            print("\n✓ 使用已配置的阿里云OSS设置")
            print(f"  CDN域名: {OSS_CONFIG['cdn_domain']}")
            print(f"  Bucket: {OSS_CONFIG['bucket_name']}")
            print(f"  Endpoint: {OSS_CONFIG['endpoint']}")
    else:
        print("\n✓ 测试模式: 跳过OSS配置")

    try:
        # 5. 获取Notion内容
        print_step(0, "从Notion获取页面内容")
        try:
            print("获取Notion页面内容...")
            # print(fetch_notion_page(page_id))
            notion_title, content, notion_tags, notion_category, notion_description, notion_mathjax = fetch_notion_page(page_id)
        except Exception as e:
            raise Exception(f"获取Notion页面失败: {str(e)}")
        
        # 使用配置文件中的值，如果配置为空则使用Notion页面的值
        title = HEXO_CONFIG['default_title'] or notion_title
        tags = HEXO_CONFIG['default_tags'] if HEXO_CONFIG['default_tags'] else notion_tags
        category = HEXO_CONFIG['default_category'] or notion_category
        description = HEXO_CONFIG['default_description'] or notion_description
        mathjax = HEXO_CONFIG['default_mathjax'] or notion_mathjax

        # 若标题、分类等仍为空，则提示用户输入
        if not title:
            title = input("请输入文章标题: ").strip() or "无标题文章"
        if not category:
            category = input("请输入文章分类: ").strip() or "学习笔记"
        if not tags:
            tags_input = input("请输入文章标签(逗号分隔): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
        if not description:
            description = title
        if not mathjax:
            mathjax_input = input("是否启用MathJax? (y/n): ").strip().lower()
            mathjax = (mathjax_input == 'y')

        print(f"标题: {title}")
        print(f"标签: {tags}")
        print(f"分类: {category}")
        print(f"MathJax: {mathjax}")

        # Checkpoint: Show content preview and ask for confirmation
        print(f"\n内容预览 (前50字符):")
        print(f"  {content[:50]}...")

        confirm = input("\n确认继续创建Hexo文章? (y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消操作")
            sys.exit(0)

        # Check for existing post with same title (only in non-test mode)
        if not test_mode:
            safe_title = sanitize_filename(title)
            existing_post = HEXO_ROOT / 'source' / '_posts' / f'{safe_title}.md'
            existing_asset_folder = HEXO_ROOT / 'source' / '_posts' / safe_title
            if existing_post.exists():
                print(f"\n警告: 已存在同名文章: {existing_post}")
                choice = input("是否替换现有文章? (y/n): ").strip().lower()
                if choice != 'y':
                    print("已取消操作")
                    sys.exit(0)
                # Delete existing post file
                existing_post.unlink()
                print(f"已删除旧文章: {existing_post}")
                # Delete existing asset folder if it exists
                if existing_asset_folder.exists() and existing_asset_folder.is_dir():
                    import shutil
                    shutil.rmtree(existing_asset_folder)
                    print(f"已删除旧资源文件夹: {existing_asset_folder}")

        if test_mode:
            # Test mode: export to test folder without Hexo commands
            print_step(1, "导出Markdown到测试目录")
            test_file = test_mode_export(title, content, tags, category, description, mathjax)

            # 完成
            print("\n" + "="*60)
            print("测试导出完成!")
            print("="*60)
            print(f"测试文件: {test_file}")
            print(f"\n注意: 测试模式下图片URL保持原始Notion链接,未上传到OSS")
        else:
            # 6. 创建Hexo文章
            post_file = create_hexo_post(title, content, tags, category, description, mathjax)

            # 7. 生成静态文件
            print_step(4, "生成Hexo静态文件")
            success, _ = run_hexo_command("hexo generate")

            if not success:
                print(f"警告: 生成静态文件时出现错误")

            # 8. 完成
            print("\n" + "="*60)
            print("发布完成!")
            print("="*60)
            print(f"文章文件: {post_file}")
            print(f"\n请检查文章内容,确认无误后运行:")
            print(f"  cd {HEXO_ROOT}")
            print(f"  hexo deploy")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
