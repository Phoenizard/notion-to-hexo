# CLAUDE.MD - AI Assistant Guide for Notion to Hexo Project

## Project Overview

**notion-to-hexo** is a Python-based automation tool that converts Notion pages into Hexo blog posts with automatic image upload to Aliyun OSS.

**Purpose**: Streamline the workflow of publishing content from Notion to a Hexo static blog, handling markdown conversion, image hosting, and front matter generation automatically.

**Tech Stack**: Python 3, Notion API, Aliyun OSS SDK, Hexo CLI

**Language**: Mixed Chinese/English (documentation in Chinese, code comments in English)

---

## Architecture

### Project Structure

```
notion-to-hexo/
├── notion_to_hexo.py         # Core workflow engine (main script)
├── publish_notion.py          # Simplified launcher with config support
├── config.json               # User configuration (gitignored, sensitive)
├── config.example.json       # Configuration template
├── README.md                 # Main documentation (Chinese)
├── QUICKSTART.md            # Quick start guide
├── README_WORKFLOW.md       # Detailed workflow documentation
├── NOTION_WORKFLOW_SUMMARY.md # Workflow summary
└── CLAUDE.MD                # This file - AI assistant guide
```

### Key Components

#### 1. **notion_to_hexo.py** (697 lines)
The main workflow engine containing:

- **Configuration Management** (lines 31-98)
  - `load_config()`: Loads settings from config.json
  - Global configs: `HEXO_ROOT`, `NOTION_TOKEN`, `OSS_CONFIG`, `HEXO_CONFIG`

- **Notion API Integration** (lines 289-366)
  - `fetch_notion_page(page_id)`: Fetches page content and properties
  - `blocks_to_markdown(blocks, headers, level)`: Converts Notion blocks to markdown
  - `rich_text_to_markdown(rich_text_array)`: Handles text formatting

- **Image Processing** (lines 156-286)
  - `download_notion_image(image_url, save_dir)`: Downloads images from Notion S3
  - `upload_to_oss(file_path, object_name)`: Uploads to Aliyun OSS
  - `process_images_in_markdown(content, temp_dir)`: Replaces image URLs in markdown

- **Hexo Integration** (lines 490-563)
  - `create_hexo_post(title, content, tags, category, description, mathjax)`: Creates Hexo article
  - Uses `hexo new` command to create post template
  - Generates front matter with metadata

- **Utility Functions** (lines 102-153)
  - `sanitize_filename(filename)`: Cleans filenames for filesystem compatibility
  - `extract_notion_page_id(url)`: Extracts UUID from Notion URLs
  - `run_hexo_command(command, cwd)`: Executes Hexo CLI commands

#### 2. **publish_notion.py** (67 lines)
Simplified launcher that:
- Loads config.json before execution
- Sets global variables in notion_to_hexo module
- Provides better UX for configured environments

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
  }
}
```

### Configuration Loading Flow

1. **publish_notion.py** loads config.json (lines 19-31)
2. **notion_to_hexo.py** also loads config on import (lines 60-98)
3. Missing values fall back to interactive prompts
4. Environment variable `NOTION_TOKEN` can override config

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

### Code Flow (notion_to_hexo.py main())

```python
main() (lines 566-693)
  ├─ Set HEXO_ROOT path
  ├─ Extract page_id from URL
  ├─ Validate NOTION_TOKEN
  ├─ Configure OSS credentials
  ├─ fetch_notion_page()
  │   ├─ GET /v1/pages/{page_id} → properties
  │   ├─ GET /v1/blocks/{page_id}/children → content
  │   └─ blocks_to_markdown() → content_markdown
  ├─ create_hexo_post()
  │   ├─ hexo new "{title}"
  │   ├─ process_images_in_markdown()
  │   │   ├─ download_notion_image() → temp file
  │   │   ├─ upload_to_oss() → CDN URL
  │   │   └─ replace URL in markdown
  │   └─ Write front matter + content
  └─ hexo generate
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
- UUID extracted from path for stable filenames (lines 210-226)

**OSS Upload Strategy**:
- Check if object exists before upload (lines 185-188)
- Prefix with `img/` for organization (line 179)
- Return CDN URL for markdown replacement

**Filename Generation** (lines 211-226):
```python
# Stable naming based on Notion image UUID
image_uuid = path_parts[-2]  # e.g., c2dd9413-e1b4-4ee5-97b1-64b4292f82c3
filename = f"notion_{image_uuid[:8]}{ext}"
```

### Hexo Integration

**File Creation**:
- Uses `hexo new "{title}"` command (line 507)
- Target: `{HEXO_ROOT}/source/_posts/{sanitized_title}.md`
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
   - Edit `blocks_to_markdown()` (lines 368-459)
   - Add new `elif block_type == 'new_type':` case
   - Handle nested blocks with recursion if needed

2. **Changing Image Processing**:
   - Modify `download_notion_image()` for download logic
   - Modify `upload_to_oss()` for upload logic
   - Update `process_images_in_markdown()` for URL replacement

3. **Adding Configuration Options**:
   - Update `config.example.json` with new field
   - Add to `load_config()` function
   - Document in README.md

4. **Error Handling**:
   - Notion API errors: Check response status codes
   - OSS upload errors: Validate credentials in config
   - Hexo command errors: Check `HEXO_ROOT` path exists

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
# In fetch_notion_page() after line 350
if 'CustomField' in properties:
    custom_property = properties['CustomField']
    if custom_property.get('type') == 'rich_text':
        custom_value = ''.join([t['plain_text']
                               for t in custom_property.get('rich_text', [])])
```

### Supporting a New Block Type

```python
# In blocks_to_markdown() after line 444
elif block_type == 'callout':
    icon = block_content.get('icon', {}).get('emoji', '💡')
    text = rich_text_to_markdown(block_content.get('rich_text', []))
    markdown.append(f"> {icon} {text}")
    markdown.append('')
```

### Changing Image Upload Path

```python
# In upload_to_oss() line 179
object_name = f"blog/images/{object_name}"  # Instead of "img/"
```

---

## Testing Workflow

### Manual Testing Checklist

1. **Test with sample Notion page**:
   ```bash
   python publish_notion.py "https://www.notion.so/Test-Page-xxx"
   ```

2. **Verify outputs**:
   - [ ] Markdown file created in `_posts/`
   - [ ] Images uploaded to OSS
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
# Add verbose logging in fetch_notion_page()
print(f"DEBUG: Page data: {json.dumps(page_data, indent=2)}")
print(f"DEBUG: Blocks data: {json.dumps(blocks_data, indent=2)}")
```

**OSS Upload Failures**:
- Check endpoint region matches bucket
- Verify CDN domain is configured
- Test with `oss2.Bucket.put_object()` directly

**Hexo Command Failures**:
- Ensure `hexo-cli` installed globally
- Check `HEXO_ROOT` points to valid Hexo project
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
2. **Verify HEXO_ROOT path** - common source of errors
3. **Check Notion Integration authorization** - users forget this step
4. **OSS credentials** - must have upload permission, not just read

### Code Modification Principles

1. **Preserve Chinese documentation** - target audience is Chinese users
2. **Don't break config compatibility** - users have existing config.json
3. **Maintain workflow steps** - users expect specific output messages
4. **Keep interactive prompts** - fallback when config missing

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

**Current Branch**: `claude/update-claude-md-BbLJ8`

**Commit Conventions**:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `refactor:` Code restructuring

**Never Commit**:
- `config.json` (contains secrets)
- `temp_images/` directory
- User-specific paths in code

---

## Version History

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

**Last Updated**: 2025-01-24
**Maintained By**: Phoenizard
**For**: AI assistants working with this codebase
