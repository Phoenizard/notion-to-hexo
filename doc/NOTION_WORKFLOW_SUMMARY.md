# Notion to Hexo 工作流摘要

## 📦 已创建的文件

```
Blog/
├── notion_to_hexo.py       # 核心工作流脚本
├── publish_notion.py        # 简化版启动脚本(支持配置文件)
├── config.example.json      # 配置文件模板
├── QUICKSTART.md           # 快速开始指南
├── README_WORKFLOW.md      # 详细使用文档
└── .gitignore              # 已添加config.json等到忽略列表
```

## ⚡ 快速使用 (3步)

### 1. 配置 (首次使用)

```bash
# 复制配置模板
cp config.example.json config.json

# 编辑配置文件,填入:
# - Notion Integration Token
# - 阿里云OSS配置 (从PicGo获取)
```

### 2. 发布文章

```bash
# 方式1: 使用配置文件 (推荐)
python publish_notion.py <notion_page_url>

# 方式2: 交互式输入
python notion_to_hexo.py <notion_page_url>
```

### 3. 审查并部署

```bash
# 本地预览
hexo server

# 确认后部署
hexo deploy
```

## 🔧 工作流功能

| 步骤 | 功能 | 自动化程度 |
|------|------|-----------|
| 1 | `hexo new [name]` 创建文章模板 | ✅ 自动 |
| 2 | 从Notion获取内容和图片 | ✅ 自动 |
| 3 | 上传图片到阿里云OSS图床 | ✅ 自动 |
| 4 | 转换为Markdown格式 | ✅ 自动 |
| 5 | 生成Front Matter (标题/标签/分类等) | ✅ 自动 |
| 6 | `hexo generate` 生成静态文件 | ✅ 自动 |
| 7 | `hexo deploy` 部署 | ⏸️ 手动 (保留审查环节) |

## 📋 前置要求

### Notion配置
1. 创建Integration: https://www.notion.so/my-integrations
2. 复制Token (以`secret_`开头)
3. **重要:** 对每个要发布的页面,点击 "•••" > "Add connections" > 选择Integration

### 阿里云OSS配置
从PicGo中获取:
- Access Key ID/Secret
- Bucket名称
- Endpoint (如: `oss-cn-hangzhou.aliyuncs.com`)
- CDN域名 (如: `phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com`)

### Python依赖
```bash
pip install -r requirements.txt
```

## 📝 Notion页面属性建议

在Notion中添加以下属性,可自动生成Front Matter:

| 属性 | 类型 | 用途 | 示例 |
|------|------|------|------|
| Tags | Multi-select | 文章标签 | `[概率论, 金融数学]` |
| Category | Select | 文章分类 | `学习笔记` |
| Description | Text | 文章描述 | 简短摘要 |
| MathJax | Checkbox | 数学公式支持 | ✓ |

**注:** 如果内容中包含`$`或`\[`数学公式,会自动启用MathJax

## 🎯 支持的Notion内容

### ✅ 完全支持
- 段落、标题(H1/H2/H3)
- 列表(有序/无序)
- 代码块(支持语法高亮)
- 数学公式(行内`$...$`和块级`$$...$$`)
- 图片(自动上传到OSS)
- 引用
- 分割线
- **嵌套内容**

### ⚠️ 部分支持
- Toggle: 展开显示
- Callout: 显示为引用
- Table: 可能需要手动调整

### ❌ 不支持
- Database视图
- Embed嵌入内容

## 🔍 故障排查

### 常见错误及解决

| 错误信息 | 原因 | 解决方法 |
|---------|------|---------|
| `object_not_found` | 未授权访问 | 在Notion页面添加Connection |
| `401 Unauthorized` | Token错误 | 检查`config.json`中的token |
| 图片上传失败 | OSS配置错误 | 检查OSS配置和权限 |
| 无法提取页面ID | URL格式错误 | 使用完整Notion页面URL |

## 📚 文档索引

- **快速开始:** `QUICKSTART.md`
- **完整文档:** `README_WORKFLOW.md`
- **配置模板:** `config.example.json`

## 💡 使用示例

### 示例1: 发布单篇文章

```bash
# 1. 在Notion中完成文章
# 2. 授权Integration访问
# 3. 复制页面URL
# 4. 运行脚本
python publish_notion.py https://www.notion.so/My-Article-abc123

# 5. 预览
hexo server

# 6. 部署
hexo deploy
```

### 示例2: 批量发布

```bash
# 创建urls.txt文件,每行一个URL
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
hexo deploy
```

## 🔐 安全建议

1. **不要提交配置文件:**
   - `config.json` 已在 `.gitignore` 中
   - 包含敏感信息(Token、密钥)

2. **使用环境变量 (可选):**
   ```bash
   export NOTION_TOKEN="secret_xxx"
   export OSS_ACCESS_KEY_ID="xxx"
   # ... 其他配置
   ```

3. **定期轮换密钥:**
   - 在阿里云控制台定期更新Access Key
   - 在Notion中可以随时刷新Integration Token

## 🚀 工作流程图

```
┌─────────────────┐
│  Notion页面    │
│  (已授权访问)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 运行脚本        │
│ publish_notion  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. 获取内容     │
│ 2. 创建文章模板 │
│ 3. 处理图片     │
│ 4. 上传到OSS    │
│ 5. 生成MD文件   │
│ 6. hexo generate│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 人工审查        │
│ hexo server     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 确认后部署      │
│ hexo deploy     │
└─────────────────┘
```

## 📞 获取帮助

遇到问题?
1. 查看 `QUICKSTART.md` 快速排查
2. 阅读 `README_WORKFLOW.md` 了解详情
3. 检查Notion Integration授权
4. 验证OSS配置正确性

---

**版本:** 1.0
**更新日期:** 2025-01-24
**兼容:** Hexo 博客系统 + Notion API + 阿里云OSS
