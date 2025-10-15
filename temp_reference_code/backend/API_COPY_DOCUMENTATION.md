# API复制功能文档

## 功能概述

API复制功能允许管理员将现有的自定义API复制到其他客户，包括API的所有配置和字段定义。这个功能特别适用于以下场景：

- 为新客户快速创建相似的API
- 复用成功的API模板
- 批量部署标准化API

## 功能特性

✅ **完整复制**：复制API的所有配置信息，包括：
- API基本信息（名称、代码、描述等）
- HTTP方法和状态
- 频率限制设置
- 认证要求
- 所有字段定义和验证规则

✅ **安全检查**：
- 验证目标客户权限
- 检查新API代码是否冲突
- 确保客户API数量限制

✅ **自动处理**：
- 自动生成新的API URL
- 更新客户API计数
- 保持字段排序和关联关系

## API接口

### 复制API

**端点**: `POST /admin/apis/{api_id}/copy`

**权限**: 管理员

**路径参数**:
- `api_id` (int): 要复制的源API的ID

**请求体**:
```json
{
  "target_customer_id": 123,
  "new_api_code": "new_api_code",
  "new_api_name": "新API名称"
}
```

**字段说明**:
- `target_customer_id`: 目标客户ID（必填）
- `new_api_code`: 新API的代码，必须符合格式要求（必填）
- `new_api_name`: 新API的名称（必填）

**响应示例**:
```json
{
  "id": 456,
  "customer_id": 123,
  "api_name": "新API名称",
  "api_code": "new_api_code",
  "api_url": "/api/v1/custom/APP_XXXXX/new_api_code",
  "api_description": "复制的API描述",
  "http_method": "POST",
  "status": true,
  "rate_limit": 100,
  "require_authentication": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

## 使用示例

### 1. 基本复制操作

```bash
curl -X POST "http://localhost:8000/admin/apis/123/copy" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "target_customer_id": 456,
    "new_api_code": "customer_data_v2",
    "new_api_name": "客户数据API v2"
  }'
```

### 2. Python代码示例

```python
import requests

# 复制API
response = requests.post(
    "http://localhost:8000/admin/apis/123/copy",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_ADMIN_TOKEN"
    },
    json={
        "target_customer_id": 456,
        "new_api_code": "customer_data_v2",
        "new_api_name": "客户数据API v2"
    }
)

if response.status_code == 200:
    copied_api = response.json()
    print(f"API复制成功，新API ID: {copied_api['id']}")
    print(f"新API URL: {copied_api['api_url']}")
else:
    print(f"复制失败: {response.text}")
```

## 错误处理

### 常见错误码

- `404`: 源API不存在
- `400`: 请求参数错误
  - API代码格式不正确
  - API代码已存在冲突
  - 目标客户不存在
- `403`: 权限不足
- `422`: 客户API数量超出限制

### 错误响应示例

```json
{
  "detail": "API代码 'existing_code' 在客户 123 中已存在"
}
```

## 验证规则

### API代码格式要求
- 只能包含字母、数字和下划线
- 长度在3-50个字符之间
- 不能以数字开头
- 在目标客户中必须唯一

### 业务规则
- 源API必须存在且可访问
- 目标客户必须存在且状态正常
- 目标客户的API数量不能超过限制
- 管理员必须有相应权限

## 测试

项目包含完整的测试脚本 `test_api_copy.py`，可以验证API复制功能的正确性：

```bash
cd backend
python test_api_copy.py
```

测试脚本会：
1. 创建测试客户
2. 创建源API和字段
3. 执行API复制
4. 验证复制结果的完整性

## 注意事项

1. **数据一致性**: 复制操作在数据库事务中执行，确保数据一致性
2. **性能考虑**: 复制包含大量字段的API可能需要较长时间
3. **权限管理**: 只有管理员可以执行API复制操作
4. **审计日志**: 所有复制操作都会记录在系统日志中

## 相关文件

- **服务层**: `app/services/api.py` - `CustomApiService.copy_api()`
- **API路由**: `app/api/v1/endpoints/admin.py` - `/apis/{api_id}/copy`
- **数据模型**: `app/schemas/api.py` - `CustomApiCopy`
- **测试脚本**: `test_api_copy.py`

---

*最后更新: 2024年1月*