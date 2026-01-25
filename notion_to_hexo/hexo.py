"""
Hexo CLI utilities for Notion to Hexo.

Provides functions for interacting with the Hexo CLI and
file/filename utilities for blog post creation.
"""

import re
import shlex
import shutil
import subprocess
from pathlib import Path

from .config import config


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
        Path.home() / '.nvm' / 'versions' / 'node',  # NVM installs
        Path('/usr/local/bin/hexo'),
        Path('/opt/homebrew/bin/hexo'),
    ]

    for p in npm_paths:
        if p.exists() and p.is_file():
            return str(p)

    # Check for npx as fallback (npx hexo always works if npm is installed)
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

    # Convert string command to list if needed (for simple commands)
    if isinstance(command_args, str):
        # Only allow simple commands without user input to use string form
        command_list = shlex.split(command_args)
    else:
        command_list = list(command_args)

    # Find hexo executable and replace 'hexo' with full path
    if command_list and command_list[0] == 'hexo':
        hexo_path = find_hexo_executable()
        if hexo_path:
            command_list[0] = hexo_path
        else:
            # Fall back to npx hexo
            npx_path = shutil.which('npx')
            if npx_path:
                command_list = [npx_path, 'hexo'] + command_list[1:]
            # else: keep 'hexo' and let FileNotFoundError be raised

    print(f"执行命令: {' '.join(command_list)}")

    try:
        result = subprocess.run(
            command_list,
            cwd=str(cwd),  # Use cwd parameter instead of cd &&
            capture_output=True,
            text=True,
            # shell=False is the default, explicitly noted for clarity
        )

        if result.returncode != 0:
            print(f"错误: {result.stderr}")
            return False, result.stderr

        print(f"成功: {result.stdout}")
        return True, result.stdout

    except FileNotFoundError:
        error_msg = f"命令未找到: {command_list[0]}。请确保hexo-cli已安装 (npm install -g hexo-cli)。"
        print(f"错误: {error_msg}")
        return False, error_msg
    except Exception as e:
        print(f"错误: {str(e)}")
        return False, str(e)


def sanitize_filename(filename):
    """
    Clean filename by removing illegal characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace illegal characters
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    filename = re.sub(r'\s+', '-', filename)
    # Remove leading/trailing hyphens to avoid command-line argument parsing
    filename = filename.strip('-')
    # Merge multiple consecutive hyphens
    filename = re.sub(r'-+', '-', filename)
    return filename
