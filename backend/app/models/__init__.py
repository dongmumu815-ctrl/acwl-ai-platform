#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模型包
"""

# 导入Base类
from app.core.database import Base

# 导入所有模型以确保它们被SQLAlchemy注册
from .user import User
from .model import Model, ModelType
from .model_service_config import ModelServiceConfig
from .deployment import Deployment, DeploymentGPU, DeploymentTemplate, DeploymentType, DeploymentStatus
from .server import Server, GPUResource, ServerMetrics
from .dataset import Dataset, DatasetType, DatasetStatus
from .datasource import (
    Datasource, DatasourceTestLog, DatasourceUsageStats, 
    DatasourcePermission, DatasourceTemplate,
    DatasourceType, DatasourceStatus, TestResult, PermissionType
)
from .project import (
    Project, ProjectMember, ProjectDatasource, ProjectQuota, 
    ProjectActivity, ProjectTemplate,
    ProjectStatus, ProjectType, ProjectPriority, ProjectMemberRole,
    ProjectDatasourceAccessType, ProjectResourceType, ProjectQuotaResetPeriod,
    ProjectActivityType, ProjectActivityTargetType
)
from .task import (
    TaskDefinition, TaskTemplate, TaskDependency,
    TaskSchedule, TaskInstance, TaskExecution, TaskLog, TaskResult,
    TaskType, TaskPriority, TaskStatus
)
from .executor import (
    ExecutorGroup, ExecutorNode, ExecutorStatus, GroupType, LoadBalanceStrategy
)
from .scheduler import (
    SchedulerNode, SchedulerLock, SchedulerRole, SchedulerStatus
)
from .workflow import (
    Workflow, WorkflowNode, WorkflowConnection, WorkflowInstance, 
    WorkflowNodeInstance, WorkflowSchedule,
    WorkflowStatus, NodeType, ConnectionType, ErrorHandling, InstanceStatus,
    Priority, TriggerType, ScheduleType, MisfirePolicy
)
from .unified_node import (
    UnifiedNode, UnifiedNodeInstance, NodeExecution, NodeLog, NodeResult,
    UnifiedNodeType, NodeInstanceStatus, NodePriority, ErrorHandling
)
from .agent import Agent, AgentConversation, AgentMessage, AgentTool
from .instruction_set import (
    InstructionSet, InstructionNode, InstructionExecution,
    InstructionSetStatus, NodeType, ConditionType, ActionType, ExecutionStatus
)
from .es_query_template import ESQueryTemplate
from .sql_query_template import SQLQueryTemplate

# 导出所有模型
__all__ = [
    "Base",
    "User",
    "Model",
    "ModelType",
    "Deployment",
    "DeploymentGPU",
    "DeploymentTemplate",
    "DeploymentType",
    "DeploymentStatus",
    "Server",
    "GPUResource",
    "ServerMetrics",
    "Dataset",
    "DatasetType",
    "DatasetStatus",
    "Datasource",
    "DatasourceTestLog",
    "DatasourceUsageStats",
    "DatasourcePermission",
    "DatasourceTemplate",
    "DatasourceType",
    "DatasourceStatus",
    "TestResult",
    "PermissionType",
    "Project",
    "ProjectMember",
    "ProjectDatasource",
    "ProjectQuota",
    "ProjectActivity",
    "ProjectTemplate",
    "ProjectStatus",
    "ProjectType",
    "ProjectPriority",
    "ProjectMemberRole",
    "ProjectDatasourceAccessType",
    "ProjectResourceType",
    "ProjectQuotaResetPeriod",
    "ProjectActivityType",
    "ProjectActivityTargetType",
    # 任务管理相关
    "TaskDefinition",
    "TaskTemplate",
    "TaskDependency",
    "TaskSchedule",
    "TaskInstance",
    "TaskExecution",
    "TaskLog",
    "TaskResult",
    "TaskType",
    "TaskPriority",
    "TaskStatus",
    # 执行器相关
    "ExecutorGroup",
    "ExecutorNode",
    "ExecutorStatus",
    "GroupType",
    "LoadBalanceStrategy",
    # 调度器相关
    "SchedulerNode",
    "SchedulerLock",
    "SchedulerRole",
    "SchedulerStatus",
    # 工作流管理相关
    "Workflow",
    "WorkflowNode",
    "WorkflowConnection",
    "WorkflowInstance",
    "WorkflowNodeInstance",
    "WorkflowSchedule",
    "WorkflowStatus",
    "NodeType",
    "ConnectionType",
    "ErrorHandling",
    "InstanceStatus",
    "Priority",
    "TriggerType",
    "ScheduleType",
    "MisfirePolicy",
    # 统一节点模型
    "UnifiedNode",
    "UnifiedNodeInstance",
    "NodeExecution",
    "NodeLog",
    "NodeResult",
    "UnifiedNodeType",
    "NodeInstanceStatus",
    "NodePriority",
    "ErrorHandling",
    # 智能体相关
    "Agent",
    "AgentConversation",
    "AgentMessage",
    "AgentTool",
    "ModelServiceConfig",
    # 指令集相关
    "InstructionSet",
    "InstructionNode",
    "InstructionExecution",
    "InstructionSetStatus",
    "NodeType",
    "ConditionType",
    "ActionType",
    "ExecutionStatus",
    "ESQueryTemplate",
    "SQLQueryTemplate",
]