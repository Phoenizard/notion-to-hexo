# Notion to Hexo

Automatically convert Notion pages into Hexo blog posts with image upload to Aliyun OSS. Supports both CLI and Web UI.

> **中文文档**: [README_zh.md](./README_zh.md)

## Features

- Fetch Notion pages via API (with pagination for long articles)
- Auto-upload images to Aliyun OSS and replace URLs with CDN links
- Convert to Hexo-compatible Markdown with proper front matter (YAML-safe)
- Optional LLM-generated article summaries (DashScope)
- Streamlit Web UI for visual editing and publishing
- Docker deployment — one command to start
- Full CLI with non-interactive mode (`--yes`), test mode, dry-run, and more

## Quick Start

### Option A: Docker (Recommended)

```bash
git clone https://github.com/Phoenizard/notion-to-hexo.git
cd notion-to-hexo
cp config.example.json config.json   # Edit with your credentials
docker compose up --build -d
open http://localhost:8501
```

On macOS, double-click `start.command` to launch automatically.

### Option B: Local Install

```bash
git clone https://github.com/Phoenizard/notion-to-hexo.git
cd notion-to-hexo
pip install -e ".[ui,llm]"
cp config.example.json config.json   # Edit with your credentials

# Publish an article
notion-to-hexo "https://www.notion.so/My-Article-abc123"

# Or launch Web UI
notion-to-hexo --ui
```

**Requirements**: Python 3.8+, Node.js + hexo-cli (`npm install -g hexo-cli`)

## Configuration

### config.json

```json
{
  "notion": { "token": "secret_xxx" },
  "oss": {
    "access_key_id": "LTAI...",
    "access_key_secret": "xxx",
    "bucket_name": "my-bucket",
    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
    "cdn_domain": "my-bucket.oss-cn-hangzhou.aliyuncs.com"
  },
  "hexo": {
    "blog_path": "/path/to/hexo/blog",
    "default_category": "",
    "default_tags": []
  },
  "llm": { "dashscope_api_key": "sk-xxx" }
}
```

Environment variables override config.json. See [README_zh.md](./README_zh.md#详细配置说明) for full details.

### Notion Page Properties (Optional)

| Property | Type | Purpose |
|----------|------|---------|
| Tags | Multi-select | Blog tags |
| Category | Select | Blog category |
| Description | Text | Meta description |
| MathJax | Checkbox | Enable math rendering |

## CLI Usage

```
notion-to-hexo [options] <notion_url>

Options:
  --test              Export to test/ directory without Hexo commands
  --yes, -y           Non-interactive mode
  --ui                Launch Streamlit Web UI
  --title TITLE       Custom title
  --category CAT      Set category
  --tags T [T ...]    Set tags
  --llm-summary       Generate LLM summary
  --dry-run           Preview only, no file writes
  --deploy            Auto-deploy after publishing
  --verbose, -v       Verbose logging
```

## Supported Notion Blocks

Fully supported: paragraphs, headings, lists (ordered/unordered/todo), code blocks, math equations, images, quotes, dividers, callouts.

Partially supported: toggles, tables. Not supported: database views, embeds.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `object_not_found` | Page not shared with Integration | Add connection in Notion page settings |
| Image upload 403 | Invalid OSS credentials | Check access key and permissions |
| `hexo: command not found` | Hexo CLI missing | Use Docker, or `npm install -g hexo-cli` |

## Changelog

- **v3.0**: Docker support, Streamlit Web UI, CLI overhaul, pagination fix, 68 tests
- **v2.1**: LLM summary generation
- **v1.0**: Initial release

---

**Author**: Phoenizard | **License**: MIT
