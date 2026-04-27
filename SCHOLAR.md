# Scholar CLI Harness

学术搜索命令行工具，将 OpenAlex 学者/论文检索功能迁移为独立 Python CLI。

## 技术栈

- **API**: OpenAlex 公开 API（无需鉴权）
- **CLI**: Click 8+
- **Python**: 3.11+
- **HTTP**: 标准库 `urllib.request`（零额外依赖）

## 文件结构

```
cli_anything/scholar/
├── __init__.py
├── __main__.py          # 入口，REPL 默认模式
├── scholar_cli.py       # Click 命令定义
├── core/
│   └── openalex.py      # OpenAlex API 客户端
├── utils/
│   └── output.py        # 表格/JSON 输出工具
└── tests/
    ├── test_core.py     # 单元测试（mock HTTP）
    └── test_full_e2e.py # 端到端测试（真实 API）
```

## 快速开始

```bash
pip install -e .
cli-anything-scholar scholar search "Yoshua Bengio"
```

## 风险与限制

- OpenAlex API 无 SLA 保证，偶发超时
- 添加 `--email` 参数可进入 polite pool 获得更稳定访问
- XPAC 数据集（`--xpac`）数据质量较低
