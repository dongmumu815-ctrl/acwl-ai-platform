# 项目管理模块

## 概述

项目管理模块是ACWL AI数据平台的核心功能之一，提供了完整的项目生命周期管理、成员权限控制、数据源分配和资源配额管理功能。通过项目管理模块，可以有效地组织和管理数据科学项目，确保资源的合理分配和权限的精确控制。

## 核心功能

### 1. 项目管理
- **项目创建**：支持创建不同类型的项目（开发、生产、研究、演示）
- **项目配置**：设置项目基本信息、时间范围、优先级和标签
- **项目状态管理**：支持活跃、暂停、完成、归档等状态
- **项目模板**：提供预定义的项目模板，快速创建标准化项目

### 2. 成员权限管理
- **角色定义**：所有者、管理员、开发者、访客四种角色
- **权限控制**：精细化的权限控制，包括读取、写入、管理等权限
- **成员邀请**：支持邀请用户加入项目并分配角色
- **权限继承**：基于角色的权限继承机制

### 3. 数据源分配
- **数据源关联**：将数据源分配给项目使用
- **访问类型控制**：只读、读写、管理员三种访问类型
- **权限隔离**：确保项目间数据源访问的隔离性
- **使用监控**：监控数据源的使用情况和性能

### 4. 资源配额管理
- **配额设置**：设置CPU、内存、存储、GPU等资源配额
- **使用监控**：实时监控资源使用情况
- **配额重置**：支持按日、周、月重置配额
- **超限告警**：资源使用超限时自动告警

### 5. 活动日志
- **操作记录**：记录所有项目相关的操作活动
- **审计追踪**：提供完整的审计追踪功能
- **活动分析**：分析项目活动趋势和模式

## 数据模型

### 项目表 (acwl_projects)
```sql
CREATE TABLE acwl_projects (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    project_type ENUM('development', 'production', 'research', 'demo'),
    status ENUM('active', 'paused', 'completed', 'archived'),
    priority ENUM('low', 'medium', 'high', 'critical'),
    start_date DATE,
    end_date DATE,
    tags JSON,
    settings JSON,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);
```

### 项目成员表 (acwl_project_members)
```sql
CREATE TABLE acwl_project_members (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    user_id INT NOT NULL,
    role ENUM('owner', 'admin', 'developer', 'viewer'),
    permissions JSON,
    added_by INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE KEY unique_project_user (project_id, user_id)
);
```

### 项目数据源关联表 (acwl_project_datasources)
```sql
CREATE TABLE acwl_project_datasources (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    datasource_id INT NOT NULL,
    access_type ENUM('read_only', 'read_write', 'admin'),
    assigned_by INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE KEY unique_project_datasource (project_id, datasource_id)
);
```

## API接口

### 项目管理接口

#### 创建项目
```http
POST /api/v1/projects/
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "数据分析项目",
    "description": "客户行为数据分析项目",
    "project_type": "development",
    "priority": "high",
    "start_date": "2024-01-01",
    "end_date": "2024-06-30",
    "tags": ["数据分析", "机器学习"]
}
```

#### 获取项目列表
```http
GET /api/v1/projects/?page=1&size=10&status=active
Authorization: Bearer <token>
```

#### 获取项目详情
```http
GET /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

#### 更新项目
```http
PUT /api/v1/projects/{project_id}
Content-Type: application/json
Authorization: Bearer <token>

{
    "name": "更新后的项目名称",
    "description": "更新后的项目描述",
    "status": "paused"
}
```

#### 删除项目
```http
DELETE /api/v1/projects/{project_id}
Authorization: Bearer <token>
```

### 成员管理接口

#### 添加项目成员
```http
POST /api/v1/projects/{project_id}/members
Content-Type: application/json
Authorization: Bearer <token>

{
    "user_id": 123,
    "role": "developer"
}
```

#### 获取项目成员列表
```http
GET /api/v1/projects/{project_id}/members
Authorization: Bearer <token>
```

#### 更新成员角色
```http
PUT /api/v1/projects/{project_id}/members/{user_id}
Content-Type: application/json
Authorization: Bearer <token>

{
    "role": "admin"
}
```

#### 移除项目成员
```http
DELETE /api/v1/projects/{project_id}/members/{user_id}
Authorization: Bearer <token>
```

### 数据源管理接口

#### 分配数据源给项目
```http
POST /api/v1/projects/{project_id}/datasources
Content-Type: application/json
Authorization: Bearer <token>

{
    "datasource_id": 456,
    "access_type": "read_write"
}
```

#### 获取项目数据源列表
```http
GET /api/v1/projects/{project_id}/datasources
Authorization: Bearer <token>
```

### 统计和监控接口

#### 获取项目统计信息
```http
GET /api/v1/projects/{project_id}/stats
Authorization: Bearer <token>
```

#### 获取项目活动日志
```http
GET /api/v1/projects/{project_id}/activities?page=1&size=20
Authorization: Bearer <token>
```

#### 获取项目仪表盘数据
```http
GET /api/v1/projects/dashboard
Authorization: Bearer <token>
```

## 权限模型

### 角色权限矩阵

| 操作 | 所有者 | 管理员 | 开发者 | 访客 |
|------|--------|--------|--------|------|
| 查看项目信息 | ✓ | ✓ | ✓ | ✓ |
| 编辑项目信息 | ✓ | ✓ | ✗ | ✗ |
| 删除项目 | ✓ | ✗ | ✗ | ✗ |
| 添加成员 | ✓ | ✓ | ✗ | ✗ |
| 移除成员 | ✓ | ✓ | ✗ | ✗ |
| 分配数据源 | ✓ | ✓ | ✗ | ✗ |
| 使用数据源 | ✓ | ✓ | ✓ | 只读 |
| 查看活动日志 | ✓ | ✓ | ✓ | ✗ |
| 管理配额 | ✓ | ✓ | ✗ | ✗ |

### 权限检查流程

1. **身份验证**：验证用户身份和令牌有效性
2. **项目存在性检查**：验证项目是否存在且未被删除
3. **成员资格检查**：验证用户是否为项目成员
4. **角色权限检查**：根据用户角色检查操作权限
5. **特殊权限检查**：检查特定资源的特殊权限

## 使用示例

### 创建数据分析项目

```python
import httpx

# 创建项目
project_data = {
    "name": "客户行为分析",
    "description": "分析客户购买行为和偏好",
    "project_type": "research",
    "priority": "high",
    "start_date": "2024-01-01",
    "end_date": "2024-03-31",
    "tags": ["数据分析", "客户行为", "机器学习"]
}

response = httpx.post(
    "http://localhost:8000/api/v1/projects/",
    json=project_data,
    headers={"Authorization": "Bearer your_token"}
)

project = response.json()
project_id = project["id"]

# 添加团队成员
member_data = {
    "user_id": 123,
    "role": "developer"
}

httpx.post(
    f"http://localhost:8000/api/v1/projects/{project_id}/members",
    json=member_data,
    headers={"Authorization": "Bearer your_token"}
)

# 分配数据源
datasource_data = {
    "datasource_id": 456,
    "access_type": "read_write"
}

httpx.post(
    f"http://localhost:8000/api/v1/projects/{project_id}/datasources",
    json=datasource_data,
    headers={"Authorization": "Bearer your_token"}
)
```

### 监控项目状态

```python
# 获取项目统计信息
stats_response = httpx.get(
    f"http://localhost:8000/api/v1/projects/{project_id}/stats",
    headers={"Authorization": "Bearer your_token"}
)

stats = stats_response.json()
print(f"项目成员数: {stats['member_count']}")
print(f"数据源数量: {stats['datasource_count']}")
print(f"活动记录数: {stats['activity_count']}")

# 获取最近活动
activities_response = httpx.get(
    f"http://localhost:8000/api/v1/projects/{project_id}/activities?page=1&size=10",
    headers={"Authorization": "Bearer your_token"}
)

activities = activities_response.json()
for activity in activities["items"]:
    print(f"{activity['created_at']}: {activity['description']}")
```

## 最佳实践

### 1. 项目组织
- 按业务领域或团队组织项目
- 使用有意义的项目名称和描述
- 合理设置项目标签便于分类和搜索
- 定期清理不活跃的项目

### 2. 权限管理
- 遵循最小权限原则
- 定期审查项目成员和权限
- 使用角色而非直接分配权限
- 及时移除离职人员的项目访问权限

### 3. 数据源管理
- 根据实际需要分配数据源访问权限
- 避免给予过高的数据源权限
- 定期审查数据源使用情况
- 监控数据源访问日志

### 4. 资源配额
- 根据项目规模合理设置资源配额
- 定期监控资源使用情况
- 及时调整配额设置
- 设置合理的告警阈值

### 5. 监控和审计
- 定期查看项目活动日志
- 监控异常操作和访问模式
- 建立项目健康度评估机制
- 定期生成项目报告

## 故障排除

### 常见问题

1. **权限不足错误**
   - 检查用户是否为项目成员
   - 验证用户角色是否有足够权限
   - 确认项目状态是否正常

2. **数据源访问失败**
   - 检查数据源是否已分配给项目
   - 验证访问类型是否正确
   - 确认数据源状态是否正常

3. **资源配额超限**
   - 检查当前资源使用情况
   - 调整资源配额设置
   - 优化资源使用策略

### 日志分析

项目管理模块的日志包含以下信息：
- 用户操作记录
- 权限检查结果
- 资源使用情况
- 错误和异常信息

通过分析这些日志，可以快速定位和解决问题。

## 扩展功能

### 计划中的功能
- 项目模板市场
- 自动化工作流
- 项目协作工具集成
- 高级分析和报告
- 项目成本核算
- 多租户支持

### 集成能力
- Git仓库集成
- CI/CD流水线集成
- 第三方工具集成
- 消息通知集成
- 外部认证系统集成