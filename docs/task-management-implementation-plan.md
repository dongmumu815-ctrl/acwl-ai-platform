# 任务管理系统实现计划

## 项目概述

本文档详细描述了ACWL AI数据平台任务管理系统的完整实现步骤，包括数据库设计、后端API开发、前端界面开发、调度器和执行器模块开发等各个阶段的具体实施计划。

## 实现阶段划分

### 阶段一：基础设施搭建 (1-2周)
- 数据库表结构创建
- 基础模型和CRUD操作
- 核心API接口框架

### 阶段二：核心功能开发 (3-4周)
- 任务定义和调度功能
- 执行器注册和管理
- 调度器集群实现

### 阶段三：高级功能开发 (2-3周)
- 分布式锁和Leader选举
- 负载均衡和故障恢复
- 监控和日志系统

### 阶段四：前端界面开发 (2-3周)
- 任务管理界面
- 系统监控面板
- 实时状态展示

### 阶段五：测试和部署 (1-2周)
- 单元测试和集成测试
- 性能测试和优化
- 生产环境部署

---

## 详细实现步骤

## 阶段一：基础设施搭建

### 步骤1.1：数据库表结构创建

**时间估计**: 1天

**任务描述**: 在现有数据库中创建任务管理相关的所有表结构

**具体操作**:

1. **执行数据库迁移脚本**
   ```bash
   # 连接到MySQL数据库
   mysql -u root -p acwl_ai_data
   
   # 执行任务管理表创建脚本
   source database/task_management_schema.sql
   ```

2. **验证表结构**
   ```sql
   -- 检查所有任务管理相关表是否创建成功
   SHOW TABLES LIKE 'acwl_task_%';
   SHOW TABLES LIKE 'acwl_executor_%';
   SHOW TABLES LIKE 'acwl_scheduler_%';
   
   -- 检查表结构
   DESCRIBE acwl_task_definitions;
   DESCRIBE acwl_executor_nodes;
   DESCRIBE acwl_scheduler_nodes;
   ```

3. **插入初始化数据**
   ```sql
   -- 创建默认执行器分组
   INSERT INTO acwl_executor_groups (group_name, group_type, description) VALUES
   ('default', 'general', '默认执行器分组'),
   ('gpu_group', 'gpu', 'GPU密集型任务分组'),
   ('cpu_intensive', 'cpu_intensive', 'CPU密集型任务分组');
   
   -- 创建系统配置
   INSERT INTO acwl_system_configs (config_key, config_value, description) VALUES
   ('scheduler.heartbeat_interval', '30', '调度器心跳间隔(秒)'),
   ('executor.heartbeat_interval', '30', '执行器心跳间隔(秒)'),
   ('task.default_timeout', '3600', '任务默认超时时间(秒)');
   ```

**交付物**:
- ✅ 所有任务管理表创建完成
- ✅ 初始化数据插入完成
- ✅ 数据库连接测试通过

### 步骤1.2：创建数据模型 (SQLAlchemy Models)

**时间估计**: 2天

**任务描述**: 创建对应数据库表的SQLAlchemy模型类

**具体操作**:

1. **创建任务相关模型**
   
   创建文件: `backend/app/models/task.py`
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, ForeignKey, Boolean, Float
   from sqlalchemy.orm import relationship
   from sqlalchemy.ext.declarative import declarative_base
   from datetime import datetime
   import enum
   
   Base = declarative_base()
   
   class TaskStatus(enum.Enum):
       """任务状态枚举"""
       ACTIVE = "active"
       INACTIVE = "inactive"
       ARCHIVED = "archived"
   
   class TaskDefinition(Base):
       """任务定义模型"""
       __tablename__ = "acwl_task_definitions"
       
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String(255), nullable=False, comment="任务名称")
       description = Column(Text, comment="任务描述")
       task_type = Column(String(100), nullable=False, comment="任务类型")
       executor_group = Column(String(100), nullable=False, default="default", comment="执行器分组")
       resource_requirements = Column(JSON, comment="资源需求")
       config = Column(JSON, comment="任务配置")
       timeout_seconds = Column(Integer, default=3600, comment="超时时间(秒)")
       max_retry_count = Column(Integer, default=3, comment="最大重试次数")
       status = Column(Enum(TaskStatus), default=TaskStatus.ACTIVE, comment="状态")
       project_id = Column(Integer, ForeignKey("acwl_projects.id"), comment="项目ID")
       created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者")
       created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
       
       # 关系
       schedules = relationship("TaskSchedule", back_populates="task_definition")
       instances = relationship("TaskInstance", back_populates="task_definition")
   
   class ScheduleType(enum.Enum):
       """调度类型枚举"""
       MANUAL = "manual"
       CRON = "cron"
       INTERVAL = "interval"
       ONCE = "once"
   
   class TaskSchedule(Base):
       """任务调度配置模型"""
       __tablename__ = "acwl_task_schedules"
       
       id = Column(Integer, primary_key=True, index=True)
       task_definition_id = Column(Integer, ForeignKey("acwl_task_definitions.id"), nullable=False)
       schedule_type = Column(Enum(ScheduleType), nullable=False, comment="调度类型")
       cron_expression = Column(String(100), comment="Cron表达式")
       interval_seconds = Column(Integer, comment="间隔秒数")
       timezone = Column(String(50), default="UTC", comment="时区")
       enabled = Column(Boolean, default=True, comment="是否启用")
       start_date = Column(DateTime, comment="开始日期")
       end_date = Column(DateTime, comment="结束日期")
       max_instances = Column(Integer, default=1, comment="最大并发实例数")
       next_run_time = Column(DateTime, comment="下次运行时间")
       last_run_time = Column(DateTime, comment="上次运行时间")
       created_by = Column(Integer, ForeignKey("acwl_users.id"), comment="创建者")
       created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
       
       # 关系
       task_definition = relationship("TaskDefinition", back_populates="schedules")
   ```

2. **创建执行器相关模型**
   
   创建文件: `backend/app/models/executor.py`
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Boolean, Float
   from sqlalchemy.orm import relationship
   from datetime import datetime
   import enum
   
   class ExecutorStatus(enum.Enum):
       """执行器状态枚举"""
       ONLINE = "online"
       OFFLINE = "offline"
       BUSY = "busy"
       MAINTENANCE = "maintenance"
   
   class ExecutorGroup(Base):
       """执行器分组模型"""
       __tablename__ = "acwl_executor_groups"
       
       id = Column(Integer, primary_key=True, index=True)
       group_name = Column(String(100), unique=True, nullable=False, comment="分组名称")
       group_type = Column(String(50), nullable=False, comment="分组类型")
       description = Column(Text, comment="分组描述")
       task_types = Column(JSON, comment="支持的任务类型")
       load_balance_strategy = Column(String(50), default="round_robin", comment="负载均衡策略")
       max_concurrent_tasks_per_executor = Column(Integer, default=5, comment="每个执行器最大并发任务数")
       resource_requirements = Column(JSON, comment="资源要求")
       config = Column(JSON, comment="分组配置")
       enabled = Column(Boolean, default=True, comment="是否启用")
       created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
       
       # 关系
       executors = relationship("ExecutorNode", back_populates="group")
   
   class ExecutorNode(Base):
       """执行器节点模型"""
       __tablename__ = "acwl_executor_nodes"
       
       id = Column(Integer, primary_key=True, index=True)
       node_id = Column(String(100), unique=True, nullable=False, comment="节点ID")
       node_name = Column(String(255), nullable=False, comment="节点名称")
       executor_group_id = Column(Integer, ForeignKey("acwl_executor_groups.id"), nullable=False)
       host_info = Column(JSON, comment="主机信息")
       resource_capacity = Column(JSON, comment="资源容量")
       resource_usage = Column(JSON, comment="资源使用情况")
       supported_task_types = Column(JSON, comment="支持的任务类型")
       max_concurrent_tasks = Column(Integer, default=5, comment="最大并发任务数")
       current_load = Column(Integer, default=0, comment="当前负载")
       status = Column(Enum(ExecutorStatus), default=ExecutorStatus.OFFLINE, comment="状态")
       tags = Column(JSON, comment="标签")
       last_heartbeat = Column(DateTime, comment="最后心跳时间")
       registered_at = Column(DateTime, default=datetime.utcnow, comment="注册时间")
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
       
       # 关系
       group = relationship("ExecutorGroup", back_populates="executors")
   ```

3. **创建调度器相关模型**
   
   创建文件: `backend/app/models/scheduler.py`
   ```python
   from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, Boolean
   from datetime import datetime
   import enum
   
   class SchedulerRole(enum.Enum):
       """调度器角色枚举"""
       LEADER = "leader"
       FOLLOWER = "follower"
       CANDIDATE = "candidate"
   
   class SchedulerStatus(enum.Enum):
       """调度器状态枚举"""
       ACTIVE = "active"
       INACTIVE = "inactive"
       MAINTENANCE = "maintenance"
   
   class SchedulerNode(Base):
       """调度器节点模型"""
       __tablename__ = "acwl_scheduler_nodes"
       
       id = Column(Integer, primary_key=True, index=True)
       node_id = Column(String(100), unique=True, nullable=False, comment="节点ID")
       node_name = Column(String(255), nullable=False, comment="节点名称")
       host_info = Column(JSON, comment="主机信息")
       role = Column(Enum(SchedulerRole), default=SchedulerRole.FOLLOWER, comment="角色")
       status = Column(Enum(SchedulerStatus), default=SchedulerStatus.ACTIVE, comment="状态")
       priority = Column(Integer, default=100, comment="优先级")
       capabilities = Column(JSON, comment="能力列表")
       metrics = Column(JSON, comment="性能指标")
       leader_lease_expires_at = Column(DateTime, comment="Leader租约过期时间")
       last_heartbeat = Column(DateTime, comment="最后心跳时间")
       registered_at = Column(DateTime, default=datetime.utcnow, comment="注册时间")
       updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
   ```

4. **更新模型初始化文件**
   
   修改文件: `backend/app/models/__init__.py`
   ```python
   from .user import User
   from .model import Model
   from .deployment import Deployment
   from .project import Project
   # 新增任务管理模型
   from .task import TaskDefinition, TaskSchedule, TaskInstance, TaskExecution
   from .executor import ExecutorGroup, ExecutorNode
   from .scheduler import SchedulerNode
   
   __all__ = [
       "User", "Model", "Deployment", "Project",
       "TaskDefinition", "TaskSchedule", "TaskInstance", "TaskExecution",
       "ExecutorGroup", "ExecutorNode", "SchedulerNode"
   ]
   ```

**交付物**:
- ✅ 任务管理相关SQLAlchemy模型创建完成
- ✅ 模型关系定义正确
- ✅ 枚举类型定义完整

### 步骤1.3：创建Pydantic Schema

**时间估计**: 1天

**任务描述**: 创建API请求和响应的数据验证模式

**具体操作**:

1. **创建任务相关Schema**
   
   创建文件: `backend/app/schemas/task.py`
   ```python
   from pydantic import BaseModel, Field, validator
   from typing import Optional, Dict, Any, List
   from datetime import datetime
   from enum import Enum
   
   class TaskStatus(str, Enum):
       """任务状态枚举"""
       ACTIVE = "active"
       INACTIVE = "inactive"
       ARCHIVED = "archived"
   
   class TaskDefinitionCreate(BaseModel):
       """创建任务定义的请求模式"""
       name: str = Field(..., min_length=1, max_length=255, description="任务名称")
       description: Optional[str] = Field(None, description="任务描述")
       task_type: str = Field(..., min_length=1, max_length=100, description="任务类型")
       executor_group: str = Field(default="default", description="执行器分组")
       resource_requirements: Optional[Dict[str, Any]] = Field(None, description="资源需求")
       config: Optional[Dict[str, Any]] = Field(None, description="任务配置")
       timeout_seconds: int = Field(default=3600, ge=1, description="超时时间(秒)")
       max_retry_count: int = Field(default=3, ge=0, description="最大重试次数")
       project_id: Optional[int] = Field(None, description="项目ID")
       
       @validator('resource_requirements')
       def validate_resource_requirements(cls, v):
           """验证资源需求格式"""
           if v is not None:
               allowed_keys = ['cpu_cores', 'memory_gb', 'gpu', 'disk_gb']
               for key in v.keys():
                   if key not in allowed_keys:
                       raise ValueError(f'不支持的资源类型: {key}')
           return v
   
   class TaskDefinitionUpdate(BaseModel):
       """更新任务定义的请求模式"""
       name: Optional[str] = Field(None, min_length=1, max_length=255)
       description: Optional[str] = None
       task_type: Optional[str] = Field(None, min_length=1, max_length=100)
       executor_group: Optional[str] = None
       resource_requirements: Optional[Dict[str, Any]] = None
       config: Optional[Dict[str, Any]] = None
       timeout_seconds: Optional[int] = Field(None, ge=1)
       max_retry_count: Optional[int] = Field(None, ge=0)
       status: Optional[TaskStatus] = None
   
   class TaskDefinitionResponse(BaseModel):
       """任务定义响应模式"""
       id: int
       name: str
       description: Optional[str]
       task_type: str
       executor_group: str
       resource_requirements: Optional[Dict[str, Any]]
       config: Optional[Dict[str, Any]]
       timeout_seconds: int
       max_retry_count: int
       status: TaskStatus
       project_id: Optional[int]
       created_by: Optional[int]
       created_at: datetime
       updated_at: datetime
       
       class Config:
           from_attributes = True
   
   class TaskTriggerRequest(BaseModel):
       """手动触发任务请求模式"""
       task_definition_id: int = Field(..., description="任务定义ID")
       priority: str = Field(default="normal", description="优先级")
       parameters: Optional[Dict[str, Any]] = Field(None, description="任务参数")
       
       @validator('priority')
       def validate_priority(cls, v):
           """验证优先级"""
           allowed_priorities = ['low', 'normal', 'high', 'urgent']
           if v not in allowed_priorities:
               raise ValueError(f'不支持的优先级: {v}')
           return v
   ```

2. **创建执行器相关Schema**
   
   创建文件: `backend/app/schemas/executor.py`
   ```python
   from pydantic import BaseModel, Field, validator
   from typing import Optional, Dict, Any, List
   from datetime import datetime
   from enum import Enum
   
   class ExecutorStatus(str, Enum):
       """执行器状态枚举"""
       ONLINE = "online"
       OFFLINE = "offline"
       BUSY = "busy"
       MAINTENANCE = "maintenance"
   
   class ExecutorRegisterRequest(BaseModel):
       """执行器注册请求模式"""
       node_id: str = Field(..., min_length=1, max_length=100, description="节点ID")
       node_name: str = Field(..., min_length=1, max_length=255, description="节点名称")
       executor_group: str = Field(..., description="执行器分组")
       host_info: Dict[str, Any] = Field(..., description="主机信息")
       resource_capacity: Dict[str, Any] = Field(..., description="资源容量")
       supported_task_types: List[str] = Field(..., description="支持的任务类型")
       max_concurrent_tasks: int = Field(default=5, ge=1, description="最大并发任务数")
       tags: Optional[Dict[str, Any]] = Field(None, description="标签")
       
       @validator('host_info')
       def validate_host_info(cls, v):
           """验证主机信息"""
           required_keys = ['hostname', 'ip_address', 'port']
           for key in required_keys:
               if key not in v:
                   raise ValueError(f'缺少必需的主机信息: {key}')
           return v
   
   class ExecutorHeartbeatRequest(BaseModel):
       """执行器心跳请求模式"""
       status: ExecutorStatus = Field(..., description="状态")
       current_load: int = Field(..., ge=0, description="当前负载")
       resource_usage: Dict[str, Any] = Field(..., description="资源使用情况")
       running_tasks: List[Dict[str, Any]] = Field(default=[], description="运行中的任务")
   
   class ExecutorResponse(BaseModel):
       """执行器响应模式"""
       id: int
       node_id: str
       node_name: str
       executor_group: str
       status: ExecutorStatus
       current_load: int
       max_concurrent_tasks: int
       resource_usage: Optional[Dict[str, Any]]
       last_heartbeat: Optional[datetime]
       registered_at: datetime
       
       class Config:
           from_attributes = True
   ```

**交付物**:
- ✅ 完整的Pydantic Schema定义
- ✅ 数据验证规则完善
- ✅ API请求响应格式标准化

### 步骤1.4：创建CRUD操作

**时间估计**: 2天

**任务描述**: 创建数据库操作的CRUD函数

**具体操作**:

1. **创建任务相关CRUD**
   
   创建文件: `backend/app/crud/task.py`
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import and_, or_
   from typing import List, Optional, Dict, Any
   from datetime import datetime
   
   from app.models.task import TaskDefinition, TaskSchedule
   from app.schemas.task import TaskDefinitionCreate, TaskDefinitionUpdate
   
   class TaskDefinitionCRUD:
       """任务定义CRUD操作类"""
       
       def create(self, db: Session, *, obj_in: TaskDefinitionCreate, created_by: int) -> TaskDefinition:
           """创建任务定义"""
           db_obj = TaskDefinition(
               **obj_in.dict(),
               created_by=created_by
           )
           db.add(db_obj)
           db.commit()
           db.refresh(db_obj)
           return db_obj
       
       def get(self, db: Session, id: int) -> Optional[TaskDefinition]:
           """根据ID获取任务定义"""
           return db.query(TaskDefinition).filter(TaskDefinition.id == id).first()
       
       def get_multi(
           self, 
           db: Session, 
           *, 
           skip: int = 0, 
           limit: int = 100,
           task_type: Optional[str] = None,
           status: Optional[str] = None,
           project_id: Optional[int] = None
       ) -> List[TaskDefinition]:
           """获取任务定义列表"""
           query = db.query(TaskDefinition)
           
           if task_type:
               query = query.filter(TaskDefinition.task_type == task_type)
           if status:
               query = query.filter(TaskDefinition.status == status)
           if project_id:
               query = query.filter(TaskDefinition.project_id == project_id)
           
           return query.offset(skip).limit(limit).all()
       
       def update(
           self, 
           db: Session, 
           *, 
           db_obj: TaskDefinition, 
           obj_in: TaskDefinitionUpdate
       ) -> TaskDefinition:
           """更新任务定义"""
           update_data = obj_in.dict(exclude_unset=True)
           for field, value in update_data.items():
               setattr(db_obj, field, value)
           
           db_obj.updated_at = datetime.utcnow()
           db.commit()
           db.refresh(db_obj)
           return db_obj
       
       def delete(self, db: Session, *, id: int) -> TaskDefinition:
           """删除任务定义"""
           obj = db.query(TaskDefinition).get(id)
           db.delete(obj)
           db.commit()
           return obj
       
       def get_by_name(self, db: Session, *, name: str, project_id: Optional[int] = None) -> Optional[TaskDefinition]:
           """根据名称获取任务定义"""
           query = db.query(TaskDefinition).filter(TaskDefinition.name == name)
           if project_id:
               query = query.filter(TaskDefinition.project_id == project_id)
           return query.first()
   
   # 创建CRUD实例
   task_definition = TaskDefinitionCRUD()
   ```

2. **创建执行器相关CRUD**
   
   创建文件: `backend/app/crud/executor.py`
   ```python
   from sqlalchemy.orm import Session
   from sqlalchemy import and_
   from typing import List, Optional
   from datetime import datetime, timedelta
   
   from app.models.executor import ExecutorGroup, ExecutorNode
   from app.schemas.executor import ExecutorRegisterRequest
   
   class ExecutorNodeCRUD:
       """执行器节点CRUD操作类"""
       
       def register(
           self, 
           db: Session, 
           *, 
           obj_in: ExecutorRegisterRequest
       ) -> ExecutorNode:
           """注册执行器节点"""
           # 检查执行器分组是否存在
           group = db.query(ExecutorGroup).filter(
               ExecutorGroup.group_name == obj_in.executor_group
           ).first()
           
           if not group:
               raise ValueError(f"执行器分组 {obj_in.executor_group} 不存在")
           
           # 检查节点ID是否已存在
           existing = db.query(ExecutorNode).filter(
               ExecutorNode.node_id == obj_in.node_id
           ).first()
           
           if existing:
               # 更新现有节点信息
               for field, value in obj_in.dict().items():
                   if field != 'executor_group':
                       setattr(existing, field, value)
               existing.executor_group_id = group.id
               existing.status = "online"
               existing.last_heartbeat = datetime.utcnow()
               existing.updated_at = datetime.utcnow()
               db.commit()
               db.refresh(existing)
               return existing
           else:
               # 创建新节点
               db_obj = ExecutorNode(
                   **obj_in.dict(exclude={'executor_group'}),
                   executor_group_id=group.id,
                   status="online",
                   last_heartbeat=datetime.utcnow()
               )
               db.add(db_obj)
               db.commit()
               db.refresh(db_obj)
               return db_obj
       
       def update_heartbeat(
           self, 
           db: Session, 
           *, 
           node_id: str, 
           status: str,
           current_load: int,
           resource_usage: dict,
           running_tasks: list
       ) -> Optional[ExecutorNode]:
           """更新执行器心跳"""
           executor = db.query(ExecutorNode).filter(
               ExecutorNode.node_id == node_id
           ).first()
           
           if executor:
               executor.status = status
               executor.current_load = current_load
               executor.resource_usage = resource_usage
               executor.last_heartbeat = datetime.utcnow()
               executor.updated_at = datetime.utcnow()
               db.commit()
               db.refresh(executor)
           
           return executor
       
       def get_available_executors(
           self, 
           db: Session, 
           *, 
           executor_group: str
       ) -> List[ExecutorNode]:
           """获取可用的执行器节点"""
           # 心跳超时时间（2分钟）
           heartbeat_timeout = datetime.utcnow() - timedelta(minutes=2)
           
           return db.query(ExecutorNode).join(ExecutorGroup).filter(
               and_(
                   ExecutorGroup.group_name == executor_group,
                   ExecutorNode.status == "online",
                   ExecutorNode.last_heartbeat > heartbeat_timeout,
                   ExecutorNode.current_load < ExecutorNode.max_concurrent_tasks
               )
           ).all()
       
       def mark_offline_stale_executors(self, db: Session) -> int:
           """标记长时间未心跳的执行器为离线状态"""
           heartbeat_timeout = datetime.utcnow() - timedelta(minutes=5)
           
           count = db.query(ExecutorNode).filter(
               and_(
                   ExecutorNode.status == "online",
                   ExecutorNode.last_heartbeat < heartbeat_timeout
               )
           ).update({"status": "offline"})
           
           db.commit()
           return count
   
   # 创建CRUD实例
   executor_node = ExecutorNodeCRUD()
   ```

**交付物**:
- ✅ 完整的CRUD操作函数
- ✅ 数据库查询优化
- ✅ 错误处理机制完善

### 步骤1.5：创建基础API路由

**时间估计**: 2天

**任务描述**: 创建任务管理的基础API接口

**具体操作**:

1. **创建任务定义API**
   
   创建文件: `backend/app/api/v1/endpoints/tasks.py`
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Query
   from sqlalchemy.orm import Session
   from typing import List, Optional
   
   from app.api import deps
   from app.crud import task_definition
   from app.schemas.task import (
       TaskDefinitionCreate,
       TaskDefinitionUpdate,
       TaskDefinitionResponse,
       TaskTriggerRequest
   )
   from app.schemas.common import ResponseModel, PaginatedResponse
   
   router = APIRouter()
   
   @router.post("/definitions", response_model=ResponseModel[TaskDefinitionResponse])
   def create_task_definition(
       *,
       db: Session = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user),
       task_in: TaskDefinitionCreate
   ):
       """创建任务定义"""
       try:
           # 检查任务名称是否已存在
           existing = task_definition.get_by_name(
               db, name=task_in.name, project_id=task_in.project_id
           )
           if existing:
               raise HTTPException(
                   status_code=409,
                   detail="任务名称已存在"
               )
           
           # 创建任务定义
           task_def = task_definition.create(
               db, obj_in=task_in, created_by=current_user.id
           )
           
           return ResponseModel(
               code=200,
               message="任务定义创建成功",
               data=task_def
           )
       except Exception as e:
           raise HTTPException(status_code=400, detail=str(e))
   
   @router.get("/definitions", response_model=ResponseModel[PaginatedResponse[TaskDefinitionResponse]])
   def get_task_definitions(
       db: Session = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user),
       page: int = Query(1, ge=1),
       size: int = Query(20, ge=1, le=100),
       task_type: Optional[str] = Query(None),
       status: Optional[str] = Query(None),
       project_id: Optional[int] = Query(None)
   ):
       """获取任务定义列表"""
       skip = (page - 1) * size
       
       # 获取任务定义列表
       task_defs = task_definition.get_multi(
           db,
           skip=skip,
           limit=size,
           task_type=task_type,
           status=status,
           project_id=project_id
       )
       
       # 获取总数
       total = len(task_definition.get_multi(db, skip=0, limit=10000))
       
       return ResponseModel(
           code=200,
           message="success",
           data=PaginatedResponse(
               items=task_defs,
               total=total,
               page=page,
               size=size
           )
       )
   
   @router.get("/definitions/{task_id}", response_model=ResponseModel[TaskDefinitionResponse])
   def get_task_definition(
       task_id: int,
       db: Session = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user)
   ):
       """获取任务定义详情"""
       task_def = task_definition.get(db, id=task_id)
       if not task_def:
           raise HTTPException(status_code=404, detail="任务定义不存在")
       
       return ResponseModel(
           code=200,
           message="success",
           data=task_def
       )
   
   @router.put("/definitions/{task_id}", response_model=ResponseModel[TaskDefinitionResponse])
   def update_task_definition(
       task_id: int,
       task_in: TaskDefinitionUpdate,
       db: Session = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user)
   ):
       """更新任务定义"""
       task_def = task_definition.get(db, id=task_id)
       if not task_def:
           raise HTTPException(status_code=404, detail="任务定义不存在")
       
       updated_task = task_definition.update(db, db_obj=task_def, obj_in=task_in)
       
       return ResponseModel(
           code=200,
           message="任务定义更新成功",
           data=updated_task
       )
   
   @router.delete("/definitions/{task_id}")
   def delete_task_definition(
       task_id: int,
       db: Session = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user)
   ):
       """删除任务定义"""
       task_def = task_definition.get(db, id=task_id)
       if not task_def:
           raise HTTPException(status_code=404, detail="任务定义不存在")
       
       task_definition.delete(db, id=task_id)
       
       return ResponseModel(
           code=200,
           message="任务定义删除成功"
       )
   
   @router.post("/trigger", response_model=ResponseModel[dict])
   def trigger_task(
       trigger_request: TaskTriggerRequest,
       db: Session = Depends(deps.get_db),
       current_user = Depends(deps.get_current_user)
   ):
       """手动触发任务"""
       # 检查任务定义是否存在
       task_def = task_definition.get(db, id=trigger_request.task_definition_id)
       if not task_def:
           raise HTTPException(status_code=404, detail="任务定义不存在")
       
       # TODO: 实现任务触发逻辑
       # 这里暂时返回模拟数据
       task_instance_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{task_def.id:03d}"
       
       return ResponseModel(
           code=200,
           message="任务触发成功",
           data={
               "task_instance_id": task_instance_id,
               "status": "pending",
               "created_at": datetime.utcnow().isoformat()
           }
       )
   ```

2. **创建执行器管理API**
   
   创建文件: `backend/app/api/v1/endpoints/executors.py`
   ```python
   from fastapi import APIRouter, Depends, HTTPException, Query
   from sqlalchemy.orm import Session
   from typing import List, Optional
   
   from app.api import deps
   from app.crud import executor_node
   from app.schemas.executor import (
       ExecutorRegisterRequest,
       ExecutorHeartbeatRequest,
       ExecutorResponse
   )
   from app.schemas.common import ResponseModel
   
   router = APIRouter()
   
   @router.post("/register", response_model=ResponseModel[dict])
   def register_executor(
       register_request: ExecutorRegisterRequest,
       db: Session = Depends(deps.get_db)
   ):
       """执行器注册"""
       try:
           executor = executor_node.register(db, obj_in=register_request)
           
           # 生成注册令牌（简化版本）
           registration_token = f"token_{executor.node_id}_{int(datetime.utcnow().timestamp())}"
           
           return ResponseModel(
               code=200,
               message="执行器注册成功",
               data={
                   "node_id": executor.node_id,
                   "registration_token": registration_token,
                   "heartbeat_interval": 30,
                   "registered_at": executor.registered_at.isoformat()
               }
           )
       except Exception as e:
           raise HTTPException(status_code=400, detail=str(e))
   
   @router.post("/{node_id}/heartbeat", response_model=ResponseModel[dict])
   def executor_heartbeat(
       node_id: str,
       heartbeat_request: ExecutorHeartbeatRequest,
       db: Session = Depends(deps.get_db)
   ):
       """执行器心跳"""
       executor = executor_node.update_heartbeat(
           db,
           node_id=node_id,
           status=heartbeat_request.status,
           current_load=heartbeat_request.current_load,
           resource_usage=heartbeat_request.resource_usage,
           running_tasks=heartbeat_request.running_tasks
       )
       
       if not executor:
           raise HTTPException(status_code=404, detail="执行器不存在")
       
       return ResponseModel(
           code=200,
           message="心跳更新成功",
           data={
               "next_heartbeat_time": (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
               "commands": []  # TODO: 实现命令下发逻辑
           }
       )
   
   @router.get("", response_model=ResponseModel[List[ExecutorResponse]])
   def get_executors(
       db: Session = Depends(deps.get_db),
       group: Optional[str] = Query(None),
       status: Optional[str] = Query(None)
   ):
       """获取执行器列表"""
       # TODO: 实现执行器列表查询
       return ResponseModel(
           code=200,
           message="success",
           data=[]
       )
   ```

3. **更新API路由注册**
   
   修改文件: `backend/app/api/v1/api.py`
   ```python
   from fastapi import APIRouter
   
   from app.api.v1.endpoints import (
       auth, users, models, deployments, projects, datasets,
       # 新增任务管理路由
       tasks, executors, schedulers
   )
   
   api_router = APIRouter()
   
   # 现有路由
   api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
   api_router.include_router(users.router, prefix="/users", tags=["users"])
   api_router.include_router(models.router, prefix="/models", tags=["models"])
   api_router.include_router(deployments.router, prefix="/deployments", tags=["deployments"])
   api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
   api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
   
   # 新增任务管理路由
   api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
   api_router.include_router(executors.router, prefix="/executors", tags=["executors"])
   api_router.include_router(schedulers.router, prefix="/schedulers", tags=["schedulers"])
   ```

**交付物**:
- ✅ 基础API接口创建完成
- ✅ 请求响应格式标准化
- ✅ 错误处理机制完善
- ✅ API文档自动生成

---

## 阶段二：核心功能开发

### 步骤2.1：实现任务调度核心逻辑

**时间估计**: 3天

**任务描述**: 实现任务调度的核心算法和逻辑

**具体操作**:

1. **创建任务调度服务**
   
   创建文件: `backend/app/services/task_scheduler.py`
   ```python
   import asyncio
   import logging
   from datetime import datetime, timedelta
   from typing import List, Optional, Dict, Any
   from sqlalchemy.orm import Session
   from croniter import croniter
   
   from app.core.database import SessionLocal
   from app.crud import task_definition, task_schedule, task_instance
   from app.models.task import TaskSchedule, TaskInstance
   from app.services.task_queue import TaskQueue
   from app.services.load_balancer import LoadBalancer
   
   logger = logging.getLogger(__name__)
   
   class TaskScheduler:
       """任务调度器核心类"""
       
       def __init__(self):
           self.is_running = False
           self.is_leader = False
           self.schedule_interval = 10  # 调度间隔（秒）
           self.task_queue = TaskQueue()
           self.load_balancer = LoadBalancer()
       
       async def start(self):
           """启动调度器"""
           self.is_running = True
           logger.info("任务调度器启动")
           
           # 启动主调度循环
           await asyncio.gather(
               self.schedule_loop(),
               self.monitor_loop(),
               self.cleanup_loop()
           )
       
       async def stop(self):
           """停止调度器"""
           self.is_running = False
           logger.info("任务调度器停止")
       
       async def schedule_loop(self):
           """主调度循环"""
           while self.is_running:
               try:
                   if self.is_leader:
                       await self.process_scheduled_tasks()
                       await self.process_pending_tasks()
                   
                   await asyncio.sleep(self.schedule_interval)
               except Exception as e:
                   logger.error(f"调度循环异常: {e}")
                   await asyncio.sleep(5)
       
       async def process_scheduled_tasks(self):
           """处理定时任务"""
           db = SessionLocal()
           try:
               # 获取需要执行的定时任务
               now = datetime.utcnow()
               due_schedules = db.query(TaskSchedule).filter(
                   TaskSchedule.enabled == True,
                   TaskSchedule.next_run_time <= now
               ).all()
               
               for schedule in due_schedules:
                   await self.create_task_instance(db, schedule)
                   await self.update_next_run_time(db, schedule)
           
           finally:
               db.close()
       
       async def create_task_instance(self, db: Session, schedule: TaskSchedule):
           """创建任务实例"""
           try:
               # 检查最大并发实例数限制
               running_count = db.query(TaskInstance).filter(
                   TaskInstance.task_definition_id == schedule.task_definition_id,
                   TaskInstance.status.in_(['pending', 'running'])
               ).count()
               
               if running_count >= schedule.max_instances:
                   logger.warning(f"任务 {schedule.task_definition_id} 已达到最大并发实例数")
                   return
               
               # 生成任务实例ID
               instance_id = self.generate_instance_id(schedule.task_definition_id)
               
               # 创建任务实例
               task_inst = TaskInstance(
                   id=instance_id,
                   task_definition_id=schedule.task_definition_id,
                   task_schedule_id=schedule.id,
                   status='pending',
                   priority='normal',
                   parameters=schedule.parameters or {},
                   created_at=datetime.utcnow()
               )
               
               db.add(task_inst)
               db.commit()
               
               # 加入任务队列
               await self.task_queue.enqueue(task_inst)
               
               logger.info(f"创建任务实例: {instance_id}")
           
           except Exception as e:
               logger.error(f"创建任务实例失败: {e}")
               db.rollback()
       
       async def update_next_run_time(self, db: Session, schedule: TaskSchedule):
           """更新下次运行时间"""
           try:
               if schedule.schedule_type == 'cron':
                   cron = croniter(schedule.cron_expression, datetime.utcnow())
                   next_run = cron.get_next(datetime)
               elif schedule.schedule_type == 'interval':
                   next_run = datetime.utcnow() + timedelta(seconds=schedule.interval_seconds)
               elif schedule.schedule_type == 'once':
                   # 一次性任务，禁用调度
                   schedule.enabled = False
                   next_run = None
               else:
                   next_run = None
               
               schedule.next_run_time = next_run
               schedule.last_run_time = datetime.utcnow()
               db.commit()
           
           except Exception as e:
               logger.error(f"更新下次运行时间失败: {e}")
       
       async def process_pending_tasks(self):
           """处理待执行任务"""
           db = SessionLocal()
           try:
               # 获取待执行的任务
               pending_tasks = db.query(TaskInstance).filter(
                   TaskInstance.status == 'pending'
               ).order_by(
                   TaskInstance.priority.desc(),
                   TaskInstance.created_at.asc()
               ).limit(50).all()
               
               for task_inst in pending_tasks:
                   await self.assign_task_to_executor(db, task_inst)
           
           finally:
               db.close()
       
       async def assign_task_to_executor(self, db: Session, task_inst: TaskInstance):
           """将任务分配给执行器"""
           try:
               # 获取任务定义
               task_def = task_definition.get(db, id=task_inst.task_definition_id)
               if not task_def:
                   logger.error(f"任务定义不存在: {task_inst.task_definition_id}")
                   return
               
               # 选择执行器
               executor = await self.load_balancer.select_executor(
                   db, 
                   executor_group=task_def.executor_group,
                   resource_requirements=task_def.resource_requirements
               )
               
               if not executor:
                   logger.warning(f"没有可用的执行器: {task_def.executor_group}")
                   return
               
               # 分配任务
               task_inst.executor_node_id = executor.node_id
               task_inst.status = 'assigned'
               task_inst.assigned_at = datetime.utcnow()
               
               # 更新执行器负载
               executor.current_load += 1
               
               db.commit()
               
               # 通知执行器执行任务
               await self.notify_executor(executor, task_inst)
               
               logger.info(f"任务 {task_inst.id} 分配给执行器 {executor.node_id}")
           
           except Exception as e:
               logger.error(f"分配任务失败: {e}")
               db.rollback()
       
       async def notify_executor(self, executor, task_instance):
           """通知执行器执行任务"""
           # TODO: 实现执行器通知机制（WebSocket/HTTP回调）
           pass
       
       def generate_instance_id(self, task_definition_id: int) -> str:
           """生成任务实例ID"""
           timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
           return f"task_{timestamp}_{task_definition_id:03d}"
       
       async def monitor_loop(self):
           """监控循环"""
           while self.is_running:
               try:
                   await self.check_task_timeouts()
                   await self.check_executor_health()
                   await asyncio.sleep(30)
               except Exception as e:
                   logger.error(f"监控循环异常: {e}")
       
       async def cleanup_loop(self):
           """清理循环"""
           while self.is_running:
               try:
                   await self.cleanup_completed_tasks()
                   await asyncio.sleep(3600)  # 每小时清理一次
               except Exception as e:
                   logger.error(f"清理循环异常: {e}")
   ```

2. **创建任务队列服务**
   
   创建文件: `backend/app/services/task_queue.py`
   ```python
   import asyncio
   import json
   from typing import Dict, List, Optional
   from datetime import datetime
   from sqlalchemy.orm import Session
   
   from app.core.database import SessionLocal
   from app.models.task import TaskInstance, TaskQueue as TaskQueueModel
   
   class TaskQueue:
       """任务队列管理类"""
       
       def __init__(self):
           self.queues: Dict[str, asyncio.Queue] = {}
           self.queue_stats: Dict[str, dict] = {}
       
       async def enqueue(self, task_instance: TaskInstance):
           """将任务加入队列"""
           db = SessionLocal()
           try:
               # 获取执行器分组
               executor_group = task_instance.task_definition.executor_group
               
               # 创建队列记录
               queue_item = TaskQueueModel(
                   task_instance_id=task_instance.id,
                   executor_group=executor_group,
                   priority=task_instance.priority,
                   status='pending',
                   queued_at=datetime.utcnow()
               )
               
               db.add(queue_item)
               db.commit()
               
               # 更新队列统计
               self.update_queue_stats(executor_group, 'enqueue')
               
           finally:
               db.close()
       
       async def dequeue(self, executor_group: str) -> Optional[TaskInstance]:
           """从队列中取出任务"""
           db = SessionLocal()
           try:
               # 按优先级和创建时间排序获取任务
               queue_item = db.query(TaskQueueModel).filter(
                   TaskQueueModel.executor_group == executor_group,
                   TaskQueueModel.status == 'pending'
               ).order_by(
                   TaskQueueModel.priority.desc(),
                   TaskQueueModel.queued_at.asc()
               ).first()
               
               if queue_item:
                   # 标记为已分配
                   queue_item.status = 'assigned'
                   queue_item.assigned_at = datetime.utcnow()
                   db.commit()
                   
                   # 获取任务实例
                   task_instance = db.query(TaskInstance).filter(
                       TaskInstance.id == queue_item.task_instance_id
                   ).first()
                   
                   # 更新队列统计
                   self.update_queue_stats(executor_group, 'dequeue')
                   
                   return task_instance
               
               return None
           
           finally:
               db.close()
       
       def get_queue_status(self, executor_group: str) -> dict:
           """获取队列状态"""
           db = SessionLocal()
           try:
               pending_count = db.query(TaskQueueModel).filter(
                   TaskQueueModel.executor_group == executor_group,
                   TaskQueueModel.status == 'pending'
               ).count()
               
               running_count = db.query(TaskQueueModel).filter(
                   TaskQueueModel.executor_group == executor_group,
                   TaskQueueModel.status == 'running'
               ).count()
               
               return {
                   'executor_group': executor_group,
                   'pending_count': pending_count,
                   'running_count': running_count,
                   'total_count': pending_count + running_count
               }
           
           finally:
               db.close()
       
       def update_queue_stats(self, executor_group: str, operation: str):
           """更新队列统计信息"""
           if executor_group not in self.queue_stats:
               self.queue_stats[executor_group] = {
                   'enqueue_count': 0,
                   'dequeue_count': 0,
                   'last_activity': datetime.utcnow()
               }
           
           if operation == 'enqueue':
               self.queue_stats[executor_group]['enqueue_count'] += 1
           elif operation == 'dequeue':
               self.queue_stats[executor_group]['dequeue_count'] += 1
           
           self.queue_stats[executor_group]['last_activity'] = datetime.utcnow()
   ```

3. **创建负载均衡服务**
   
   创建文件: `backend/app/services/load_balancer.py`
   ```python
   import random
   from typing import List, Optional, Dict, Any
   from sqlalchemy.orm import Session
   
   from app.crud import executor_node
   from app.models.executor import ExecutorNode
   
   class LoadBalancer:
       """负载均衡器类"""
       
       def __init__(self):
           self.strategies = {
               'round_robin': self.round_robin_select,
               'least_connections': self.least_connections_select,
               'resource_based': self.resource_based_select,
               'random': self.random_select
           }
           self.round_robin_counters: Dict[str, int] = {}
       
       async def select_executor(
           self, 
           db: Session, 
           executor_group: str,
           resource_requirements: Optional[Dict[str, Any]] = None,
           strategy: str = 'least_connections'
       ) -> Optional[ExecutorNode]:
           """选择执行器"""
           # 获取可用执行器
           available_executors = executor_node.get_available_executors(
               db, executor_group=executor_group
           )
           
           if not available_executors:
               return None
           
           # 资源过滤
           if resource_requirements:
               available_executors = self.filter_by_resources(
                   available_executors, resource_requirements
               )
           
           if not available_executors:
               return None
           
           # 应用负载均衡策略
           strategy_func = self.strategies.get(strategy, self.least_connections_select)
           return strategy_func(available_executors, executor_group)
       
       def round_robin_select(self, executors: List[ExecutorNode], group: str) -> ExecutorNode:
           """轮询选择"""
           if group not in self.round_robin_counters:
               self.round_robin_counters[group] = 0
           
           selected = executors[self.round_robin_counters[group] % len(executors)]
           self.round_robin_counters[group] += 1
           return selected
       
       def least_connections_select(self, executors: List[ExecutorNode], group: str) -> ExecutorNode:
           """最少连接选择"""
           return min(executors, key=lambda x: x.current_load)
       
       def resource_based_select(self, executors: List[ExecutorNode], group: str) -> ExecutorNode:
           """基于资源的选择"""
           # 计算资源利用率得分
           def resource_score(executor):
               usage = executor.resource_usage or {}
               cpu_usage = usage.get('cpu_percent', 0)
               memory_usage = usage.get('memory_percent', 0)
               return (cpu_usage + memory_usage) / 2
           
           return min(executors, key=resource_score)
       
       def random_select(self, executors: List[ExecutorNode], group: str) -> ExecutorNode:
           """随机选择"""
           return random.choice(executors)
       
       def filter_by_resources(
           self, 
           executors: List[ExecutorNode], 
           requirements: Dict[str, Any]
       ) -> List[ExecutorNode]:
           """根据资源需求过滤执行器"""
           filtered = []
           
           for executor in executors:
               capacity = executor.resource_capacity or {}
               usage = executor.resource_usage or {}
               
               # 检查CPU需求
               if 'cpu_cores' in requirements:
                   available_cpu = capacity.get('cpu_cores', 0) - usage.get('cpu_cores', 0)
                   if available_cpu < requirements['cpu_cores']:
                       continue
               
               # 检查内存需求
               if 'memory_gb' in requirements:
                   available_memory = capacity.get('memory_gb', 0) - usage.get('memory_gb', 0)
                   if available_memory < requirements['memory_gb']:
                       continue
               
               # 检查GPU需求
               if 'gpu' in requirements and requirements['gpu'] > 0:
                   available_gpu = capacity.get('gpu', 0) - usage.get('gpu', 0)
                   if available_gpu < requirements['gpu']:
                       continue
               
               filtered.append(executor)
           
           return filtered
   ```

**交付物**:
- ✅ 任务调度核心逻辑实现
- ✅ 任务队列管理机制
- ✅ 负载均衡算法实现
- ✅ 资源匹配和过滤机制

### 步骤2.2：实现执行器注册和管理

**时间估计**: 2天

**任务描述**: 实现执行器的注册、心跳、状态管理等功能

**具体操作**:

1. **创建执行器管理服务**
   
   创建文件: `backend/app/services/executor_manager.py`
   ```python
   import asyncio
   import logging
   from datetime import datetime, timedelta
   from typing import List, Dict, Any, Optional
   from sqlalchemy.orm import Session
   
   from app.core.database import SessionLocal
   from app.crud import executor_node, executor_group
   from app.models.executor import ExecutorNode, ExecutorStatus
   from app.services.notification import NotificationService
   
   logger = logging.getLogger(__name__)
   
   class ExecutorManager:
       """执行器管理器"""
       
       def __init__(self):
           self.heartbeat_timeout = 300  # 5分钟心跳超时
           self.cleanup_interval = 60    # 1分钟清理间隔
           self.notification_service = NotificationService()
           self.is_running = False
       
       async def start(self):
           """启动执行器管理器"""
           self.is_running = True
           logger.info("执行器管理器启动")
           
           # 启动监控循环
           await asyncio.gather(
               self.health_check_loop(),
               self.cleanup_loop(),
               self.metrics_collection_loop()
           )
       
       async def stop(self):
           """停止执行器管理器"""
           self.is_running = False
           logger.info("执行器管理器停止")
       
       async def register_executor(
           self, 
           db: Session, 
           registration_data: Dict[str, Any]
       ) -> Dict[str, Any]:
           """注册执行器"""
           try:
               # 验证执行器分组
               group = executor_group.get_by_name(
                   db, name=registration_data['executor_group']
               )
               if not group:
                   raise ValueError(f"执行器分组不存在: {registration_data['executor_group']}")
               
               # 检查节点ID是否已存在
               existing = executor_node.get_by_node_id(
                   db, node_id=registration_data['node_id']
               )
               
               if existing:
                   # 更新现有执行器
                   updated_executor = await self.update_executor_info(
                       db, existing, registration_data
                   )
                   return self.generate_registration_response(updated_executor)
               else:
                   # 创建新执行器
                   new_executor = await self.create_new_executor(
                       db, registration_data, group.id
                   )
                   return self.generate_registration_response(new_executor)
           
           except Exception as e:
               logger.error(f"执行器注册失败: {e}")
               raise
       
       async def update_heartbeat(
           self, 
           db: Session, 
           node_id: str, 
           heartbeat_data: Dict[str, Any]
       ) -> Dict[str, Any]:
           """更新执行器心跳"""
           executor = executor_node.get_by_node_id(db, node_id=node_id)
           if not executor:
               raise ValueError(f"执行器不存在: {node_id}")
           
           # 更新心跳信息
           executor.status = heartbeat_data['status']
           executor.current_load = heartbeat_data['current_load']
           executor.resource_usage = heartbeat_data['resource_usage']
           executor.last_heartbeat = datetime.utcnow()
           executor.updated_at = datetime.utcnow()
           
           db.commit()
           
           # 检查是否有待执行的命令
           commands = await self.get_pending_commands(db, node_id)
           
           return {
               'next_heartbeat_time': (datetime.utcnow() + timedelta(seconds=30)).isoformat(),
               'commands': commands,
               'status': 'success'
           }
       
       async def health_check_loop(self):
           """健康检查循环"""
           while self.is_running:
               try:
                   await self.check_executor_health()
                   await asyncio.sleep(60)  # 每分钟检查一次
               except Exception as e:
                   logger.error(f"健康检查异常: {e}")
       
       async def check_executor_health(self):
           """检查执行器健康状态"""
           db = SessionLocal()
           try:
               timeout_threshold = datetime.utcnow() - timedelta(seconds=self.heartbeat_timeout)
               
               # 查找超时的执行器
               timeout_executors = db.query(ExecutorNode).filter(
                   ExecutorNode.status == ExecutorStatus.ONLINE,
                   ExecutorNode.last_heartbeat < timeout_threshold
               ).all()
               
               for executor in timeout_executors:
                   logger.warning(f"执行器心跳超时: {executor.node_id}")
                   
                   # 标记为离线
                   executor.status = ExecutorStatus.OFFLINE
                   executor.updated_at = datetime.utcnow()
                   
                   # 发送告警通知
                   await self.notification_service.send_alert(
                       'executor_offline',
                       f"执行器 {executor.node_id} 离线",
                       {'executor_id': executor.id, 'node_id': executor.node_id}
                   )
               
               if timeout_executors:
                   db.commit()
                   logger.info(f"标记 {len(timeout_executors)} 个执行器为离线状态")
           
           finally:
               db.close()
   ```

2. **创建执行器客户端SDK**
   
   创建文件: `executor_sdk/executor_client.py`
   ```python
   import asyncio
   import aiohttp
   import logging
   import psutil
   import socket
   from datetime import datetime
   from typing import Dict, Any, List, Optional, Callable
   
   logger = logging.getLogger(__name__)
   
   class ExecutorClient:
       """执行器客户端"""
       
       def __init__(
           self, 
           server_url: str,
           node_id: str,
           node_name: str,
           executor_group: str,
           max_concurrent_tasks: int = 5
       ):
           self.server_url = server_url.rstrip('/')
           self.node_id = node_id
           self.node_name = node_name
           self.executor_group = executor_group
           self.max_concurrent_tasks = max_concurrent_tasks
           
           self.is_running = False
           self.registration_token = None
           self.heartbeat_interval = 30
           self.running_tasks: Dict[str, asyncio.Task] = {}
           self.task_handlers: Dict[str, Callable] = {}
           
           # 系统信息
           self.host_info = self.get_host_info()
           self.resource_capacity = self.get_resource_capacity()
       
       async def start(self):
           """启动执行器客户端"""
           self.is_running = True
           logger.info(f"执行器客户端启动: {self.node_id}")
           
           try:
               # 注册到服务器
               await self.register()
               
               # 启动心跳和任务处理循环
               await asyncio.gather(
                   self.heartbeat_loop(),
                   self.task_processing_loop()
               )
           except Exception as e:
               logger.error(f"执行器启动失败: {e}")
               raise
       
       async def stop(self):
           """停止执行器客户端"""
           self.is_running = False
           
           # 等待所有任务完成
           if self.running_tasks:
               logger.info(f"等待 {len(self.running_tasks)} 个任务完成...")
               await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
           
           logger.info("执行器客户端停止")
       
       async def register(self):
           """注册到服务器"""
           registration_data = {
               'node_id': self.node_id,
               'node_name': self.node_name,
               'executor_group': self.executor_group,
               'host_info': self.host_info,
               'resource_capacity': self.resource_capacity,
               'supported_task_types': list(self.task_handlers.keys()),
               'max_concurrent_tasks': self.max_concurrent_tasks
           }
           
           async with aiohttp.ClientSession() as session:
               async with session.post(
                   f"{self.server_url}/api/v1/executors/register",
                   json=registration_data
               ) as response:
                   if response.status == 200:
                       result = await response.json()
                       self.registration_token = result['data']['registration_token']
                       self.heartbeat_interval = result['data'].get('heartbeat_interval', 30)
                       logger.info(f"执行器注册成功: {self.node_id}")
                   else:
                       error_text = await response.text()
                       raise Exception(f"注册失败: {response.status} - {error_text}")
       
       async def heartbeat_loop(self):
           """心跳循环"""
           while self.is_running:
               try:
                   await self.send_heartbeat()
                   await asyncio.sleep(self.heartbeat_interval)
               except Exception as e:
                   logger.error(f"心跳发送失败: {e}")
                   await asyncio.sleep(5)
       
       async def send_heartbeat(self):
           """发送心跳"""
           heartbeat_data = {
               'status': 'online' if len(self.running_tasks) < self.max_concurrent_tasks else 'busy',
               'current_load': len(self.running_tasks),
               'resource_usage': self.get_resource_usage(),
               'running_tasks': [{
                   'task_id': task_id,
                   'start_time': task.get_name() if hasattr(task, 'get_name') else 'unknown'
               } for task_id, task in self.running_tasks.items()]
           }
           
           async with aiohttp.ClientSession() as session:
               async with session.post(
                   f"{self.server_url}/api/v1/executors/{self.node_id}/heartbeat",
                   json=heartbeat_data
               ) as response:
                   if response.status == 200:
                       result = await response.json()
                       # 处理服务器返回的命令
                       commands = result['data'].get('commands', [])
                       for command in commands:
                           await self.handle_command(command)
                   else:
                       logger.warning(f"心跳响应异常: {response.status}")
       
       def register_task_handler(self, task_type: str, handler: Callable):
           """注册任务处理器"""
           self.task_handlers[task_type] = handler
           logger.info(f"注册任务处理器: {task_type}")
       
       def get_host_info(self) -> Dict[str, Any]:
           """获取主机信息"""
           return {
               'hostname': socket.gethostname(),
               'ip_address': socket.gethostbyname(socket.gethostname()),
               'port': 8080,  # 可配置
               'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown',
               'python_version': f"{psutil.version_info.major}.{psutil.version_info.minor}"
           }
       
       def get_resource_capacity(self) -> Dict[str, Any]:
           """获取资源容量"""
           return {
               'cpu_cores': psutil.cpu_count(),
               'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
               'disk_gb': round(psutil.disk_usage('/').total / (1024**3), 2),
               'gpu': 0  # 需要根据实际情况配置
           }
       
       def get_resource_usage(self) -> Dict[str, Any]:
           """获取资源使用情况"""
           return {
               'cpu_percent': psutil.cpu_percent(interval=1),
               'memory_percent': psutil.virtual_memory().percent,
               'disk_percent': psutil.disk_usage('/').percent,
               'cpu_cores': len(self.running_tasks),  # 简化计算
               'memory_gb': round(psutil.virtual_memory().used / (1024**3), 2)
           }
   ```

**交付物**:
- ✅ 执行器管理服务实现
- ✅ 执行器客户端SDK
- ✅ 心跳和健康检查机制
- ✅ 资源监控和报告功能

### 步骤2.3：实现调度器集群和Leader选举

**时间估计**: 3天

**任务描述**: 实现调度器的高可用集群和Leader选举机制

**具体操作**:

1. **创建调度器集群管理服务**
   
   创建文件: `backend/app/services/scheduler_cluster.py`
   ```python
   import asyncio
   import logging
   import uuid
   from datetime import datetime, timedelta
   from typing import Optional, Dict, Any
   from sqlalchemy.orm import Session
   
   from app.core.database import SessionLocal
   from app.crud import scheduler_node
   from app.models.scheduler import SchedulerNode, SchedulerRole, SchedulerStatus
   from app.services.distributed_lock import DistributedLock
   
   logger = logging.getLogger(__name__)
   
   class SchedulerCluster:
       """调度器集群管理类"""
       
       def __init__(self, node_id: str = None):
           self.node_id = node_id or str(uuid.uuid4())
           self.node_name = f"scheduler-{self.node_id[:8]}"
           self.is_running = False
           self.is_leader = False
           self.leader_lease_duration = 60  # Leader租约时长（秒）
           self.election_timeout = 30       # 选举超时时间（秒）
           self.heartbeat_interval = 15     # 心跳间隔（秒）
           
           self.distributed_lock = DistributedLock()
           self.current_term = 0
           self.voted_for = None
           self.last_heartbeat = datetime.utcnow()
       
       async def start(self):
           """启动调度器节点"""
           self.is_running = True
           logger.info(f"调度器节点启动: {self.node_id}")
           
           # 注册节点
           await self.register_node()
           
           # 启动各种循环
           await asyncio.gather(
               self.leader_election_loop(),
               self.heartbeat_loop(),
               self.cluster_monitor_loop()
           )
       
       async def stop(self):
           """停止调度器节点"""
           self.is_running = False
           
           # 如果是Leader，释放Leader锁
           if self.is_leader:
               await self.release_leadership()
           
           # 更新节点状态为非活跃
           await self.update_node_status(SchedulerStatus.INACTIVE)
           
           logger.info(f"调度器节点停止: {self.node_id}")
       
       async def register_node(self):
           """注册调度器节点"""
           db = SessionLocal()
           try:
               # 检查节点是否已存在
               existing = scheduler_node.get_by_node_id(db, node_id=self.node_id)
               
               if existing:
                   # 更新现有节点
                   existing.status = SchedulerStatus.ACTIVE
                   existing.last_heartbeat = datetime.utcnow()
                   existing.updated_at = datetime.utcnow()
               else:
                   # 创建新节点
                   new_node = SchedulerNode(
                       node_id=self.node_id,
                       node_name=self.node_name,
                       host_info=self.get_host_info(),
                       role=SchedulerRole.FOLLOWER,
                       status=SchedulerStatus.ACTIVE,
                       priority=100,
                       capabilities=['task_scheduling', 'load_balancing'],
                       last_heartbeat=datetime.utcnow()
                   )
                   db.add(new_node)
               
               db.commit()
               logger.info(f"调度器节点注册成功: {self.node_id}")
           
           finally:
               db.close()
       
       async def leader_election_loop(self):
           """Leader选举循环"""
           while self.is_running:
               try:
                   if not self.is_leader:
                       await self.attempt_leader_election()
                   else:
                       await self.maintain_leadership()
                   
                   await asyncio.sleep(5)
               except Exception as e:
                   logger.error(f"Leader选举异常: {e}")
                   await asyncio.sleep(10)
       
       async def attempt_leader_election(self):
           """尝试Leader选举"""
           db = SessionLocal()
           try:
               # 检查是否已有活跃的Leader
               current_leader = db.query(SchedulerNode).filter(
                   SchedulerNode.role == SchedulerRole.LEADER,
                   SchedulerNode.status == SchedulerStatus.ACTIVE,
                   SchedulerNode.leader_lease_expires_at > datetime.utcnow()
               ).first()
               
               if current_leader and current_leader.node_id != self.node_id:
                   # 已有Leader，等待
                   logger.debug(f"当前Leader: {current_leader.node_id}")
                   return
               
               # 尝试获取Leader锁
               lock_acquired = await self.distributed_lock.acquire(
                   'scheduler_leader_election',
                   self.node_id,
                   self.leader_lease_duration
               )
               
               if lock_acquired:
                   await self.become_leader(db)
           
           finally:
               db.close()
       
       async def become_leader(self, db: Session):
           """成为Leader"""
           try:
               # 更新节点角色为Leader
               node = scheduler_node.get_by_node_id(db, node_id=self.node_id)
               if node:
                   node.role = SchedulerRole.LEADER
                   node.leader_lease_expires_at = datetime.utcnow() + timedelta(seconds=self.leader_lease_duration)
                   node.updated_at = datetime.utcnow()
                   db.commit()
                   
                   self.is_leader = True
                   logger.info(f"成为Leader: {self.node_id}")
                   
                   # 通知其他节点
                   await self.notify_leadership_change()
           
           except Exception as e:
               logger.error(f"成为Leader失败: {e}")
               db.rollback()
       
       async def maintain_leadership(self):
           """维护Leader身份"""
           db = SessionLocal()
           try:
               # 续约Leader锁
               lock_renewed = await self.distributed_lock.renew(
                   'scheduler_leader_election',
                   self.node_id,
                   self.leader_lease_duration
               )
               
               if lock_renewed:
                   # 更新租约过期时间
                   node = scheduler_node.get_by_node_id(db, node_id=self.node_id)
                   if node:
                       node.leader_lease_expires_at = datetime.utcnow() + timedelta(seconds=self.leader_lease_duration)
                       node.updated_at = datetime.utcnow()
                       db.commit()
               else:
                   # 失去Leader身份
                   await self.lose_leadership(db)
           
           finally:
               db.close()
       
       async def lose_leadership(self, db: Session):
           """失去Leader身份"""
           try:
               node = scheduler_node.get_by_node_id(db, node_id=self.node_id)
               if node:
                   node.role = SchedulerRole.FOLLOWER
                   node.leader_lease_expires_at = None
                   node.updated_at = datetime.utcnow()
                   db.commit()
               
               self.is_leader = False
               logger.warning(f"失去Leader身份: {self.node_id}")
           
           except Exception as e:
               logger.error(f"失去Leader身份处理异常: {e}")
       
       async def heartbeat_loop(self):
           """心跳循环"""
           while self.is_running:
               try:
                   await self.send_heartbeat()
                   await asyncio.sleep(self.heartbeat_interval)
               except Exception as e:
                   logger.error(f"心跳发送失败: {e}")
       
       async def send_heartbeat(self):
           """发送心跳"""
           db = SessionLocal()
           try:
               node = scheduler_node.get_by_node_id(db, node_id=self.node_id)
               if node:
                   node.last_heartbeat = datetime.utcnow()
                   node.metrics = self.get_node_metrics()
                   node.updated_at = datetime.utcnow()
                   db.commit()
           
           finally:
               db.close()
       
       def get_host_info(self) -> Dict[str, Any]:
           """获取主机信息"""
           import socket
           import psutil
           
           return {
               'hostname': socket.gethostname(),
               'ip_address': socket.gethostbyname(socket.gethostname()),
               'port': 8000,
               'pid': psutil.Process().pid,
               'start_time': datetime.utcnow().isoformat()
           }
       
       def get_node_metrics(self) -> Dict[str, Any]:
           """获取节点性能指标"""
           import psutil
           
           return {
               'cpu_percent': psutil.cpu_percent(interval=1),
               'memory_percent': psutil.virtual_memory().percent,
               'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0],
               'is_leader': self.is_leader,
               'uptime_seconds': (datetime.utcnow() - self.last_heartbeat).total_seconds()
           }
   ```

2. **创建分布式锁服务**
   
   创建文件: `backend/app/services/distributed_lock.py`
   ```python
   import asyncio
   import logging
   from datetime import datetime, timedelta
   from typing import Optional, Dict, Any
   from sqlalchemy.orm import Session
   from sqlalchemy import text
   
   from app.core.database import SessionLocal
   
   logger = logging.getLogger(__name__)
   
   class DistributedLock:
       """基于数据库的分布式锁实现"""
       
       def __init__(self):
           self.locks: Dict[str, Dict[str, Any]] = {}
       
       async def acquire(
           self, 
           lock_name: str, 
           owner_id: str, 
           lease_duration: int = 60
       ) -> bool:
           """获取分布式锁"""
           db = SessionLocal()
           try:
               expires_at = datetime.utcnow() + timedelta(seconds=lease_duration)
               
               # 尝试插入锁记录
               result = db.execute(text("""
                   INSERT INTO acwl_distributed_locks 
                   (lock_name, owner_id, expires_at, created_at) 
                   VALUES (:lock_name, :owner_id, :expires_at, :created_at)
                   ON DUPLICATE KEY UPDATE 
                   owner_id = CASE 
                       WHEN expires_at < :now THEN :owner_id 
                       ELSE owner_id 
                   END,
                   expires_at = CASE 
                       WHEN expires_at < :now THEN :expires_at 
                       ELSE expires_at 
                   END,
                   updated_at = :created_at
               """), {
                   'lock_name': lock_name,
                   'owner_id': owner_id,
                   'expires_at': expires_at,
                   'created_at': datetime.utcnow(),
                   'now': datetime.utcnow()
               })
               
               db.commit()
               
               # 检查是否成功获取锁
               lock_record = db.execute(text("""
                   SELECT owner_id FROM acwl_distributed_locks 
                   WHERE lock_name = :lock_name AND expires_at > :now
               """), {
                   'lock_name': lock_name,
                   'now': datetime.utcnow()
               }).fetchone()
               
               if lock_record and lock_record[0] == owner_id:
                   logger.debug(f"获取锁成功: {lock_name} by {owner_id}")
                   return True
               else:
                   logger.debug(f"获取锁失败: {lock_name} by {owner_id}")
                   return False
           
           except Exception as e:
               logger.error(f"获取锁异常: {e}")
               db.rollback()
               return False
           finally:
               db.close()
       
       async def renew(
           self, 
           lock_name: str, 
           owner_id: str, 
           lease_duration: int = 60
       ) -> bool:
           """续约分布式锁"""
           db = SessionLocal()
           try:
               expires_at = datetime.utcnow() + timedelta(seconds=lease_duration)
               
               result = db.execute(text("""
                   UPDATE acwl_distributed_locks 
                   SET expires_at = :expires_at, updated_at = :updated_at
                   WHERE lock_name = :lock_name AND owner_id = :owner_id AND expires_at > :now
               """), {
                   'lock_name': lock_name,
                   'owner_id': owner_id,
                   'expires_at': expires_at,
                   'updated_at': datetime.utcnow(),
                   'now': datetime.utcnow()
               })
               
               db.commit()
               
               if result.rowcount > 0:
                   logger.debug(f"续约锁成功: {lock_name} by {owner_id}")
                   return True
               else:
                   logger.debug(f"续约锁失败: {lock_name} by {owner_id}")
                   return False
           
           except Exception as e:
               logger.error(f"续约锁异常: {e}")
               db.rollback()
               return False
           finally:
               db.close()
       
       async def release(self, lock_name: str, owner_id: str) -> bool:
           """释放分布式锁"""
           db = SessionLocal()
           try:
               result = db.execute(text("""
                   DELETE FROM acwl_distributed_locks 
                   WHERE lock_name = :lock_name AND owner_id = :owner_id
               """), {
                   'lock_name': lock_name,
                   'owner_id': owner_id
               })
               
               db.commit()
               
               if result.rowcount > 0:
                   logger.debug(f"释放锁成功: {lock_name} by {owner_id}")
                   return True
               else:
                   logger.debug(f"释放锁失败: {lock_name} by {owner_id}")
                   return False
           
           except Exception as e:
               logger.error(f"释放锁异常: {e}")
               db.rollback()
               return False
           finally:
               db.close()
       
       async def cleanup_expired_locks(self):
           """清理过期的锁"""
           db = SessionLocal()
           try:
               result = db.execute(text("""
                   DELETE FROM acwl_distributed_locks 
                   WHERE expires_at < :now
               """), {
                   'now': datetime.utcnow()
               })
               
               db.commit()
               
               if result.rowcount > 0:
                   logger.info(f"清理过期锁: {result.rowcount} 个")
           
           except Exception as e:
               logger.error(f"清理过期锁异常: {e}")
           finally:
               db.close()
   ```

**交付物**:
- ✅ 调度器集群管理实现
- ✅ Leader选举机制
- ✅ 分布式锁服务
- ✅ 节点心跳和监控

### 步骤2.4：集成任务调度和执行流程

**时间估计**: 2天

**任务描述**: 将调度器、执行器和任务管理整合成完整的工作流程

**具体操作**:

1. **创建任务调度主服务**
   
   创建文件: `backend/app/services/task_orchestrator.py`
   ```python
   import asyncio
   import logging
   from datetime import datetime
   from typing import Dict, Any, Optional
   
   from app.services.task_scheduler import TaskScheduler
   from app.services.executor_manager import ExecutorManager
   from app.services.scheduler_cluster import SchedulerCluster
   from app.services.monitoring import MonitoringService
   
   logger = logging.getLogger(__name__)
   
   class TaskOrchestrator:
       """任务编排器 - 整合所有任务管理组件"""
       
       def __init__(self, node_id: str = None):
           self.node_id = node_id
           self.is_running = False
           
           # 初始化各个服务组件
           self.scheduler_cluster = SchedulerCluster(node_id)
           self.task_scheduler = TaskScheduler()
           self.executor_manager = ExecutorManager()
           self.monitoring_service = MonitoringService()
       
       async def start(self):
           """启动任务编排器"""
           self.is_running = True
           logger.info("任务编排器启动")
           
           try:
               # 启动所有服务组件
               await asyncio.gather(
                   self.scheduler_cluster.start(),
                   self.executor_manager.start(),
                   self.monitoring_service.start(),
                   self.start_task_scheduler_when_leader()
               )
           except Exception as e:
               logger.error(f"任务编排器启动失败: {e}")
               raise
       
       async def stop(self):
           """停止任务编排器"""
           self.is_running = False
           logger.info("任务编排器停止")
           
           # 停止所有服务组件
           await asyncio.gather(
               self.task_scheduler.stop(),
               self.executor_manager.stop(),
               self.scheduler_cluster.stop(),
               self.monitoring_service.stop(),
               return_exceptions=True
           )
       
       async def start_task_scheduler_when_leader(self):
           """当成为Leader时启动任务调度器"""
           while self.is_running:
               try:
                   if self.scheduler_cluster.is_leader:
                       if not self.task_scheduler.is_running:
                           logger.info("作为Leader启动任务调度器")
                           await self.task_scheduler.start()
                   else:
                       if self.task_scheduler.is_running:
                           logger.info("不再是Leader，停止任务调度器")
                           await self.task_scheduler.stop()
                   
                   await asyncio.sleep(10)
               except Exception as e:
                   logger.error(f"Leader状态检查异常: {e}")
                   await asyncio.sleep(5)
       
       def get_status(self) -> Dict[str, Any]:
           """获取编排器状态"""
           return {
               'node_id': self.node_id,
               'is_running': self.is_running,
               'is_leader': self.scheduler_cluster.is_leader,
               'scheduler_running': self.task_scheduler.is_running,
               'executor_manager_running': self.executor_manager.is_running,
               'uptime': datetime.utcnow().isoformat()
           }
   ```

**交付物**:
- ✅ 任务编排器集成实现
- ✅ 服务组件协调机制
- ✅ Leader切换时的调度器启停
- ✅ 统一的状态管理接口

---

## 阶段三：高级功能开发

### 步骤3.1：实现监控和日志系统

**时间估计**: 2天

**任务描述**: 实现系统监控、日志收集和告警功能

**具体操作**:

1. **创建监控服务**
   
   创建文件: `backend/app/services/monitoring.py`
   ```python
   import asyncio
   import logging
   from datetime import datetime, timedelta
   from typing import Dict, Any, List
   from sqlalchemy.orm import Session
   
   from app.core.database import SessionLocal
   from app.models.monitoring import SystemMetrics, AlertRule, AlertLog
   from app.services.notification import NotificationService
   
   logger = logging.getLogger(__name__)
   
   class MonitoringService:
       """监控服务"""
       
       def __init__(self):
           self.is_running = False
           self.collection_interval = 60  # 指标收集间隔（秒）
           self.notification_service = NotificationService()
           self.alert_rules: List[Dict[str, Any]] = []
       
       async def start(self):
           """启动监控服务"""
           self.is_running = True
           logger.info("监控服务启动")
           
           # 加载告警规则
           await self.load_alert_rules()
           
           # 启动监控循环
           await asyncio.gather(
               self.metrics_collection_loop(),
               self.alert_evaluation_loop(),
               self.cleanup_loop()
           )
       
       async def stop(self):
           """停止监控服务"""
           self.is_running = False
           logger.info("监控服务停止")
       
       async def metrics_collection_loop(self):
           """指标收集循环"""
           while self.is_running:
               try:
                   await self.collect_system_metrics()
                   await self.collect_task_metrics()
                   await self.collect_executor_metrics()
                   await asyncio.sleep(self.collection_interval)
               except Exception as e:
                   logger.error(f"指标收集异常: {e}")
       
       async def collect_system_metrics(self):
           """收集系统指标"""
           import psutil
           
           db = SessionLocal()
           try:
               metrics = SystemMetrics(
                   metric_type='system',
                   metric_name='resource_usage',
                   metric_value={
                       'cpu_percent': psutil.cpu_percent(interval=1),
                       'memory_percent': psutil.virtual_memory().percent,
                       'disk_percent': psutil.disk_usage('/').percent,
                       'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                   },
                   collected_at=datetime.utcnow()
               )
               
               db.add(metrics)
               db.commit()
           
           finally:
               db.close()
       
       async def alert_evaluation_loop(self):
           """告警评估循环"""
           while self.is_running:
               try:
                   await self.evaluate_alerts()
                   await asyncio.sleep(30)  # 每30秒评估一次
               except Exception as e:
                   logger.error(f"告警评估异常: {e}")
       
       async def evaluate_alerts(self):
           """评估告警规则"""
           db = SessionLocal()
           try:
               for rule in self.alert_rules:
                   await self.evaluate_single_alert(db, rule)
           finally:
               db.close()
       
       async def evaluate_single_alert(self, db: Session, rule: Dict[str, Any]):
           """评估单个告警规则"""
           try:
               # 获取最新指标数据
               latest_metrics = db.query(SystemMetrics).filter(
                   SystemMetrics.metric_type == rule['metric_type'],
                   SystemMetrics.metric_name == rule['metric_name']
               ).order_by(SystemMetrics.collected_at.desc()).first()
               
               if not latest_metrics:
                   return
               
               # 评估告警条件
               if self.check_alert_condition(latest_metrics.metric_value, rule):
                   await self.trigger_alert(db, rule, latest_metrics)
           
           except Exception as e:
               logger.error(f"评估告警规则失败: {e}")
       
       def check_alert_condition(self, metric_value: Dict[str, Any], rule: Dict[str, Any]) -> bool:
           """检查告警条件"""
           field = rule['field']
           operator = rule['operator']
           threshold = rule['threshold']
           
           if field not in metric_value:
               return False
           
           value = metric_value[field]
           
           if operator == 'gt':
               return value > threshold
           elif operator == 'lt':
               return value < threshold
           elif operator == 'eq':
               return value == threshold
           elif operator == 'gte':
               return value >= threshold
           elif operator == 'lte':
               return value <= threshold
           
           return False
   ```

**交付物**:
- ✅ 系统监控服务实现
- ✅ 指标收集和存储
- ✅ 告警规则评估
- ✅ 通知服务集成

### 步骤3.2：实现故障恢复和容错机制

**时间估计**: 2天

**任务描述**: 实现任务失败重试、执行器故障恢复等容错功能

**具体操作**:

1. **创建故障恢复服务**
   
   创建文件: `backend/app/services/fault_recovery.py`
   ```python
   import asyncio
   import logging
   from datetime import datetime, timedelta
   from typing import List, Dict, Any
   from sqlalchemy.orm import Session
   
   from app.core.database import SessionLocal
   from app.models.task import TaskInstance, TaskExecution
   from app.models.executor import ExecutorNode
   from app.crud import task_instance, executor_node
   
   logger = logging.getLogger(__name__)
   
   class FaultRecoveryService:
       """故障恢复服务"""
       
       def __init__(self):
           self.is_running = False
           self.recovery_interval = 60  # 恢复检查间隔（秒）
           self.task_timeout_threshold = 3600  # 任务超时阈值（秒）
       
       async def start(self):
           """启动故障恢复服务"""
           self.is_running = True
           logger.info("故障恢复服务启动")
           
           await asyncio.gather(
               self.task_recovery_loop(),
               self.executor_recovery_loop(),
               self.orphaned_task_cleanup_loop()
           )
       
       async def stop(self):
           """停止故障恢复服务"""
           self.is_running = False
           logger.info("故障恢复服务停止")
       
       async def task_recovery_loop(self):
           """任务恢复循环"""
           while self.is_running:
               try:
                   await self.recover_failed_tasks()
                   await self.recover_timeout_tasks()
                   await asyncio.sleep(self.recovery_interval)
               except Exception as e:
                   logger.error(f"任务恢复异常: {e}")
       
       async def recover_failed_tasks(self):
           """恢复失败的任务"""
           db = SessionLocal()
           try:
               # 查找失败且可重试的任务
               failed_tasks = db.query(TaskInstance).filter(
                   TaskInstance.status == 'failed',
                   TaskInstance.retry_count < TaskInstance.max_retry_count
               ).all()
               
               for task in failed_tasks:
                   await self.retry_task(db, task)
           
           finally:
               db.close()
       
       async def retry_task(self, db: Session, task: TaskInstance):
           """重试任务"""
           try:
               # 增加重试次数
               task.retry_count += 1
               task.status = 'pending'
               task.executor_node_id = None
               task.assigned_at = None
               task.started_at = None
               task.completed_at = None
               task.error_message = None
               task.updated_at = datetime.utcnow()
               
               db.commit()
               
               logger.info(f"任务重试: {task.id} (第{task.retry_count}次)")
           
           except Exception as e:
               logger.error(f"任务重试失败: {e}")
               db.rollback()
   ```

**交付物**:
- ✅ 故障恢复服务实现
- ✅ 任务失败重试机制
- ✅ 超时任务处理
- ✅ 孤儿任务清理

---

## 阶段四：前端界面开发

### 步骤4.1：创建任务管理界面

**时间估计**: 3天

**任务描述**: 开发任务定义、调度配置和执行监控的前端界面

**具体操作**:

1. **创建任务管理页面组件**
   
   创建文件: `frontend/src/pages/TaskManagement/index.tsx`
   ```typescript
   import React, { useState, useEffect } from 'react';
   import { Card, Table, Button, Modal, Form, Input, Select, Space, Tag, Popconfirm } from 'antd';
   import { PlusOutlined, PlayCircleOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
   import { taskApi } from '@/api/tasks';
   import TaskForm from './components/TaskForm';
   import TaskScheduleModal from './components/TaskScheduleModal';
   
   const { Option } = Select;
   
   const TaskManagement: React.FC = () => {
     const [tasks, setTasks] = useState([]);
     const [loading, setLoading] = useState(false);
     const [modalVisible, setModalVisible] = useState(false);
     const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
     const [editingTask, setEditingTask] = useState(null);
     const [selectedTask, setSelectedTask] = useState(null);
     
     // 获取任务列表
     const fetchTasks = async () => {
       setLoading(true);
       try {
         const response = await taskApi.getTaskDefinitions();
         setTasks(response.data.items);
       } catch (error) {
         console.error('获取任务列表失败:', error);
       } finally {
         setLoading(false);
       }
     };
     
     useEffect(() => {
       fetchTasks();
     }, []);
     
     // 表格列定义
     const columns = [
       {
         title: '任务名称',
         dataIndex: 'name',
         key: 'name',
       },
       {
         title: '任务类型',
         dataIndex: 'task_type',
         key: 'task_type',
       },
       {
         title: '执行器分组',
         dataIndex: 'executor_group',
         key: 'executor_group',
       },
       {
         title: '状态',
         dataIndex: 'status',
         key: 'status',
         render: (status: string) => {
           const color = status === 'active' ? 'green' : status === 'inactive' ? 'orange' : 'red';
           return <Tag color={color}>{status}</Tag>;
         },
       },
       {
         title: '创建时间',
         dataIndex: 'created_at',
         key: 'created_at',
         render: (date: string) => new Date(date).toLocaleString(),
       },
       {
         title: '操作',
         key: 'action',
         render: (_, record) => (
           <Space size="middle">
             <Button
               type="link"
               icon={<PlayCircleOutlined />}
               onClick={() => handleTriggerTask(record)}
             >
               触发
             </Button>
             <Button
               type="link"
               icon={<EditOutlined />}
               onClick={() => handleEditTask(record)}
             >
               编辑
             </Button>
             <Button
               type="link"
               onClick={() => handleScheduleTask(record)}
             >
               调度
             </Button>
             <Popconfirm
               title="确定删除这个任务吗？"
               onConfirm={() => handleDeleteTask(record.id)}
               okText="确定"
               cancelText="取消"
             >
               <Button type="link" danger icon={<DeleteOutlined />}>
                 删除
               </Button>
             </Popconfirm>
           </Space>
         ),
       },
     ];
     
     // 处理函数
     const handleCreateTask = () => {
       setEditingTask(null);
       setModalVisible(true);
     };
     
     const handleEditTask = (task) => {
       setEditingTask(task);
       setModalVisible(true);
     };
     
     const handleScheduleTask = (task) => {
       setSelectedTask(task);
       setScheduleModalVisible(true);
     };
     
     const handleTriggerTask = async (task) => {
       try {
         await taskApi.triggerTask({
           task_definition_id: task.id,
           priority: 'normal',
           parameters: {}
         });
         message.success('任务触发成功');
       } catch (error) {
         message.error('任务触发失败');
       }
     };
     
     const handleDeleteTask = async (taskId) => {
       try {
         await taskApi.deleteTaskDefinition(taskId);
         message.success('任务删除成功');
         fetchTasks();
       } catch (error) {
         message.error('任务删除失败');
       }
     };
     
     return (
       <div>
         <Card
           title="任务管理"
           extra={
             <Button
               type="primary"
               icon={<PlusOutlined />}
               onClick={handleCreateTask}
             >
               创建任务
             </Button>
           }
         >
           <Table
             columns={columns}
             dataSource={tasks}
             loading={loading}
             rowKey="id"
             pagination={{
               showSizeChanger: true,
               showQuickJumper: true,
               showTotal: (total) => `共 ${total} 条记录`,
             }}
           />
         </Card>
         
         <TaskForm
           visible={modalVisible}
           task={editingTask}
           onCancel={() => setModalVisible(false)}
           onSuccess={() => {
             setModalVisible(false);
             fetchTasks();
           }}
         />
         
         <TaskScheduleModal
           visible={scheduleModalVisible}
           task={selectedTask}
           onCancel={() => setScheduleModalVisible(false)}
           onSuccess={() => {
             setScheduleModalVisible(false);
           }}
         />
       </div>
     );
   };
   
   export default TaskManagement;
   ```

**交付物**:
- ✅ 任务管理界面实现
- ✅ 任务创建和编辑功能
- ✅ 任务调度配置界面
- ✅ 任务触发和监控功能

---

## 阶段五：测试和部署

### 步骤5.1：单元测试和集成测试

**时间估计**: 1周

**任务描述**: 编写完整的测试用例，确保系统稳定性

### 步骤5.2：性能测试和优化

**时间估计**: 3天

**任务描述**: 进行性能测试，优化系统性能

### 步骤5.3：生产环境部署

**时间估计**: 2天

**任务描述**: 部署到生产环境，配置监控和告警

---

## 总结

本实现计划详细描述了ACWL AI数据平台任务管理系统的完整开发流程，包括：

1. **基础设施搭建**：数据库表结构、模型定义、API接口
2. **核心功能开发**：任务调度、执行器管理、集群高可用
3. **高级功能开发**：监控告警、故障恢复、性能优化
4. **前端界面开发**：用户界面、实时监控、操作体验
5. **测试和部署**：质量保证、性能优化、生产部署

整个项目预计需要**10-12周**完成，可以根据实际情况调整各阶段的时间分配和优先级。