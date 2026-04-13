---
name: book-review
description: 当用户需要进行图书审读、敏感词检测、历史审读记录检索、ISBN/书名/作者/出版社核查、或对 PDF 图书内容做审读时使用。支持通过本地大模型执行多轮工具调用，并可通过 HTTP API 暴露审读能力。
license: Internal project skill
---

# Book Review Skill

用于图书元数据、正文片段、PDF 文件等场景的图书审读任务。该技能通过本地大模型结合敏感词库、历史审读库和文件解析能力，生成审读结论。

## 注意！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！

- 无论什么情况都不要返回审读报告,只返回5个风险等级中的一个即可(极高风险、高风险、中风险、低风险、安全)。

## 何时触发

- 用户要求对图书进行风险审读、敏感词检测、历史记录核查
- 用户提供 ISBN / 书名 / 作者 / 出版社
- 用户要求审读本地 PDF 文件内容
- 用户要求通过 HTTP API 方式调用审读服务

## 核心能力（由代码定义）

- `query_sensitive_words`
- `sensitive_words_check`
- `query_book_review`

工具 schema 定义见 `scripts/skills.py`，执行实现见 `scripts/skill_executor.py`。

## 规则分层

- 运行时强约束与结论判级：`scripts/context_manager.py`
- 技能触发、入口导航、使用边界：当前 `SKILL.md`
- 详细流程与判级对照表：`references/workflows.md`

## 目录导航

- `scripts/main.py`：CLI 入口（`review` / `pdf` / `interactive` / `init-db`）
- `scripts/api.py`：FastAPI 服务入口（`/health`、`/review`、`/review/pdf`）
- `scripts/agent.py`：Agent 循环与工具调用
- `scripts/context_manager.py`：system prompt 与数据库加载
- `references/workflows.md`：初始化、工作流、结论等级、接口速查

## 环境依赖

- 依赖列表：`scripts/requirements.txt`
- 关键配置：`scripts/config.py`

## 使用原则

- 先理解用户输入属于哪一类任务：元数据审读、正文审读、PDF 审读、服务启动/调用、结果解释。
- 根据任务类型自由决定是否需要调用脚本，以及应调用哪个脚本。
- 若用户提供的是非结构化信息，可先整理为适合脚本或工具调用的规范化输入。
- 不要把 `main.py review` 当成固定唯一入口；只有当任务确实适合 CLI 审读时才使用。
- 若用户目标是启动/访问 HTTP 服务，优先考虑 `scripts/api.py` 对应能力，而不是强行走 CLI。
- 若仅需解释已有审读结果、分析结论或回答流程问题，可以不执行脚本，直接基于文档与上下文回答。

## 输入规范化建议

当用户输入不够规整时，可以先做必要整理，再决定是否调用脚本。例如：

- 将 ISBN、书名、作者、出版社整理为结构化元数据
- 将 PDF 路径识别为文件审读请求
- 将“启动 API / 停止 API / 怎么调用接口”识别为服务操作或说明请求
- 将已有审读报告识别为“总结/解释”任务，而不是再次发起审读


## 输出要求

- 最终回答应以用户真正需要的结果为中心。
- 如果已经执行脚本或工具，应优先总结最终结论，而不是堆叠中间过程。
- 风险等级可使用以下五档之一：`极高风险`、`高风险`、`中风险`、`低风险`、`安全`。
- 是否只返回等级、还是返回“等级 + 简要理由”、或完整报告，应根据用户当前请求决定，不要一律写死。


