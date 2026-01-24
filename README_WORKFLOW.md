# Notion to Hexo 工作流使用指南

## 概述

这个工作流可以自动将Notion笔记转换为Hexo博客文章,包括:
1. ✅ 使用`hexo new [name]`创建文章模板
2. ✅ 从Notion获取内容和图片
3. ✅ 自动上传图片到阿里云OSS图床
4. ✅ 生成Markdown文件
5. ✅ 运行`hexo generate`生成静态文件
6. ⏸️ **不**自动运行`hexo deploy`,保留人工审查环节

## 前置准备

### 1. Notion配置

#### 步骤1: 创建Notion Integration
1. 访问 https://www.notion.so/my-integrations
2. 点击 "+ New integration"
3. 填写基本信息:
   - Name: "Hexo Blog Publisher" (或任意名称)
   - Associated workspace: 选择你的工作区
   - Type: Internal integration
4. 点击 "Submit" 创建
5. **复制 "Internal Integration Token"** (以`secret_`开头)

#### 步骤2: 授权Integration访问页面
1. 打开你想要发布的Notion页面
2. 点击右上角的 "•••" (更多选项)
3. 选择 "Add connections"
4. 选择你刚创建的Integration ("Hexo Blog Publisher")
5. 点击 "Confirm"

#### 步骤3: (可选) 在Notion数据库中添加属性
为了更好地控制博客文章的元数据,建议在Notion页面中添加以下属性:

- **Tags** (Multi-select): 文章标签
- **Category** (Select): 文章分类 (默认: 学习笔记)
- **Description** (Text): 文章描述
- **MathJax** (Checkbox): 是否启用数学公式渲染

### 2. 阿里云OSS配置

你已经在使用PicGo,配置信息应该在PicGo中。你需要以下信息:

- **Access Key ID**: 阿里云访问密钥ID
- **Access Key Secret**: 阿里云访问密钥Secret
- **Bucket名称**: OSS Bucket名称
- **Endpoint**: OSS访问端点 (例如: `oss-cn-hangzhou.aliyuncs.com`)
- **CDN域名**: OSS CDN域名 (例如: `phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com`)

查看PicGo配置的方法:
1. 打开PicGo应用
2. 进入 "图床设置" > "阿里云OSS"
3. 查看并记录上述配置信息

### 3. 安装Python依赖

```bash
cd /path/to/your/Blog
pip install requests oss2 --break-system-packages
```

## 使用方法

### 方式1: 命令行运行

```bash
cd /path/to/your/Blog
python notion_to_hexo.py <notion_page_url>
```

**示例:**
```bash
python notion_to_hexo.py https://www.notion.so/My-Article-abc123def456
```

运行后,脚本会提示你输入:
1. Notion Integration Token
2. 阿里云OSS配置信息 (如果未在脚本中预配置)

### 方式2: 交互式运行

```bash
cd /path/to/your/Blog
python notion_to_hexo.py
```

脚本会依次提示你输入所有必要信息。

## 工作流程说明

脚本执行以下步骤:

### 步骤0: 从Notion获取页面内容
- 使用Notion API读取页面标题、属性和内容块
- 自动检测是否需要启用MathJax (如果内容包含`$`或`\[`数学公式)

### 步骤1: 创建Hexo文章
- 运行 `hexo new "<文章标题>"`
- 在 `source/_posts/` 目录创建新的Markdown文件

### 步骤2: 处理图片并上传到OSS
- 检测Markdown中的所有图片 `![](url)`
- 下载Notion托管的图片
- 上传到阿里云OSS
- 替换为OSS CDN链接

### 步骤3: 写入Markdown文件
- 生成符合Hexo格式的Front Matter:
  ```yaml
  ---
  title: 文章标题
  date: 2025-01-24 12:00:00
  tags: [标签1, 标签2]
  categories: 学习笔记
  mathjax: true
  description: 文章描述
  ---
  ```
- 写入转换后的Markdown内容

### 步骤4: 生成Hexo静态文件
- 运行 `hexo generate`
- 生成静态HTML文件到 `public/` 目录

### 最后: 人工审查
脚本**不会**自动运行 `hexo deploy`。你需要:

1. 检查生成的文章:
   ```bash
   cat source/_posts/<文章名>.md
   ```

2. 本地预览:
   ```bash
   hexo server
   ```
   访问 http://localhost:4000 查看效果

3. 确认无误后部署:
   ```bash
   hexo deploy
   ```

## 常见问题

### Q1: "无法从URL中提取Notion页面ID"

**原因:** URL格式不正确

**解决:** 确保使用完整的Notion页面URL,格式类似:
```
https://www.notion.so/Title-abc123def456...
```

### Q2: "401 Unauthorized" 或 "object_not_found"

**原因:** Integration未授权访问该页面

**解决:**
1. 打开Notion页面
2. 点击右上角 "•••" > "Add connections"
3. 选择你的Integration并确认

### Q3: 图片上传失败

**原因:** OSS配置错误或权限不足

**解决:**
1. 检查Access Key ID/Secret是否正确
2. 检查Bucket名称和Endpoint是否正确
3. 确认OSS Bucket权限设置允许上传
4. 在阿里云控制台检查RAM权限

### Q4: 数学公式渲染异常

**原因:** Front Matter中`mathjax: true`未设置

**解决:**
- 脚本会自动检测`$`符号并启用mathjax
- 如果仍有问题,手动在Notion中添加"MathJax"属性并勾选

### Q5: 中文文件名乱码

**原因:** 文件系统编码问题

**解决:** 脚本已自动清理文件名,将空格和特殊字符替换为`-`

## 高级配置

### 在脚本中预配置OSS (避免每次输入)

编辑 `notion_to_hexo.py`,找到 `OSS_CONFIG` 部分:

```python
OSS_CONFIG = {
    'access_key_id': 'YOUR_ACCESS_KEY_ID',
    'access_key_secret': 'YOUR_ACCESS_KEY_SECRET',
    'bucket_name': 'YOUR_BUCKET_NAME',
    'endpoint': 'oss-cn-hangzhou.aliyuncs.com',
    'cdn_domain': 'your-bucket.oss-cn-hangzhou.aliyuncs.com',
}
```

### 设置环境变量 (推荐)

为了安全,建议使用环境变量:

```bash
# 在 ~/.bashrc 或 ~/.zshrc 中添加:
export NOTION_TOKEN="secret_your_token_here"
export OSS_ACCESS_KEY_ID="your_access_key_id"
export OSS_ACCESS_KEY_SECRET="your_access_key_secret"
export OSS_BUCKET_NAME="your_bucket_name"
export OSS_ENDPOINT="oss-cn-hangzhou.aliyuncs.com"
export OSS_CDN_DOMAIN="your-bucket.oss-cn-hangzhou.aliyuncs.com"
```

然后修改脚本读取环境变量。

## 支持的Notion Block类型

当前脚本支持以下Notion Block:

- ✅ Paragraph (段落)
- ✅ Heading 1/2/3 (标题)
- ✅ Bulleted list (无序列表)
- ✅ Numbered list (有序列表)
- ✅ Code block (代码块)
- ✅ Equation (数学公式)
- ✅ Image (图片)
- ✅ Quote (引用)
- ✅ Divider (分割线)
- ✅ 嵌套Block (子内容)

**不支持的Block:**
- ❌ Toggle (折叠块) - 将展开显示
- ❌ Callout (提示框) - 显示为引用
- ❌ Table (表格) - 需要手动调整
- ❌ Database (数据库视图) - 不支持
- ❌ Embed (嵌入内容) - 仅显示链接

## 工作流优化建议

### 批量发布多篇文章

创建一个批处理脚本:

```bash
#!/bin/bash
# batch_publish.sh

URLS=(
    "https://www.notion.so/Article-1-abc123"
    "https://www.notion.so/Article-2-def456"
    "https://www.notion.so/Article-3-ghi789"
)

for url in "${URLS[@]}"; do
    echo "Processing: $url"
    python notion_to_hexo.py "$url"
    echo "---"
done

echo "All articles processed. Run 'hexo deploy' to publish."
```

### 定时同步 (使用cron)

```bash
# 编辑crontab
crontab -e

# 添加定时任务 (每天凌晨2点运行)
0 2 * * * cd /path/to/Blog && python notion_to_hexo.py <notion_url> >> /tmp/hexo_sync.log 2>&1
```

## 贡献与反馈

如有问题或建议,欢迎反馈!

## 许可

MIT License
