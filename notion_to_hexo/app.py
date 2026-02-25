"""
Streamlit Web UI for Notion to Hexo.

Provides a visual interface for converting Notion pages to Hexo blog posts.

Usage:
    streamlit run notion_to_hexo/app.py
    or
    notion-to-hexo --ui
"""

import json
import logging
from pathlib import Path
from datetime import datetime

import streamlit as st

from notion_to_hexo.config import config, load_config
from notion_to_hexo.hexo import sanitize_filename, run_hexo_command
from notion_to_hexo.notion import fetch_notion_page, extract_notion_page_id
from notion_to_hexo.oss import process_images_in_markdown
from notion_to_hexo.cli import _build_front_matter, generate_summary_with_llm

logger = logging.getLogger(__name__)


def _save_config_to_file(cfg_dict):
    """Save configuration to config.json."""
    config_path = config.get_config_path()
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(cfg_dict, f, indent=2, ensure_ascii=False)


def _load_config_dict():
    """Load raw config dict from config.json."""
    config_path = config.get_config_path()
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def sidebar_config():
    """Render sidebar configuration panel."""
    st.sidebar.header("配置管理")

    cfg = _load_config_dict()

    with st.sidebar.expander("Notion 配置", expanded=False):
        notion_token = st.text_input(
            "Notion Token",
            value=cfg.get('notion', {}).get('token', config.notion_token),
            type="password",
            key="notion_token"
        )

    with st.sidebar.expander("OSS 配置", expanded=False):
        oss_cfg = cfg.get('oss', {})
        oss_key_id = st.text_input("Access Key ID",
                                    value=oss_cfg.get('access_key_id', config.oss_config['access_key_id']),
                                    type="password", key="oss_key_id")
        oss_key_secret = st.text_input("Access Key Secret",
                                        value=oss_cfg.get('access_key_secret', config.oss_config['access_key_secret']),
                                        type="password", key="oss_key_secret")
        oss_bucket = st.text_input("Bucket 名称",
                                    value=oss_cfg.get('bucket_name', config.oss_config['bucket_name']),
                                    key="oss_bucket")
        oss_endpoint = st.text_input("Endpoint",
                                      value=oss_cfg.get('endpoint', config.oss_config['endpoint']),
                                      key="oss_endpoint")
        oss_cdn = st.text_input("CDN 域名",
                                 value=oss_cfg.get('cdn_domain', config.oss_config['cdn_domain']),
                                 key="oss_cdn")

    with st.sidebar.expander("Hexo 配置", expanded=False):
        hexo_cfg = cfg.get('hexo', {})
        blog_path = st.text_input("Blog 路径",
                                   value=hexo_cfg.get('blog_path', str(config.hexo_root)),
                                   key="blog_path")
        default_category = st.text_input("默认分类",
                                          value=hexo_cfg.get('default_category', config.hexo_config['default_category']),
                                          key="default_category")

    with st.sidebar.expander("LLM 配置", expanded=False):
        llm_cfg = cfg.get('llm', {})
        dashscope_key = st.text_input("DashScope API Key",
                                       value=llm_cfg.get('dashscope_api_key', config.dashscope_api_key),
                                       type="password", key="dashscope_key")

    if st.sidebar.button("保存配置"):
        new_cfg = {
            'notion': {'token': notion_token},
            'oss': {
                'access_key_id': oss_key_id,
                'access_key_secret': oss_key_secret,
                'bucket_name': oss_bucket,
                'endpoint': oss_endpoint,
                'cdn_domain': oss_cdn,
            },
            'hexo': {
                'blog_path': blog_path,
                'default_category': default_category,
                'default_tags': hexo_cfg.get('default_tags', []),
                'default_title': hexo_cfg.get('default_title', ''),
                'default_description': hexo_cfg.get('default_description', ''),
                'default_mathjax': hexo_cfg.get('default_mathjax', False),
            },
            'llm': {'dashscope_api_key': dashscope_key},
        }
        _save_config_to_file(new_cfg)
        # Apply to runtime config
        config.notion_token = notion_token
        config.oss_config['access_key_id'] = oss_key_id
        config.oss_config['access_key_secret'] = oss_key_secret
        config.oss_config['bucket_name'] = oss_bucket
        config.oss_config['endpoint'] = oss_endpoint
        config.oss_config['cdn_domain'] = oss_cdn
        config.hexo_root = Path(blog_path)
        config.dashscope_api_key = dashscope_key
        st.sidebar.success("配置已保存!")

    # Always apply current sidebar values to runtime config
    config.notion_token = notion_token
    config.oss_config['access_key_id'] = oss_key_id
    config.oss_config['access_key_secret'] = oss_key_secret
    config.oss_config['bucket_name'] = oss_bucket
    config.oss_config['endpoint'] = oss_endpoint
    config.oss_config['cdn_domain'] = oss_cdn
    config.hexo_root = Path(blog_path)
    config.dashscope_api_key = dashscope_key


def main_ui():
    """Main Streamlit application."""
    st.set_page_config(page_title="Notion to Hexo", page_icon="📝", layout="wide")
    st.title("📝 Notion to Hexo Publisher")

    # Load config on first run
    load_config()

    # Sidebar configuration
    sidebar_config()

    # Initialize session state
    if 'page_data' not in st.session_state:
        st.session_state.page_data = None
    if 'processed_content' not in st.session_state:
        st.session_state.processed_content = None

    # Input section
    st.subheader("1. 输入 Notion 页面")
    notion_url = st.text_input("Notion URL", placeholder="https://www.notion.so/...")

    if st.button("获取页面", type="primary"):
        if not notion_url:
            st.error("请输入 Notion URL")
            return

        page_id = extract_notion_page_id(notion_url)
        if not page_id:
            st.error("无法从 URL 中提取 Notion 页面 ID")
            return

        if not config.notion_token:
            st.error("请在侧边栏配置 Notion Token")
            return

        with st.status("正在获取页面内容...", expanded=True) as status:
            try:
                st.write("正在连接 Notion API...")
                title, content, tags, category, description, mathjax = fetch_notion_page(page_id)
                st.session_state.page_data = {
                    'title': title,
                    'content': content,
                    'tags': tags,
                    'category': category,
                    'description': description,
                    'mathjax': mathjax,
                }
                status.update(label="页面获取成功!", state="complete")
            except Exception as e:
                status.update(label="获取失败", state="error")
                st.error(f"获取 Notion 页面失败: {e}")
                return

    # Metadata editing
    if st.session_state.page_data:
        data = st.session_state.page_data

        st.subheader("2. 编辑元数据")

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("标题", value=data['title'])
            front_title = st.text_input("前端显示标题", value=data['title'],
                                         help="front matter 中的 title，留空则使用标题")
            category = st.text_input("分类", value=data['category'])

        with col2:
            tags_str = st.text_input("标签 (逗号分隔)",
                                      value=', '.join(data['tags']) if data['tags'] else '')
            tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
            description = st.text_area("描述/摘要", value=data.get('description', ''), height=100)

        # Options
        col3, col4 = st.columns(2)
        with col3:
            mathjax = st.checkbox("启用 MathJax", value=data['mathjax'])
        with col4:
            if st.button("LLM 生成摘要"):
                with st.spinner("正在生成摘要..."):
                    summary = generate_summary_with_llm(data['content'], front_title or title)
                    if summary:
                        description = summary
                        st.success("摘要生成成功!")
                        st.write(summary)
                    else:
                        st.warning("摘要生成失败，请检查 DashScope API Key 配置")

        # Preview
        st.subheader("3. 内容预览")
        with st.expander("查看 Markdown 内容", expanded=False):
            st.markdown(data['content'])

        # Build front matter for preview
        front_matter = {
            'title': front_title or title,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tags': tags,
            'categories': category,
            'mathjax': mathjax,
        }
        if description:
            front_matter['description'] = description

        with st.expander("查看 Front Matter", expanded=True):
            st.code(_build_front_matter(front_matter), language='yaml')

        # Actions
        st.subheader("4. 操作")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            if st.button("测试导出", help="导出到 test/ 目录"):
                with st.status("正在导出...", expanded=True) as status:
                    try:
                        from .cli import test_mode_export
                        test_file = test_mode_export(
                            title, data['content'], tags, category,
                            description, mathjax, front_title or title
                        )
                        status.update(label="导出成功!", state="complete")
                        st.success(f"测试文件已创建: {test_file}")
                    except Exception as e:
                        status.update(label="导出失败", state="error")
                        st.error(f"导出失败: {e}")

        with col_b:
            if st.button("发布到 Hexo", type="primary"):
                if not config.oss_config['access_key_id']:
                    st.error("请先在侧边栏配置 OSS 凭证")
                    return

                with st.status("正在发布...", expanded=True) as status:
                    try:
                        from .cli import create_hexo_post
                        st.write("创建 Hexo 文章...")
                        post_file = create_hexo_post(
                            title, data['content'], tags, category,
                            description, mathjax, front_title or title
                        )
                        st.write("生成静态文件...")
                        run_hexo_command("hexo generate")
                        status.update(label="发布成功!", state="complete")
                        st.success(f"文章已发布: {post_file}")
                    except Exception as e:
                        status.update(label="发布失败", state="error")
                        st.error(f"发布失败: {e}")

        with col_c:
            # Download button
            md_content = _build_front_matter(front_matter) + data['content']
            safe_title = sanitize_filename(title)
            st.download_button(
                "下载 Markdown",
                data=md_content,
                file_name=f"{safe_title}.md",
                mime="text/markdown"
            )


if __name__ == '__main__':
    main_ui()
