# CLAUDE.MD - AI Assistant Guide for Notion to Hexo Project

## Project Overview

**notion-to-hexo** is a Python-based automation tool that converts Notion pages into Hexo blog posts with automatic image upload to Aliyun OSS.

**Purpose**: Streamline the workflow of publishing content from Notion to a Hexo static blog, handling markdown conversion, image hosting, and front matter generation automatically.

**Tech Stack**: Python 3, Notion API, Aliyun OSS SDK, Aliyun DashScope (LLM), Hexo CLI

**Language**: Mixed Chinese/English (documentation in Chinese, code comments in English)

---

## Architecture

### Project Structure (v2.0 - Modular)

```
notion-to-hexo/
├── notion_to_hexo/               # Main package directory
│   ├── __init__.py               # Package initialization, exports public API
│   ├── config.py                 # Configuration management
│   ├── network.py                # Network utilities (retry, timeouts)
│   ├── hexo.py                   # Hexo-related utilities
│   ├── oss.py                    # Aliyun OSS image handling
│   ├── notion.py                 # Notion API integration
│   ├── converter.py              # Markdown conversion logic
│   └── cli.py                    # Command-line interface and main workflow
│
├── notion_to_hexo.py             # Backwards-compatible entry point (thin wrapper)
├── publish_notion.py             # Simplified launcher with config support
├── config.json                   # User configuration (gitignored, sensitive)
├── config.example.json           # Configuration template
├── README.md                     # Main documentation (Chinese)
├── QUICKSTART.md                 # Quick start guide
├── README_WORKFLOW.md            # Detailed workflow documentation
├── NOTION_WORKFLOW_SUMMARY.md    # Workflow summary
└── CLAUDE.MD                     # This file - AI assistant guide
```

### Module Responsibilities

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `config.py` | Configuration management | `load_config()`, `Config` class, constants |
| `network.py` | HTTP with retry/timeout | `request_with_retry()` |
| `hexo.py` | Hexo CLI interaction | `run_hexo_command()`, `sanitize_filename()`, `find_hexo_executable()` |
| `oss.py` | Image upload to Aliyun OSS | `upload_to_oss()`, `download_notion_image()`, `process_images_in_markdown()` |
| `notion.py` | Notion API client | `fetch_notion_page()`, `extract_notion_page_id()` |
| `converter.py` | Notion blocks to Markdown | `blocks_to_markdown()`, `rich_text_to_markdown()` |
| `cli.py` | Main workflow & CLI | `main()`, `create_hexo_post()`, `test_mode_export()`, `generate_summary_with_llm()` |

### Dependency Flow (No Circular Dependencies)

```
config.py       <- base, no dependencies
    ^
network.py      <- depends on config
    ^
converter.py    <- depends on network
    ^
notion.py       <- depends on network, config, converter
    ^
oss.py          <- depends on network, config
    ^
hexo.py         <- depends on config only
    ^
cli.py          <- depends on all above
```

### Key Components

#### 1. **notion_to_hexo/** (Package)

##### config.py
- `Config` class: Holds all configuration as instance attributes
- `config`: Global config instance
- `load_config()`: Loads settings from config.json and environment variables
- `dashscope_api_key`: DashScope API key for LLM summary generation
- Network constants: `TIMEOUT_API`, `TIMEOUT_IMAGE`, `MAX_RETRIES`, `RETRY_BACKOFF`

##### network.py
- `request_with_retry()`: HTTP requests with exponential backoff retry

##### hexo.py
- `find_hexo_executable()`: Locates hexo binary
- `run_hexo_command()`: Safely executes Hexo CLI commands
- `sanitize_filename()`: Cleans filenames for filesystem compatibility

##### notion.py
- `extract_notion_page_id()`: Extracts UUID from Notion URLs
- `fetch_notion_page()`: Fetches page content and properties from Notion API

##### converter.py
- `rich_text_to_markdown()`: Converts Notion rich text to Markdown
- `blocks_to_markdown()`: Converts Notion blocks to Markdown

##### oss.py
- `upload_to_oss()`: Uploads files to Aliyun OSS
- `download_notion_image()`: Downloads images from Notion S3
- `process_images_in_markdown()`: Replaces image URLs in markdown

##### cli.py
- `main()`: Main entry point and workflow orchestration
- `create_hexo_post()`: Creates Hexo article with front matter
- `test_mode_export()`: Test mode export without Hexo commands
- `print_step()`: Step formatting utility

#### 2. **notion_to_hexo.py** (Backwards-Compatible Wrapper)
- Thin wrapper that imports everything from the package
- Maintains backwards compatibility for existing code
- Exposes config attributes as module-level globals

#### 3. **publish_notion.py**
- Simplified launcher with config file support
- Imports from the package directly

---

## Configuration System

### config.json Structure

```json
{
  "notion": {
    "token": "secret_xxx"  // Notion Integration token
  },
  "oss": {
    "access_key_id": "LTAI...",
    "access_key_secret": "xxx",
    "bucket_name": "phoenizard-picgo",
    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
    "cdn_domain": "phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com"
  },
  "hexo": {
    "blog_path": "/Users/shay/Documents/Blog",
    "default_category": "学习笔记",
    "default_tags": [],
    "default_title": "",
    "default_description": "",
    "default_mathjax": false
  },
  "llm": {
    "dashscope_api_key": "sk-xxx"  // Or use DASHSCOPE_API_KEY env var
  }
}
```

### Configuration Loading Flow

1. `config.py` loads .env file (if python-dotenv available)
2. `config.py` loads config.json on module import
3. Environment variables override config.json values
4. Missing values fall back to interactive prompts in CLI

### Accessing Configuration

```python
# New way (recommended)
from notion_to_hexo import config
print(config.hexo_root)
print(config.notion_token)
print(config.oss_config['bucket_name'])

# Old way (backwards compatible)
import notion_to_hexo
print(notion_to_hexo.HEXO_ROOT)
print(notion_to_hexo.NOTION_TOKEN)
```

---

## Workflow Execution

### Publishing Workflow (7 steps)

```
User Input (Notion URL)
    ↓
1. Extract page ID from URL
    ↓
2. Fetch content via Notion API
    ↓
3. Convert blocks to markdown
    ↓
4. Download images from Notion S3
    ↓
5. Upload images to Aliyun OSS
    ↓
6. Create Hexo post with front matter
    ↓
7. Run `hexo generate`
    ↓
Manual review → `hexo deploy`
```

### Code Flow

```python
cli.main()
  ├─ Load config (from config.py on import)
  ├─ Extract page_id (notion.extract_notion_page_id)
  ├─ Validate NOTION_TOKEN
  ├─ Configure OSS credentials
  ├─ notion.fetch_notion_page()
  │   ├─ network.request_with_retry() → page properties
  │   ├─ network.request_with_retry() → content blocks
  │   └─ converter.blocks_to_markdown() → content_markdown
  ├─ cli.create_hexo_post()
  │   ├─ hexo.run_hexo_command(['hexo', 'new', title])
  │   ├─ oss.process_images_in_markdown()
  │   │   ├─ oss.download_notion_image() → temp file
  │   │   ├─ oss.upload_to_oss() → CDN URL
  │   │   └─ replace URL in markdown
  │   └─ Write front matter + content
  └─ hexo.run_hexo_command('hexo generate')
```

---

## Key Technical Details

### Notion API

- **API Version**: 2022-06-28
- **Authentication**: Bearer token in Authorization header
- **Supported Properties**:
  - `Tags` (multi_select) → blog tags
  - `Category` (select) → blog category
  - `Description` (rich_text) → meta description
  - `MathJax` (checkbox) → enable math formulas

### Notion Block Types Supported

**Fully Supported**:
- paragraph, heading_1/2/3
- bulleted_list_item, numbered_list_item
- code (with language syntax highlighting)
- equation (LaTeX math blocks)
- image (file/external URLs)
- quote, divider

**Partially Supported**:
- Nested blocks (via recursive `has_children` handling)
- Toggle, Callout → rendered as basic elements

**Not Supported**:
- Database views, Embeds, Complex tables

### Image Handling

**Notion Image URLs**: Signed S3 URLs with expiration
- Format: `https://prod-files-secure.s3.../workspace-uuid/image-uuid/filename.png?params`
- **Important**: Don't add Authorization header (AWS rejects with 400)
- UUID extracted from path for stable filenames

**OSS Upload Strategy** (in `oss.py`):
- Check if object exists before upload
- Prefix with `img/` for organization
- Return CDN URL for markdown replacement

**Filename Generation**:
```python
# Stable naming based on Notion image UUID
image_uuid = path_parts[-2]  # e.g., c2dd9413-e1b4-4ee5-97b1-64b4292f82c3
filename = f"notion_{image_uuid[:8]}{ext}"
```

### Hexo Integration

**File Creation**:
- Uses `hexo new "{title}"` command
- Target: `{hexo_root}/source/_posts/{sanitized_title}.md`
- Filename sanitization removes special chars: `<>:"/\|?*`

**Front Matter Format**:
```yaml
---
title: Article Title
date: 2025-01-24 12:34:56
tags: [tag1, tag2]
categories: 分类名
description: Optional description
mathjax: true  # if math formulas detected
---
```

---

## Development Guidelines

### When Modifying Code

1. **Adding Block Type Support**:
   - Edit `converter.py` → `blocks_to_markdown()`
   - Add new `elif block_type == 'new_type':` case
   - Handle nested blocks with recursion if needed

2. **Changing Image Processing**:
   - Modify `oss.py` → `download_notion_image()` for download logic
   - Modify `oss.py` → `upload_to_oss()` for upload logic
   - Update `oss.py` → `process_images_in_markdown()` for URL replacement

3. **Adding Configuration Options**:
   - Update `config.example.json` with new field
   - Add to `config.py` → `Config` class and `load_config()` function
   - Document in README.md

4. **Error Handling**:
   - Notion API errors: Check response status codes in `notion.py`
   - OSS upload errors: Validate credentials in `oss.py`
   - Hexo command errors: Check hexo_root path in `hexo.py`

### Code Style Conventions

- **Print messages**: Chinese for user-facing, English for technical
- **Docstrings**: English with Chinese in module headers
- **Indentation**: 4 spaces
- **String quotes**: Single quotes for code, double for user input

### Security Considerations

- **config.json is gitignored** - contains secrets
- Never commit: `access_key_secret`, `NOTION_TOKEN`
- Use environment variables in CI/CD
- OSS permissions: Bucket should allow public read for CDN

---

## Common Tasks

### Adding a New Notion Property

```python
# In notion.py → fetch_notion_page()
if 'CustomField' in properties:
    custom_property = properties['CustomField']
    if custom_property.get('type') == 'rich_text':
        custom_value = ''.join([t['plain_text']
                               for t in custom_property.get('rich_text', [])])
```

### Supporting a New Block Type

```python
# In converter.py → blocks_to_markdown()
elif block_type == 'callout':
    icon = block_content.get('icon', {}).get('emoji', '💡')
    text = rich_text_to_markdown(block_content.get('rich_text', []))
    markdown.append(f"> {icon} {text}")
    markdown.append('')
```

### Changing Image Upload Path

```python
# In oss.py → upload_to_oss()
object_name = f"blog/images/{object_name}"  # Instead of "img/"
```

### Using the Package Programmatically

```python
from notion_to_hexo import (
    fetch_notion_page,
    extract_notion_page_id,
    upload_to_oss,
    config
)

# Configure
config.notion_token = "your_token"
config.oss_config['access_key_id'] = "your_key"

# Use
page_id = extract_notion_page_id("https://notion.so/...")
title, content, tags, category, desc, mathjax = fetch_notion_page(page_id)
```

---

## Testing Workflow

### Manual Testing Checklist

1. **Test with sample Notion page**:
   ```bash
   python publish_notion.py --test "https://www.notion.so/Test-Page-xxx"
   ```

2. **Verify outputs**:
   - [ ] Markdown file created in `test/` (test mode) or `_posts/`
   - [ ] Images uploaded to OSS (non-test mode)
   - [ ] CDN URLs in markdown
   - [ ] Front matter correct

3. **Test edge cases**:
   - [ ] Page with no images
   - [ ] Page with math formulas
   - [ ] Special characters in title
   - [ ] Nested lists and blocks

### Debugging Tips

**Notion API Issues**:
```python
# Add verbose logging in notion.py → fetch_notion_page()
import json
print(f"DEBUG: Page data: {json.dumps(page_data, indent=2)}")
print(f"DEBUG: Blocks data: {json.dumps(blocks_data, indent=2)}")
```

**OSS Upload Failures**:
- Check endpoint region matches bucket
- Verify CDN domain is configured
- Test with `oss2.Bucket.put_object()` directly

**Hexo Command Failures**:
- Ensure `hexo-cli` installed globally
- Check `config.hexo_root` points to valid Hexo project
- Run `hexo version` manually to verify

---

## Deployment

### User Installation Steps

1. Clone repository
2. Copy `config.example.json` → `config.json`
3. Fill in credentials (Notion token, OSS keys, blog path)
4. Install dependencies: `pip install -r requirements.txt`
5. Run: `python publish_notion.py <notion_url>`

### System Requirements

- Python 3.6+
- Hexo CLI installed (`npm install -g hexo-cli`)
- Valid Hexo blog project at configured path
- Notion Integration with page access
- Aliyun OSS bucket with upload permissions

---

## Important Notes for AI Assistants

### When Helping Users

1. **Always check config.json exists** before debugging
2. **Verify hexo_root path** - common source of errors
3. **Check Notion Integration authorization** - users forget this step
4. **OSS credentials** - must have upload permission, not just read

### Code Modification Principles

1. **Preserve Chinese documentation** - target audience is Chinese users
2. **Don't break config compatibility** - users have existing config.json
3. **Maintain workflow steps** - users expect specific output messages
4. **Keep interactive prompts** - fallback when config missing
5. **Respect module boundaries** - keep dependencies flowing downward

### Common User Issues

**"object_not_found" error**:
- Cause: Notion page not shared with Integration
- Solution: Add connection in Notion page settings

**"hexo: command not found"**:
- Cause: Hexo CLI not installed or not in PATH
- Solution: `npm install -g hexo-cli`

**Image upload 403**:
- Cause: Invalid OSS credentials or permissions
- Solution: Verify Access Key has upload permission

**Wrong blog path**:
- Cause: config.json has incorrect `blog_path`
- Solution: Update to correct Hexo project directory

---

## Git Workflow

**Commit Conventions**:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `refactor:` Code restructuring

**Never Commit**:
- `config.json` (contains secrets)
- `temp_images/` directory
- `test/` directory
- User-specific paths in code

---

## Version History

- **v2.1** (2025-01-25): LLM Summary Feature
  - Added DashScope API integration for article summary generation
  - New `generate_summary_with_llm()` function in cli.py
  - Added `dashscope_api_key` to Config class

- **v2.0** (2025-01-25): Modular refactoring
  - Split monolithic script into package structure
  - Improved code organization and maintainability
  - Added Config class for better configuration management
  - Maintained backwards compatibility

- **v1.0** (2025-01-24): Initial release
  - Notion API integration
  - Aliyun OSS image hosting
  - Hexo post generation
  - Standalone workflow directory design

---

## Quick Reference

### Entry Points
- **With config**: `python publish_notion.py <url>`
- **Interactive**: `python notion_to_hexo.py <url>`
- **Test mode**: `python publish_notion.py --test <url>`

### Importing from Package
```python
from notion_to_hexo import fetch_notion_page, upload_to_oss, config
```

### Key Functions
- `fetch_notion_page(page_id)` - Get content from Notion
- `blocks_to_markdown(blocks, headers, level)` - Convert to markdown
- `upload_to_oss(file_path, object_name)` - Upload to OSS
- `create_hexo_post(...)` - Generate Hexo article

### Configuration Files
- `config.json` - User settings (gitignored)
- `config.example.json` - Template with documentation

### Documentation
- `README.md` - Main user guide
- `QUICKSTART.md` - Quick start tutorial
- `README_WORKFLOW.md` - Detailed workflow
- `CLAUDE.MD` - This file (for AI assistants)

---

**Last Updated**: 2025-01-25
**Maintained By**: Phoenizard
**For**: AI assistants working with this codebase
