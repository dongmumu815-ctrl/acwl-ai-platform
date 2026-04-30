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
from .script_execution import ScriptExecutionRecord, ScriptExecutionDetail, ScriptExecutionStatus, ScriptDetailStatus
from .dataset import Dataset, DatasetType, DatasetStatus
from .datasource import (
    Datasource, DatasourceTestLog, DatasourceUsageStats, 
    DatasourcePermission, DatasourceTemplate,
    DatasourceType, DatasourceStatus, TestResult, PermissionType
)
from .data_resource import (
    DataResourceCategory,
    DataResource,
    DataResourcePermission,
    DataResourceAccessLog,
    DataResourceFavorite,
    DataResourceQueryHistory,
    DataResourceTag,
    DataResourceTagRelation,
)

from .resource_type import DataResourceType
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
from .fine_tuning import FineTuningJob, FineTuningMethod, FineTuningStatus
from .instruction_set import (
    InstructionSet, InstructionNode, InstructionExecution,
    InstructionSetStatus, NodeType, ConditionType, ActionType, ExecutionStatus
)
from .es_query_template import ESQueryTemplate
from .sql_query_template import SQLQueryTemplate
from .role import Role, UserRole, RolePermission
from .permission import Permission
from .environment import Environment
from .resource_package import (
    ResourcePackage,
    ResourcePackagePermission,
    ResourcePackageQueryHistory,
    ResourcePackageTag,
)

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
    "ScriptExecutionRecord",
    "ScriptExecutionDetail",
    "ScriptExecutionStatus",
    "ScriptDetailStatus",
    "Dataset",
    "DatasetType",
    "DatasetStatus",
    "HarborConfig",
    "AppTemplate",
    "AppInstance",
    "AppDeployment",
    "AppType",
    "AppStatus",
    "Datasource",
    "DatasourceTestLog",
    "DatasourceUsageStats",
    "DatasourcePermission",
    "DatasourceTemplate",
    "DatasourceType",
    "DatasourceStatus",
    "TestResult",
    "PermissionType",
    # 数据资源中心相关
    "DataResourceCategory",
    "DataResource",
    "DataResourcePermission",
    "DataResourceAccessLog",
    "DataResourceFavorite",
    "DataResourceQueryHistory",
    "DataResourceTag",
    "DataResourceTagRelation",
	"DataResourceType",
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
    # 微调任务相关
    "FineTuningJob",
    "FineTuningMethod",
    "FineTuningStatus",
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
    # 角色权限系统
    "Role",
    "UserRole", 
    "RolePermission",
    "Permission",
    # 资源包相关
    "ResourcePackage",
    "ResourcePackagePermission",
    "ResourcePackageQueryHistory",
    "ResourcePackageTag",
    "Environment",
]