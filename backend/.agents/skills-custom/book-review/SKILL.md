---
name: book-review
description: 当用户需要进行图书审读、敏感词检测、历史审读记录检索、ISBN/书名/作者/出版社核查、或对 PDF 图书内容做审读时使用。支持通过本地大模型执行多轮工具调用，并可通过 HTTP API 暴露审读能力。
license: Internal project skill
---

# Book Review Skill

该技能将你现有的 `book_review` 项目按 `.agents` 结构封装为可复用技能包。

## 适用场景

- 图书内容审读（文本/元数据）
- 敏感词库查询与扫描
- 历史审读库（Doris）检索
- PDF 图书解析
- 通过 FastAPI 提供审读接口

## 目录说明

- `scripts/`：核心执行代码（已从原 `book_review` 项目迁移）
- `references/`：使用说明与流程文档

## 快速使用

先查看脚本帮助或入口文件：

- CLI 审读入口：`scripts/main.py`
- API 服务入口：`scripts/api.py`

常见启动方式（在该 skill 根目录下执行）：

```bash
python scripts/main.py review "ISBN:9781760763992,正题名:About Face，作者:Amber Creswell Bell，出版社：Thames & Hudson Australia"
python scripts/main.py pdf /path/to/book.pdf
python scripts/main.py interactive
uvicorn scripts.api:app --host 0.0.0.0 --port 5080 --reload
```

## 环境依赖

依赖列表位于 `scripts/requirements.txt`。

涉及配置项：

- Doris：`DORIS_*`
- MySQL：`MYSQL_*`
- LLM：`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`
- MinIO：`MINIO_*`

具体变量见 `scripts/config.py`。

## 可用能力（由代码定义）

工具定义位于 `scripts/skills.py`，包含：

- `query_sensitive_words`
- `sensitive_words_check`
- `query_book_review`
- `pdf_parse`
- `image_analysis`

## 注意事项

- 该技能保留了原项目执行逻辑，主要做结构重组，不改变核心业务行为。
- 若需进一步“技能化”（例如拆分更轻量脚本、统一输出协议），可在此基础上继续迭代。
