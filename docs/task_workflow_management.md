# 任务和工作流管理系统

## 概述

本系统为ACWL AI数据平台提供了完整的任务管理和工作流编排功能，支持复杂的数据处理、模型训练和业务流程自动化。

## 核心功能

### 1. 工作流管理

#### 工作流定义
- **工作流创建**: 支持可视化工作流设计
- **版本管理**: 工作流版本控制和历史追踪
- **状态管理**: 草稿、激活、停用、归档状态
- **项目关联**: 工作流与项目的关联管理

#### 工作流节点类型
- **START**: 工作流开始节点
- **END**: 工作流结束节点
- **TASK**: 任务执行节点
- **CONDITION**: 条件判断节点
- **PARALLEL**: 并行执行节点
- **MERGE**: 并行合并节点

#### 工作流连接
- **SEQUENCE**: 顺序连接
- **CONDITION**: 条件连接
- **PARALLEL**: 并行连接

### 2. 任务管理

#### 任务类型
- **PYTHON_CODE**: Python代码执行任务
- **SQL_QUERY**: SQL查询任务
- **CONDITION**: 条件判断任务
- **DATA_PROCESSING**: 数据处理任务
- **MODEL_TRAINING**: 模型训练任务
- **MODEL_INFERENCE**: 模型推理任务
- **DATA_VALIDATION**: 数据验证任务
- **NOTIFICATION**: 通知任务

#### 任务优先级
- **LOW**: 低优先级
- **NORMAL**: 普通优先级
- **HIGH**: 高优先级
- **URGENT**: 紧急优先级

#### 任务状态
- **PENDING**: 等待执行
- **RUNNING**: 正在执行
- **COMPLETED**: 执行完成
- **FAILED**: 执行失败
- **CANCELLED**: 已取消
- **PAUSED**: 已暂停

### 3. 执行器管理

#### 执行器分组
- 支持按功能、资源类型等维度对执行器进行分组
- 每个分组可配置不同的资源限制和调度策略

#### 执行器节点
- 分布式执行器节点管理
- 节点健康状态监控
- 动态负载均衡

### 4. 调度系统

#### 触发类型
- **MANUAL**: 手动触发
- **CRON**: 定时触发
- **EVENT**: 事件触发
- **API**: API触发

#### 调度策略
- **ONCE**: 单次执行
- **RECURRING**: 循环执行
- **CONDITIONAL**: 条件执行

#### 错过执行策略
- **DO_NOTHING**: 不执行
- **FIRE_ONCE_NOW**: 立即执行一次
- **FIRE_ALL_MISSED**: 执行所有错过的任务

## API接口

### 工作流管理接口

#### 基础CRUD操作
```
GET    /api/v1/workflows/              # 获取工作流列表
POST   /api/v1/workflows/              # 创建工作流
GET    /api/v1/workflows/{id}          # 获取工作流详情
PUT    /api/v1/workflows/{id}          # 更新工作流
DELETE /api/v1/workflows/{id}          # 删除工作流
```

#### 节点管理
```
GET    /api/v1/workflows/{id}/nodes                    # 获取工作流节点列表
POST   /api/v1/workflows/{id}/nodes                    # 创建工作流节点
PUT    /api/v1/workflows/{workflow_id}/nodes/{node_id} # 更新工作流节点
DELETE /api/v1/workflows/{workflow_id}/nodes/{node_id} # 删除工作流节点
```

#### 连接管理
```
GET    /api/v1/workflows/{id}/connections                          # 获取工作流连接列表
POST   /api/v1/workflows/{id}/connections                          # 创建工作流连接
DELETE /api/v1/workflows/{workflow_id}/connections/{connection_id} # 删除工作流连接
```

#### 实例执行
```
POST   /api/v1/workflows/{id}/execute          # 执行工作流
GET    /api/v1/workflows/instances             # 获取工作流实例列表
GET    /api/v1/workflows/instances/{id}        # 获取工作流实例详情
POST   /api/v1/workflows/instances/{id}/cancel # 取消工作流实例
```

### 任务管理接口

#### 任务定义
```
GET    /api/v1/tasks/definitions/              # 获取任务定义列表
POST   /api/v1/tasks/definitions/              # 创建任务定义
GET    /api/v1/tasks/definitions/{id}          # 获取任务定义详情
PUT    /api/v1/tasks/definitions/{id}          # 更新任务定义
DELETE /api/v1/tasks/definitions/{id}          # 删除任务定义
```

#### 任务执行
```
POST   /api/v1/tasks/definitions/{id}/execute  # 执行任务
GET    /api/v1/tasks/instances/                # 获取任务实例列表
GET    /api/v1/tasks/instances/{id}            # 获取任务实例详情
POST   /api/v1/tasks/instances/{id}/cancel     # 取消任务实例
```

#### 执行器管理
```
GET    /api/v1/tasks/executor-groups/          # 获取执行器分组列表
POST   /api/v1/tasks/executor-groups/          # 创建执行器分组
GET    /api/v1/tasks/executor-nodes/           # 获取执行器节点列表
POST   /api/v1/tasks/executor-nodes/           # 注册执行器节点
```

## 数据库设计

### 核心表结构

#### 工作流相关表
- `acwl_workflows`: 工作流定义表
- `acwl_workflow_nodes`: 工作流节点表
- `acwl_workflow_connections`: 工作流连接表
- `acwl_workflow_instances`: 工作流实例表
- `acwl_workflow_node_instances`: 工作流节点实例表
- `acwl_workflow_schedules`: 工作流调度配置表

#### 任务相关表
- `acwl_task_definitions`: 任务定义表
- `acwl_task_templates`: 任务模板表
- `acwl_task_dependencies`: 任务依赖表
- `acwl_task_instances`: 任务实例表
- `acwl_task_executions`: 任务执行记录表
- `acwl_task_logs`: 任务日志表
- `acwl_task_results`: 任务结果表

#### 执行器相关表
- `acwl_executor_groups`: 执行器分组表
- `acwl_executor_nodes`: 执行器节点表
- `acwl_task_schedules`: 任务调度配置表

## 使用示例

### 1. 创建数据处理工作流

```python
# 创建工作流
workflow_data = {
    "name": "数据ETL工作流",
    "description": "从数据源提取、转换并加载数据",
    "project_id": 1
}
workflow = await create_workflow(workflow_data)

# 创建开始节点
start_node = await create_workflow_node(workflow.id, {
    "name": "开始",
    "node_type": "START",
    "position_x": 100,
    "position_y": 100
})

# 创建数据提取任务节点
extract_node = await create_workflow_node(workflow.id, {
    "name": "数据提取",
    "node_type": "TASK",
    "position_x": 300,
    "position_y": 100,
    "config": {
        "task_type": "SQL_QUERY",
        "sql": "SELECT * FROM source_table",
        "timeout": 3600
    }
})

# 创建连接
connection = await create_workflow_connection(workflow.id, {
    "source_node_id": start_node.id,
    "target_node_id": extract_node.id,
    "connection_type": "SEQUENCE"
})
```

### 2. 执行工作流

```python
# 执行工作流
instance = await execute_workflow(workflow.id, {
    "input_data": {
        "source_database": "production",
        "target_database": "warehouse"
    },
    "priority": "HIGH"
})

# 监控执行状态
while instance.status in ["PENDING", "RUNNING"]:
    instance = await get_workflow_instance(instance.id)
    print(f"工作流状态: {instance.status}")
    await asyncio.sleep(5)

print(f"工作流执行完成，最终状态: {instance.status}")
```

### 3. 创建定时任务

```python
# 创建任务定义
task_def = await create_task_definition({
    "name": "每日数据同步",
    "description": "每天凌晨同步数据",
    "task_type": "DATA_PROCESSING",
    "executor_group_id": 1,
    "config": {
        "script_path": "/scripts/daily_sync.py",
        "timeout": 7200
    }
})

# 创建调度配置
schedule = await create_task_schedule({
    "task_definition_id": task_def.id,
    "name": "每日凌晨执行",
    "trigger_type": "CRON",
    "cron_expression": "0 2 * * *",
    "timezone": "Asia/Shanghai",
    "is_active": True
})
```

## 部署和配置

### 1. 数据库迁移

```bash
# 执行数据库迁移脚本
mysql -u username -p database_name < database/migrations/add_task_workflow_tables.sql
```

### 2. 启动服务

```bash
# 启动FastAPI服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 配置执行器

```python
# 注册执行器节点
executor_node = {
    "name": "worker-01",
    "host": "192.168.1.100",
    "port": 8001,
    "executor_group_id": 1,
    "max_concurrent_tasks": 10,
    "supported_task_types": ["PYTHON_CODE", "SQL_QUERY", "DATA_PROCESSING"]
}
```

## 监控和日志

### 1. 任务执行监控
- 实时任务状态监控
- 执行时间统计
- 成功率分析
- 资源使用情况

### 2. 日志管理
- 结构化日志记录
- 日志级别控制
- 日志查询和过滤
- 日志归档和清理

### 3. 告警机制
- 任务执行失败告警
- 执行器节点异常告警
- 资源使用超限告警
- 调度延迟告警

## 扩展和定制

### 1. 自定义任务类型
- 继承基础任务类
- 实现特定业务逻辑
- 注册到任务执行器

### 2. 插件机制
- 支持第三方插件
- 动态加载和卸载
- 插件配置管理

### 3. 集成外部系统
- 支持多种数据源
- 集成消息队列
- 对接监控系统

## 最佳实践

### 1. 工作流设计
- 保持工作流简洁明了
- 合理设置超时时间
- 添加错误处理节点
- 使用并行节点提高效率

### 2. 任务配置
- 设置合适的重试策略
- 配置资源限制
- 使用任务模板提高复用性
- 定期清理历史数据

### 3. 性能优化
- 合理分配执行器资源
- 优化SQL查询性能
- 使用缓存减少重复计算
- 监控系统性能指标

## 故障排除

### 1. 常见问题
- 任务执行超时
- 执行器节点离线
- 数据库连接异常
- 内存不足

### 2. 调试方法
- 查看任务日志
- 检查执行器状态
- 分析性能指标
- 使用调试模式

### 3. 恢复策略
- 重启失败任务
- 重新调度工作流
- 手动数据修复
- 回滚到历史版本