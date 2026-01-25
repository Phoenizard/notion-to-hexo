"""
Command-line interface and main workflow for Notion to Hexo.

Provides the main entry point and workflow orchestration.
"""

import sys
import time
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

from .config import config, load_config
from .hexo import run_hexo_command, sanitize_filename, find_hexo_executable
from .notion import fetch_notion_page, extract_notion_page_id
from .oss import process_images_in_markdown


def print_step(step_num, message):
    """Print step information with formatting."""
    print(f"\n{'='*60}")
    print(f"步骤 {step_num}: {message}")
    print(f"{'='*60}")


def generate_summary_with_llm(content, front_title):
    """
    Generate article summary using Aliyun 百炼 (DashScope) API.

    Args:
        content: Full article content (markdown)
        front_title: Article display title

    Returns:
        Generated summary string, or None if generation fails
    """
    try:
        from dashscope import Generation
    except ImportError:
        print("警告: dashscope 未安装，无法生成摘要")
        print("请运行: pip install dashscope")
        return None

    api_key = config.dashscope_api_key
    if not api_key:
        print("警告: DASHSCOPE_API_KEY 未配置")
        print("请在 .env 文件中设置 DASHSCOPE_API_KEY")
        return None

    # Build prompts
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
            print(f"API 调用失败: {response.code} - {response.message}")
            return None
    except Exception as e:
        print(f"生成摘要时出错: {e}")
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
    # 1. Use hexo new to create the article
    print_step(1, f"创建Hexo文章: {title}")

    safe_title = sanitize_filename(title)
    # Pass title as separate argument to avoid shell injection
    success, output = run_hexo_command(['hexo', 'new', safe_title])

    if not success:
        raise Exception(f"创建Hexo文章失败: {output}")

    # 2. Find the created file
    post_file = config.hexo_root / 'source' / '_posts' / f'{safe_title}.md'

    if not post_file.exists():
        raise Exception(f"找不到创建的文章文件: {post_file}")

    # 3. Prepare front matter
    # Use front_title for display if provided, otherwise use title
    front_matter = {
        'title': front_title if front_title else title,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'tags': tags,
        'categories': category,
        'mathjax': mathjax,
    }

    if description:
        front_matter['description'] = description

    # 4. Process images
    print_step(2, "处理图片并上传到OSS")

    # Create temporary directory
    temp_dir = config.hexo_root / 'temp_images'
    temp_dir.mkdir(exist_ok=True)

    processed_content = process_images_in_markdown(content, temp_dir)

    # 5. Write file
    print_step(3, "写入Markdown文件")

    with open(post_file, 'w', encoding='utf-8') as f:
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

        # Write content
        f.write(processed_content)

    print(f"文章已创建: {post_file}")

    # Clean up temporary directory
    shutil.rmtree(temp_dir, ignore_errors=True)

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
    # Create test folder
    test_dir = Path(__file__).parent.parent / 'test'
    test_dir.mkdir(exist_ok=True)

    # Prepare front matter
    # Use front_title for display if provided, otherwise use title
    front_matter = {
        'title': front_title if front_title else title,
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
    """Main entry point."""
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

    # 0. Check and set Hexo path (skip in test mode)
    if not test_mode and not config.hexo_root.exists():
        print(f"\n警告: 默认Blog路径不存在: {config.hexo_root}")
        custom_path = input("请输入你的Hexo博客路径 (或按Enter跳过): ").strip()
        if custom_path:
            config.hexo_root = Path(custom_path)
            if not config.hexo_root.exists():
                print(f"错误: 路径不存在: {config.hexo_root}")
                sys.exit(1)

    if not test_mode:
        print(f"Blog路径: {config.hexo_root}\n")
    else:
        test_dir = Path(__file__).parent.parent / 'test'
        print(f"测试输出目录: {test_dir}\n")

    # 1. Get Notion page URL
    if len(sys.argv) < 2:
        # Try to read from page_url.txt
        page_url_file = Path(__file__).parent.parent / 'page_url.txt'
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

    # 2. Extract page ID
    page_id = extract_notion_page_id(notion_url)
    if not page_id:
        print("错误: 无法从URL中提取Notion页面ID")
        sys.exit(1)

    print(f"Notion页面ID: {page_id}")

    # 3. Check Notion Token
    if not config.notion_token:
        config.notion_token = input("\n请输入Notion Integration Token: ").strip()

    # 4. Configure Aliyun OSS (skip in test mode)
    if not test_mode:
        # Check if OSS config is already loaded
        if not config.oss_config['access_key_id']:
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
                # Try to infer OSS config from sample article
                config.oss_config['cdn_domain'] = 'phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com'
                print(f"使用默认CDN域名: {config.oss_config['cdn_domain']}")
                print("请手动配置OSS认证信息...")
                config.oss_config['access_key_id'] = input("Access Key ID: ").strip()
                config.oss_config['access_key_secret'] = input("Access Key Secret: ").strip()
                config.oss_config['bucket_name'] = input("Bucket名称: ").strip()
                config.oss_config['endpoint'] = input("Endpoint: ").strip()
        else:
            print("\n✓ 使用已配置的阿里云OSS设置")
            print(f"  CDN域名: {config.oss_config['cdn_domain']}")
            print(f"  Bucket: {config.oss_config['bucket_name']}")
            print(f"  Endpoint: {config.oss_config['endpoint']}")
    else:
        print("\n✓ 测试模式: 跳过OSS配置")

    try:
        # 5. Fetch Notion content
        print_step(0, "从Notion获取页面内容")
        try:
            print("获取Notion页面内容...")
            notion_title, content, notion_tags, notion_category, notion_description, notion_mathjax = fetch_notion_page(page_id)
        except Exception as e:
            raise Exception(f"获取Notion页面失败: {str(e)}")

        # Use config values, fall back to Notion page values if config is empty
        title = config.hexo_config['default_title'] or notion_title
        tags = config.hexo_config['default_tags'] if config.hexo_config['default_tags'] else notion_tags
        category = config.hexo_config['default_category'] or notion_category
        description = config.hexo_config['default_description'] or notion_description
        mathjax = config.hexo_config['default_mathjax'] or notion_mathjax

        # Prompt user for missing values
        if not title:
            title = input("请输入文章标题: ").strip() or "无标题文章"
        if not category:
            category = input("请输入文章分类: ").strip() or "学习笔记"
        if not tags:
            tags_input = input("请输入文章标签(逗号分隔): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
        if not mathjax:
            mathjax_input = input("是否启用MathJax? (y/n): ").strip().lower()
            mathjax = (mathjax_input == 'y')

        print(f"标题: {title}")
        print(f"标签: {tags}")
        print(f"分类: {category}")
        print(f"MathJax: {mathjax}")

        # Ask user for front_title (display title in front matter)
        front_title_input = input("请输入前端显示标题 (留空则使用文章标题): ").strip()
        front_title = front_title_input if front_title_input else title
        if front_title != title:
            print(f"前端标题: {front_title}")

        # Ask about summary generation
        generate_summary = input("\n是否需要生成摘要? (y/n): ").strip().lower()
        if generate_summary == 'y':
            # Try to generate summary with LLM
            generated_description = generate_summary_with_llm(content, front_title)
            if generated_description:
                description = generated_description
                print(f"生成的摘要: {description}")
            else:
                # LLM generation failed, fall back to manual input
                description_input = input("请手动输入文章摘要 (留空则使用前端标题): ").strip()
                description = description_input if description_input else front_title
        else:
            # User chose manual input
            description_input = input("请输入文章摘要 (留空则使用前端标题): ").strip()
            description = description_input if description_input else front_title

        if description:
            print(f"摘要: {description}")

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
            existing_post = config.hexo_root / 'source' / '_posts' / f'{safe_title}.md'
            existing_asset_folder = config.hexo_root / 'source' / '_posts' / safe_title
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
                    shutil.rmtree(existing_asset_folder)
                    print(f"已删除旧资源文件夹: {existing_asset_folder}")

        if test_mode:
            # Test mode: export to test folder without Hexo commands
            print_step(1, "导出Markdown到测试目录")
            test_file = test_mode_export(title, content, tags, category, description, mathjax, front_title)

            # Done
            print("\n" + "="*60)
            print("测试导出完成!")
            print("="*60)
            print(f"测试文件: {test_file}")
            print(f"\n注意: 测试模式下图片URL保持原始Notion链接,未上传到OSS")
        else:
            # 6. Create Hexo post
            post_file = create_hexo_post(title, content, tags, category, description, mathjax, front_title)

            # 7. Generate static files
            print_step(4, "生成Hexo静态文件")
            success, _ = run_hexo_command("hexo generate")

            if not success:
                print("警告: 生成静态文件时出现错误")

            # 8. Start local preview server
            print_step(5, "启动本地预览服务器")
            print("正在启动 hexo serve...")

            # Build the serve command using found hexo path
            hexo_path = find_hexo_executable()
            if hexo_path:
                serve_cmd = [hexo_path, 'serve']
            else:
                # Fall back to npx hexo
                npx_path = shutil.which('npx')
                if npx_path:
                    serve_cmd = [npx_path, 'hexo', 'serve']
                else:
                    serve_cmd = ['hexo', 'serve']  # Last resort, may fail

            serve_process = subprocess.Popen(
                serve_cmd,
                cwd=str(config.hexo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for server to start
            time.sleep(3)

            # Check if server started successfully
            if serve_process.poll() is not None:
                # Server failed to start, capture and display error
                _, stderr = serve_process.communicate()
                error_msg = stderr.decode() if stderr else "未知错误"
                print(f"警告: hexo serve 启动失败: {error_msg}")
            else:
                print("\n" + "="*60)
                print("本地预览服务器已启动!")
                print("="*60)
                print(f"文章文件: {post_file}")
                print(f"\n预览地址: http://localhost:4000")
                print("请在浏览器中检查文章内容")
                print("="*60)

                # Ask whether to deploy
                deploy_choice = input("\n确认部署到远程? (y/n): ").strip().lower()

                # Stop preview server
                print("\n正在停止预览服务器...")
                serve_process.terminate()
                try:
                    serve_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    serve_process.kill()
                print("预览服务器已停止")

                if deploy_choice == 'y':
                    print_step(6, "部署到远程")
                    deploy_success, _ = run_hexo_command("hexo deploy")
                    if deploy_success:
                        print("\n" + "="*60)
                        print("部署完成!")
                        print("="*60)
                    else:
                        print("警告: 部署时出现错误")
                else:
                    print("\n已跳过部署。如需稍后部署,请运行:")
                    print(f"  cd {config.hexo_root}")
                    print("  hexo deploy")

    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
