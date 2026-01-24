# 快速开始指南

## 一、前置配置 (仅需配置一次)

### 1. 获取Notion Integration Token

1. 访问: https://www.notion.so/my-integrations
2. 点击 **"+ New integration"**
3. 填写名称 (如: "Hexo Publisher"),选择工作区
4. 点击 **Submit**
5. **复制Token** (以`secret_`开头,妥善保存)

### 2. 授权Integration访问Notion页面

**重要:** 对于每个要发布的Notion页面,都需要授权!

1. 打开Notion页面
2. 点击右上角 **"•••"**
3. 选择 **"Add connections"**
4. 选择刚创建的Integration
5. 点击 **"Confirm"**

### 3. 获取阿里云OSS配置

从PicGo中查看配置:
- 打开PicGo
- "图床设置" > "阿里云OSS"
- 记录以下信息:
  - Access Key ID
  - Access Key Secret
  - Bucket名称
  - 存储区域/Endpoint (如: `oss-cn-hangzhou.aliyuncs.com`)
  - 自定义域名 (如: `phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com`)

### 4. 创建配置文件

在Blog目录下:

```bash
cd /path/to/Blog
cp config.example.json config.json
```

编辑`config.json`,填入上述信息:

```json
{
  "notion": {
    "token": "secret_xxxxxxxxx"
  },
  "oss": {
    "access_key_id": "LTAI5t...",
    "access_key_secret": "xxxxxx",
    "bucket_name": "phoenizard-picgo",
    "endpoint": "oss-cn-hangzhou.aliyuncs.com",
    "cdn_domain": "phoenizard-picgo.oss-cn-hangzhou.aliyuncs.com"
  }
}
```

**注意:** `config.json`已被添加到`.gitignore`,不会被提交到Git

### 5. 安装依赖

```bash
pip install requests oss2 --break-system-packages
```

## 二、使用工作流发布文章

### 方法1: 使用配置文件 (推荐)

```bash
python publish_notion.py https://www.notion.so/Your-Article-xxxxx
```

### 方法2: 交互式输入

```bash
python notion_to_hexo.py https://www.notion.so/Your-Article-xxxxx
```

程序会提示输入配置信息。

## 三、发布流程

1. **运行脚本**
   ```bash
   python publish_notion.py <notion_url>
   ```

2. **脚本自动完成:**
   - ✓ 从Notion获取内容
   - ✓ 创建Hexo文章
   - ✓ 下载并上传图片到OSS
   - ✓ 生成Markdown文件
   - ✓ 运行`hexo generate`

3. **人工审查**
   ```bash
   # 查看生成的文章
   cat source/_posts/<文章名>.md

   # 本地预览
   hexo server
   # 访问 http://localhost:4000
   ```

4. **确认后部署**
   ```bash
   hexo deploy
   ```

## 四、Notion页面建议结构

为了更好的转换效果,建议在Notion中添加以下属性:

| 属性名 | 类型 | 说明 |
|--------|------|------|
| Tags | Multi-select | 文章标签 (如: `概率论`, `金融数学`) |
| Category | Select | 文章分类 (如: `学习笔记`) |
| Description | Text | 文章描述/摘要 |
| MathJax | Checkbox | 是否包含数学公式 |

**示例:**

```
[Notion页面]
Title: 基于BS模型的期权定价

Properties:
- Tags: [概率论, 金融数学]
- Category: 学习笔记
- Description: 本文基于BS模型假设,通过构造混合随机分布...
- MathJax: ✓

Content:
## BS模型基本假设
...
```

## 五、常见问题速查

### Q: "object_not_found" 或 "401 Unauthorized"
**A:** 未授权Integration访问该页面
→ 打开页面 > "•••" > "Add connections" > 选择Integration

### Q: 图片无法上传
**A:** 检查OSS配置
→ 确认`config.json`中的OSS信息正确
→ 在阿里云控制台检查权限

### Q: 数学公式显示异常
**A:** 检查mathjax设置
→ Notion中勾选"MathJax"属性
→ 或在生成的md文件中确认`mathjax: true`

### Q: 中文标题文件名乱码
**A:** 脚本已自动处理
→ 特殊字符会被替换为`-`
→ 如仍有问题,手动重命名文件

## 六、进阶技巧

### 批量发布

创建URL列表文件 `urls.txt`:
```
https://www.notion.so/Article-1-xxxxx
https://www.notion.so/Article-2-xxxxx
https://www.notion.so/Article-3-xxxxx
```

批量发布:
```bash
while read url; do
    python publish_notion.py "$url"
done < urls.txt
```

### 预览单篇文章

```bash
python publish_notion.py <notion_url>
hexo server --draft  # 包含草稿的预览
```

### 仅生成不部署

默认行为已经是"仅生成不部署",运行脚本后:
- ✓ 文章已创建
- ✓ 静态文件已生成
- ✗ **未部署** (需手动运行`hexo deploy`)

## 七、获取帮助

详细文档请查看: `README_WORKFLOW.md`

问题反馈或功能建议,欢迎提出!
