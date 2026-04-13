# 技能调用接口文档

本文档说明 ACWL-AI 项目中技能调用相关接口的使用方式，包括：

- Bearer Token 调用
- API Key 调用
- 获取技能名列表
- 统一请求/响应格式
- 典型 `curl` 示例

## 1. 基础信息

- 服务地址：`http://127.0.0.1:8082`
- API 前缀：`/api/v1`
- 技能接口基础路径：`/api/v1/agents`

## 2. 认证方式

### 2.1 Bearer Token 模式
适用于平台内部前端或已登录用户。

请求头：

```http
Authorization: Bearer <TOKEN>
Content-Type: application/json
```

### 2.2 API Key 模式
适用于第三方系统、脚本或无需登录令牌的对接方式。

请求头：

```http
X-API-Key: <AGENT_SKILL_API_KEY>
Content-Type: application/json
```

后端配置项：

```env
AGENT_SKILL_API_KEY=your-strong-api-key
```

> 修改配置后需要重启后端服务。

---

## 3. 接口总览

| 接口 | 方法 | 认证方式 | 说明 |
|---|---|---|---|
| `/api/v1/agents/tools/execute` | POST | Bearer Token | 通过自然语言 + 技能列表执行技能 |
| `/api/v1/agents/tools/{skill_name}/invoke` | POST | Bearer Token | 按技能名直接调用单个技能，传结构化参数 |
| `/api/v1/agents/public/tools/{skill_name}/invoke` | POST | API Key | 按技能名调用单个技能，但请求模式与 `/tools/execute` 一致 |
| `/api/v1/agents/public/tools/names` | GET | API Key | 获取所有已启用技能名 |

---

## 4. Bearer Token：自然语言执行技能

### 4.1 接口

- `POST /api/v1/agents/tools/execute`

### 4.2 请求体

```json
{
  "prompt": "请把儿童图书书名 The Very Hungry Caterpillar 翻译成中文，要有童趣",
  "skill_names": ["kids-book-translator"],
  "model_service_config_id": 1
}
```

### 4.3 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `prompt` | string | 是 | 用户提问/自然语言指令 |
| `skill_names` | string[] | 是 | 启用的技能名称列表 |
| `model_name` | string | 否 | 指定模型名称，对应 `acwl_model_service_configs.model_name`；不传则尝试使用第一个激活配置 |

### 4.4 curl 示例

```bash
curl -X POST "http://127.0.0.1:8082/api/v1/agents/tools/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "prompt": "请把儿童图书书名 The Very Hungry Caterpillar 翻译成中文，要有童趣",
    "skill_names": ["kids-book-translator"],
    "model_name": "qwen-max"
  }'
```

### 4.5 返回示例

```json
{
  "result": "好饿好饿的毛毛虫"
}
```

---

## 5. Bearer Token：结构化直调技能

> 这个接口保留原有结构化参数模式，适合已有直调脚本型技能。

### 5.1 接口

- `POST /api/v1/agents/tools/{skill_name}/invoke`

### 5.2 请求体

```json
{
  "params": {
    "key": "value"
  }
}
```

### 5.3 示例

```bash
curl -X POST "http://127.0.0.1:8082/api/v1/agents/tools/book-review/invoke" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{
    "params": {
      "isbn": "9781760763992",
      "title": "About Face",
      "author": "Amber Creswell Bell",
      "publisher": "Thames & Hudson Australia"
    }
  }'
```

### 5.4 返回示例

```json
{
  "skill_name": "book-review",
  "result": "...技能执行结果..."
}
```

---

## 6. API Key：按技能名发起大模型提问

> 这个接口已经调整为**和 `/api/v1/agents/tools/execute` 一样的提问形式**，只是：
>
> - 路径里只传一个 `skill_name`
> - 不需要 Bearer Token
> - 使用 `X-API-Key` 认证

### 6.1 接口

- `POST /api/v1/agents/public/tools/{skill_name}/invoke`

### 6.2 统一请求体

```json
{
  "prompt": "请将儿童图书书名 About Face 翻译成中文，要求符合童书命名风格，富有童趣。",
  "model_service_config_id": 1
}
```

### 6.3 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `prompt` | string | 是 | 用户提问/自然语言指令 |
| `model_name` | string | 否 | 指定模型名称，对应 `acwl_model_service_configs.model_name`；不传则尝试使用第一个激活配置 |

### 6.4 与 `/tools/execute` 的关系

等价理解为：

```json
{
  "prompt": "你的提问",
  "skill_names": ["路径中的 skill_name"],
  "model_service_config_id": 1
}
```

也就是说，下面这个请求：

```http
POST /api/v1/agents/public/tools/kids-book-translator/invoke
```

请求体：

```json
{
  "prompt": "请将儿童图书书名 About Face 翻译成中文，要求符合童书命名风格，富有童趣。",
  "model_service_config_id": 1
}
```

在执行逻辑上等价于：

```json
{
  "prompt": "请将儿童图书书名 About Face 翻译成中文，要求符合童书命名风格，富有童趣。",
  "skill_names": ["kids-book-translator"],
  "model_service_config_id": 1
}
```

### 6.5 curl 示例：儿童图书标题翻译

```bash
curl -X POST "http://127.0.0.1:8082/api/v1/agents/public/tools/kids-book-translator/invoke" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-strong-api-key" \
  -d '{
    "prompt": "请将儿童图书书名 About Face 翻译成中文，要求符合童书命名风格，富有童趣。",
    "model_name": "qwen-max"
  }'
```

### 6.6 curl 示例：图书审读

```bash
curl -X POST "http://127.0.0.1:8082/api/v1/agents/public/tools/book-review/invoke" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-strong-api-key" \
  -d '{
    "prompt": "请审读图书：ISBN:9781760763992,正题名:About Face,作者:Amber Creswell Bell,出版社:Thames & Hudson Australia",
    "model_name": "qwen-max"
  }'
```

### 6.7 curl 示例：PDF 元数据解析

```bash
curl -X POST "http://127.0.0.1:8082/api/v1/agents/public/tools/book-pdf-meta-parser/invoke" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-strong-api-key" \
  -d '{
    "prompt": "请解析这个 PDF 的图书元数据：http://example.com/book.pdf",
    "model_name": "qwen-max"
  }'
```

### 6.8 返回示例

```json
{
  "skill_name": "kids-book-translator",
  "result": "适合的中文书名"
}
```

---

## 7. 获取所有技能名（API Key）

### 7.1 接口

- `GET /api/v1/agents/public/tools/names`

### 7.2 curl 示例

```bash
curl -X GET "http://127.0.0.1:8082/api/v1/agents/public/tools/names" \
  -H "X-API-Key: your-strong-api-key"
```

### 7.3 返回示例

```json
{
  "skills": [
    "book-pdf-meta-parser",
    "book-review",
    "kids-book-translator"
  ]
}
```

---

## 8. 当前推荐用法

### 内部前端 / 已登录用户
优先使用：

- `/api/v1/agents/tools/execute`
- `/api/v1/agents/tools/{skill_name}/invoke`

### 第三方系统 / 外部脚本
优先使用：

- `/api/v1/agents/public/tools/names`
- `/api/v1/agents/public/tools/{skill_name}/invoke`

推荐流程：

1. 先通过 `/public/tools/names` 获取技能名
2. 再通过 `/public/tools/{skill_name}/invoke` 发起自然语言提问
3. 使用 `X-API-Key` 完成认证，无需登录令牌

---

## 9. 常见错误码

| 状态码 | 含义 |
|---|---|
| `400` | 请求参数错误，技能被禁用，或未找到可用模型配置 |
| `401` | API Key 无效 |
| `404` | 技能不存在，或指定模型配置不存在 |
| `500` | 服务内部错误，或 `AGENT_SKILL_API_KEY` 未配置 |
