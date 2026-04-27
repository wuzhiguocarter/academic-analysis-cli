# cli-anything-scholar

学术搜索 CLI — 学者与论文检索（OpenAlex 公开 API）

## 安装

```bash
pip install -e .
```

## 使用

### 单次执行

```bash
# 搜索学者
cli-anything-scholar scholar search "Yoshua Bengio" -n 5

# 查看学者详情（支持 ORCID 或 OpenAlex ID）
cli-anything-scholar scholar profile 0000-0001-6187-6610
cli-anything-scholar scholar profile 0000-0001-6187-6610 --stats

# 获取论文列表
cli-anything-scholar scholar works 0000-0001-6187-6610 -n 10
cli-anything-scholar scholar works 0000-0001-6187-6610 --sort date

# 查找相关论文
cli-anything-scholar scholar related 10.1145/3292500.3330671

# 语义主题标注
cli-anything-scholar scholar tag "Attention is All You Need"
cli-anything-scholar scholar tag "Deep Learning" --abstract "We propose..."

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

## 命令一览

| 命令 | 说明 |
|------|------|
| `scholar search <name>` | 按姓名搜索学者 |
| `scholar profile <orcid\|id>` | 查看学者详情 |
| `scholar works <orcid\|id>` | 获取论文列表 |
| `scholar related <doi\|id>` | 查找相关论文 |
| `scholar tag <title>` | 语义主题标注 |

## 全局选项

- `--json` — 输出机器可读的 JSON 格式

## API

基于 [OpenAlex](https://openalex.org/) 公开 API，无需注册，无需鉴权。

## 测试

```bash
# 单元测试（无网络）
pytest cli_anything/scholar/tests/test_core.py -v

# 端到端测试（需要网络）
pytest cli_anything/scholar/tests/test_full_e2e.py -v -m e2e
```
