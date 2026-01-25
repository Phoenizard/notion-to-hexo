"""
Aliyun OSS image handling for Notion to Hexo.

Provides functions for downloading images from Notion and
uploading them to Aliyun OSS.
"""

import os
import re
import hashlib
from urllib.parse import urlparse

from .config import config
from .network import request_with_retry


def upload_to_oss(file_path, object_name=None, oss_config=None):
    """
    Upload file to Aliyun OSS.

    Args:
        file_path: Local file path
        object_name: Object name in OSS. If None, uses the filename.
        oss_config: Optional OSS config override (uses config.oss_config if not provided)

    Returns:
        URL after upload (CDN URL)
    """
    import oss2

    oss_cfg = oss_config or config.oss_config

    if object_name is None:
        object_name = os.path.basename(file_path)

    # Add img/ prefix to maintain consistency with existing image paths
    object_name = f"img/{object_name}"

    auth = oss2.Auth(oss_cfg['access_key_id'], oss_cfg['access_key_secret'])
    bucket = oss2.Bucket(auth, oss_cfg['endpoint'], oss_cfg['bucket_name'])

    # Check if object already exists in OSS
    if bucket.object_exists(object_name):
        cdn_url = f"https://{oss_cfg['cdn_domain']}/{object_name}"
        print(f"图片已存在,跳过上传: {cdn_url}")
        return cdn_url

    # Upload file
    bucket.put_object_from_file(object_name, file_path)

    # Return CDN URL
    cdn_url = f"https://{oss_cfg['cdn_domain']}/{object_name}"
    print(f"图片已上传: {cdn_url}")
    return cdn_url


def download_notion_image(image_url, save_dir):
    """
    Download image from Notion.

    Args:
        image_url: Image URL from Notion
        save_dir: Directory to save the downloaded image

    Returns:
        Path to the saved file
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

    # Download image
    # Note: Notion S3 signed URLs already contain auth info, no Authorization header needed
    # Adding Authorization header causes AWS to return 400 error
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    response = request_with_retry('get', image_url, headers=headers, stream=True, timeout_type='image')

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return filepath


def process_images_in_markdown(markdown_content, temp_dir, oss_config=None):
    """
    Process images in Markdown content, download and upload to OSS.

    Args:
        markdown_content: Markdown content with image references
        temp_dir: Temporary directory for downloaded images
        oss_config: Optional OSS config override

    Returns:
        Processed Markdown content with OSS URLs
    """
    oss_cfg = oss_config or config.oss_config

    # Match Markdown image syntax: ![alt](url)
    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'

    def replace_image(match):
        alt_text = match.group(1)
        image_url = match.group(2)

        # If already an OSS link, don't process
        if oss_cfg['cdn_domain'] in image_url:
            return match.group(0)

        try:
            print(f"处理图片: {image_url}")

            # Download image
            local_path = download_notion_image(image_url, temp_dir)

            # Upload to OSS
            oss_url = upload_to_oss(local_path, oss_config=oss_cfg)

            # Return new Markdown image syntax
            return f"![{alt_text}]({oss_url})"

        except Exception as e:
            print(f"图片处理失败: {image_url}, 错误: {str(e)}")
            # Keep original link
            return match.group(0)

    return re.sub(image_pattern, replace_image, markdown_content)
