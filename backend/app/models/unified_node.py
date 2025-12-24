#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一节点管理相关数据模型
整合了原有的任务定义和工作流节点功能
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, JSON, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import List, Optional, TYPE_CHECKING
from enum import Enum as PyEnum
from datetime import datetime

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from .user import User
    from .project import Project
    from .workflow import Workflow, WorkflowInstance


class UnifiedNodeType(str, PyEnum):
    """统一节点类型枚举"""
    # 任务类型
    DATA_SYNC = "data_sync"           # 数据同步
    MODEL_TRAINING = "model_training" # 模型训练
    SHELL_SCRIPT = "shell-script"     # Shell脚本
    DATA_ANALYSIS = "data_analysis"   # 数据分析
    ETL = "etl"                       # ETL处理
    PYTHON_CODE = "python_code"       # Python代码执行
    SQL_QUERY = "sql_query"           # SQL查询执行
    CONDITION = "condition"           # 条件判断
    DATA_TRANSFORM = "data_transform" # 数据转换
    API_CALL = "api_call"             # API调用
    FILE_OPERATION = "file_operation" # 文件操作
    EMAIL_SEND = "email_send"         # 邮件发送
    CUSTOM = "custom"                 # 自定义
    
    # 工作流节点类型
    START = "start"                   # 开始节点
    END = "end"                       # 结束节点
    LOOP = "loop"                     # 循环节点
    PARALLEL = "parallel"             # 并行节点
    MERGE = "merge"                   # 合并节点
    DELAY = "delay"                   # 延时节点
    SUBPROCESS = "subprocess"         # 子流程


class NodePriority(str, PyEnum):
    """节点优先级枚举"""
    LOW = "low"                       # 低
    NORMAL = "normal"                 # 普通
    HIGH = "high"                     # 高
    URGENT = "urgent"                 # 紧急


class NodeInstanceStatus(str, PyEnum):
    """节点实例状态枚举"""
    PENDING = "pending"               # 等待中
    QUEUED = "queued"                 # 已排队
    RUNNING = "running"               # 运行中
    SUCCESS = "success"               # 成功
    FAILED = "failed"                 # 失败
    CANCELLED = "cancelled"           # 已取消
    TIMEOUT = "timeout"               # 超时
    RETRY = "retry"                   # 重试中
    PAUSED = "paused"                 # 暂停
    SKIPPED = "skipped"               # 跳过


class ErrorHandling(str, PyEnum):
    """错误处理策略枚举"""
    FAIL = "fail"                     # 失败停止
    SKIP = "skip"                     # 跳过继续
    RETRY = "retry"                   # 重试
    CUSTOM = "custom"                 # 自定义处理


class UnifiedNode(Base, TimestampMixin, UserMixin):
    """统一节点定义表
    
    整合了原有的 acwl_task_definitions 和 acwl_workflow_nodes 表的功能
    支持独立任务和工作流节点两种使用模式
    """
    __tablename__ = "acwl_unified_nodes"
    __table_args__ = {"comment": "统一节点定义表，支持独立任务和工作流节点"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="节点ID，自增主键"
    )

    name: Mapped[str] = mapped_column(
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

    node_type: Mapped[UnifiedNodeType] = mapped_column(
        Enum(UnifiedNodeType),
        nullable=False,
        comment="节点类型"
    )

    node_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="节点分类"
    )

    # 工作流相关字段
    workflow_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_workflows.id", ondelete="CASCADE"),
        nullable=True,
        comment="所属工作流ID（为空表示独立任务）"
    )

    position_x: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="节点在画布上的X坐标"
    )

    position_y: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="节点在画布上的Y坐标"
    )

    # 执行配置
    executor_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="执行器分组名称"
    )

    priority: Mapped[NodePriority] = mapped_column(
        Enum(NodePriority),
        nullable=False,
        default=NodePriority.NORMAL,
        comment="节点优先级"
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=3600,
        comment="节点超时时间（秒）"
    )

    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="最大重试次数"
    )

    retry_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        default=60,
        comment="重试间隔（秒）"
    )

    error_handling: Mapped[ErrorHandling] = mapped_column(
        Enum(ErrorHandling),
        nullable=False,
        default=ErrorHandling.FAIL,
        comment="错误处理策略"
    )

    # 配置和参数
    node_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
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
    
    # 工作流连接关系
    source_connections = relationship(
        "WorkflowConnection",
        foreign_keys="WorkflowConnection.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan"
    )
    
    target_connections = relationship(
        "WorkflowConnection",
        foreign_keys="WorkflowConnection.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan"
    )

    resource_requirements: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="资源需求配置（CPU、内存、GPU等）"
    )

    environment_variables: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="环境变量配置"
    )

    command_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="命令模板"
    )

    script_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="脚本内容"
    )

    dependencies: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="依赖的其他节点ID列表"
    )

    # 项目关联
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属项目ID"
    )

    # 状态和版本
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )

    is_optional: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否为可选节点（工作流中使用）"
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="版本号"
    )

    # 关系定义
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="unified_nodes"
    )

    workflow: Mapped[Optional["Workflow"]] = relationship(
        "Workflow",
        back_populates="unified_nodes"
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys="[UnifiedNode.created_by]",
        back_populates="created_unified_nodes"
    )

    instances: Mapped[List["UnifiedNodeInstance"]] = relationship(
        "UnifiedNodeInstance",
        back_populates="node",
        cascade="all, delete-orphan"
    )
    
    # 工作流连接关系
    source_connections = relationship(
        "WorkflowConnection", 
        foreign_keys="WorkflowConnection.source_node_id",
        back_populates="source_node"
    )
    
    target_connections = relationship(
        "WorkflowConnection", 
        foreign_keys="WorkflowConnection.target_node_id",
        back_populates="target_node"
    )

    def __repr__(self) -> str:
        return f"<UnifiedNode(id={self.id}, name='{self.name}', type='{self.node_type}')>"

    @property
    def is_workflow_node(self) -> bool:
        """判断是否为工作流节点"""
        return self.workflow_id is not None

    @property
    def is_standalone_task(self) -> bool:
        """判断是否为独立任务"""
        return self.workflow_id is None


class UnifiedNodeInstance(Base, TimestampMixin):
    """统一节点实例表
    
    整合了原有的 acwl_task_instances 和 acwl_workflow_node_instances 表的功能
    记录节点的执行实例信息
    """
    __tablename__ = "acwl_unified_node_instances"
    __table_args__ = {"comment": "统一节点实例表，记录节点执行实例"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="实例ID，自增主键"
    )

    instance_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="实例唯一标识"
    )

    node_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_nodes.id", ondelete="CASCADE"),
        nullable=False,
        comment="节点定义ID"
    )

    # 工作流实例关联（仅工作流节点使用）
    workflow_instance_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_workflow_instances.id", ondelete="CASCADE"),
        nullable=True,
        comment="工作流实例ID（独立任务为空）"
    )

    # 调度关联（仅独立任务使用）
    schedule_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_task_schedules.id", ondelete="SET NULL"),
        nullable=True,
        comment="调度ID（工作流节点为空）"
    )

    # 父子实例关系
    parent_instance_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_node_instances.id", ondelete="SET NULL"),
        nullable=True,
        comment="父实例ID"
    )

    # 基本信息
    node_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="节点名称（冗余存储）"
    )

    node_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="节点类型（冗余存储）"
    )

    status: Mapped[NodeInstanceStatus] = mapped_column(
        Enum(NodeInstanceStatus),
        nullable=False,
        default=NodeInstanceStatus.PENDING,
        comment="实例状态"
    )

    # 执行信息
    executor_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="执行器分组"
    )

    assigned_executor_node: Mapped[Optional[str]] = mapped_column(
        String(100),
        ForeignKey("acwl_executor_nodes.node_id", ondelete="SET NULL"),
        nullable=True,
        comment="分配的执行器节点ID"
    )

    # 时间信息
    scheduled_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        nullable=False,
        comment="计划执行时间"
    )

    actual_start_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="实际开始时间"
    )

    actual_end_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="实际结束时间"
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行时长（秒）"
    )

    # 重试信息
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="重试次数"
    )

    max_retry_count: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="最大重试次数"
    )

    # 数据和配置
    input_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="输入数据"
    )

    output_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="输出数据"
    )

    context_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="上下文数据"
    )

    result_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="执行结果数据"
    )

    runtime_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="运行时配置"
    )

    resource_usage: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="资源使用情况"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )

    # 创建信息
    created_by_scheduler: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="创建该实例的调度器节点ID"
    )

    # 关系定义
    node: Mapped["UnifiedNode"] = relationship(
        "UnifiedNode",
        back_populates="instances"
    )

    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance"
    )

    schedule: Mapped[Optional["TaskSchedule"]] = relationship(
        "TaskSchedule"
    )

    parent_instance: Mapped[Optional["UnifiedNodeInstance"]] = relationship(
        "UnifiedNodeInstance",
        remote_side=[id],
        back_populates="child_instances"
    )

    child_instances: Mapped[List["UnifiedNodeInstance"]] = relationship(
        "UnifiedNodeInstance",
        back_populates="parent_instance"
    )

    assigned_executor: Mapped[Optional["ExecutorNode"]] = relationship(
        "ExecutorNode",
        foreign_keys=[assigned_executor_node],
        primaryjoin="UnifiedNodeInstance.assigned_executor_node == ExecutorNode.node_id"
    )

    executions: Mapped[List["NodeExecution"]] = relationship(
        "NodeExecution",
        back_populates="node_instance",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UnifiedNodeInstance(id={self.id}, instance_id='{self.instance_id}', status='{self.status}')>"

    @property
    def is_running(self) -> bool:
        """判断实例是否正在运行"""
        return self.status in [NodeInstanceStatus.RUNNING, NodeInstanceStatus.QUEUED]

    @property
    def is_finished(self) -> bool:
        """判断实例是否已完成"""
        return self.status in [
            NodeInstanceStatus.SUCCESS,
            NodeInstanceStatus.FAILED,
            NodeInstanceStatus.CANCELLED,
            NodeInstanceStatus.TIMEOUT,
            NodeInstanceStatus.SKIPPED
        ]

    @property
    def can_retry(self) -> bool:
        """判断实例是否可以重试"""
        return (
            self.status in [NodeInstanceStatus.FAILED, NodeInstanceStatus.TIMEOUT] and
            self.retry_count < self.max_retry_count
        )

    @property
    def is_workflow_node_instance(self) -> bool:
        """判断是否为工作流节点实例"""
        return self.workflow_instance_id is not None

    @property
    def is_standalone_task_instance(self) -> bool:
        """判断是否为独立任务实例"""
        return self.workflow_instance_id is None


class NodeExecution(Base, TimestampMixin):
    """节点执行记录表
    
    记录节点在执行器上的详细执行过程
    """
    __tablename__ = "acwl_node_executions"
    __table_args__ = {"comment": "节点执行记录表，记录节点在执行器上的详细执行过程"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="执行ID，自增主键"
    )

    execution_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="执行唯一标识"
    )

    node_instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_unified_node_instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="节点实例ID"
    )

    executor_node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="执行器节点ID"
    )

    process_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="进程ID"
    )

    status: Mapped[NodeInstanceStatus] = mapped_column(
        Enum(NodeInstanceStatus),
        nullable=False,
        default=NodeInstanceStatus.PENDING,
        comment="执行状态"
    )

    start_time: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="开始时间"
    )

    end_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="结束时间"
    )

    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="执行时长（秒）"
    )

    exit_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="退出码"
    )

    stdout_log: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="标准输出日志"
    )

    stderr_log: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="标准错误日志"
    )

    resource_usage: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="资源使用情况（CPU、内存、GPU等）"
    )

    performance_metrics: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="性能指标"
    )

    execution_context: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="执行上下文信息"
    )

    # 关系定义
    node_instance: Mapped["UnifiedNodeInstance"] = relationship(
        "UnifiedNodeInstance",
        back_populates="executions"
    )

    logs: Mapped[List["NodeLog"]] = relationship(
        "NodeLog",
        back_populates="execution",
        cascade="all, delete-orphan"
    )

    results: Mapped[List["NodeResult"]] = relationship(
        "NodeResult",
        back_populates="execution",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<NodeExecution(id={self.id}, execution_id='{self.execution_id}', status='{self.status}')>"


class NodeLog(Base):
    """节点执行日志表"""
    __tablename__ = "acwl_node_logs"
    __table_args__ = {"comment": "节点执行日志表，记录节点执行过程中的详细日志信息"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="日志ID，自增主键"
    )

    execution_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("acwl_node_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
        comment="执行ID"
    )

    log_level: Mapped[str] = mapped_column(
        Enum("DEBUG", "INFO", "WARN", "ERROR", "FATAL", name="log_level_enum"),
        nullable=False,
        comment="日志级别"
    )

    log_source: Mapped[str] = mapped_column(
        Enum("system", "application", "user", name="log_source_enum"),
        nullable=False,
        default="application",
        comment="日志来源"
    )

    log_message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="日志消息"
    )

    log_context: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="日志上下文"
    )

    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="日志时间"
    )

    # 关系定义
    execution: Mapped["NodeExecution"] = relationship(
        "NodeExecution",
        back_populates="logs"
    )

    def __repr__(self) -> str:
        return f"<NodeLog(id={self.id}, level='{self.log_level}', message='{self.log_message[:50]}...')>"


class NodeResult(Base):
    """节点执行结果表"""
    __tablename__ = "acwl_node_results"
    __table_args__ = {"comment": "节点执行结果表，存储节点执行产生的各种结果数据"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="结果ID，自增主键"
    )

    execution_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("acwl_node_executions.execution_id", ondelete="CASCADE"),
        nullable=False,
        comment="执行ID"
    )

    result_type: Mapped[str] = mapped_column(
        Enum("output", "file", "metrics", "error", "custom", name="result_type_enum"),
        nullable=False,
        comment="结果类型"
    )

    result_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="结果名称"
    )

    result_value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="结果值"
    )

    result_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="结果文件路径"
    )

    result_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="结果大小（字节）"
    )

    result_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="结果元数据"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )

    # 关系定义
    execution: Mapped["NodeExecution"] = relationship(
        "NodeExecution",
        back_populates="results"
    )

    def __repr__(self) -> str:
        return f"<NodeResult(id={self.id}, type='{self.result_type}', name='{self.result_name}')>"