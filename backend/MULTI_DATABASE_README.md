# 多数据库管理系统

这是一个为 ACWL-AI 项目设计的多数据库管理系统，支持在单个应用中连接和管理多个数据库，提供智能路由、连接池管理和统一的CRUD接口。

## 🌟 主要特性

- **多数据库支持**：支持 MySQL、PostgreSQL、SQLite、Oracle、SQL Server 等多种数据库
- **智能路由**：根据业务标签、表名、用户ID等条件自动选择合适的数据库
- **连接池管理**：为每个数据库维护独立的连接池，避免连接泄漏
- **统一CRUD接口**：提供统一的增删改查操作接口
- **REST API**：完整的HTTP API接口，支持数据库管理和查询操作
- **配置管理**：灵活的配置管理，支持动态添加和删除数据库
- **健康监控**：实时监控数据库连接状态

## 📁 文件结构

```
backend/
├── app/
│   ├── core/
│   │   ├── multi_db_config.py      # 多数据库配置管理
│   │   ├── multi_db_manager.py     # 多数据库连接管理器
│   │   └── db_router.py            # 智能数据库路由器
│   ├── services/
│   │   └── multi_db_service.py     # 多数据库CRUD服务
│   └── api/
│       └── v1/
│           └── multi_database.py   # 多数据库API端点
├── multi_db_config.json            # 数据库配置文件
├── multi_database_usage_example.py # 使用示例
└── MULTI_DATABASE_README.md        # 本文档
```

## 🚀 快速开始

### 1. 配置数据库

编辑 `multi_db_config.json` 文件，添加你的数据库配置：

```json
{
  "databases": {
    "primary": {
      "name": "primary",
      "type": "mysql",
      "host": "localhost",
      "port": 3306,
      "username": "root",
      "password": "your_password",
      "database": "main_db",
      "business_tags": ["primary", "main"],
      "is_primary": true,
      "is_active": true
    },
    "analytics": {
      "name": "analytics",
      "type": "mysql",
      "host": "analytics-server",
      "port": 3306,
      "username": "analytics_user",
      "password": "analytics_password",
      "database": "analytics_db",
      "business_tags": ["analytics", "reporting"],
      "is_primary": false,
      "is_active": true
    }
  }
}
```

### 2. 初始化多数据库管理器

```python
from app.core.multi_db_manager import get_multi_db_manager

# 获取多数据库管理器
db_manager = await get_multi_db_manager()

# 测试所有数据库连接
connection_results = await db_manager.test_all_connections()
print(connection_results)
```

### 3. 使用智能路由

```python
from app.core.db_router import route_database

# 根据业务标签路由
connection_manager = await route_database(
    business_tag="analytics",
    operation_type="read"
)

# 使用连接管理器执行查询
async with connection_manager.get_async_session() as session:
    result = await session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
```

### 4. 执行SQL查询

```python
from app.services.multi_db_service import execute_sql

# 简单查询
result = await execute_sql(
    query="SELECT * FROM users WHERE status = :status",
    params={"status": "active"},
    business_tag="user_management"
)

# 指定数据库查询
result = await execute_sql(
    query="SELECT * FROM analytics_data",
    db_name="analytics"
)
```

### 5. 使用CRUD服务

```python
from app.services.multi_db_service import MultiDatabaseCRUDService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# 创建CRUD服务
user_service = MultiDatabaseCRUDService[User, UserCreate, UserUpdate](User)

# 创建用户
new_user = await user_service.create(
    UserCreate(name="张三", email="zhangsan@example.com"),
    business_tag="user_management"
)

# 查询用户
user = await user_service.get(id=1, business_tag="user_management")

# 更新用户
updated_user = await user_service.update(
    id=1,
    obj_in=UserUpdate(name="李四"),
    business_tag="user_management"
)
```

## 🔧 API 接口

### 数据库管理

```bash
# 获取所有数据库配置
GET /api/v1/multi-db/databases

# 创建新数据库配置
POST /api/v1/multi-db/databases
{
  "name": "new_db",
  "type": "mysql",
  "host": "localhost",
  "port": 3306,
  "username": "root",
  "password": "password",
  "database": "new_database",
  "business_tags": ["new", "test"]
}

# 更新数据库配置
PUT /api/v1/multi-db/databases/{db_name}

# 删除数据库配置
DELETE /api/v1/multi-db/databases/{db_name}

# 测试数据库连接
GET /api/v1/multi-db/databases/{db_name}/test

# 测试所有数据库连接
GET /api/v1/multi-db/databases/test-all
```

### SQL查询

```bash
# 执行SQL查询
POST /api/v1/multi-db/query
{
  "query": "SELECT * FROM users WHERE id = :user_id",
  "params": {"user_id": 1},
  "business_tag": "user_management"
}

# 批量执行SQL查询
POST /api/v1/multi-db/query/batch
{
  "queries": [
    {"query": "SELECT COUNT(*) FROM users", "operation_type": "read"},
    {"query": "SELECT COUNT(*) FROM orders", "operation_type": "read"}
  ],
  "business_tag": "analytics"
}

# 简单查询（GET方式）
GET /api/v1/multi-db/query/simple?sql=SELECT 1&db_name=primary
```

### 路由和监控

```bash
# 获取路由信息
GET /api/v1/multi-db/routing/info

# 根据标签获取数据库
GET /api/v1/multi-db/databases/by-tag/{tag}

# 健康检查
GET /api/v1/multi-db/health
```

## 🎯 路由策略

系统支持多种路由策略：

### 1. 基于标签的路由（默认）

```python
# 配置数据库时设置业务标签
business_tags = ["user_management", "read_replica"]

# 查询时指定业务标签
result = await execute_sql(
    query="SELECT * FROM users",
    business_tag="user_management"
)
```

### 2. 负载均衡路由

```python
from app.core.db_router import SmartDatabaseRouter, RoutingStrategy

# 创建负载均衡路由器
router = SmartDatabaseRouter(db_manager, RoutingStrategy.LOAD_BALANCE)
```

### 3. 自定义路由规则

```python
# 添加自定义路由规则
def custom_rule(context):
    if context.user_id and context.user_id % 2 == 0:
        return True
    return False

router.add_routing_rule({
    "condition": custom_rule,
    "target_db": "analytics",
    "priority": 10
})
```

## 📊 监控和健康检查

### 连接状态监控

```python
from app.services.multi_db_service import DatabaseSwitchService

# 测试所有数据库连接
results = await DatabaseSwitchService.test_all_connections()
for db_name, is_connected in results.items():
    print(f"{db_name}: {'✅' if is_connected else '❌'}")
```

### 健康检查API

访问 `/api/v1/multi-db/health` 获取完整的健康状态报告：

```json
{
  "status": "healthy",
  "total_databases": 3,
  "healthy_databases": 3,
  "health_percentage": 100.0,
  "connection_status": {
    "primary": true,
    "analytics": true,
    "logs": true
  },
  "routing_info": {
    "strategy": "tag_based",
    "rules_count": 2,
    "available_databases": ["primary", "analytics", "logs"]
  }
}
```

## 🔒 安全考虑

1. **密码加密**：数据库密码在配置文件中应该加密存储
2. **连接限制**：合理设置连接池大小，避免数据库连接耗尽
3. **SQL注入防护**：使用参数化查询，避免SQL注入攻击
4. **权限控制**：为不同的数据库配置不同的用户权限

## 🛠️ 扩展和自定义

### 添加新的数据库类型

1. 在 `DatabaseType` 枚举中添加新类型
2. 在 `DatabaseConfig.connection_url` 属性中添加连接URL生成逻辑
3. 安装相应的数据库驱动

### 自定义路由策略

```python
from app.core.db_router import DatabaseRouter

class CustomRouter(DatabaseRouter):
    async def route(self, context):
        # 实现自定义路由逻辑
        if context.table_name.startswith('log_'):
            return 'logs'
        elif context.operation_type == 'read':
            return 'read_replica'
        else:
            return 'primary'
```

## 📝 最佳实践

1. **读写分离**：将读操作路由到只读副本，写操作路由到主数据库
2. **业务隔离**：不同业务模块使用不同的数据库或schema
3. **连接池优化**：根据实际负载调整连接池大小
4. **监控告警**：定期检查数据库连接状态，设置告警机制
5. **备份策略**：为每个数据库制定合适的备份策略

## 🐛 故障排除

### 常见问题

1. **连接失败**：检查数据库配置、网络连接和防火墙设置
2. **连接池耗尽**：增加连接池大小或检查连接泄漏
3. **路由错误**：检查业务标签配置和路由规则
4. **性能问题**：优化SQL查询、调整连接池参数

### 调试模式

```python
import logging
logging.getLogger('app.core.multi_db_manager').setLevel(logging.DEBUG)
logging.getLogger('app.core.db_router').setLevel(logging.DEBUG)
```

## 📚 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 异步支持](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [aiomysql 文档](https://aiomysql.readthedocs.io/)

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个多数据库管理系统！

## 📄 许可证

本项目采用 MIT 许可证。