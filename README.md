# Notion to Hexo 博客发布工作流

自动将Notion笔记发布到Hexo博客的Python工具。

## 📁 项目位置

- **工作流文件**: `/Users/shay/Documents/Workplace/notion-to-hexo/`
- **博客项目**: `/Users/shay/Documents/Blog/`

这样设计的好处：
- ✅ Blog项目保持纯净，不受工作流文件干扰
- ✅ 工作流可以独立管理和版本控制
- ✅ 可以同时管理多个Hexo博客项目

## ⚡ 快速开始

### 1. 配置（首次使用）

```bash
cd /Users/shay/Documents/Workplace/notion-to-hexo

# 复制配置模板
cp config.example.json config.json

# 编辑配置文件
# 填入 Notion Token、阿里云OSS配置、Blog路径
```

**config.json 示例:**
```json
{
  "notion": {
    "token": "secret_your_token_here"
  },
  "oss": {
    "access_key_id": "LTAI5t...",
    "access_key_secret": "your_secret",
    "bucket_name": "phoenizard-picgo",
    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
    "cdn_domain": "phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com"
  },
  "hexo": {
    "blog_path": "/Users/shay/Documents/Blog",
    "default_category": "学习笔记"
  }
}
```

### 2. 安装依赖

```bash
pip install requests oss2 --break-system-packages
```

### 3. 发布文章

```bash
cd /Users/shay/Documents/Workplace/notion-to-hexo

# 使用配置文件（推荐）
python publish_notion.py <notion_page_url>

# 或交互式输入
python notion_to_hexo.py <notion_page_url>
```

### 4. 审查并部署

```bash
cd /Users/shay/Documents/Blog

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

从PicGo中获取以下信息：
- Access Key ID / Secret
- Bucket名称
- Endpoint（如: `oss-cn-hangzhou.aliyuncs.com`）
- CDN域名（如: `phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com`）

### Notion页面属性（可选）

在Notion中添加以下属性可自动生成元数据：

| 属性 | 类型 | 用途 |
|------|------|------|
| Tags | Multi-select | 文章标签 |
| Category | Select | 文章分类 |
| Description | Text | 文章描述 |
| MathJax | Checkbox | 数学公式支持 |

## 📦 文件说明

```
notion-to-hexo/
├── notion_to_hexo.py        # 核心工作流脚本
├── publish_notion.py         # 简化启动脚本（支持配置文件）
├── config.example.json       # 配置文件模板
├── config.json              # 实际配置（不提交到Git）
├── README.md                # 本文档
├── QUICKSTART.md            # 快速开始指南
├── README_WORKFLOW.md       # 详细使用文档
└── NOTION_WORKFLOW_SUMMARY.md  # 工作流摘要
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

cd /Users/shay/Documents/Workplace/notion-to-hexo
python publish_notion.py "https://www.notion.so/My-Article-abc123"

# 5. 预览和部署
cd /Users/shay/Documents/Blog
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
cd /Users/shay/Documents/Workplace/notion-to-hexo
while read url; do
    python publish_notion.py "$url"
done < urls.txt

# 统一部署
cd /Users/shay/Documents/Blog
hexo deploy
```

## ❓ 常见问题

### Q1: "object_not_found" 错误
**原因**: 未授权Integration访问页面
**解决**: 在Notion页面 > "•••" > "Add connections" > 选择Integration

### Q2: 图片上传失败
**原因**: OSS配置错误
**解决**: 检查`config.json`中的OSS配置，确认权限正确

### Q3: Blog路径错误
**原因**: config.json中的blog_path配置不正确
**解决**: 修改`config.json`中的`hexo.blog_path`为正确路径

### Q4: 数学公式不显示
**原因**: Front Matter未启用mathjax
**解决**:
- 在Notion中勾选"MathJax"属性
- 或手动在生成的md文件中添加`mathjax: true`

## 🔐 安全提醒

- ✅ `config.json` 包含敏感信息，**请勿提交到Git**
- ✅ 建议使用环境变量存储密钥
- ✅ 定期轮换阿里云Access Key

## 📚 更多文档

- **快速开始**: `QUICKSTART.md`
- **详细文档**: `README_WORKFLOW.md`
- **工作流摘要**: `NOTION_WORKFLOW_SUMMARY.md`

## 🚀 工作流程图

```
┌─────────────────────────────────┐
│  Notion页面 (已授权访问)         │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  /Users/shay/Documents/         │
│  Workplace/notion-to-hexo/      │
│  python publish_notion.py       │
└────────────┬────────────────────┘
             │
             ├─> 获取Notion内容
             ├─> 下载并上传图片到OSS
             ├─> 转换为Markdown
             │
             ▼
┌─────────────────────────────────┐
│  /Users/shay/Documents/Blog/    │
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

- **v1.0** (2025-01-24)
  - ✅ 初始版本
  - ✅ 支持Notion API获取内容
  - ✅ 支持阿里云OSS图床
  - ✅ 自动生成Hexo文章
  - ✅ 独立工作目录设计

## 📞 获取帮助

遇到问题？
1. 检查`config.json`配置
2. 确认Notion Integration授权
3. 验证Blog路径正确
4. 查看详细文档

---

**版本**: 1.0
**作者**: Phoenizard
**最后更新**: 2025-01-24
