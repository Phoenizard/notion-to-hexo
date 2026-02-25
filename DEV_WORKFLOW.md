# 开发工作流 (DEV_WORKFLOW.md)

每次代码修改遵循以下标准流程，确保代码质量：

## 标准流程

```
1. Write   — 编写/修改代码
2. Lint    — python -m py_compile <file> 检查语法
3. Test    — pytest tests/ -x -v 运行测试
4. Verify  — python -c "import notion_to_hexo" 确认 import 无副作用（无输出）
5. Smoke   — 针对性功能验证（如 URL 解析、front matter 生成）
6. Fix     — 如有失败，分析错误 → 修复 → 回到步骤 2
7. Commit  — 通过后提交（仅在用户要求时）
```

## 规则

- 每个 Phase 完成后运行全量测试 `pytest tests/ -v`
- 新增功能必须同步写测试
- 修 bug 必须先写复现测试再修复
- Streamlit UI 用 `streamlit run --server.headless true notion_to_hexo/app.py` 验证启动
- `python -c "import notion_to_hexo"` 必须无任何输出（no import side effects）

## 测试命令

```bash
# 全量测试
pytest tests/ -v

# 单个模块
pytest tests/test_converter.py -v
pytest tests/test_notion.py -v
pytest tests/test_cli.py -v
pytest tests/test_hexo.py -v

# 语法检查
python -m py_compile notion_to_hexo/config.py
python -m py_compile notion_to_hexo/cli.py
# ... etc

# Import 无副作用检查
python -c "import notion_to_hexo" 2>&1 | head -1
# 期望：无输出

# Docker 构建验证
docker compose build
docker compose up -d
# 访问 http://localhost:8501 验证 Streamlit UI
docker compose down
```
