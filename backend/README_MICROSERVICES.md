# 微服务架构部署指南

本文档介绍如何使用微服务架构部署和管理执行器和调度器集群。

## 架构概述

### 服务组件

1. **主应用服务** (`main.py`)
   - 提供Web API接口
   - 管理数据库连接
   - 提供前端界面

2. **调度器服务** (`scheduler_service.py`)
   - 独立的调度器节点
   - 支持Leader选举
   - 负责任务调度

3. **执行器服务** (`executor_service.py`)
   - 独立的执行器节点
   - 支持分组管理
   - 负责任务执行

4. **集群管理器** (`cluster_manager.py`)
   - 批量管理多个实例
   - 配置化部署
   - 状态监控

## 快速开始

### 1. 环境准备

确保已安装所需依赖：
```bash
cd d:\works\codes\acwl-ai-data\backend
pip install -r requirements.txt
pip install psutil  # 用于系统监控
```

### 2. 启动主应用

首先启动主应用服务（提供API和Web界面）：
```bash
python main.py
```

主应用将在 http://localhost:8000 提供服务。

### 3. 初始化集群配置

生成默认的集群配置文件：
```bash
python cluster_manager.py init-config
```

这将创建 `cluster_config.json` 文件，包含默认的调度器和执行器配置。

### 4. 启动集群

#### 方式一：使用集群管理器（推荐）

启动完整集群（3个调度器 + 3个执行器）：
```bash
python cluster_manager.py start
```

启动指定数量的服务：
```bash
# 启动2个调度器
python cluster_manager.py start --schedulers 2

# 启动3个执行器
python cluster_manager.py start --executors 3

# 启动指定分组的执行器
python cluster_manager.py start --executors 2 --group default
```

#### 方式二：手动启动单个实例

启动调度器：
```bash
# 调度器1
python scheduler_service.py --node-id scheduler-001 --node-name "主调度器-1" --port 8002

# 调度器2
python scheduler_service.py --node-id scheduler-002 --node-name "主调度器-2" --port 8003

# 调度器3
python scheduler_service.py --node-id scheduler-003 --node-name "主调度器-3" --port 8004
```

启动执行器：
```bash
# 执行器1（默认分组）
python executor_service.py --node-id executor-001 --node-name "执行器-1" --group-id default --port 8011

# 执行器2（默认分组）
python executor_service.py --node-id executor-002 --node-name "执行器-2" --group-id default --port 8012

# 执行器3（高性能分组）
python executor_service.py --node-id executor-003 --node-name "执行器-3" --group-id high-performance --port 8013 --max-concurrent-tasks 10
```

## 集群管理

### 查看集群状态

```bash
python cluster_manager.py status
```

输出示例：
```
=== 集群状态 ===

调度器 (3 个):
  - scheduler-scheduler-001: 运行中 (PID: 12345, 运行时间: 120秒)
  - scheduler-scheduler-002: 运行中 (PID: 12346, 运行时间: 118秒)
  - scheduler-scheduler-003: 运行中 (PID: 12347, 运行时间: 115秒)

执行器 (3 个):
  - executor-executor-001: 运行中 (PID: 12348, 分组: default, 运行时间: 110秒)
  - executor-executor-002: 运行中 (PID: 12349, 分组: default, 运行时间: 108秒)
  - executor-executor-003: 运行中 (PID: 12350, 分组: high-performance, 运行时间: 105秒)
```

### 停止服务

```bash
# 停止所有服务
python cluster_manager.py stop

# 只停止调度器
python cluster_manager.py stop --type schedulers

# 只停止执行器
python cluster_manager.py stop --type executors

# 停止指定分组的执行器
python cluster_manager.py stop --type executors --group default
```

### 重启集群

```bash
python cluster_manager.py restart
```

## 配置说明

### 集群配置文件 (cluster_config.json)

```json
{
  "schedulers": [
    {
      "node_id": "scheduler-001",
      "node_name": "主调度器-1",
      "host_ip": "127.0.0.1",
      "port": 8002,
      "log_level": "INFO"
    }
  ],
  "executors": [
    {
      "node_id": "executor-001",
      "node_name": "执行器-1",
      "group_id": "default",
      "host_ip": "127.0.0.1",
      "port": 8011,
      "max_concurrent_tasks": 5,
      "log_level": "INFO"
    }
  ]
}
```

### 调度器参数

- `--node-id`: 节点唯一标识
- `--node-name`: 节点显示名称
- `--host-ip`: 绑定IP地址
- `--port`: 监听端口
- `--log-level`: 日志级别 (DEBUG, INFO, WARNING, ERROR)
- `--log-file`: 日志文件路径

### 执行器参数

- `--node-id`: 节点唯一标识
- `--node-name`: 节点显示名称
- `--group-id`: 执行器分组
- `--host-ip`: 绑定IP地址
- `--port`: 监听端口
- `--max-concurrent-tasks`: 最大并发任务数
- `--log-level`: 日志级别
- `--log-file`: 日志文件路径

## 高可用部署

### 调度器高可用

建议部署至少3个调度器实例以实现高可用：

1. **Leader选举**: 自动选举一个Leader负责任务调度
2. **故障转移**: Leader故障时自动选举新的Leader
3. **负载分担**: Follower节点分担监控和管理任务

### 执行器分组

可以根据业务需求创建不同的执行器分组：

- `default`: 默认分组，处理一般任务
- `high-performance`: 高性能分组，处理计算密集型任务
- `gpu`: GPU分组，处理需要GPU的任务
- `batch`: 批处理分组，处理大批量任务

## 监控和日志

### 日志文件

- 主应用: `logs/app.log`
- 调度器: `logs/scheduler_{node_id}.log`
- 执行器: `logs/executor_{node_id}.log`

### 系统监控

每个节点都会自动监控：
- CPU使用率
- 内存使用率
- 磁盘使用率
- 任务执行状态

### Web界面监控

通过主应用的Web界面可以查看：
- 集群状态
- 节点列表
- 任务执行情况
- 性能指标

访问地址：http://localhost:8000

## 生产环境部署

### 1. 分布式部署

在不同服务器上部署不同组件：

**服务器1 (管理节点)**:
```bash
# 启动主应用
python main.py

# 启动调度器1
python scheduler_service.py --node-id scheduler-001 --host-ip 192.168.1.10 --port 8002
```

**服务器2 (调度节点)**:
```bash
# 启动调度器2
python scheduler_service.py --node-id scheduler-002 --host-ip 192.168.1.11 --port 8002

# 启动调度器3
python scheduler_service.py --node-id scheduler-003 --host-ip 192.168.1.11 --port 8003
```

**服务器3-5 (执行节点)**:
```bash
# 在每台服务器上启动执行器
python executor_service.py --node-id executor-{server_id} --host-ip {server_ip} --port 8011
```

### 2. 容器化部署

可以使用Docker容器化部署：

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 根据需要启动不同服务
CMD ["python", "scheduler_service.py"]
```

### 3. 进程管理

使用进程管理工具（如systemd、supervisor）管理服务：

```ini
# /etc/supervisor/conf.d/scheduler.conf
[program:scheduler-001]
command=python /path/to/scheduler_service.py --node-id scheduler-001
directory=/path/to/backend
autorestart=true
user=app
```

## 故障排除

### 常见问题

1. **节点注册失败**
   - 检查数据库连接
   - 确认主应用已启动
   - 检查网络连接

2. **Leader选举失败**
   - 检查数据库锁表
   - 确认多个调度器实例正常运行
   - 查看调度器日志

3. **任务执行失败**
   - 检查执行器状态
   - 查看执行器日志
   - 确认任务配置正确

### 日志分析

查看特定节点的日志：
```bash
# 查看调度器日志
tail -f logs/scheduler_scheduler-001.log

# 查看执行器日志
tail -f logs/executor_executor-001.log
```

### 性能调优

1. **调度器优化**
   - 调整心跳间隔
   - 优化Leader选举超时
   - 增加调度器实例数量

2. **执行器优化**
   - 调整最大并发任务数
   - 优化资源监控间隔
   - 根据硬件配置调整分组

## 总结

通过这套微服务架构，您可以：

1. **灵活部署**: 独立启动和管理执行器、调度器实例
2. **高可用性**: 支持多实例部署和故障转移
3. **可扩展性**: 根据负载动态增减实例
4. **易管理性**: 统一的配置和管理工具
5. **监控完善**: 完整的日志和监控体系

这种架构相比之前的集成式架构，提供了更好的灵活性和可维护性，适合生产环境的大规模部署。