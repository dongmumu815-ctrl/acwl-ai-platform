#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一节点管理相关的Pydantic Schema
整合了原有的任务定义和工作流节点的Schema功能
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from .common import PaginatedResponse
from .base import BaseQueryParams


# ============================================
# 枚举类定义
# ============================================

class UnifiedNodeType(str, Enum):
    """统一节点类型枚举"""
    # 任务类型
    python_code = "python_code"          # Python代码执行
    sql_query = "sql_query"              # SQL查询
    data_transform = "data_transform"    # 数据转换
    api_call = "api_call"                # API调用
    file_operation = "file_operation"    # 文件操作
    email_send = "email_send"            # 邮件发送
    data_sync = "data_sync"              # 数据同步
    model_training = "model_training"    # 模型训练
    data_analysis = "data_analysis"      # 数据分析
    etl = "etl"                          # ETL处理
    custom = "custom"                    # 自定义任务
    
    # 工作流节点类型
    start = "start"                      # 开始节点
    end = "end"                          # 结束节点
    condition = "condition"              # 条件判断
    parallel = "parallel"                # 并行处理
    merge = "merge"                      # 合并节点
    loop = "loop"                        # 循环节点
    timer = "timer"                      # 定时器
    webhook = "webhook"                  # Webhook触发
    manual = "manual"                    # 手动触发


class UnifiedNodeStatus(str, Enum):
    """统一节点状态枚举"""
    draft = "draft"                      # 草稿
    active = "active"                    # 激活
    inactive = "inactive"                # 未激活
    deprecated = "deprecated"            # 已弃用
    archived = "archived"                # 已归档


class ExecutionStatus(str, Enum):
    """执行状态枚举"""
    pending = "pending"                  # 等待中
    running = "running"                  # 运行中
    completed = "completed"              # 已完成
    failed = "failed"                    # 失败
    cancelled = "cancelled"              # 已取消
    timeout = "timeout"                  # 超时
    skipped = "skipped"                  # 跳过
    retry = "retry"                      # 重试中


class LogLevel(str, Enum):
    """日志级别枚举"""
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class NodePriority(str, Enum):
    """节点优先级枚举"""
    low = "low"                          # 低
    normal = "normal"                    # 普通
    high = "high"                        # 高
    urgent = "urgent"                    # 紧急


class ErrorHandling(str, Enum):
    """错误处理策略枚举"""
    fail_fast = "fail_fast"              # 快速失败
    retry = "retry"                      # 重试
    skip = "skip"                        # 跳过
    ignore = "ignore"                    # 忽略
    manual = "manual"                    # 手动处理


# ============================================
# 统一节点相关Schema
# ============================================

class UnifiedNodeBase(BaseModel):
    """统一节点基础Schema"""
    name: str = Field(..., description="节点名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="节点描述")
    node_type: UnifiedNodeType = Field(..., description="节点类型")
    node_category: Optional[str] = Field(None, description="节点分类")
    status: UnifiedNodeStatus = Field(UnifiedNodeStatus.draft, description="节点状态")
    priority: NodePriority = Field(NodePriority.normal, description="优先级")
    
    # 关联信息
    project_id: Optional[int] = Field(None, description="项目ID")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    
    # 执行配置
    executor_group: Optional[str] = Field(None, description="执行器分组")
    timeout_seconds: Optional[int] = Field(None, description="超时时间（秒）")
    max_retry_count: int = Field(3, description="最大重试次数")
    retry_interval_seconds: int = Field(60, description="重试间隔（秒）")
    error_handling: ErrorHandling = Field(ErrorHandling.fail_fast, description="错误处理策略")
    
    # 节点配置
    node_config: Optional[Dict[str, Any]] = Field(None, description="节点配置")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="输入参数定义")
    output_parameters: Optional[Dict[str, Any]] = Field(None, description="输出参数定义")
    resource_requirements: Optional[Dict[str, Any]] = Field(None, description="资源需求")
    environment_variables: Optional[Dict[str, Any]] = Field(None, description="环境变量")
    
    # 工作流相关（仅工作流节点使用）
    position_x: Optional[int] = Field(None, description="X坐标位置")
    position_y: Optional[int] = Field(None, description="Y坐标位置")
    is_optional: bool = Field(False, description="是否可选节点")
    
    # 任务相关（仅独立任务使用）
    command_template: Optional[str] = Field(None, description="命令模板")
    script_content: Optional[str] = Field(None, description="脚本内容")
    dependencies: Optional[List[str]] = Field(None, description="依赖包列表")
    
    # 标识
    is_template: bool = Field(False, description="是否为模板")
    is_system: bool = Field(False, description="是否为系统节点")
    is_active: bool = Field(True, description="是否激活")
    
    # 扩展信息
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    version: str = Field("1.0.0", description="版本号")


class UnifiedNodeCreate(UnifiedNodeBase):
    """创建统一节点的请求Schema"""
    pass


class UnifiedNodeUpdate(BaseModel):
    """更新统一节点的请求Schema"""
    name: Optional[str] = Field(None, description="节点名称")
    display_name: Optional[str] = Field(None, description="显示名称")
    description: Optional[str] = Field(None, description="节点描述")
    node_type: Optional[UnifiedNodeType] = Field(None, description="节点类型")
    node_category: Optional[str] = Field(None, description="节点分类")
    status: Optional[UnifiedNodeStatus] = Field(None, description="节点状态")
    priority: Optional[NodePriority] = Field(None, description="优先级")
    
    # 执行配置
    executor_group: Optional[str] = Field(None, description="执行器分组")
    timeout_seconds: Optional[int] = Field(None, description="超时时间（秒）")
    max_retry_count: Optional[int] = Field(None, description="最大重试次数")
    retry_interval_seconds: Optional[int] = Field(None, description="重试间隔（秒）")
    error_handling: Optional[ErrorHandling] = Field(None, description="错误处理策略")
    
    # 节点配置
    node_config: Optional[Dict[str, Any]] = Field(None, description="节点配置")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="输入参数定义")
    output_parameters: Optional[Dict[str, Any]] = Field(None, description="输出参数定义")
    resource_requirements: Optional[Dict[str, Any]] = Field(None, description="资源需求")
    environment_variables: Optional[Dict[str, Any]] = Field(None, description="环境变量")
    
    # 工作流相关
    position_x: Optional[int] = Field(None, description="X坐标位置")
    position_y: Optional[int] = Field(None, description="Y坐标位置")
    is_optional: Optional[bool] = Field(None, description="是否可选节点")
    
    # 任务相关
    command_template: Optional[str] = Field(None, description="命令模板")
    script_content: Optional[str] = Field(None, description="脚本内容")
    dependencies: Optional[List[str]] = Field(None, description="依赖包列表")
    
    # 标识
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_active: Optional[bool] = Field(None, description="是否激活")
    
    # 扩展信息
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    version: Optional[str] = Field(None, description="版本号")


class UnifiedNodeInDB(UnifiedNodeBase):
    """数据库中的统一节点Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="节点ID")
    created_by: int = Field(..., description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UnifiedNodeResponse(UnifiedNodeInDB):
    """统一节点响应Schema"""
    pass


class UnifiedNodeListResponse(PaginatedResponse):
    """统一节点列表响应Schema"""
    items: List[UnifiedNodeResponse] = Field(..., description="节点列表")


# ============================================
# 统一节点实例相关Schema
# ============================================

class UnifiedNodeInstanceBase(BaseModel):
    """统一节点实例基础Schema"""
    instance_id: str = Field(..., description="实例唯一标识")
    node_id: int = Field(..., description="节点ID")
    workflow_instance_id: Optional[int] = Field(None, description="工作流实例ID")
    schedule_id: Optional[int] = Field(None, description="调度ID")
    parent_instance_id: Optional[int] = Field(None, description="父实例ID")
    
    status: ExecutionStatus = Field(ExecutionStatus.pending, description="执行状态")
    priority: NodePriority = Field(NodePriority.normal, description="优先级")
    
    # 执行信息
    executor_group: Optional[str] = Field(None, description="执行器分组")
    assigned_executor_node: Optional[str] = Field(None, description="分配的执行器节点")
    
    # 时间信息
    scheduled_time: datetime = Field(..., description="计划执行时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    
    # 重试信息
    retry_count: int = Field(0, description="重试次数")
    max_retry_count: int = Field(3, description="最大重试次数")
    
    # 数据
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    context_data: Optional[Dict[str, Any]] = Field(None, description="上下文数据")
    runtime_config: Optional[Dict[str, Any]] = Field(None, description="运行时配置")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 创建信息
    created_by_scheduler: Optional[str] = Field(None, description="创建该实例的调度器节点ID")


class UnifiedNodeInstanceCreate(BaseModel):
    """创建统一节点实例的请求Schema"""
    instance_id: str = Field(..., description="实例唯一标识")
    node_id: int = Field(..., description="节点ID")
    workflow_instance_id: Optional[int] = Field(None, description="工作流实例ID")
    schedule_id: Optional[int] = Field(None, description="调度ID")
    parent_instance_id: Optional[int] = Field(None, description="父实例ID")
    
    priority: NodePriority = Field(NodePriority.normal, description="优先级")
    scheduled_time: datetime = Field(..., description="计划执行时间")
    
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    context_data: Optional[Dict[str, Any]] = Field(None, description="上下文数据")
    runtime_config: Optional[Dict[str, Any]] = Field(None, description="运行时配置")
    
    created_by_scheduler: Optional[str] = Field(None, description="创建该实例的调度器节点ID")


class UnifiedNodeInstanceUpdate(BaseModel):
    """更新统一节点实例的请求Schema"""
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    assigned_executor_node: Optional[str] = Field(None, description="分配的执行器节点")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    retry_count: Optional[int] = Field(None, description="重试次数")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    context_data: Optional[Dict[str, Any]] = Field(None, description="上下文数据")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")


class UnifiedNodeInstanceInDB(UnifiedNodeInstanceBase):
    """数据库中的统一节点实例Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="实例ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class UnifiedNodeInstanceResponse(UnifiedNodeInstanceInDB):
    """统一节点实例响应Schema"""
    pass


class UnifiedNodeInstanceListResponse(PaginatedResponse):
    """统一节点实例列表响应Schema"""
    items: List[UnifiedNodeInstanceResponse] = Field(..., description="实例列表")


# ============================================
# 节点执行相关Schema
# ============================================

class NodeExecutionBase(BaseModel):
    """节点执行基础Schema"""
    execution_id: str = Field(..., description="执行唯一标识")
    node_instance_id: int = Field(..., description="节点实例ID")
    executor_node: str = Field(..., description="执行器节点")
    
    status: ExecutionStatus = Field(ExecutionStatus.pending, description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    
    exit_code: Optional[int] = Field(None, description="退出码")
    stdout: Optional[str] = Field(None, description="标准输出")
    stderr: Optional[str] = Field(None, description="标准错误")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")
    execution_context: Optional[Dict[str, Any]] = Field(None, description="执行上下文")


class NodeExecutionCreate(BaseModel):
    """创建节点执行的请求Schema"""
    execution_id: str = Field(..., description="执行唯一标识")
    node_instance_id: int = Field(..., description="节点实例ID")
    executor_node: str = Field(..., description="执行器节点")
    start_time: datetime = Field(..., description="开始时间")
    execution_context: Optional[Dict[str, Any]] = Field(None, description="执行上下文")


class NodeExecutionUpdate(BaseModel):
    """更新节点执行的请求Schema"""
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    exit_code: Optional[int] = Field(None, description="退出码")
    stdout: Optional[str] = Field(None, description="标准输出")
    stderr: Optional[str] = Field(None, description="标准错误")
    error_message: Optional[str] = Field(None, description="错误信息")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")


class NodeExecutionInDB(NodeExecutionBase):
    """数据库中的节点执行Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="执行ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class NodeExecutionResponse(NodeExecutionInDB):
    """节点执行响应Schema"""
    pass


# ============================================
# 节点日志相关Schema
# ============================================

class NodeLogBase(BaseModel):
    """节点日志基础Schema"""
    node_instance_id: int = Field(..., description="节点实例ID")
    execution_id: Optional[str] = Field(None, description="执行ID")
    log_level: LogLevel = Field(LogLevel.info, description="日志级别")
    message: str = Field(..., description="日志消息")
    details: Optional[Dict[str, Any]] = Field(None, description="日志详情")
    source: Optional[str] = Field(None, description="日志来源")
    timestamp: datetime = Field(..., description="时间戳")


class NodeLogCreate(NodeLogBase):
    """创建节点日志的请求Schema"""
    pass


class NodeLogInDB(NodeLogBase):
    """数据库中的节点日志Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="日志ID")
    created_at: datetime = Field(..., description="创建时间")


class NodeLogResponse(NodeLogInDB):
    """节点日志响应Schema"""
    pass


class NodeLogListResponse(PaginatedResponse):
    """节点日志列表响应Schema"""
    items: List[NodeLogResponse] = Field(..., description="日志列表")


# ============================================
# 节点结果相关Schema
# ============================================

class NodeResultBase(BaseModel):
    """节点结果基础Schema"""
    node_instance_id: int = Field(..., description="节点实例ID")
    execution_id: Optional[str] = Field(None, description="执行ID")
    result_type: str = Field(..., description="结果类型")
    result_data: Dict[str, Any] = Field(..., description="结果数据")
    file_paths: Optional[List[str]] = Field(None, description="结果文件路径")
    metadata: Optional[Dict[str, Any]] = Field(None, description="结果元数据")
    created_at: datetime = Field(..., description="创建时间")


class NodeResultCreate(NodeResultBase):
    """创建节点结果的请求Schema"""
    pass


class NodeResultInDB(NodeResultBase):
    """数据库中的节点结果Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="结果ID")


class NodeResultResponse(NodeResultInDB):
    """节点结果响应Schema"""
    pass


# ============================================
# 查询参数Schema
# ============================================

class UnifiedNodeQueryParams(BaseQueryParams):
    """统一节点查询参数Schema"""
    name: Optional[str] = Field(None, description="节点名称（模糊匹配）")
    node_type: Optional[UnifiedNodeType] = Field(None, description="节点类型")
    node_category: Optional[str] = Field(None, description="节点分类")
    status: Optional[UnifiedNodeStatus] = Field(None, description="节点状态")
    project_id: Optional[int] = Field(None, description="项目ID")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    executor_group: Optional[str] = Field(None, description="执行器分组")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_system: Optional[bool] = Field(None, description="是否为系统节点")
    is_active: Optional[bool] = Field(None, description="是否激活")
    created_by: Optional[int] = Field(None, description="创建者ID")


class UnifiedNodeInstanceQueryParams(BaseQueryParams):
    """统一节点实例查询参数Schema"""
    instance_id: Optional[str] = Field(None, description="实例ID")
    node_id: Optional[int] = Field(None, description="节点ID")
    workflow_instance_id: Optional[int] = Field(None, description="工作流实例ID")
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    executor_group: Optional[str] = Field(None, description="执行器分组")
    assigned_executor_node: Optional[str] = Field(None, description="分配的执行器节点")
    scheduled_time_start: Optional[datetime] = Field(None, description="计划执行时间开始")
    scheduled_time_end: Optional[datetime] = Field(None, description="计划执行时间结束")
    created_by_scheduler: Optional[str] = Field(None, description="创建该实例的调度器节点ID")


# ============================================
# 节点执行请求相关Schema
# ============================================

class NodeExecuteRequest(BaseModel):
    """节点执行请求Schema"""
    instance_id: Optional[str] = Field(None, description="实例ID，如果不提供则自动生成")
    priority: NodePriority = Field(NodePriority.normal, description="优先级")
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间，如果不提供则立即执行")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    context_data: Optional[Dict[str, Any]] = Field(None, description="上下文数据")
    runtime_config: Optional[Dict[str, Any]] = Field(None, description="运行时配置")


class NodeLogQueryParams(BaseQueryParams):
    """节点日志查询参数Schema"""
    node_instance_id: Optional[int] = Field(None, description="节点实例ID")
    execution_id: Optional[str] = Field(None, description="执行ID")
    log_level: Optional[LogLevel] = Field(None, description="日志级别")
    source: Optional[str] = Field(None, description="日志来源")
    timestamp_start: Optional[datetime] = Field(None, description="时间戳开始")
    timestamp_end: Optional[datetime] = Field(None, description="时间戳结束")
    message: Optional[str] = Field(None, description="日志消息（模糊匹配）")


# ============================================
# 统计相关Schema
# ============================================

class NodeExecutionStats(BaseModel):
    """节点执行统计Schema"""
    node_id: int = Field(..., description="节点ID")
    node_name: str = Field(..., description="节点名称")
    node_type: UnifiedNodeType = Field(..., description="节点类型")
    total_executions: int = Field(..., description="总执行次数")
    successful_executions: int = Field(..., description="成功执行次数")
    failed_executions: int = Field(..., description="失败执行次数")
    average_duration_seconds: Optional[float] = Field(None, description="平均执行时长（秒）")
    last_execution_time: Optional[datetime] = Field(None, description="最后执行时间")
    success_rate: float = Field(..., description="成功率")


class NodeExecutionStatsListResponse(PaginatedResponse):
    """节点执行统计列表响应Schema"""
    items: List[NodeExecutionStats] = Field(..., description="统计列表")