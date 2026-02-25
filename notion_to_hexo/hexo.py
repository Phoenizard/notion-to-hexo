"""
Hexo CLI utilities for Notion to Hexo.

Provides functions for interacting with the Hexo CLI and
file/filename utilities for blog post creation.
"""

import re
import glob
import shlex
import shutil
import logging
import subprocess
from pathlib import Path

from .config import config

logger = logging.getLogger(__name__)


def find_hexo_executable():
    """
    Find the hexo executable path.

    Returns:
        str: Path to hexo executable, or None if not found
    """
    # First, try shutil.which (uses PATH)
    hexo_path = shutil.which('hexo')
    if hexo_path:
        return hexo_path

    # Try common npm global paths
    npm_paths = [
        Path.home() / '.npm-global' / 'bin' / 'hexo',
        Path('/usr/local/bin/hexo'),
        Path('/opt/homebrew/bin/hexo'),
    ]

    for p in npm_paths:
        if p.exists() and p.is_file():
            return str(p)

    # Try NVM installations - glob for hexo under all node versions
    nvm_pattern = str(Path.home() / '.nvm' / 'versions' / 'node' / '*/bin/hexo')
    nvm_hexo = sorted(glob.glob(nvm_pattern))
    if nvm_hexo:
        return nvm_hexo[-1]  # Use latest node version

    # Check for npx as fallback
    npx_path = shutil.which('npx')
    if npx_path:
        return None  # Signal to use npx instead

    return None


def run_hexo_command(command_args, cwd=None):
    """
    Run Hexo command (secure version, no shell execution).

    Args:
        command_args: Command argument list, e.g., ['hexo', 'new', 'Title']
                      or string form for simple commands like 'hexo generate'
        cwd: Working directory, defaults to config.hexo_root

    Returns:
        (success: bool, output: str)
    """
    if cwd is None:
        cwd = config.hexo_root

    # Convert string command to list if needed
    if isinstance(command_args, str):
        command_list = shlex.split(command_args)
    else:
        command_list = list(command_args)

    # Find hexo executable and replace 'hexo' with full path
    if command_list and command_list[0] == 'hexo':
        hexo_path = find_hexo_executable()
        if hexo_path:
            command_list[0] = hexo_path
        else:
            npx_path = shutil.which('npx')
            if npx_path:
                command_list = [npx_path, 'hexo'] + command_list[1:]

    logger.info("执行命令: %s", ' '.join(command_list))

    try:
        result = subprocess.run(
            command_list,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            logger.error("命令失败: %s", result.stderr)
            return False, result.stderr

        logger.info("命令成功: %s", result.stdout[:200] if result.stdout else '')
        return True, result.stdout

    except FileNotFoundError:
        error_msg = (
            f"命令未找到: {command_list[0]}。"
            "请确保hexo-cli已安装 (npm install -g hexo-cli)。"
        )
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        logger.error("执行命令出错: %s", e)
        return False, str(e)


def sanitize_filename(filename):
    """
    Clean filename by removing illegal characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    filename = re.sub(r'\s+', '-', filename)
    filename = filename.strip('-')
    filename = re.sub(r'-+', '-', filename)
    return filename
