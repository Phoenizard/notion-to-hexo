# Notion to Hexo 博客发布工作流

自动将Notion笔记发布到Hexo博客的Python工具。

## 特性

- ✅ 自动从Notion获取页面内容
- ✅ 自动上传图片到阿里云OSS图床
- ✅ 自动转换为Hexo兼容的Markdown格式
- ✅ 支持LLM自动生成文章摘要（可选）
- ✅ 独立工作目录，不影响博客项目

## ⚡ 快速开始

### 1. 配置（首次使用）

```bash
cd notion-to-hexo

# 推荐：使用 .env 存储敏感信息
cp .env.example .env
# 编辑 .env，填入 Notion Token、OSS 密钥

# 可选：使用 config.json 存储非敏感配置
cp config.example.json config.json
# 编辑 config.json，填入 blog_path 等非敏感配置
```

**.env 文件:**
```bash
NOTION_TOKEN=secret_your_token_here
NOTION_OSS_ACCESS_KEY_ID=your_access_key_id
NOTION_OSS_ACCESS_KEY_SECRET=your_access_key_secret
NOTION_OSS_BUCKET_NAME=your-bucket-name
NOTION_OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com # 以阿里云为例
NOTION_OSS_CDN_DOMAIN=your-bucket.oss-cn-hangzhou.aliyuncs.com # 以阿里云为例
DASHSCOPE_API_KEY=sk-your_dashscope_api_key_here
```

**config.json:**
```json
{
  "hexo": {
    "blog_path": "Path/To/Blog",
    "default_category": ""
  }
}
```

> **配置优先级**: 环境变量 > config.json > 默认值

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 发布文章

```bash
cd /Path/To/notion-to-hexo

# 使用配置文件（推荐）
python publish_notion.py <notion_page_url>

# 或交互式输入
python notion_to_hexo.py <notion_page_url>
```

### 4. 审查并部署

```bash
cd /path/to/your/hexo/blog

# 预览
hexo server

# 确认后部署
hexo deploy
```

## 🎯 工作流功能

| 步骤 | 功能 | 状态 |
|------|------|------|
| 1 | `hexo new [name]` 创建文章模板 | ✅ 自动 |
| 2 | 从Notion获取内容和图片 | ✅ 自动 |
| 3 | 上传图片到阿里云OSS图床 | ✅ 自动 |
| 4 | 转换为Markdown格式 | ✅ 自动 |
| 4.5 | 使用LLM生成文章摘要 | ✅ 可选（需配置DashScope API） |
| 5 | 生成Front Matter | ✅ 自动 |
| 6 | `hexo generate` 生成静态文件 | ✅ 自动 |
| 7 | `hexo deploy` 部署 | ⏸️ 手动审查 |

## 📋 前置要求

### Notion配置

1. **创建Integration**
   - 访问: https://www.notion.so/my-integrations
   - 创建新Integration
   - 复制Token（以`secret_`开头）

2. **授权页面访问**（重要！）
   - 打开要发布的Notion页面
   - 点击右上角 "•••" > "Add connections"
   - 选择你的Integration

### 阿里云OSS配置

从阿里云控制台或PicGo中获取以下信息：
- Access Key ID / Secret
- Bucket名称
- Endpoint（如: `oss-cn-hangzhou.aliyuncs.com`）
- CDN域名（如: `your-bucket.oss-cn-hangzhou.aliyuncs.com`）

### Notion页面属性（可选）

在Notion中添加以下属性可自动生成元数据：

| 属性 | 类型 | 用途 |
|------|------|------|
| Tags | Multi-select | 文章标签 |
| Category | Select | 文章分类 |
| Description | Text | 文章描述 |
| MathJax | Checkbox | 数学公式支持 |

## 📦 项目结构

```
notion-to-hexo/
├── notion_to_hexo/           # 主程序包
│   ├── __init__.py           # 包初始化，导出公共API
│   ├── config.py             # 配置管理
│   ├── network.py            # 网络工具（重试、超时）
│   ├── hexo.py               # Hexo相关工具
│   ├── oss.py                # 阿里云OSS图片处理
│   ├── notion.py             # Notion API集成
│   ├── converter.py          # Markdown转换逻辑
│   └── cli.py                # 命令行接口和主流程
├── notion_to_hexo.py         # 向后兼容入口
├── publish_notion.py         # 简化启动脚本
├── requirements.txt          # Python依赖列表
├── .env.example              # 环境变量模板
├── config.example.json       # 配置文件模板
└── README.md                 # 本文档
```

## 🔧 支持的Notion内容

### ✅ 完全支持
- 段落、标题（H1/H2/H3）
- 列表（有序/无序）
- 代码块（支持语法高亮）
- 数学公式（行内 `$...$` 和块级 `$$...$$`）
- 图片（自动上传到OSS）
- 引用、分割线
- 嵌套Block

### ⚠️ 部分支持
- Toggle: 展开显示
- Callout: 显示为引用

### ❌ 不支持
- Database视图
- Embed嵌入内容
- 复杂表格

## 🛠️ 使用示例

### 示例1: 发布单篇文章

```bash
# 1. 在Notion中写好文章
# 2. 授权Integration访问该页面
# 3. 复制页面URL
# 4. 运行发布脚本

python publish_notion.py "https://www.notion.so/My-Article-abc123"

# 5. 预览和部署
cd /path/to/your/hexo/blog
hexo server
hexo deploy
```

### 示例2: 批量发布

```bash
# 创建URL列表
cat > urls.txt << EOF
https://www.notion.so/Article-1-xxx
https://www.notion.so/Article-2-xxx
https://www.notion.so/Article-3-xxx
EOF

# 批量发布
while read url; do
    python publish_notion.py "$url"
done < urls.txt

# 统一部署
cd /path/to/your/hexo/blog
hexo deploy
```

## ❓ 常见问题

### Q1: "object_not_found" 错误
**原因**: 未授权Integration访问页面
**解决**: 在Notion页面 > "•••" > "Add connections" > 选择Integration

### Q2: 图片上传失败
**原因**: OSS配置错误
**解决**: 检查 `.env` 中的 OSS 配置（Access Key ID/Secret），确认权限正确

### Q3: Blog路径错误
**原因**: config.json中的blog_path配置不正确
**解决**: 修改`config.json`中的`hexo.blog_path`为正确路径

### Q4: 数学公式不显示
**原因**: Front Matter未启用mathjax
**解决**:
- 在Notion中勾选"MathJax"属性
- 或手动在生成的md文件中添加`mathjax: true`

## 🔐 安全提醒

- ⚠️ **必须使用 `.env` 文件存储敏感密钥**（Token、Access Key Secret）
- ✅ `.env` 和 `config.json` 已添加到 `.gitignore`，不会被提交
- ✅ `config.json` 仅用于非敏感配置（如 `blog_path`、`default_category`）
- ✅ 定期轮换阿里云 Access Key
- ✅ 配置优先级：环境变量 > config.json > 默认值

## 🚀 工作流程图

```
┌─────────────────────────────────┐
│  Notion页面 (已授权访问)         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  notion-to-hexo/                │
│  python publish_notion.py       │
└────────────┬────────────────────┘
             │
             ├─> 获取Notion内容
             ├─> 下载并上传图片到OSS
             ├─> 转换为Markdown
             ├─> (可选) LLM生成摘要
             │
             ▼
┌─────────────────────────────────┐
│  your-hexo-blog/                │
│  source/_posts/文章名.md        │
└────────────┬────────────────────┘
             │
             ├─> hexo new [name]
             ├─> 写入Front Matter
             ├─> hexo generate
             │
             ▼
┌─────────────────────────────────┐
│  人工审查                        │
│  hexo server (预览)              │
│  hexo deploy (部署)              │
└─────────────────────────────────┘
```

## 📝 更新日志

- **v2.1** (2025-01-25)
  - ✅ 新增LLM摘要生成功能（阿里云百炼 DashScope API）
  - ✅ 支持自动生成150-250字文章摘要

- **v1.0** (2025-01-24)
  - ✅ 初始版本
  - ✅ 支持Notion API获取内容
  - ✅ 支持阿里云OSS图床
  - ✅ 自动生成Hexo文章
  - ✅ 独立工作目录设计

## 📞 获取帮助

遇到问题？
1. 检查 `.env` 中的敏感配置（Token、OSS密钥）
2. 检查 `config.json` 中的非敏感配置（blog_path）
3. 确认 Notion Integration 授权
4. 验证 Blog 路径正确
5. 提交 [Issue](https://github.com/Phoenizard/notion-to-hexo/issues)

---

**版本**: 2.1
**作者**: Phoenizard
**最后更新**: 2025-01-25
