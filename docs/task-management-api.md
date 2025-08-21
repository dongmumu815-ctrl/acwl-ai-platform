# 任务管理系统 API 接口设计

## 概述

本文档定义了ACWL AI数据平台任务管理系统的API接口规范，包括任务定义、调度器管理、执行器管理等核心功能的REST API。

## API 基础信息

- **Base URL**: `https://api.acwl.ai/v1`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "参数错误",
  "error": "详细错误信息",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 1. 任务定义管理 API

### 1.1 创建任务定义

**接口**: `POST /tasks/definitions`

**请求体**:
```json
{
  "name": "数据同步任务",
  "description": "从源数据库同步数据到目标数据库",
  "task_type": "data_sync",
  "executor_group": "default",
  "resource_requirements": {
    "cpu_cores": 2,
    "memory_gb": 4,
    "gpu": 0,
    "disk_gb": 10
  },
  "config": {
    "source_db": "mysql://source:3306/db",
    "target_db": "postgresql://target:5432/db",
    "batch_size": 1000
  },
  "timeout_seconds": 3600,
  "max_retry_count": 3,
  "project_id": 1,
  "created_by": 1
}
```

**响应**:
```json
{
  "code": 200,
  "message": "任务定义创建成功",
  "data": {
    "id": 1,
    "name": "数据同步任务",
    "task_type": "data_sync",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 1.2 获取任务定义列表

**接口**: `GET /tasks/definitions`

**查询参数**:
- `page`: 页码 (默认: 1)
- `size`: 每页大小 (默认: 20)
- `task_type`: 任务类型过滤
- `status`: 状态过滤
- `project_id`: 项目ID过滤

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "数据同步任务",
        "task_type": "data_sync",
        "executor_group": "default",
        "status": "active",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 1.3 获取任务定义详情

**接口**: `GET /tasks/definitions/{id}`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "数据同步任务",
    "description": "从源数据库同步数据到目标数据库",
    "task_type": "data_sync",
    "executor_group": "default",
    "resource_requirements": {
      "cpu_cores": 2,
      "memory_gb": 4,
      "gpu": 0,
      "disk_gb": 10
    },
    "config": {
      "source_db": "mysql://source:3306/db",
      "target_db": "postgresql://target:5432/db",
      "batch_size": 1000
    },
    "timeout_seconds": 3600,
    "max_retry_count": 3,
    "status": "active",
    "project_id": 1,
    "created_by": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
}
```

### 1.4 更新任务定义

**接口**: `PUT /tasks/definitions/{id}`

**请求体**: (同创建任务定义)

### 1.5 删除任务定义

**接口**: `DELETE /tasks/definitions/{id}`

## 2. 任务调度管理 API

### 2.1 创建调度配置

**接口**: `POST /tasks/schedules`

**请求体**:
```json
{
  "task_definition_id": 1,
  "schedule_type": "cron",
  "cron_expression": "0 2 * * *",
  "timezone": "Asia/Shanghai",
  "enabled": true,
  "start_date": "2024-01-15T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "max_instances": 1,
  "created_by": 1
}
```

**响应**:
```json
{
  "code": 200,
  "message": "调度配置创建成功",
  "data": {
    "id": 1,
    "task_definition_id": 1,
    "schedule_type": "cron",
    "cron_expression": "0 2 * * *",
    "enabled": true,
    "next_run_time": "2024-01-16T02:00:00Z",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2.2 手动触发任务

**接口**: `POST /tasks/trigger`

**请求体**:
```json
{
  "task_definition_id": 1,
  "priority": "high",
  "parameters": {
    "custom_param": "value"
  },
  "triggered_by": 1
}
```

**响应**:
```json
{
  "code": 200,
  "message": "任务触发成功",
  "data": {
    "task_instance_id": "task_20240115_103000_001",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### 2.3 获取任务实例列表

**接口**: `GET /tasks/instances`

**查询参数**:
- `page`: 页码
- `size`: 每页大小
- `status`: 状态过滤 (pending, running, completed, failed)
- `task_definition_id`: 任务定义ID
- `start_time`: 开始时间
- `end_time`: 结束时间

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "task_20240115_103000_001",
        "task_definition_id": 1,
        "task_name": "数据同步任务",
        "status": "running",
        "executor_node_id": "executor_001",
        "executor_group": "default",
        "priority": "normal",
        "progress": 45,
        "started_at": "2024-01-15T10:30:00Z",
        "estimated_completion": "2024-01-15T11:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 2.4 获取任务实例详情

**接口**: `GET /tasks/instances/{id}`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": "task_20240115_103000_001",
    "task_definition_id": 1,
    "task_name": "数据同步任务",
    "status": "running",
    "executor_node_id": "executor_001",
    "executor_group": "default",
    "priority": "normal",
    "progress": 45,
    "parameters": {
      "custom_param": "value"
    },
    "resource_usage": {
      "cpu_percent": 25.5,
      "memory_mb": 1024,
      "disk_mb": 512
    },
    "created_at": "2024-01-15T10:25:00Z",
    "started_at": "2024-01-15T10:30:00Z",
    "estimated_completion": "2024-01-15T11:30:00Z",
    "logs_url": "/tasks/instances/task_20240115_103000_001/logs"
  }
}
```

### 2.5 停止任务实例

**接口**: `POST /tasks/instances/{id}/stop`

**请求体**:
```json
{
  "reason": "用户手动停止",
  "force": false
}
```

### 2.6 重启任务实例

**接口**: `POST /tasks/instances/{id}/restart`

## 3. 执行器管理 API

### 3.1 执行器注册

**接口**: `POST /executors/register`

**请求体**:
```json
{
  "node_id": "executor_001",
  "node_name": "GPU执行器-1",
  "executor_group": "gpu_group",
  "host_info": {
    "hostname": "gpu-server-01",
    "ip_address": "192.168.1.100",
    "port": 8080
  },
  "resource_capacity": {
    "cpu_cores": 16,
    "memory_gb": 64,
    "gpu": 2,
    "disk_gb": 1000
  },
  "supported_task_types": ["model_training", "deep_learning"],
  "max_concurrent_tasks": 4,
  "tags": {
    "environment": "production",
    "gpu_type": "RTX4090"
  }
}
```

**响应**:
```json
{
  "code": 200,
  "message": "执行器注册成功",
  "data": {
    "node_id": "executor_001",
    "registration_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "heartbeat_interval": 30,
    "registered_at": "2024-01-15T10:30:00Z"
  }
}
```

### 3.2 执行器心跳

**接口**: `POST /executors/{node_id}/heartbeat`

**请求体**:
```json
{
  "status": "online",
  "current_load": 2,
  "resource_usage": {
    "cpu_percent": 45.2,
    "memory_percent": 60.8,
    "gpu_percent": 80.5,
    "disk_percent": 25.0
  },
  "running_tasks": [
    {
      "task_instance_id": "task_20240115_103000_001",
      "progress": 45,
      "resource_usage": {
        "cpu_percent": 25.0,
        "memory_mb": 2048
      }
    }
  ]
}
```

**响应**:
```json
{
  "code": 200,
  "message": "心跳更新成功",
  "data": {
    "next_heartbeat_time": "2024-01-15T10:31:00Z",
    "commands": [
      {
        "type": "stop_task",
        "task_instance_id": "task_20240115_102000_001",
        "reason": "用户取消"
      }
    ]
  }
}
```

### 3.3 获取执行器列表

**接口**: `GET /executors`

**查询参数**:
- `group`: 执行器分组
- `status`: 状态过滤 (online, offline, busy)
- `page`: 页码
- `size`: 每页大小

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "node_id": "executor_001",
        "node_name": "GPU执行器-1",
        "executor_group": "gpu_group",
        "status": "online",
        "current_load": 2,
        "max_concurrent_tasks": 4,
        "resource_usage": {
          "cpu_percent": 45.2,
          "memory_percent": 60.8,
          "gpu_percent": 80.5
        },
        "last_heartbeat": "2024-01-15T10:30:00Z",
        "registered_at": "2024-01-15T09:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 20
  }
}
```

### 3.4 获取执行器详情

**接口**: `GET /executors/{node_id}`

### 3.5 注销执行器

**接口**: `DELETE /executors/{node_id}`

## 4. 调度器管理 API

### 4.1 调度器注册

**接口**: `POST /schedulers/register`

**请求体**:
```json
{
  "node_id": "scheduler_001",
  "node_name": "主调度器-1",
  "host_info": {
    "hostname": "scheduler-server-01",
    "ip_address": "192.168.1.10",
    "port": 8090
  },
  "priority": 100,
  "capabilities": ["task_scheduling", "load_balancing", "failure_recovery"]
}
```

### 4.2 调度器心跳

**接口**: `POST /schedulers/{node_id}/heartbeat`

**请求体**:
```json
{
  "role": "leader",
  "status": "active",
  "metrics": {
    "scheduled_tasks_count": 150,
    "pending_tasks_count": 25,
    "failed_tasks_count": 3,
    "average_schedule_latency_ms": 45
  },
  "leader_lease_expires_at": "2024-01-15T10:31:00Z"
}
```

### 4.3 获取调度器集群状态

**接口**: `GET /schedulers/cluster/status`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "leader": {
      "node_id": "scheduler_001",
      "node_name": "主调度器-1",
      "elected_at": "2024-01-15T09:00:00Z",
      "lease_expires_at": "2024-01-15T10:31:00Z"
    },
    "followers": [
      {
        "node_id": "scheduler_002",
        "node_name": "备用调度器-1",
        "status": "standby",
        "last_heartbeat": "2024-01-15T10:30:00Z"
      }
    ],
    "cluster_health": "healthy",
    "total_nodes": 2,
    "online_nodes": 2
  }
}
```

### 4.4 触发Leader选举

**接口**: `POST /schedulers/cluster/elect-leader`

## 5. 执行器分组管理 API

### 5.1 创建执行器分组

**接口**: `POST /executor-groups`

**请求体**:
```json
{
  "group_name": "gpu_group",
  "group_type": "gpu",
  "description": "GPU密集型任务执行器分组",
  "task_types": ["model_training", "deep_learning", "image_processing"],
  "load_balance_strategy": "resource_based",
  "max_concurrent_tasks_per_executor": 4,
  "resource_requirements": {
    "min_gpu": 1,
    "min_memory_gb": 16
  },
  "config": {
    "auto_scaling": true,
    "min_executors": 2,
    "max_executors": 10
  }
}
```

### 5.2 获取执行器分组列表

**接口**: `GET /executor-groups`

### 5.3 更新执行器分组

**接口**: `PUT /executor-groups/{group_name}`

### 5.4 删除执行器分组

**接口**: `DELETE /executor-groups/{group_name}`

## 6. 任务队列管理 API

### 6.1 获取队列状态

**接口**: `GET /queues/status`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "queues": [
      {
        "executor_group": "gpu_group",
        "pending_count": 15,
        "running_count": 8,
        "priority_distribution": {
          "high": 3,
          "normal": 10,
          "low": 2
        },
        "average_wait_time_seconds": 120,
        "oldest_task_wait_time_seconds": 300
      }
    ],
    "total_pending": 25,
    "total_running": 18
  }
}
```

### 6.2 清空队列

**接口**: `POST /queues/{executor_group}/clear`

## 7. 任务日志 API

### 7.1 获取任务日志

**接口**: `GET /tasks/instances/{id}/logs`

**查询参数**:
- `level`: 日志级别 (debug, info, warning, error)
- `start_time`: 开始时间
- `end_time`: 结束时间
- `page`: 页码
- `size`: 每页大小

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "logs": [
      {
        "timestamp": "2024-01-15T10:30:15Z",
        "level": "info",
        "message": "开始执行数据同步任务",
        "source": "task_executor"
      },
      {
        "timestamp": "2024-01-15T10:30:30Z",
        "level": "info",
        "message": "已同步 1000 条记录",
        "source": "task_executor"
      }
    ],
    "total": 2,
    "page": 1,
    "size": 50
  }
}
```

### 7.2 实时日志流

**接口**: `GET /tasks/instances/{id}/logs/stream`

**协议**: WebSocket

**消息格式**:
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "info",
  "message": "任务进度: 50%",
  "source": "task_executor"
}
```

## 8. 系统监控 API

### 8.1 获取系统概览

**接口**: `GET /system/overview`

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "tasks": {
      "total_definitions": 25,
      "active_schedules": 18,
      "running_instances": 12,
      "pending_instances": 8,
      "completed_today": 156,
      "failed_today": 3
    },
    "executors": {
      "total_groups": 4,
      "total_executors": 15,
      "online_executors": 14,
      "busy_executors": 8,
      "average_load": 0.65
    },
    "schedulers": {
      "total_schedulers": 3,
      "online_schedulers": 3,
      "current_leader": "scheduler_001",
      "leader_elections_today": 0
    },
    "system_health": "healthy"
  }
}
```

### 8.2 获取性能指标

**接口**: `GET /system/metrics`

**查询参数**:
- `start_time`: 开始时间
- `end_time`: 结束时间
- `interval`: 时间间隔 (1m, 5m, 1h, 1d)

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "task_metrics": {
      "success_rate": 0.98,
      "average_execution_time_seconds": 1800,
      "throughput_per_hour": 45
    },
    "resource_metrics": {
      "cpu_utilization": 0.65,
      "memory_utilization": 0.72,
      "gpu_utilization": 0.85
    },
    "queue_metrics": {
      "average_wait_time_seconds": 120,
      "max_queue_length": 25
    }
  }
}
```

## 9. 错误码定义

| 错误码 | 说明 | 描述 |
|--------|------|------|
| 200 | 成功 | 请求成功 |
| 400 | 参数错误 | 请求参数不正确 |
| 401 | 未授权 | 缺少或无效的认证信息 |
| 403 | 禁止访问 | 没有权限访问该资源 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 409 | 冲突 | 资源冲突，如重复创建 |
| 422 | 业务逻辑错误 | 请求格式正确但业务逻辑有误 |
| 500 | 服务器内部错误 | 服务器内部错误 |
| 503 | 服务不可用 | 服务暂时不可用 |

### 业务错误码

| 错误码 | 说明 |
|--------|------|
| 10001 | 任务定义不存在 |
| 10002 | 任务实例不存在 |
| 10003 | 执行器不在线 |
| 10004 | 执行器分组不存在 |
| 10005 | 调度器集群异常 |
| 10006 | 任务队列已满 |
| 10007 | 资源不足 |
| 10008 | 任务依赖未满足 |
| 10009 | 任务已在运行 |
| 10010 | 任务不能停止 |

## 10. SDK 示例

### Python SDK 示例

```python
from acwl_task_client import TaskClient

# 初始化客户端
client = TaskClient(
    base_url="https://api.acwl.ai/v1",
    token="your_api_token"
)

# 创建任务定义
task_def = client.create_task_definition(
    name="数据同步任务",
    task_type="data_sync",
    executor_group="default",
    config={
        "source_db": "mysql://source:3306/db",
        "target_db": "postgresql://target:5432/db"
    }
)

# 手动触发任务
task_instance = client.trigger_task(
    task_definition_id=task_def.id,
    priority="high"
)

# 监控任务状态
while True:
    status = client.get_task_instance(task_instance.id)
    print(f"任务状态: {status.status}, 进度: {status.progress}%")
    
    if status.status in ["completed", "failed"]:
        break
    
    time.sleep(10)

# 获取任务日志
logs = client.get_task_logs(task_instance.id)
for log in logs:
    print(f"[{log.timestamp}] {log.level}: {log.message}")
```

### JavaScript SDK 示例

```javascript
import { TaskClient } from '@acwl/task-client';

// 初始化客户端
const client = new TaskClient({
  baseURL: 'https://api.acwl.ai/v1',
  token: 'your_api_token'
});

// 创建任务定义
const taskDef = await client.createTaskDefinition({
  name: '数据同步任务',
  taskType: 'data_sync',
  executorGroup: 'default',
  config: {
    sourceDb: 'mysql://source:3306/db',
    targetDb: 'postgresql://target:5432/db'
  }
});

// 手动触发任务
const taskInstance = await client.triggerTask({
  taskDefinitionId: taskDef.id,
  priority: 'high'
});

// 实时监控任务日志
const logStream = client.streamTaskLogs(taskInstance.id);
logStream.on('log', (log) => {
  console.log(`[${log.timestamp}] ${log.level}: ${log.message}`);
});

logStream.on('error', (error) => {
  console.error('日志流错误:', error);
});
```

## 11. 认证和授权

### API Token 获取

**接口**: `POST /auth/tokens`

**请求体**:
```json
{
  "username": "admin",
  "password": "password",
  "scope": "task_management"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "scope": "task_management"
  }
}
```

### 权限范围

- `task_management:read`: 只读权限
- `task_management:write`: 读写权限
- `task_management:admin`: 管理员权限
- `executor:register`: 执行器注册权限
- `scheduler:register`: 调度器注册权限

## 12. 限流和配额

### API 限流

- **普通用户**: 1000 请求/小时
- **高级用户**: 5000 请求/小时
- **企业用户**: 无限制

### 响应头

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

### 超限响应

```json
{
  "code": 429,
  "message": "请求频率超限",
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

这套API设计提供了完整的任务管理功能，支持多实例部署、分组管理、高可用调度等核心需求，同时考虑了安全性、性能和可扩展性。