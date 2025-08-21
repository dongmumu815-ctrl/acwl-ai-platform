# 任务管理系统架构设计

## 概述

本文档描述了ACWL AI数据平台的分布式任务管理系统架构设计，支持多实例部署、执行器分组管理、调度器高可用集群等核心功能。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACWL AI 数据平台                              │
├─────────────────────────────────────────────────────────────────┤
│  任务定义模块 (当前后台系统)                                      │
│  ├── 任务定义管理                                                │
│  ├── 任务模板管理                                                │
│  ├── 调度配置管理                                                │
│  └── 系统监控面板                                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    调度器集群 (高可用)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Scheduler-1 │  │ Scheduler-2 │  │ Scheduler-3 │              │
│  │   (Leader)  │  │ (Follower)  │  │ (Follower)  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│           │               │               │                     │
│           └───────────────┼───────────────┘                     │
│                          │                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              分布式锁 & Leader选举                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    任务队列系统                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ GPU队列     │  │ CPU队列     │  │ 通用队列     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    执行器分组集群                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GPU分组 (gpu_group)                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Executor-G1 │  │ Executor-G2 │  │ Executor-G3 │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  CPU密集型分组 (cpu_intensive)                          │   │
│  │  ┌─────────────┐  ┌─────────────┐                      │   │
│  │  │ Executor-C1 │  │ Executor-C2 │                      │   │
│  │  └─────────────┘  └─────────────┘                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  默认分组 (default)                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │  │ Executor-D1 │  │ Executor-D2 │  │ Executor-D3 │    │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 核心组件设计

### 1. 任务定义模块

**功能职责：**
- 任务定义和配置管理
- 任务模板管理
- 调度规则配置
- 执行器分组管理
- 系统监控和管理界面

**关键特性：**
- 集成到现有后台管理系统
- 支持任务模板化配置
- 提供可视化的任务编排界面
- 实时监控调度器和执行器状态

### 2. 调度器集群 (高可用设计)

**架构特点：**
- **多实例部署**：支持3个或更多调度器实例
- **Leader选举**：基于分布式锁实现Leader选举
- **故障转移**：Leader故障时自动选举新的Leader
- **负载分担**：Follower节点分担监控和管理任务

**高可用机制：**

#### Leader选举算法
```python
def elect_leader():
    """
    Leader选举算法
    """
    # 1. 尝试获取Leader锁
    lock_acquired = acquire_distributed_lock(
        lock_name="scheduler_leader",
        owner=self.node_id,
        lease_duration=60  # 60秒租约
    )
    
    if lock_acquired:
        # 2. 成为Leader
        self.role = "leader"
        self.start_scheduling_tasks()
        self.start_heartbeat_monitor()
    else:
        # 3. 成为Follower
        self.role = "follower"
        self.monitor_leader_health()
```

#### 冲突避免机制
- **分布式锁**：使用数据库行锁实现分布式锁
- **租约机制**：Leader定期续约，防止脑裂
- **心跳检测**：Follower监控Leader心跳状态
- **优雅切换**：Leader下线时优雅转移任务

### 3. 执行器分组管理

**分组策略：**

#### 3.1 按资源类型分组
```sql
-- GPU密集型分组
INSERT INTO acwl_executor_groups (group_name, group_type, task_types) VALUES
('gpu_group', 'gpu', '["model_training", "deep_learning", "image_processing"]');

-- CPU密集型分组
INSERT INTO acwl_executor_groups (group_name, group_type, task_types) VALUES
('cpu_intensive', 'cpu_intensive', '["data_analysis", "report_generation"]');

-- 内存密集型分组
INSERT INTO acwl_executor_groups (group_name, group_type, task_types) VALUES
('memory_intensive', 'memory_intensive', '["data_sync", "etl_processing"]');
```

#### 3.2 按业务类型分组
```sql
-- 数据处理分组
INSERT INTO acwl_executor_groups (group_name, group_type, task_types) VALUES
('data_processing', 'custom', '["data_sync", "etl", "data_cleaning"]');

-- 模型服务分组
INSERT INTO acwl_executor_groups (group_name, group_type, task_types) VALUES
('model_service', 'custom', '["model_training", "model_inference", "model_evaluation"]');
```

**负载均衡策略：**
- **轮询 (Round Robin)**：按顺序分配任务
- **最少连接 (Least Connections)**：分配给当前负载最低的执行器
- **资源感知 (Resource Based)**：根据资源使用情况智能分配
- **随机 (Random)**：随机选择可用执行器

### 4. 任务路由和分发

**路由规则：**

#### 4.1 基于任务类型路由
```python
def route_task_to_group(task_definition):
    """
    根据任务类型路由到对应的执行器分组
    """
    task_type = task_definition.task_type
    executor_group = task_definition.executor_group
    
    # 验证分组是否支持该任务类型
    group_info = get_executor_group(executor_group)
    if task_type not in group_info.supported_task_types:
        raise ValueError(f"分组 {executor_group} 不支持任务类型 {task_type}")
    
    return executor_group
```

#### 4.2 基于资源需求路由
```python
def route_task_by_resource(task_definition):
    """
    根据资源需求路由任务
    """
    resource_requirements = task_definition.resource_requirements
    
    if resource_requirements.get('gpu', 0) > 0:
        return 'gpu_group'
    elif resource_requirements.get('memory_gb', 0) > 16:
        return 'memory_intensive'
    elif resource_requirements.get('cpu_cores', 0) > 4:
        return 'cpu_intensive'
    else:
        return 'default'
```

## 数据库设计详解

### 核心表关系图

```
acwl_task_definitions
        │
        ├── acwl_task_schedules
        │        │
        │        └── acwl_task_instances
        │                 │
        │                 ├── acwl_task_queues
        │                 └── acwl_task_executions
        │                          │
        │                          ├── acwl_task_logs
        │                          └── acwl_task_results
        │
        └── acwl_task_dependencies

acwl_executor_groups
        │
        └── acwl_executor_nodes

acwl_scheduler_nodes
        │
        └── acwl_scheduler_locks
```

### 关键设计原则

1. **数据一致性**：使用外键约束保证数据完整性
2. **性能优化**：合理设计索引，支持高并发查询
3. **扩展性**：使用JSON字段存储灵活配置
4. **监控友好**：记录详细的状态和时间戳信息

## 部署架构

### 推荐部署方案

#### 生产环境 (3节点)
```yaml
# 调度器集群
scheduler_cluster:
  - node: scheduler-1
    role: leader_candidate
    priority: 100
  - node: scheduler-2
    role: leader_candidate
    priority: 90
  - node: scheduler-3
    role: leader_candidate
    priority: 80

# 执行器分组
executor_groups:
  gpu_group:
    - node: gpu-executor-1
      resources: { gpu: 2, memory: "32GB", cpu: 8 }
    - node: gpu-executor-2
      resources: { gpu: 2, memory: "32GB", cpu: 8 }
  
  cpu_intensive:
    - node: cpu-executor-1
      resources: { cpu: 16, memory: "64GB" }
    - node: cpu-executor-2
      resources: { cpu: 16, memory: "64GB" }
  
  default:
    - node: default-executor-1
      resources: { cpu: 4, memory: "16GB" }
    - node: default-executor-2
      resources: { cpu: 4, memory: "16GB" }
    - node: default-executor-3
      resources: { cpu: 4, memory: "16GB" }
```

#### 开发环境 (单节点)
```yaml
# 最小化部署
dev_deployment:
  scheduler: 1  # 单个调度器实例
  executors:
    default: 2  # 2个通用执行器
```

## 关键算法实现

### 1. 任务调度算法

```python
class TaskScheduler:
    """
    任务调度器核心算法
    """
    
    def schedule_tasks(self):
        """
        主调度循环
        """
        while self.is_leader:
            # 1. 扫描待调度任务
            pending_tasks = self.get_pending_tasks()
            
            # 2. 按优先级排序
            sorted_tasks = self.sort_by_priority(pending_tasks)
            
            # 3. 分配到执行器分组
            for task in sorted_tasks:
                self.assign_to_executor_group(task)
            
            # 4. 检查依赖关系
            self.check_task_dependencies()
            
            # 5. 更新任务状态
            self.update_task_status()
            
            time.sleep(self.schedule_interval)
    
    def assign_to_executor_group(self, task_instance):
        """
        将任务分配到执行器分组
        """
        # 获取目标分组
        target_group = task_instance.executor_group
        
        # 检查分组可用性
        available_executors = self.get_available_executors(target_group)
        if not available_executors:
            # 加入等待队列
            self.add_to_queue(task_instance, target_group)
            return
        
        # 选择最优执行器
        selected_executor = self.select_executor(
            available_executors, 
            task_instance.resource_requirements
        )
        
        # 分配任务
        self.assign_task(task_instance, selected_executor)
```

### 2. 负载均衡算法

```python
class LoadBalancer:
    """
    执行器负载均衡器
    """
    
    def select_executor(self, available_executors, resource_requirements):
        """
        选择最优执行器
        """
        strategy = self.get_load_balance_strategy()
        
        if strategy == 'round_robin':
            return self.round_robin_select(available_executors)
        elif strategy == 'least_connections':
            return self.least_connections_select(available_executors)
        elif strategy == 'resource_based':
            return self.resource_based_select(available_executors, resource_requirements)
        else:
            return self.random_select(available_executors)
    
    def resource_based_select(self, executors, requirements):
        """
        基于资源的智能选择
        """
        best_executor = None
        best_score = -1
        
        for executor in executors:
            # 计算资源匹配度
            score = self.calculate_resource_score(executor, requirements)
            
            # 考虑当前负载
            load_factor = executor.current_load / executor.max_concurrent_tasks
            adjusted_score = score * (1 - load_factor)
            
            if adjusted_score > best_score:
                best_score = adjusted_score
                best_executor = executor
        
        return best_executor
```

### 3. 故障恢复算法

```python
class FailureRecovery:
    """
    故障恢复处理器
    """
    
    def handle_executor_failure(self, failed_executor):
        """
        处理执行器故障
        """
        # 1. 标记执行器为离线状态
        self.mark_executor_offline(failed_executor)
        
        # 2. 获取该执行器上的运行中任务
        running_tasks = self.get_running_tasks(failed_executor)
        
        # 3. 重新调度任务
        for task in running_tasks:
            if task.retry_count < task.max_retry_count:
                self.reschedule_task(task)
            else:
                self.mark_task_failed(task, "执行器故障，重试次数已达上限")
    
    def handle_scheduler_failure(self, failed_scheduler):
        """
        处理调度器故障
        """
        if failed_scheduler.role == 'leader':
            # Leader故障，触发重新选举
            self.trigger_leader_election()
        
        # 清理故障节点的锁和状态
        self.cleanup_failed_scheduler(failed_scheduler)
```

## 监控和告警

### 关键监控指标

1. **调度器指标**
   - Leader选举次数
   - 任务调度延迟
   - 调度器心跳状态
   - 任务队列长度

2. **执行器指标**
   - 执行器在线状态
   - 任务执行成功率
   - 资源使用率
   - 任务执行时长

3. **系统指标**
   - 数据库连接池状态
   - 任务失败率
   - 系统响应时间
   - 存储空间使用率

### 告警规则

```yaml
alerts:
  - name: "调度器Leader选举频繁"
    condition: "leader_election_count > 5 in 10m"
    severity: "warning"
  
  - name: "执行器离线率过高"
    condition: "offline_executor_ratio > 0.3"
    severity: "critical"
  
  - name: "任务队列积压"
    condition: "pending_task_count > 1000"
    severity: "warning"
  
  - name: "任务失败率过高"
    condition: "task_failure_rate > 0.1 in 5m"
    severity: "error"
```

## 性能优化

### 数据库优化

1. **索引优化**
   - 为高频查询字段创建复合索引
   - 定期分析和优化慢查询
   - 使用分区表处理大量历史数据

2. **连接池优化**
   - 合理配置连接池大小
   - 使用读写分离减轻主库压力
   - 实现连接池监控和告警

### 应用优化

1. **缓存策略**
   - 缓存执行器状态信息
   - 缓存任务定义和配置
   - 使用Redis实现分布式缓存

2. **异步处理**
   - 使用异步I/O处理数据库操作
   - 实现任务状态的异步更新
   - 采用消息队列解耦组件

## 安全考虑

### 访问控制

1. **身份认证**
   - 执行器节点注册需要认证
   - 调度器间通信使用TLS加密
   - API访问需要有效的认证令牌

2. **权限管理**
   - 基于角色的访问控制(RBAC)
   - 任务执行权限隔离
   - 敏感配置信息加密存储

### 数据安全

1. **传输安全**
   - 所有网络通信使用HTTPS/TLS
   - 敏感数据传输加密
   - 实现消息完整性校验

2. **存储安全**
   - 数据库连接加密
   - 敏感配置信息加密存储
   - 定期备份和恢复测试

## 总结

本架构设计实现了以下核心目标：

1. **高可用性**：调度器集群支持故障自动切换
2. **可扩展性**：执行器分组支持水平扩展
3. **灵活性**：支持多种任务类型和资源需求
4. **可靠性**：完善的故障恢复和重试机制
5. **可监控性**：全面的监控指标和告警机制

该架构为ACWL AI数据平台提供了强大而灵活的任务管理能力，能够满足大规模数据处理和模型训练的需求。