"""
Aliyun OSS image handling for Notion to Hexo.

Provides functions for downloading images from Notion and
uploading them to Aliyun OSS.
"""

import os
import re
import hashlib
import logging
from urllib.parse import urlparse

from .config import config
from .network import request_with_retry
from .exceptions import OSSUploadError

logger = logging.getLogger(__name__)


def upload_to_oss(file_path, object_name=None, oss_config=None):
    """
    Upload file to Aliyun OSS.

    Args:
        file_path: Local file path
        object_name: Object name in OSS. If None, uses the filename.
        oss_config: Optional OSS config override

    Returns:
        URL after upload (CDN URL)

    Raises:
        OSSUploadError: If upload fails
    """
    import oss2

    oss_cfg = oss_config or config.oss_config

    if object_name is None:
        object_name = os.path.basename(file_path)

    object_name = f"img/{object_name}"

    try:
        auth = oss2.Auth(oss_cfg['access_key_id'], oss_cfg['access_key_secret'])
        bucket = oss2.Bucket(auth, oss_cfg['endpoint'], oss_cfg['bucket_name'])

        if bucket.object_exists(object_name):
            cdn_url = f"https://{oss_cfg['cdn_domain']}/{object_name}"
            logger.info("图片已存在,跳过上传: %s", cdn_url)
            return cdn_url

        bucket.put_object_from_file(object_name, file_path)

        cdn_url = f"https://{oss_cfg['cdn_domain']}/{object_name}"
        logger.info("图片已上传: %s", cdn_url)
        return cdn_url
    except Exception as e:
        raise OSSUploadError(f"上传到OSS失败: {e}") from e


def download_notion_image(image_url, save_dir):
    """
    Download image from Notion.

    Args:
        image_url: Image URL from Notion
        save_dir: Directory to save the downloaded image

    Returns:
        Path to the saved file
    """
    parsed = urlparse(image_url)
    path_parts = parsed.path.split('/')

    if len(path_parts) >= 3:
        image_uuid = path_parts[-2]
        original_name = path_parts[-1]
        ext = os.path.splitext(original_name)[1] or '.png'
        filename = f"notion_{image_uuid[:8]}{ext}"
    else:
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        ext = os.path.splitext(parsed.path)[1] or '.png'
        filename = f"notion_{url_hash}{ext}"

    filepath = os.path.join(save_dir, filename)

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

    image_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'

    def replace_image(match):
        alt_text = match.group(1)
        image_url = match.group(2)

        if oss_cfg['cdn_domain'] in image_url:
            return match.group(0)

        try:
            logger.info("处理图片: %s", image_url[:80])
            local_path = download_notion_image(image_url, temp_dir)
            oss_url = upload_to_oss(local_path, oss_config=oss_cfg)
            return f"![{alt_text}]({oss_url})"
        except Exception as e:
            logger.warning("图片处理失败: %s, 错误: %s", image_url[:80], e)
            return match.group(0)

    return re.sub(image_pattern, replace_image, markdown_content)
