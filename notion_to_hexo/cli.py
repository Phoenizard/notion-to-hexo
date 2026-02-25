"""
Command-line interface and main workflow for Notion to Hexo.

Provides the main entry point and workflow orchestration.
"""

import sys
import time
import shutil
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

import yaml

from .config import config, get_config, load_config
from .hexo import run_hexo_command, sanitize_filename, find_hexo_executable
from .notion import fetch_notion_page, extract_notion_page_id
from .oss import process_images_in_markdown
from .exceptions import (
    NotionAPIError, OSSUploadError, HexoCommandError, ConfigurationError
)

logger = logging.getLogger(__name__)


def print_step(step_num, message):
    """Print step information with formatting."""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {message}")
    print(f"{'='*60}")


def _build_front_matter(front_matter):
    """
    Build YAML front matter string.

    Uses PyYAML to properly escape special characters in titles
    and other fields, preventing invalid YAML output.

    Args:
        front_matter: Dictionary of front matter fields

    Returns:
        Complete front matter string with --- delimiters
    """
    content = yaml.dump(
        front_matter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{content}---\n\n"


def generate_summary_with_llm(content, front_title):
    """
    Generate article summary using Aliyun DashScope API.

    Args:
        content: Full article content (markdown)
        front_title: Article display title

    Returns:
        Generated summary string, or None if generation fails
    """
    try:
        from dashscope import Generation
    except ImportError:
        logger.warning("dashscope 未安装，无法生成摘要。请运行: pip install dashscope")
        return None

    api_key = config.dashscope_api_key
    if not api_key:
        logger.warning("DASHSCOPE_API_KEY 未配置")
        return None

    title_context = f"标题：{front_title}\n\n" if front_title else ""
    user_prompt = f"""请为以下文章生成一段简洁的摘要（150-250字），用于博客文章的description字段。
摘要应该：
1. 概括文章的主要内容和核心观点
2. 吸引读者继续阅读
3. 使用与文章相同的语言（中文文章用中文，英文文章用英文）
4. 避免使用数学符号或特殊字符

{title_context}内容：
{content[:4000]}"""

    system_prompt = "你是一个专业的内容编辑，擅长为博客文章撰写吸引人的摘要。请直接输出摘要内容，不需要任何前缀或解释。"

    try:
        print("正在调用 LLM API 生成摘要...")
        response = Generation.call(
            api_key=api_key,
            model='qwen-turbo',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            result_format='message'
        )

        if response.status_code == 200:
            summary = response.output.choices[0].message.content
            return summary.strip()
        else:
            logger.error("API 调用失败: %s - %s", response.code, response.message)
            return None
    except Exception as e:
        logger.error("生成摘要时出错: %s", e)
        return None


def create_hexo_post(title, content, tags, category, description, mathjax, front_title=None):
    """
    Create a Hexo blog post.

    Args:
        title: Article title (used for hexo new command to generate filename)
        content: Markdown content
        tags: List of tags
        category: Category name
        description: Article description
        mathjax: Whether to enable mathjax
        front_title: Display title for front matter (defaults to title)

    Returns:
        Path to the created post file
    """
    print_step(1, f"创建Hexo文章: {title}")

    safe_title = sanitize_filename(title)
    success, output = run_hexo_command(['hexo', 'new', safe_title])

    if not success:
        raise HexoCommandError(f"创建Hexo文章失败: {output}")

    post_file = config.hexo_root / 'source' / '_posts' / f'{safe_title}.md'

    if not post_file.exists():
        raise HexoCommandError(f"找不到创建的文章文件: {post_file}")

    # Prepare front matter
    front_matter = {
        'title': front_title if front_title else title,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tags': tags,
        'categories': category,
        'mathjax': mathjax,
    }

    if description:
        front_matter['description'] = description

    # Process images
    print_step(2, "处理图片并上传到OSS")
    temp_dir = config.hexo_root / 'temp_images'
    temp_dir.mkdir(exist_ok=True)

    try:
        processed_content = process_images_in_markdown(content, temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Write file
    print_step(3, "写入Markdown文件")

    with open(post_file, 'w', encoding='utf-8') as f:
        f.write(_build_front_matter(front_matter))
        f.write(processed_content)

    print(f"文章已创建: {post_file}")
    return post_file


def test_mode_export(title, content, tags, category, description, mathjax, front_title=None):
    """
    Test mode: Export markdown to test folder without running Hexo commands.

    Args:
        title: Article title (used for filename)
        content: Markdown content
        tags: Tags list
        category: Category
        description: Description
        mathjax: Whether to enable mathjax
        front_title: Display title for front matter (defaults to title)

    Returns:
        Path to the created test file
    """
    test_dir = Path(__file__).parent.parent / 'test'
    test_dir.mkdir(exist_ok=True)

    front_matter = {
        'title': front_title if front_title else title,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tags': tags,
        'categories': category,
        'mathjax': mathjax,
    }

    if description:
        front_matter['description'] = description

    safe_title = sanitize_filename(title)
    test_file = test_dir / f'{safe_title}.md'

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(_build_front_matter(front_matter))
        f.write(content)

    print(f"测试文件已创建: {test_file}")
    return test_file


def _prompt(message, default='', yes_mode=False):
    """
    Prompt user for input, respecting --yes mode.

    In --yes mode, returns the default value without prompting.
    """
    if yes_mode:
        return default
    return input(message).strip() or default


def _confirm(message, yes_mode=False):
    """
    Ask user for y/n confirmation.

    In --yes mode, returns True without prompting.
    """
    if yes_mode:
        return True
    return input(message).strip().lower() == 'y'


def build_parser():
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog='notion-to-hexo',
        description='将 Notion 页面转换为 Hexo 博客文章'
    )

    parser.add_argument('url', nargs='?', help='Notion 页面 URL')

    # Mode flags
    parser.add_argument('--test', action='store_true',
                        help='测试模式：导出到 test/ 目录，不运行 Hexo 命令')
    parser.add_argument('--dry-run', action='store_true',
                        help='预览模式：获取并转换内容，不写文件不上传')
    parser.add_argument('--ui', action='store_true',
                        help='启动 Streamlit Web 界面')

    # Article metadata
    parser.add_argument('--title', help='覆盖文章标题')
    parser.add_argument('--front-title', help='前端显示标题（front matter 中的 title）')
    parser.add_argument('--category', help='文章分类')
    parser.add_argument('--tags', nargs='+', help='文章标签')
    parser.add_argument('--description', help='文章描述/摘要')

    # Behavior flags
    parser.add_argument('-y', '--yes', action='store_true',
                        help='非交互模式，跳过所有确认提示')
    parser.add_argument('--no-serve', action='store_true',
                        help='跳过本地预览服务器')
    parser.add_argument('--deploy', action='store_true',
                        help='自动部署到远程')
    parser.add_argument('--llm-summary', action='store_true',
                        help='使用 LLM 自动生成文章摘要')

    # Configuration
    parser.add_argument('--config', dest='config_path',
                        help='指定配置文件路径')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='显示详细日志')

    return parser


def main(argv=None):
    """Main entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Handle --ui: launch Streamlit
    if args.ui:
        app_path = Path(__file__).parent / 'app.py'
        try:
            subprocess.run(
                [sys.executable, '-m', 'streamlit', 'run', str(app_path),
                 '--server.headless', 'true'],
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("错误: 无法启动 Streamlit。请安装: pip install 'notion-to-hexo[ui]'")
            sys.exit(1)
        return

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(name)s - %(levelname)s - %(message)s'
    )

    # Load configuration
    get_config(args.config_path)

    yes_mode = args.yes
    test_mode = args.test
    dry_run = args.dry_run

    print("=" * 60)
    mode_label = ""
    if test_mode:
        mode_label = " (TEST MODE)"
    elif dry_run:
        mode_label = " (DRY RUN)"
    print(f"Notion to Hexo Blog Publisher{mode_label}")
    print("=" * 60)

    # Check Hexo path (skip in test/dry-run mode)
    if not test_mode and not dry_run and not config.hexo_root.exists():
        print(f"\n警告: 默认Blog路径不存在: {config.hexo_root}")
        custom_path = _prompt("请输入你的Hexo博客路径 (或按Enter跳过): ", yes_mode=yes_mode)
        if custom_path:
            config.hexo_root = Path(custom_path)
            if not config.hexo_root.exists():
                print(f"错误: 路径不存在: {config.hexo_root}")
                sys.exit(1)
        elif yes_mode:
            raise ConfigurationError(f"Blog路径不存在: {config.hexo_root}")

    if not test_mode and not dry_run:
        print(f"Blog路径: {config.hexo_root}\n")
    elif test_mode:
        test_dir = Path(__file__).parent.parent / 'test'
        print(f"测试输出目录: {test_dir}\n")

    # Get Notion page URL
    notion_url = args.url
    if not notion_url:
        page_url_file = Path(__file__).parent.parent / 'page_url.txt'
        if page_url_file.exists():
            with open(page_url_file, 'r', encoding='utf-8') as f:
                notion_url = f.read().strip()
            if notion_url:
                print(f"从 page_url.txt 读取URL: {notion_url}")

    if not notion_url:
        if yes_mode:
            print("错误: --yes 模式下必须提供 Notion URL")
            sys.exit(1)
        notion_url = input("\n请输入Notion页面URL: ").strip()

    # Extract page ID
    page_id = extract_notion_page_id(notion_url)
    if not page_id:
        print("错误: 无法从URL中提取Notion页面ID")
        sys.exit(1)

    print(f"Notion页面ID: {page_id}")

    # Check Notion Token
    if not config.notion_token:
        if yes_mode:
            raise ConfigurationError("NOTION_TOKEN 未配置")
        config.notion_token = input("\n请输入Notion Integration Token: ").strip()

    # Configure OSS (skip in test/dry-run mode)
    if not test_mode and not dry_run:
        if not config.oss_config['access_key_id']:
            if yes_mode:
                raise ConfigurationError("OSS 凭证未配置，--yes 模式下无法交互输入")
            print("\n配置阿里云OSS")
            print("(留空则从PicGo配置读取,或跳过此步骤)")

            access_key = input("Access Key ID: ").strip()
            if access_key:
                config.oss_config['access_key_id'] = access_key
                config.oss_config['access_key_secret'] = input("Access Key Secret: ").strip()
                config.oss_config['bucket_name'] = input("Bucket名称: ").strip()
                config.oss_config['endpoint'] = input("Endpoint (如: oss-cn-hangzhou.aliyuncs.com): ").strip()
                config.oss_config['cdn_domain'] = input("CDN域名 (如: your-bucket.oss-cn-hangzhou.aliyuncs.com): ").strip()
            else:
                config.oss_config['cdn_domain'] = 'phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com'
                print(f"使用默认CDN域名: {config.oss_config['cdn_domain']}")
                print("请手动配置OSS认证信息...")
                config.oss_config['access_key_id'] = input("Access Key ID: ").strip()
                config.oss_config['access_key_secret'] = input("Access Key Secret: ").strip()
                config.oss_config['bucket_name'] = input("Bucket名称: ").strip()
                config.oss_config['endpoint'] = input("Endpoint: ").strip()
        else:
            print("\n已使用配置的阿里云OSS设置")
            print(f"  CDN域名: {config.oss_config['cdn_domain']}")
            print(f"  Bucket: {config.oss_config['bucket_name']}")
            print(f"  Endpoint: {config.oss_config['endpoint']}")
    else:
        print(f"\n{'测试' if test_mode else '预览'}模式: 跳过OSS配置")

    try:
        # Fetch Notion content
        print_step(0, "从Notion获取页面内容")
        print("获取Notion页面内容...")
        try:
            notion_title, content, notion_tags, notion_category, notion_description, notion_mathjax = fetch_notion_page(page_id)
        except NotionAPIError as e:
            raise NotionAPIError(f"获取Notion页面失败: {e}") from e

        # Merge: CLI args > config defaults > Notion page values
        title = args.title or config.hexo_config['default_title'] or notion_title
        tags = args.tags or (config.hexo_config['default_tags'] if config.hexo_config['default_tags'] else notion_tags)
        category = args.category or config.hexo_config['default_category'] or notion_category
        description = args.description or config.hexo_config['default_description'] or notion_description
        mathjax = config.hexo_config['default_mathjax'] or notion_mathjax

        # Prompt for missing values
        if not title:
            title = _prompt("请输入文章标题: ", "无标题文章", yes_mode)
        if not category:
            category = _prompt("请输入文章分类: ", "学习笔记", yes_mode)
        if not tags and not yes_mode:
            tags_input = input("请输入文章标签(逗号分隔): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
        if not mathjax and not yes_mode:
            mathjax_input = input("是否启用MathJax? (y/n): ").strip().lower()
            mathjax = (mathjax_input == 'y')

        print(f"标题: {title}")
        print(f"标签: {tags}")
        print(f"分类: {category}")
        print(f"MathJax: {mathjax}")

        # Front title
        front_title = args.front_title
        if not front_title and not yes_mode:
            front_title_input = input("请输入前端显示标题 (留空则使用文章标题): ").strip()
            front_title = front_title_input if front_title_input else title
        if not front_title:
            front_title = title
        if front_title != title:
            print(f"前端标题: {front_title}")

        # Summary generation
        if args.llm_summary:
            generated = generate_summary_with_llm(content, front_title)
            if generated:
                description = generated
                print(f"生成的摘要: {description}")
        elif not yes_mode:
            generate_summary = input("\n是否需要生成摘要? (y/n): ").strip().lower()
            if generate_summary == 'y':
                generated = generate_summary_with_llm(content, front_title)
                if generated:
                    description = generated
                    print(f"生成的摘要: {description}")
                else:
                    desc_input = input("请手动输入文章摘要 (留空则使用前端标题): ").strip()
                    description = desc_input if desc_input else front_title
            else:
                desc_input = input("请输入文章摘要 (留空则使用前端标题): ").strip()
                description = desc_input if desc_input else front_title

        if description:
            print(f"摘要: {description}")

        # Dry-run mode: show preview and exit
        if dry_run:
            front_matter = {
                'title': front_title,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tags': tags,
                'categories': category,
                'mathjax': mathjax,
            }
            if description:
                front_matter['description'] = description

            print("\n" + "=" * 60)
            print("Front Matter 预览:")
            print("=" * 60)
            print(_build_front_matter(front_matter))
            print(f"内容长度: {len(content)} 字符")
            print(f"内容预览 (前200字符):")
            print(f"  {content[:200]}...")
            print("\n" + "=" * 60)
            print("Dry-run 完成 - 未写入文件")
            print("=" * 60)
            return

        # Content preview and confirmation
        print(f"\n内容预览 (前50字符):")
        print(f"  {content[:50]}...")

        if not _confirm("\n确认继续创建Hexo文章? (y/n): ", yes_mode):
            print("已取消操作")
            sys.exit(0)

        # Check for existing post
        if not test_mode:
            safe_title = sanitize_filename(title)
            existing_post = config.hexo_root / 'source' / '_posts' / f'{safe_title}.md'
            existing_asset_folder = config.hexo_root / 'source' / '_posts' / safe_title
            if existing_post.exists():
                print(f"\n警告: 已存在同名文章: {existing_post}")
                if not _confirm("是否替换现有文章? (y/n): ", yes_mode):
                    print("已取消操作")
                    sys.exit(0)
                existing_post.unlink()
                print(f"已删除旧文章: {existing_post}")
                if existing_asset_folder.exists() and existing_asset_folder.is_dir():
                    shutil.rmtree(existing_asset_folder)
                    print(f"已删除旧资源文件夹: {existing_asset_folder}")

        if test_mode:
            print_step(1, "导出Markdown到测试目录")
            test_file = test_mode_export(title, content, tags, category, description, mathjax, front_title)

            print("\n" + "=" * 60)
            print("测试导出完成!")
            print("=" * 60)
            print(f"测试文件: {test_file}")
            print(f"\n注意: 测试模式下图片URL保持原始Notion链接,未上传到OSS")
        else:
            # Create Hexo post
            post_file = create_hexo_post(title, content, tags, category, description, mathjax, front_title)

            # Generate static files
            print_step(4, "生成Hexo静态文件")
            success, _ = run_hexo_command("hexo generate")

            if not success:
                print("警告: 生成静态文件时出现错误")

            if args.no_serve:
                print(f"\n文章文件: {post_file}")
                if args.deploy:
                    print_step(5, "部署到远程")
                    deploy_success, _ = run_hexo_command("hexo deploy")
                    if deploy_success:
                        print("\n部署完成!")
                    else:
                        print("警告: 部署时出现错误")
                return

            # Start local preview server
            print_step(5, "启动本地预览服务器")
            print("正在启动 hexo serve...")

            hexo_path = find_hexo_executable()
            if hexo_path:
                serve_cmd = [hexo_path, 'serve']
            else:
                npx_path = shutil.which('npx')
                if npx_path:
                    serve_cmd = [npx_path, 'hexo', 'serve']
                else:
                    serve_cmd = ['hexo', 'serve']

            serve_process = subprocess.Popen(
                serve_cmd,
                cwd=str(config.hexo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            time.sleep(3)

            if serve_process.poll() is not None:
                _, stderr = serve_process.communicate()
                error_msg = stderr.decode() if stderr else "未知错误"
                print(f"警告: hexo serve 启动失败: {error_msg}")
            else:
                print("\n" + "=" * 60)
                print("本地预览服务器已启动!")
                print("=" * 60)
                print(f"文章文件: {post_file}")
                print(f"\n预览地址: http://localhost:4000")
                print("请在浏览器中检查文章内容")
                print("=" * 60)

                deploy_choice = args.deploy or _confirm("\n确认部署到远程? (y/n): ", yes_mode=False)

                print("\n正在停止预览服务器...")
                serve_process.terminate()
                try:
                    serve_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    serve_process.kill()
                print("预览服务器已停止")

                if deploy_choice:
                    print_step(6, "部署到远程")
                    deploy_success, _ = run_hexo_command("hexo deploy")
                    if deploy_success:
                        print("\n" + "=" * 60)
                        print("部署完成!")
                        print("=" * 60)
                    else:
                        print("警告: 部署时出现错误")
                else:
                    print("\n已跳过部署。如需稍后部署,请运行:")
                    print(f"  cd {config.hexo_root}")
                    print("  hexo deploy")

    except (NotionAPIError, OSSUploadError, HexoCommandError, ConfigurationError) as e:
        print(f"\n错误: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
