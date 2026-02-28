from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Optional, List
import enum

from app.core.database import Base


class WorkflowStatus(enum.Enum):
    """工作流状态枚举"""
    draft = "draft"         # 草稿
    active = "active"       # 活跃
    inactive = "inactive"   # 非活跃
    archived = "archived"   # 已归档


class NodeType(enum.Enum):
    """工作流节点类型枚举"""
    START = "start"                   # 开始节点
    END = "end"                       # 结束节点
    PYTHON_CODE = "python_code"       # Python代码执行
    SQL_QUERY = "sql_query"           # SQL查询执行
    SHELL_SCRIPT = "shell_script"     # Shell脚本
    LLM_PROCESS = "llm_process"       # LLM处理
    CONDITION = "condition"           # 条件判断
    LOOP = "loop"                     # 循环节点
    PARALLEL = "parallel"             # 并行节点
    MERGE = "merge"                   # 合并节点
    DATA_TRANSFORM = "data_transform" # 数据转换
    API_CALL = "api_call"             # API调用
    FILE_OPERATION = "file_operation" # 文件操作
    EMAIL_SEND = "email_send"         # 邮件发送
    DELAY = "delay"                   # 延时节点
    SUBPROCESS = "subprocess"         # 子流程
    CUSTOM = "custom"                 # 自定义节点


class ConnectionType(enum.Enum):
    """工作流连接类型枚举"""
    SUCCESS = "success"       # 成功连接
    FAILURE = "failure"       # 失败连接
    CONDITIONAL = "conditional" # 条件连接
    ALWAYS = "always"         # 总是连接


class ErrorHandling(enum.Enum):
    """错误处理策略枚举"""
    FAIL = "fail"       # 失败停止
    SKIP = "skip"       # 跳过继续
    RETRY = "retry"     # 重试
    CUSTOM = "custom"   # 自定义处理


class InstanceStatus(enum.Enum):
    """实例状态枚举"""
    PENDING = "pending"     # 等待中
    RUNNING = "running"     # 运行中
    SUCCESS = "success"     # 成功
    FAILED = "failed"       # 失败
    CANCELLED = "cancelled" # 已取消
    TIMEOUT = "timeout"     # 超时
    PAUSED = "paused"       # 暂停
    SKIPPED = "skipped"     # 跳过


class Priority(enum.Enum):
    """优先级枚举"""
    LOW = "low"         # 低
    NORMAL = "normal"   # 普通
    HIGH = "high"       # 高
    URGENT = "urgent"   # 紧急


class TriggerType(enum.Enum):
    """触发类型枚举"""
    MANUAL = "manual"         # 手动触发
    SCHEDULE = "schedule"     # 定时触发
    EVENT = "event"           # 事件触发
    API = "api"               # API触发
    DEPENDENCY = "dependency" # 依赖触发


class ScheduleType(enum.Enum):
    """调度类型枚举"""
    CRON = "cron"               # Cron表达式
    INTERVAL = "interval"       # 间隔调度
    ONCE = "once"               # 一次性
    MANUAL = "manual"           # 手动
    EVENT_DRIVEN = "event_driven" # 事件驱动


class MisfirePolicy(enum.Enum):
    """错过执行策略枚举"""
    IGNORE = "ignore"       # 忽略
    FIRE_ONCE = "fire_once" # 执行一次
    FIRE_ALL = "fire_all"   # 执行所有


class Workflow(Base):
    """工作流定义模型"""
    __tablename__ = "acwl_workflows"
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="工作流ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="工作流名称"
    )
    
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="工作流显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="工作流描述"
    )
    
    workflow_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="工作流分类"
    )
    
    workflow_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0.0",
        comment="工作流版本"
    )
    
    workflow_status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus),
        nullable=False,
        default=WorkflowStatus.draft,
        comment="工作流状态"
    )
    
    workflow_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流全局配置"
    )
    
    input_parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流输入参数定义"
    )
    
    output_parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流输出参数定义"
    )
    
    global_variables: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流全局变量"
    )
    
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=7200,
        comment="工作流超时时间（秒）"
    )
    
    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="工作流最大重试次数"
    )
    
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属项目ID"
    )
    
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建者ID"
    )
    
    is_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否为模板"
    )
    
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否为系统工作流"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_name', 'name'),
        Index('idx_workflow_status', 'workflow_status'),
        Index('idx_project_id', 'project_id'),
        Index('idx_created_by', 'created_by'),
        Index('idx_is_template', 'is_template'),
    )
    
    # 关系映射
    project = relationship("Project", back_populates="workflows")
    creator = relationship("User", back_populates="created_workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    unified_nodes = relationship("UnifiedNode", back_populates="workflow", cascade="all, delete-orphan")
    connections = relationship("WorkflowConnection", back_populates="workflow", cascade="all, delete-orphan")
    instances = relationship("WorkflowInstance", back_populates="workflow")
    schedules = relationship("WorkflowSchedule", back_populates="workflow", cascade="all, delete-orphan")
    task_definitions = relationship("TaskDefinition", back_populates="workflow")


class WorkflowNode(Base):
    """工作流节点模型"""
    __tablename__ = "acwl_workflow_nodes"
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="节点ID，自增主键"
    )
    
    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_workflows.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属工作流ID"
    )
    
    node_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="节点名称"
    )
    
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="节点显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="节点描述"
    )
    
    node_type: Mapped[NodeType] = mapped_column(
        Enum(NodeType),
        nullable=False,
        comment="节点类型"
    )
    
    node_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="节点配置参数"
    )
    
    input_parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="节点输入参数定义"
    )
    
    output_parameters: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="节点输出参数定义"
    )
    
    position_x: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="节点在画布上的X坐标"
    )
    
    position_y: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="节点在画布上的Y坐标"
    )
    
    executor_group: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="执行器分组（继承自工作流或自定义）"
    )
    
    timeout_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="节点超时时间（秒）"
    )
    
    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="节点最大重试次数"
    )
    
    retry_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="重试间隔（秒）"
    )
    
    error_handling: Mapped[ErrorHandling] = mapped_column(
        Enum(ErrorHandling),
        nullable=False,
        default=ErrorHandling.FAIL,
        comment="错误处理策略"
    )
    
    is_optional: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否为可选节点"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_id', 'workflow_id'),
        Index('idx_node_type', 'node_type'),
        Index('idx_node_name', 'node_name'),
        Index('idx_workflow_nodes_type_workflow', 'node_type', 'workflow_id'),
    )
    
    # 关联关系
    workflow = relationship("Workflow", back_populates="nodes")
    task_definitions = relationship("TaskDefinition", back_populates="workflow_node")


class WorkflowConnection(Base):
    """工作流连接模型"""
    __tablename__ = "acwl_workflow_connections"
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="连接ID，自增主键"
    )
    
    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_workflows.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属工作流ID"
    )
    
    source_node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_nodes.id", ondelete="CASCADE"),
        nullable=False,
        comment="源节点ID（统一节点）"
    )
    
    target_node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_nodes.id", ondelete="CASCADE"),
        nullable=False,
        comment="目标节点ID（统一节点）"
    )
    
    connection_type: Mapped[ConnectionType] = mapped_column(
        Enum(ConnectionType),
        nullable=False,
        default=ConnectionType.SUCCESS,
        comment="连接类型"
    )
    
    condition_expression: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="条件表达式（用于conditional类型）"
    )
    
    connection_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="连接配置参数"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    # 索引和约束
    __table_args__ = (
        Index('idx_workflow_id', 'workflow_id'),
        Index('idx_source_node_id', 'source_node_id'),
        Index('idx_target_node_id', 'target_node_id'),
        Index('idx_workflow_connections_source_type', 'source_node_id', 'connection_type'),
        UniqueConstraint('workflow_id', 'source_node_id', 'target_node_id', 'connection_type', 
                        name='uk_workflow_source_target'),
    )
    
    # 关联关系
    workflow = relationship("Workflow", back_populates="connections")
    source_node = relationship(
        "UnifiedNode", 
        foreign_keys=[source_node_id],
        back_populates="source_connections"
    )
    target_node = relationship(
        "UnifiedNode", 
        foreign_keys=[target_node_id],
        back_populates="target_connections"
    )


class WorkflowInstance(Base):
    """工作流实例模型"""
    __tablename__ = "acwl_workflow_instances"
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="工作流实例ID，自增主键"
    )
    
    instance_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="实例唯一标识"
    )
    
    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_workflows.id", ondelete="CASCADE"),
        nullable=False,
        comment="工作流定义ID"
    )
    
    workflow_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="执行时的工作流版本"
    )
    
    instance_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="实例名称"
    )
    
    status: Mapped[InstanceStatus] = mapped_column(
        Enum(InstanceStatus),
        nullable=False,
        default=InstanceStatus.PENDING,
        comment="实例状态"
    )
    
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority),
        nullable=False,
        default=Priority.NORMAL,
        comment="实例优先级"
    )
    
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流输入数据"
    )
    
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流输出数据"
    )
    
    context_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工作流上下文数据"
    )
    
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="计划执行时间"
    )
    
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="实际开始时间"
    )
    
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="实际结束时间"
    )
    
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行时长（秒）"
    )
    
    current_node_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_nodes.id", ondelete="SET NULL"),
        nullable=True,
        comment="当前执行节点ID（统一节点）"
    )
    
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="重试次数"
    )
    
    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="最大重试次数"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    triggered_by: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType),
        nullable=False,
        comment="触发方式"
    )
    
    triggered_by_user: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="SET NULL"),
        nullable=True,
        comment="触发用户ID"
    )
    
    parent_instance_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_workflow_instances.id", ondelete="SET NULL"),
        nullable=True,
        comment="父工作流实例ID"
    )
    
    created_by_scheduler: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="创建该实例的调度器节点ID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_id', 'workflow_id'),
        Index('idx_status', 'status'),
        Index('idx_scheduled_time', 'scheduled_time'),
        Index('idx_actual_start_time', 'actual_start_time'),
        Index('idx_triggered_by_user', 'triggered_by_user'),
        Index('idx_parent_instance_id', 'parent_instance_id'),
        Index('idx_workflow_instances_status_time', 'status', 'scheduled_time'),
    )
    
    # 关联关系
    workflow = relationship("Workflow", back_populates="instances")
    current_node = relationship("UnifiedNode")
    triggered_user = relationship("User", back_populates="triggered_workflow_instances")
    parent_instance = relationship("WorkflowInstance", remote_side=[id])
    child_instances = relationship("WorkflowInstance", back_populates="parent_instance")
    node_instances = relationship("WorkflowNodeInstance", back_populates="workflow_instance")


class WorkflowNodeInstance(Base):
    """工作流节点实例模型"""
    __tablename__ = "acwl_workflow_node_instances"
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="节点实例ID，自增主键"
    )
    
    instance_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="节点实例唯一标识"
    )
    
    workflow_instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_workflow_instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="工作流实例ID"
    )
    
    node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_nodes.id", ondelete="CASCADE"),
        nullable=False,
        comment="节点定义ID（统一节点）"
    )
    
    node_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="节点名称"
    )
    
    node_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="节点类型"
    )
    
    status: Mapped[InstanceStatus] = mapped_column(
        Enum(InstanceStatus),
        nullable=False,
        default=InstanceStatus.PENDING,
        comment="节点实例状态"
    )
    
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="节点输入数据"
    )
    
    output_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="节点输出数据"
    )
    
    context_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="节点上下文数据"
    )
    
    scheduled_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="计划执行时间"
    )
    
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="实际开始时间"
    )
    
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="实际结束时间"
    )
    
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行时长（秒）"
    )
    
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="重试次数"
    )
    
    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="最大重试次数"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    executor_group: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="执行器分组"
    )
    
    assigned_executor_node: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="分配的执行器节点ID"
    )
    
    task_instance_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_task_instances.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联的任务实例ID（如果节点对应一个任务）"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_instance_id', 'workflow_instance_id'),
        Index('idx_node_id', 'node_id'),
        Index('idx_status', 'status'),
        Index('idx_scheduled_time', 'scheduled_time'),
        Index('idx_task_instance_id', 'task_instance_id'),
        Index('idx_workflow_node_instances_status_time', 'status', 'scheduled_time'),
    )
    
    # 关联关系
    workflow_instance = relationship("WorkflowInstance", back_populates="node_instances")
    node = relationship("UnifiedNode")
    task_instance = relationship("TaskInstance")


class WorkflowSchedule(Base):
    """工作流调度配置模型"""
    __tablename__ = "acwl_workflow_schedules"
    
    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True,
        comment="调度ID，自增主键"
    )
    
    workflow_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_workflows.id", ondelete="CASCADE"),
        nullable=False,
        comment="工作流定义ID"
    )
    
    schedule_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="调度名称"
    )
    
    schedule_type: Mapped[ScheduleType] = mapped_column(
        Enum(ScheduleType),
        nullable=False,
        comment="调度类型"
    )
    
    cron_expression: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Cron表达式"
    )
    
    interval_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="间隔秒数"
    )
    
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间"
    )
    
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="结束时间"
    )
    
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        comment="时区"
    )
    
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    max_instances: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="最大并发实例数"
    )
    
    misfire_policy: Mapped[MisfirePolicy] = mapped_column(
        Enum(MisfirePolicy),
        nullable=False,
        default=MisfirePolicy.FIRE_ONCE,
        comment="错过执行策略"
    )
    
    schedule_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="调度配置参数"
    )
    
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="调度时的默认输入数据"
    )
    
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建者ID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间"
    )
    
    # 索引
    __table_args__ = (
        Index('idx_workflow_id', 'workflow_id'),
        Index('idx_schedule_type', 'schedule_type'),
        Index('idx_is_enabled', 'is_enabled'),
        Index('idx_start_time', 'start_time'),
        Index('idx_end_time', 'end_time'),
    )
    
    # 关联关系
    workflow = relationship("Workflow", back_populates="schedules")
    creator = relationship("User", back_populates="created_workflow_schedules")