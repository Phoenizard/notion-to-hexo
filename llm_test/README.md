# LLM Test - 阿里云百炼 API 测试

本目录用于测试阿里云百炼（DashScope）LLM API，为后续集成到 notion_to_hexo 做准备。

## 功能

- 使用通义千问模型为文章生成摘要
- 支持从 `.env` 文件加载 API 密钥
- 提供命令行和编程两种使用方式

## 安装依赖

```bash
pip install -r requirements.txt
```

或者安装到项目虚拟环境：

```bash
cd llm_test
pip install dashscope python-dotenv
```

## 配置 API 密钥

1. 在阿里云百炼平台获取 API Key：https://bailian.console.aliyun.com/
2. 在项目根目录的 `.env` 文件中添加：

```
DASHSCOPE_API_KEY=sk-your-api-key-here
```

## 使用方法

### 命令行使用

```bash
# 生成文章摘要
python summary_generator.py <markdown_file_path>

# 示例
python summary_generator.py ../test/sample_article.md
```

### 编程使用

```python
from llm_test import generate_summary

# 基本用法
content = "这是一篇关于 Python 编程的文章..."
summary = generate_summary(content)
print(summary)

# 带标题和指定模型
summary = generate_summary(
    content=content,
    title="Python 入门教程",
    model="qwen-plus"  # 或 "qwen-turbo"
)
```

## 可用模型

| 模型 | 特点 | 适用场景 |
|------|------|----------|
| `qwen-turbo` | 响应快，成本低 | 日常使用，快速测试 |
| `qwen-plus` | 质量高，效果好 | 正式发布，高质量需求 |

## 输出示例

```
Generating summary for: sample_article.md
----------------------------------------
Summary:
本文介绍了如何使用 Python 进行数据分析，涵盖了 pandas 数据处理、
matplotlib 可视化等核心内容。通过实际案例演示，读者可以快速掌握
数据分析的基本流程和常用技巧。
----------------------------------------
Length: 89 characters
```

## 错误处理

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `DASHSCOPE_API_KEY not found` | 未配置 API 密钥 | 在 `.env` 中添加密钥 |
| `dashscope package not installed` | 未安装依赖 | 运行 `pip install dashscope` |
| `API call failed: InvalidApiKey` | API 密钥无效 | 检查密钥是否正确 |

## 后续计划

- [ ] 集成到 notion_to_hexo 主流程
- [ ] 自动生成博客 description 字段
- [ ] 支持批量处理多篇文章
