# Book Review Skill - 工作流说明

## 1. 初始化

- 配置环境变量（数据库、模型、对象存储）
- 安装依赖：`pip install -r scripts/requirements.txt`

## 2. CLI 模式

- 文本/元数据审读：
  - `python scripts/main.py review "..."`
- PDF 审读：
  - `python scripts/main.py pdf /path/to/file.pdf`
- 交互模式：
  - `python scripts/main.py interactive`

## 3. API 模式

- 启动服务：
  - `uvicorn scripts.api:app --host 0.0.0.0 --port 5080 --reload`
- 健康检查：`GET /health`
- 审读接口：`POST /review`

## 4. 核心模块关系

- `agent.py`：Agent 循环与工具调用
- `context_manager.py`：知识库加载（Doris/MySQL）
- `skills.py`：工具 schema
- `skill_executor.py`：工具执行器
- `api.py`：HTTP 接口
