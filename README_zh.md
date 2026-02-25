# Notion to Hexo 博客发布工具

自动将 Notion 笔记转换为 Hexo 博客文章，支持图片上传至阿里云 OSS，提供命令行和 Web 可视化界面两种使用方式。

> **English version**: [README.md](./README.md)

---

## 目录

- [功能特性](#功能特性)
- [使用方式](#使用方式)
  - [方式一：Docker 一键启动（推荐）](#方式一docker-一键启动推荐)
  - [方式二：命令行使用](#方式二命令行使用)
- [前置要求](#前置要求)
- [详细配置说明](#详细配置说明)
- [Notion 页面属性配置](#notion-页面属性配置)
- [Web UI 使用指南](#web-ui-使用指南)
- [CLI 命令详解](#cli-命令详解)
- [支持的 Notion 内容类型](#支持的-notion-内容类型)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [更新日志](#更新日志)

---

## 功能特性

- **Notion 内容获取**：通过 Notion API 自动获取页面内容，支持分页（长文章不截断）
- **图片自动托管**：自动下载 Notion 图片并上传至阿里云 OSS 图床，替换为 CDN 链接
- **Markdown 转换**：完整支持段落、标题、列表、代码块、数学公式、引用等格式
- **Front Matter 生成**：自动从 Notion 属性生成 Hexo 文章元数据，YAML 安全转义
- **LLM 文章摘要**：可选使用阿里云百炼 DashScope 自动生成 150-250 字摘要
- **Web 可视化界面**：Streamlit UI，支持预览、编辑元数据、一键发布
- **Docker 部署**：一键启动，无需手动安装 Python/Node.js 环境
- **完整 CLI**：支持非交互模式 (`--yes`)、测试模式 (`--test`)、自定义参数

---

## 使用方式

### 方式一：Docker 一键启动（推荐）

无需安装任何依赖，Docker 镜像内已包含 Python、Node.js 和 Hexo 环境。

#### 前提条件

- 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### 步骤

```bash
# 1. 克隆项目
git clone https://github.com/Phoenizard/notion-to-hexo.git
cd notion-to-hexo

# 2. 准备配置文件
cp config.example.json config.json
# 编辑 config.json，填入你的凭证（见下方"详细配置说明"）

# 3. 启动
docker compose up --build -d

# 4. 打开浏览器访问
open http://localhost:8501    # macOS
# 或手动访问 http://localhost:8501
```

**macOS 用户**：也可以直接双击 `start.command` 文件，自动启动并打开浏览器。

**停止服务**：

```bash
docker compose down
```

**自定义博客目录**：编辑 `docker-compose.yml`，修改 volumes 中的博客路径：

```yaml
volumes:
  - ./config.json:/app/config.json
  - /你的/博客/路径:/blog       # 修改这里
```

---

### 方式二：命令行使用

适合需要在本地直接操作 Hexo 博客的用户。

#### 安装

```bash
# 1. 克隆项目
git clone https://github.com/Phoenizard/notion-to-hexo.git
cd notion-to-hexo

# 2. 安装依赖
pip install -e ".[ui,llm]"    # 完整安装（含 Web UI 和 LLM 摘要）
pip install -e .               # 最小安装（仅命令行）

# 3. 准备配置
cp config.example.json config.json
# 编辑 config.json
```

#### 系统依赖

- Python 3.8+
- Node.js + hexo-cli（`npm install -g hexo-cli`）
- 已初始化的 Hexo 博客项目

#### 发布文章

```bash
# 基本用法 — 交互式
notion-to-hexo "https://www.notion.so/My-Article-abc123"

# 非交互模式（CI/CD 适用）
notion-to-hexo --yes "https://www.notion.so/My-Article-abc123"

# 测试模式（不执行 Hexo 命令，输出到 test/ 目录）
notion-to-hexo --test "https://www.notion.so/My-Article-abc123"

# 启动 Web UI
notion-to-hexo --ui
```

---

## 前置要求

### 1. Notion Integration 配置

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)，创建一个新的 Integration
2. 复制 Integration Token（以 `secret_` 开头）
3. **重要**：打开要发布的 Notion 页面 → 点击右上角 `···` → `Add connections` → 选择你的 Integration

### 2. 阿里云 OSS 配置

在阿里云控制台获取以下信息：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| Access Key ID | 访问密钥 ID | `LTAI5t...` |
| Access Key Secret | 访问密钥 | `xxxxxx` |
| Bucket Name | 存储桶名称 | `my-blog-images` |
| Endpoint | 地域节点 | `oss-cn-hangzhou.aliyuncs.com` |
| CDN Domain | 访问域名 | `my-blog-images.oss-cn-hangzhou.aliyuncs.com` |

### 3. LLM 摘要（可选）

使用阿里云百炼 DashScope API 自动生成文章摘要：
- 申请 API Key：[DashScope 控制台](https://dashscope.console.aliyun.com/)
- 填入 `config.json` 的 `llm.dashscope_api_key` 或设置环境变量 `DASHSCOPE_API_KEY`

---

## 详细配置说明

### config.json 完整示例

```json
{
  "notion": {
    "token": "secret_your_token_here"
  },
  "oss": {
    "access_key_id": "LTAI5t...",
    "access_key_secret": "your_secret",
    "bucket_name": "my-blog-images",
    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
    "cdn_domain": "my-blog-images.oss-cn-hangzhou.aliyuncs.com"
  },
  "hexo": {
    "blog_path": "/path/to/your/hexo/blog",
    "default_category": "学习笔记",
    "default_tags": [],
    "default_title": "",
    "default_description": "",
    "default_mathjax": false
  },
  "llm": {
    "dashscope_api_key": "sk-your_key_here"
  }
}
```

### 环境变量（可选，优先级高于 config.json）

```bash
export NOTION_TOKEN=secret_xxx
export NOTION_OSS_ACCESS_KEY_ID=LTAI5t...
export NOTION_OSS_ACCESS_KEY_SECRET=your_secret
export NOTION_OSS_BUCKET_NAME=my-blog-images
export NOTION_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com
export NOTION_OSS_CDN_DOMAIN=my-blog-images.oss-cn-hangzhou.aliyuncs.com
export DASHSCOPE_API_KEY=sk-xxx
```

> **配置优先级**：环境变量 > config.json > 交互式输入 > 默认值

---

## Notion 页面属性配置

在 Notion 页面中添加以下属性，发布时会自动读取并写入 Hexo Front Matter：

| 属性名 | 类型 | 用途 | 必填 |
|--------|------|------|------|
| `Tags` | Multi-select | 文章标签 | 否 |
| `Category` | Select | 文章分类 | 否（默认使用 `default_category`） |
| `Description` | Text | 文章描述/SEO | 否 |
| `MathJax` | Checkbox | 启用数学公式渲染 | 否 |

**生成的 Front Matter 示例**：

```yaml
---
title: 我的文章标题
date: 2025-01-24 12:34:56
tags:
  - Python
  - 教程
categories: 学习笔记
description: 这是一篇关于 Python 的教程
mathjax: true
---
```

---

## Web UI 使用指南

启动 Web UI 后（`notion-to-hexo --ui` 或 Docker），在浏览器中操作：

1. **配置**（侧边栏）：首次使用时在侧边栏填入 Notion Token、OSS 凭证等，点击保存
2. **输入 URL**：在主区域粘贴 Notion 页面 URL，点击「获取页面」
3. **编辑元数据**：自动填充标题、标签、分类等字段，可手动修改
4. **预览内容**：查看转换后的 Markdown 渲染效果
5. **发布/导出**：
   - 「测试导出」— 导出到 test/ 目录，不执行 Hexo 命令
   - 「发布到 Hexo」— 完整发布流程（上传图片 + 生成文章 + hexo generate）
   - 「下载 Markdown」— 直接下载 .md 文件到本地

---

## CLI 命令详解

```
notion-to-hexo [选项] <notion_url>

位置参数:
  notion_url                Notion 页面 URL

选项:
  --test                    测试模式，输出到 test/ 目录
  --yes, -y                 非交互模式，跳过所有确认提示
  --ui                      启动 Streamlit Web 界面
  --title TITLE             自定义文章标题
  --category CATEGORY       指定分类
  --tags TAGS [TAGS ...]    指定标签
  --description DESC        指定描述
  --llm-summary             使用 LLM 生成摘要
  --no-serve                发布后不启动预览服务器
  --deploy                  自动部署（hexo deploy）
  --dry-run                 仅预览，不写入文件
  --config PATH             指定配置文件路径
  --verbose, -v             显示详细日志
```

### 使用示例

```bash
# 基本发布
notion-to-hexo "https://www.notion.so/My-Article-abc123"

# 自定义元数据
notion-to-hexo --title "自定义标题" --category "技术" --tags Python 教程 \
  "https://www.notion.so/My-Article-abc123"

# CI/CD 自动化（非交互 + 自动部署）
notion-to-hexo --yes --deploy "https://www.notion.so/My-Article-abc123"

# 仅预览转换结果
notion-to-hexo --dry-run "https://www.notion.so/My-Article-abc123"

# 批量发布
cat urls.txt | xargs -I {} notion-to-hexo --yes "{}"
```

---

## 支持的 Notion 内容类型

| 类型 | 支持状态 | 说明 |
|------|----------|------|
| 段落 | ✅ 完全支持 | |
| 标题 (H1/H2/H3) | ✅ 完全支持 | |
| 有序/无序列表 | ✅ 完全支持 | 含嵌套 |
| 待办列表 | ✅ 完全支持 | `- [ ]` / `- [x]` |
| 代码块 | ✅ 完全支持 | 保留语言标注 |
| 数学公式 | ✅ 完全支持 | 行内 `$...$` 和块级 `$$...$$` |
| 图片 | ✅ 完全支持 | 自动上传至 OSS |
| 引用 | ✅ 完全支持 | |
| 分割线 | ✅ 完全支持 | |
| Callout | ✅ 完全支持 | 渲染为引用块 |
| Toggle | ⚠️ 部分支持 | 展开显示内容 |
| 表格 | ⚠️ 部分支持 | GFM 表格格式 |
| Database 视图 | ❌ 不支持 | |
| Embed 嵌入 | ❌ 不支持 | |

---

## 项目结构

```
notion-to-hexo/
├── notion_to_hexo/           # 主程序包
│   ├── config.py             # 配置管理（懒加载）
│   ├── network.py            # HTTP 请求（重试、超时）
│   ├── notion.py             # Notion API 客户端（含分页）
│   ├── converter.py          # Notion Block → Markdown 转换
│   ├── oss.py                # 阿里云 OSS 图片上传
│   ├── hexo.py               # Hexo CLI 工具
│   ├── cli.py                # 命令行主入口
│   ├── app.py                # Streamlit Web UI
│   └── exceptions.py         # 自定义异常
├── tests/                    # 测试套件
├── Dockerfile                # Docker 镜像定义
├── docker-compose.yml        # Docker Compose 配置
├── start.command             # macOS 一键启动脚本
├── config.example.json       # 配置模板
├── pyproject.toml            # 项目元数据和依赖
└── README.md                 # English README
```

---

## 常见问题

### "object_not_found" 错误

**原因**：Notion 页面未授权给 Integration。

**解决**：打开 Notion 页面 → `···` → `Add connections` → 选择你的 Integration。

### 图片上传失败（403）

**原因**：OSS 凭证无效或权限不足。

**解决**：
1. 检查 `config.json` 中的 `access_key_id` 和 `access_key_secret`
2. 确认 Access Key 有 `oss:PutObject` 权限
3. 确认 Endpoint 和 Bucket 所在地域一致

### "hexo: command not found"

**原因**：Hexo CLI 未安装或不在 PATH 中。

**解决**：
- 使用 Docker 方式启动（已内置 Hexo）
- 或手动安装：`npm install -g hexo-cli`

### 数学公式不渲染

**解决**：
1. 在 Notion 页面属性中勾选 `MathJax` 复选框
2. 确认 Hexo 主题支持 MathJax（需安装相关插件）

### 长文章内容被截断

v3.0 已修复此问题。如仍遇到，请确认使用最新版本：内容获取已支持 Notion API 分页，不再有 100 个 block 的限制。

### Docker 启动失败

1. 确认 Docker Desktop 正在运行
2. 确认 `config.json` 文件存在（`cp config.example.json config.json`）
3. 查看日志：`docker compose logs -f`

---

## 更新日志

- **v3.0** (2025-01-26)
  - 🐳 Docker 部署支持，双击 `start.command` 一键启动
  - 🖥️ Streamlit Web UI，可视化操作发布流程
  - 🔧 完整 CLI 重构：`argparse`、`--yes` 非交互模式、`--dry-run`
  - 🐛 Notion API 分页支持（长文章不再截断）
  - 🐛 YAML Front Matter 安全转义
  - 🐛 NVM Hexo 检测修复
  - 🐛 MathJax 误判修复
  - ✅ 测试套件（68 个测试）
  - 📦 `pyproject.toml` 标准化打包

- **v2.1** (2025-01-25)
  - LLM 摘要生成（阿里云百炼 DashScope API）

- **v1.0** (2025-01-24)
  - 初始版本：Notion API + 阿里云 OSS + Hexo 发布

---

## 安全提醒

- `config.json` 包含敏感凭证，已在 `.gitignore` 中排除，**切勿提交到 Git**
- 建议使用环境变量管理生产环境密钥
- 定期轮换阿里云 Access Key

---

## 获取帮助

- 提交 Issue：[GitHub Issues](https://github.com/Phoenizard/notion-to-hexo/issues)
- 配置模板：参考 `config.example.json`

---

**版本**: 3.0 | **作者**: Phoenizard | **许可证**: MIT
