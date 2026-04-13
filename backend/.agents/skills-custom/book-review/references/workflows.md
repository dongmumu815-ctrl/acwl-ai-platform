# Book Review Skill - 工作流与规则

## 目录

- 初始化与启动
- 审读标准流程
- 技能调用规则
- 结论等级映射
- 接口速查
- 模块关系

## 初始化与启动

1. 安装依赖
   - `pip install -r scripts/requirements.txt`
2. 配置环境变量（或 `scripts/config.py` 中对应配置项）
   - Doris：`DORIS_*`
   - MySQL：`MYSQL_*`
   - LLM：`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`
   - MinIO：`MINIO_*`
3. 启动方式
   - CLI：`python scripts/main.py review "..."`
   - PDF：`python scripts/main.py pdf /path/to/file.pdf`
   - 交互：`python scripts/main.py interactive`
   - API：`uvicorn scripts.api:app --host 0.0.0.0 --port 5080 --reload`

## 审读标准流程

按以下顺序执行：

1. 查询敏感词库：对 ISBN、书名、作者、出版社逐一查询
2. 文本扫描：必要时执行正文敏感词扫描
3. 查询历史审读：读取历史结论（`review_lib_type_cn`）
4. 文件解析：如有文件路径，解析 PDF 或图片
5. 生成报告：输出命中详情 + 历史结论 + 最终结论等级

## 技能调用规则

### 1) query_sensitive_words

- ISBN 查询：使用 `isbn` 参数，`use_tokenize=false`
- 书名/作者/出版社查询：使用 `keyword` 参数，`use_tokenize=true`
- 必须覆盖 ISBN、书名、作者、出版社四项，不可缺失

### 2) sensitive_words_check

- 将待扫描文本合并为一次调用，避免分段多次调用
- 单次建议文本长度不超过 5000 字符
- 文本过长时提取标题、摘要、作者、机构等关键段落

### 3) query_book_review

- 至少提供 ISBN / title / author / publisher 之一
- 重点关注返回字段 `review_lib_type_cn`

### 4) pdf_parse / image_analysis

- 提供本地文件路径时调用
- PDF 场景优先 `pdf_parse`，插图单文件分析使用 `image_analysis`

## 结论等级映射

| 等级 | 含义 | 适用情形 |
|------|------|----------|
| critical | 极高风险 | 命中 S1/S2，或历史结论为禁发类（实物禁发、电子禁发、采集禁发、客户禁发） |
| high | 高风险 | 命中 S3，或历史结论为问题类（电子问题、敏感文章） |
| medium | 中风险 | 命中 S4，或历史结论为限阅类（实物限阅、采集限阅、客户限阅） |
| low | 低风险 | 命中 S5，或仅存在轻度不当用词 |
| safe | 安全 | 未命中敏感词，且历史结论为通过类（实物通过、电子通过、订单通过、文章通过） |

敏感等级说明：

- S1：绝对禁词
- S2：禁词
- S3：高敏感词
- S4：敏感词
- S5：辅助词

## 接口速查

- 健康检查：`GET /health`
- 文本/元数据审读：`POST /review`
- PDF 审读：`POST /review/pdf`

`POST /review` 支持 `skills` 参数控制可调用工具范围：

- `null` / 不传：开放全部工具
- `[]`：禁用全部工具
- 指定列表：仅开放列表内工具

## 模块关系

- `scripts/agent.py`：Agent 循环、工具调用、报告生成
- `scripts/context_manager.py`：系统提示词与数据库连通性
- `scripts/skills.py`：工具 schema
- `scripts/skill_executor.py`：工具执行实现
- `scripts/api.py`：HTTP API

## 一致性说明

若本文与运行行为存在差异，以 `scripts/context_manager.py` 与实际代码实现为准。
