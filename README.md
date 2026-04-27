# academic-analysis-cli

学术搜索命令行工具，基于 [OpenAlex](https://openalex.org/) 公开 API，无需注册，无需鉴权。

## 技术栈

- **API**: OpenAlex 公开 API
- **CLI**: Click 8+
- **Python**: 3.11+
- **HTTP**: 标准库 `urllib.request`（零额外依赖）

## 文件结构

```
cli_anything/scholar/
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

## 安装

```bash
pip install -e .
```

## 使用

### 单次执行

```bash
# 搜索学者
cli-anything-scholar scholar search "Yoshua Bengio" -n 5

# 查看学者详情（ORCID 或 OpenAlex ID）
cli-anything-scholar scholar profile 0000-0001-6187-6610
cli-anything-scholar scholar profile 0000-0001-6187-6610 --stats

# 获取论文列表
cli-anything-scholar scholar works 0000-0001-6187-6610 -n 10 --sort date

# 查找相关论文
cli-anything-scholar scholar related 10.1145/3292500.3330671

# 语义主题标注
cli-anything-scholar scholar tag "Attention is All You Need" --abstract "We propose..."

# JSON 输出
cli-anything-scholar --json scholar search "Einstein" -n 3
```

### REPL 模式（无参数启动）

```bash
cli-anything-scholar
# scholar> scholar search "Einstein"
# scholar> scholar tag "Deep Learning"
# scholar> exit
```

## 命令

| 命令 | 说明 |
|------|------|
| `scholar search <name>` | 按姓名搜索学者 |
| `scholar profile <orcid\|id>` | 查看学者详情 |
| `scholar works <orcid\|id>` | 获取论文列表 |
| `scholar related <doi\|id>` | 查找相关论文 |
| `scholar tag <title>` | 语义主题标注 |

全局选项 `--json` 输出机器可读的 JSON 格式。

## 测试

```bash
# 单元测试（无网络）
pytest cli_anything/scholar/tests/test_core.py -v

# 端到端测试（需要网络）
pytest cli_anything/scholar/tests/test_full_e2e.py -v -m e2e
```

## 风险与限制

- OpenAlex API 无 SLA 保证，偶发超时
- 添加 `--email` 参数可进入 polite pool 获得更稳定访问
- XPAC 数据集（`--xpac`）数据质量较低
