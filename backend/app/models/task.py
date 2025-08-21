#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理相关数据模型
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


class TaskType(str, PyEnum):
    """任务类型枚举"""
    DATA_SYNC = "data_sync"                     # 数据同步
    MODEL_TRAIN = "model_train"                 # 模型训练
    DATA_ANALYSIS = "data_analysis"             # 数据分析
    MODEL_INFERENCE = "model_inference"         # 模型推理
    DATA_PREPROCESSING = "data_preprocessing"   # 数据预处理
    MODEL_EVALUATION = "model_evaluation"       # 模型评估
    DATA_VISUALIZATION = "data_visualization"   # 数据可视化
    WORKFLOW_ORCHESTRATION = "workflow_orchestration" # 工作流编排
    CUSTOM = "custom"                           # 自定义


class TaskPriority(str, PyEnum):
    """任务优先级枚举"""
    LOW = "low"                       # 低
    NORMAL = "normal"                 # 普通
    HIGH = "high"                     # 高
    URGENT = "urgent"                 # 紧急


class TaskStatus(str, PyEnum):
    """任务实例状态枚举"""
    PENDING = "pending"               # 等待中
    QUEUED = "queued"                 # 已排队
    RUNNING = "running"               # 运行中
    SUCCESS = "success"               # 成功
    FAILED = "failed"                 # 失败
    CANCELLED = "cancelled"           # 已取消
    TIMEOUT = "timeout"               # 超时
    RETRY = "retry"                   # 重试中


class ScheduleType(str, PyEnum):
    """调度类型枚举"""
    CRON = "cron"                     # Cron表达式
    INTERVAL = "interval"             # 间隔调度
    ONCE = "once"                     # 一次性
    MANUAL = "manual"                 # 手动触发
    EVENT_DRIVEN = "event_driven"     # 事件驱动


class MisfirePolicy(str, PyEnum):
    """错过执行策略枚举"""
    IGNORE = "ignore"                 # 忽略
    FIRE_ONCE = "fire_once"           # 执行一次
    FIRE_ALL = "fire_all"             # 执行所有


class DependencyType(str, PyEnum):
    """依赖类型枚举"""
    SUCCESS = "success"               # 成功依赖
    FAILURE = "failure"               # 失败依赖
    COMPLETION = "completion"         # 完成依赖
    CONDITIONAL = "conditional"       # 条件依赖





class TaskDefinition(Base, TimestampMixin, UserMixin):
    """任务定义表"""
    __tablename__ = "acwl_task_definitions"
    __table_args__ = {"comment": "任务定义表，存储任务的基本配置和执行参数"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="任务定义ID，自增主键"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="任务名称"
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="任务显示名称"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="任务描述"
    )

    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType),
        nullable=False,
        comment="任务类型"
    )

    task_category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="任务分类"
    )

    executor_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="执行器分组名称，指定任务运行的执行器组"
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.NORMAL,
        comment="任务优先级"
    )

    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        default=3600,
        comment="任务超时时间（秒）"
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

    task_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="任务配置参数"
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
        comment="依赖的其他任务ID列表"
    )

    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_projects.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属项目ID"
    )

    workflow_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_workflows.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属工作流ID"
    )

    workflow_node_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_workflow_nodes.id", ondelete="SET NULL"),
        nullable=True,
        comment="对应的工作流节点ID"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否激活"
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="版本号"
    )

    # 关系映射
    project: Mapped[Optional["Project"]] = relationship(
        "Project",
        back_populates="task_definitions"
    )

    workflow: Mapped[Optional["Workflow"]] = relationship(
        "Workflow",
        back_populates="task_definitions"
    )

    workflow_node: Mapped[Optional["WorkflowNode"]] = relationship(
        "WorkflowNode",
        back_populates="task_definitions"
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys="[TaskDefinition.created_by]",
        back_populates="created_task_definitions"
    )

    schedules: Mapped[List["TaskSchedule"]] = relationship(
        "TaskSchedule",
        back_populates="task_definition",
        cascade="all, delete-orphan"
    )

    instances: Mapped[List["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="task_definition",
        cascade="all, delete-orphan"
    )

    dependencies_as_parent: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="[TaskDependency.parent_task_id]",
        back_populates="parent_task",
        cascade="all, delete-orphan"
    )

    dependencies_as_child: Mapped[List["TaskDependency"]] = relationship(
        "TaskDependency",
        foreign_keys="[TaskDependency.child_task_id]",
        back_populates="child_task",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskDefinition(id={self.id}, name='{self.name}', type='{self.task_type}')>"


class TaskTemplate(Base, TimestampMixin, UserMixin):
    """任务模板表"""
    __tablename__ = "acwl_task_templates"
    __table_args__ = {"comment": "任务模板表，存储预定义的任务配置模板"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="模板ID，自增主键"
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模板名称"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述"
    )

    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType),
        nullable=False,
        comment="任务类型"
    )

    default_executor_group: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="默认执行器分组"
    )

    template_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="模板配置"
    )

    default_resource_requirements: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认资源需求"
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="是否为系统模板"
    )

    # 关系映射
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="[TaskTemplate.created_by]",
        back_populates="created_task_templates"
    )

    def __repr__(self) -> str:
        return f"<TaskTemplate(id={self.id}, name='{self.name}', type='{self.task_type}')>"


class TaskDependency(Base):
    """任务依赖关系表"""
    __tablename__ = "acwl_task_dependencies"
    __table_args__ = {"comment": "任务依赖关系表，定义任务间的执行依赖关系"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="依赖ID，自增主键"
    )

    parent_task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_task_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="父任务ID"
    )

    child_task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_task_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="子任务ID"
    )

    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(DependencyType),
        nullable=False,
        default=DependencyType.SUCCESS,
        comment="依赖类型"
    )

    condition_expression: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="条件表达式（用于conditional类型）"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )

    # 关系映射
    parent_task: Mapped["TaskDefinition"] = relationship(
        "TaskDefinition",
        foreign_keys=[parent_task_id],
        back_populates="dependencies_as_parent"
    )

    child_task: Mapped["TaskDefinition"] = relationship(
        "TaskDefinition",
        foreign_keys=[child_task_id],
        back_populates="dependencies_as_child"
    )

    def __repr__(self) -> str:
        return f"<TaskDependency(parent={self.parent_task_id}, child={self.child_task_id}, type='{self.dependency_type}')>"





class TaskSchedule(Base, TimestampMixin, UserMixin):
    """任务调度配置表"""
    __tablename__ = "acwl_task_schedules"
    __table_args__ = {"comment": "任务调度配置表，定义任务的调度规则和时间配置"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="调度ID，自增主键"
    )

    task_definition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_task_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务定义ID"
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
        TIMESTAMP,
        nullable=True,
        comment="开始时间"
    )

    end_time: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="结束时间"
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="UTC",
        comment="时区"
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否启用"
    )

    max_instances: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="最大并发实例数"
    )

    misfire_policy: Mapped[MisfirePolicy] = mapped_column(
        Enum(MisfirePolicy),
        default=MisfirePolicy.FIRE_ONCE,
        comment="错过执行策略"
    )

    schedule_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="调度配置参数"
    )

    # 关系映射
    task_definition: Mapped["TaskDefinition"] = relationship(
        "TaskDefinition",
        back_populates="schedules"
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys="[TaskSchedule.created_by]",
        back_populates="created_task_schedules"
    )

    instances: Mapped[List["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="schedule"
    )

    def __repr__(self) -> str:
        return f"<TaskSchedule(id={self.id}, name='{self.schedule_name}', type='{self.schedule_type}')>"


class TaskInstance(Base, TimestampMixin):
    """任务实例表"""
    __tablename__ = "acwl_task_instances"
    __table_args__ = {"comment": "任务实例表，记录每次任务执行的具体实例信息"}

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

    task_definition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_task_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务定义ID"
    )

    schedule_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_task_schedules.id", ondelete="SET NULL"),
        nullable=True,
        comment="调度配置ID"
    )

    parent_instance_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_task_instances.id", ondelete="SET NULL"),
        nullable=True,
        comment="父实例ID（用于依赖任务）"
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
        comment="实例状态"
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        nullable=False,
        default=TaskPriority.NORMAL,
        comment="实例优先级"
    )

    executor_group: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="目标执行器分组"
    )

    assigned_executor_node: Mapped[Optional[str]] = mapped_column(
        String(100),
        ForeignKey("acwl_executor_nodes.node_id", ondelete="SET NULL"),
        nullable=True,
        comment="分配的执行器节点ID"
    )

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

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
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

    created_by_scheduler: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="创建该实例的调度器节点ID"
    )

    # 关系映射
    task_definition: Mapped["TaskDefinition"] = relationship(
        "TaskDefinition",
        back_populates="instances"
    )

    schedule: Mapped[Optional["TaskSchedule"]] = relationship(
        "TaskSchedule",
        back_populates="instances"
    )

    parent_instance: Mapped[Optional["TaskInstance"]] = relationship(
        "TaskInstance",
        remote_side=[id],
        back_populates="child_instances"
    )

    child_instances: Mapped[List["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="parent_instance"
    )

    assigned_executor: Mapped[Optional["ExecutorNode"]] = relationship(
        "ExecutorNode",
        foreign_keys=[assigned_executor_node],
        primaryjoin="TaskInstance.assigned_executor_node == ExecutorNode.node_id",
        back_populates="task_instances"
    )

    executions: Mapped[List["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="task_instance",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskInstance(id={self.id}, instance_id='{self.instance_id}', status='{self.status}')>"

    @property
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]

    @property
    def is_finished(self) -> bool:
        """检查任务是否已完成"""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]

    @property
    def can_retry(self) -> bool:
        """检查任务是否可以重试"""
        return (
            self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT] and
            self.retry_count < self.max_retry_count
        )


class TaskExecution(Base, TimestampMixin):
    """任务执行记录表"""
    __tablename__ = "acwl_task_executions"
    __table_args__ = {"comment": "任务执行记录表，记录任务在执行器上的详细执行过程"}

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

    task_instance_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_task_instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务实例ID"
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

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING,
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

    # 关系映射
    task_instance: Mapped["TaskInstance"] = relationship(
        "TaskInstance",
        back_populates="executions"
    )

    logs: Mapped[List["TaskLog"]] = relationship(
        "TaskLog",
        back_populates="execution",
        cascade="all, delete-orphan"
    )

    results: Mapped[List["TaskResult"]] = relationship(
        "TaskResult",
        back_populates="execution",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TaskExecution(id={self.id}, execution_id='{self.execution_id}', status='{self.status}')>"


class TaskLog(Base):
    """任务执行日志表"""
    __tablename__ = "acwl_task_logs"
    __table_args__ = {"comment": "任务执行日志表，记录任务执行过程中的详细日志信息"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="日志ID，自增主键"
    )

    execution_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("acwl_task_executions.execution_id", ondelete="CASCADE"),
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

    # 关系映射
    execution: Mapped["TaskExecution"] = relationship(
        "TaskExecution",
        back_populates="logs"
    )

    def __repr__(self) -> str:
        return f"<TaskLog(id={self.id}, level='{self.log_level}', message='{self.log_message[:50]}...')>"


class TaskResult(Base):
    """任务执行结果表"""
    __tablename__ = "acwl_task_results"
    __table_args__ = {"comment": "任务执行结果表，存储任务执行产生的各种结果数据"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="结果ID，自增主键"
    )

    execution_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("acwl_task_executions.execution_id", ondelete="CASCADE"),
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

    # 关系映射
    execution: Mapped["TaskExecution"] = relationship(
        "TaskExecution",
        back_populates="results"
    )

    def __repr__(self) -> str:
        return f"<TaskResult(id={self.id}, type='{self.result_type}', name='{self.result_name}')>"