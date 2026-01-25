# -*- coding: utf-8 -*-
"""
Summary Generator - 使用阿里云百炼 API 生成文章摘要

Usage:
    python summary_generator.py <file_path>

Example:
    python summary_generator.py ../test/sample_article.md
"""

import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

try:
    from dashscope import Generation
except ImportError:
    Generation = None


def load_api_key():
    """Load DASHSCOPE_API_KEY from environment or .env file."""
    # Try to load from .env file
    if load_dotenv:
        # Look for .env in current dir and parent dir
        env_paths = [
            Path.cwd() / '.env',
            Path(__file__).parent.parent / '.env',
        ]
        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(env_path)
                break

    api_key = os.getenv('DASHSCOPE_API_KEY')
    return api_key


def generate_summary(content: str, title: str = None, model: str = 'qwen-turbo') -> str:
    """
    Generate a summary for the given content using Aliyun 百炼 API.

    Args:
        content: The article content to summarize
        title: Optional title for context
        model: Model to use ('qwen-turbo' for fast, 'qwen-plus' for quality)

    Returns:
        Generated summary text

    Raises:
        RuntimeError: If API key is missing or API call fails
    """
    if Generation is None:
        raise RuntimeError(
            "dashscope package not installed. "
            "Run: pip install dashscope"
        )

    api_key = load_api_key()
    if not api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY not found. "
            "Set it in .env file or environment variable."
        )

    # Build the prompt
    title_context = f"标题：{title}\n\n" if title else ""
    user_prompt = f"""请为以下文章生成一段简洁的摘要（150-250字），用于博客文章的description字段。
摘要应该：
1. 概括文章的主要内容和核心观点
2. 吸引读者继续阅读
3. 使用与文章相同的语言（中文文章用中文，英文文章用英文）
4. 避免使用数学符号或特殊字符

{title_context}内容：
{content[:4000]}"""  # Limit content length for API

    system_prompt = "你是一个专业的内容编辑，擅长为博客文章撰写吸引人的摘要。请直接输出摘要内容，不需要任何前缀或解释。"

    try:
        response = Generation.call(
            api_key=api_key,
            model=model,
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
            raise RuntimeError(
                f"API call failed: {response.code} - {response.message}"
            )
    except Exception as e:
        if 'response' in dir() and hasattr(response, 'code'):
            raise RuntimeError(f"API error: {response.code} - {response.message}")
        raise RuntimeError(f"Failed to generate summary: {e}")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python summary_generator.py <file_path>")
        print("Example: python summary_generator.py ../test/sample_article.md")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    # Read the file content
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    # Extract title from filename
    title = file_path.stem.replace('-', ' ').replace('_', ' ')

    print(f"Generating summary for: {file_path.name}")
    print("-" * 40)

    try:
        summary = generate_summary(content, title)
        print("Summary:")
        print(summary)
        print("-" * 40)
        print(f"Length: {len(summary)} characters")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
