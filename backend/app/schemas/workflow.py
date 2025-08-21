from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from .common import PaginatedResponse
from .task import BaseQueryParams


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    draft = "draft"
    active = "active"
    inactive = "inactive"
    archived = "archived"


class NodeType(str, Enum):
    """工作流节点类型枚举"""
    START = "start"
    END = "end"
    PYTHON_CODE = "python_code"
    PYTHON_CODE_DASH = "python-code"  # 添加前端使用的短横线格式
    SQL_QUERY = "sql_query"
    SQL_QUERY_DASH = "sql-query"  # 添加前端使用的短横线格式
    SHELL_SCRIPT = "shell-script"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    MERGE = "merge"
    DATA_TRANSFORM = "data_transform"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    EMAIL_SEND = "email_send"
    DELAY = "delay"
    SUBPROCESS = "subprocess"
    CUSTOM = "custom"


class ConnectionType(str, Enum):
    """工作流连接类型枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    CONDITIONAL = "conditional"
    ALWAYS = "always"


class ErrorHandling(str, Enum):
    """错误处理策略枚举"""
    FAIL = "fail"
    SKIP = "skip"
    RETRY = "retry"
    CUSTOM = "custom"


class InstanceStatus(str, Enum):
    """实例状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    PAUSED = "paused"
    SKIPPED = "skipped"


class Priority(str, Enum):
    """优先级枚举"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TriggerType(str, Enum):
    """触发类型枚举"""
    MANUAL = "manual"
    SCHEDULE = "schedule"
    EVENT = "event"
    API = "api"
    DEPENDENCY = "dependency"


class ScheduleType(str, Enum):
    """调度类型枚举"""
    CRON = "cron"
    INTERVAL = "interval"
    ONCE = "once"
    MANUAL = "manual"
    EVENT_DRIVEN = "event_driven"


class MisfirePolicy(str, Enum):
    """错过执行策略枚举"""
    IGNORE = "ignore"
    FIRE_ONCE = "fire_once"
    FIRE_ALL = "fire_all"


# ============================================
# 工作流基础Schema
# ============================================

class WorkflowBase(BaseModel):
    """工作流基础Schema"""
    name: str = Field(..., max_length=100, description="工作流名称")
    display_name: Optional[str] = Field(None, max_length=200, description="工作流显示名称")
    description: Optional[str] = Field(None, description="工作流描述")
    workflow_category: Optional[str] = Field(None, max_length=50, description="工作流分类")
    workflow_version: str = Field("1.0.0", max_length=20, description="工作流版本")
    workflow_status: WorkflowStatus = Field(WorkflowStatus.draft, description="工作流状态")
    workflow_config: Optional[Dict[str, Any]] = Field(None, description="工作流全局配置")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="工作流输入参数定义")
    output_parameters: Optional[Dict[str, Any]] = Field(None, description="工作流输出参数定义")
    global_variables: Optional[Dict[str, Any]] = Field(None, description="工作流全局变量")
    timeout_seconds: int = Field(7200, ge=1, description="工作流超时时间（秒）")
    max_retry_count: int = Field(1, ge=0, description="工作流最大重试次数")
    project_id: Optional[int] = Field(None, description="所属项目ID")
    is_template: bool = Field(False, description="是否为模板")
    is_system: bool = Field(False, description="是否为系统工作流")


class WorkflowCreate(WorkflowBase):
    """创建工作流Schema"""
    pass


class WorkflowUpdate(BaseModel):
    """工作流更新Schema"""
    name: Optional[str] = Field(None, max_length=100, description="工作流名称")
    display_name: Optional[str] = Field(None, max_length=200, description="工作流显示名称")
    description: Optional[str] = Field(None, description="工作流描述")
    workflow_category: Optional[str] = Field(None, max_length=50, description="工作流分类")
    workflow_version: Optional[str] = Field(None, max_length=20, description="工作流版本")
    workflow_status: Optional[WorkflowStatus] = Field(None, description="工作流状态")
    workflow_config: Optional[Dict[str, Any]] = Field(None, description="工作流全局配置")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="工作流输入参数定义")
    output_parameters: Optional[Dict[str, Any]] = Field(None, description="工作流输出参数定义")
    global_variables: Optional[Dict[str, Any]] = Field(None, description="工作流全局变量")
    timeout_seconds: Optional[int] = Field(None, ge=1, description="工作流超时时间（秒）")
    max_retry_count: Optional[int] = Field(None, ge=0, description="工作流最大重试次数")
    project_id: Optional[int] = Field(None, description="所属项目ID")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_system: Optional[bool] = Field(None, description="是否为系统工作流")
    # 新增节点和连接数据字段
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="工作流节点数据")
    connections: Optional[List[Dict[str, Any]]] = Field(None, description="工作流连接数据")


class WorkflowInDB(WorkflowBase):
    """数据库中的工作流Schema"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Workflow(WorkflowInDB):
    """工作流响应Schema"""
    project_name: Optional[str] = Field(None, description="所属项目名称")


# ============================================
# 工作流节点Schema
# ============================================

class WorkflowNodeBase(BaseModel):
    """工作流节点基础Schema"""
    node_name: str = Field(..., max_length=100, description="节点名称")
    display_name: Optional[str] = Field(None, max_length=200, description="节点显示名称")
    description: Optional[str] = Field(None, description="节点描述")
    node_type: NodeType = Field(..., description="节点类型")
    node_config: Dict[str, Any] = Field(..., description="节点配置参数")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="节点输入参数定义")
    output_parameters: Optional[Dict[str, Any]] = Field(None, description="节点输出参数定义")
    position_x: int = Field(0, description="节点在画布上的X坐标")
    position_y: int = Field(0, description="节点在画布上的Y坐标")
    executor_group: Optional[str] = Field(None, max_length=50, description="执行器分组")
    timeout_seconds: Optional[int] = Field(None, ge=1, description="节点超时时间（秒）")
    max_retry_count: int = Field(3, ge=0, description="节点最大重试次数")
    retry_interval_seconds: int = Field(60, ge=1, description="重试间隔（秒）")
    error_handling: ErrorHandling = Field(ErrorHandling.FAIL, description="错误处理策略")
    is_optional: bool = Field(False, description="是否为可选节点")


class WorkflowNodeCreate(WorkflowNodeBase):
    """创建工作流节点Schema"""
    workflow_id: int = Field(..., description="所属工作流ID")


class WorkflowNodeUpdate(BaseModel):
    """更新工作流节点Schema"""
    node_name: Optional[str] = Field(None, max_length=100, description="节点名称")
    display_name: Optional[str] = Field(None, max_length=200, description="节点显示名称")
    description: Optional[str] = Field(None, description="节点描述")
    node_type: Optional[NodeType] = Field(None, description="节点类型")
    node_config: Optional[Dict[str, Any]] = Field(None, description="节点配置参数")
    input_parameters: Optional[Dict[str, Any]] = Field(None, description="节点输入参数定义")
    output_parameters: Optional[Dict[str, Any]] = Field(None, description="节点输出参数定义")
    position_x: Optional[int] = Field(None, description="节点在画布上的X坐标")
    position_y: Optional[int] = Field(None, description="节点在画布上的Y坐标")
    executor_group: Optional[str] = Field(None, max_length=50, description="执行器分组")
    timeout_seconds: Optional[int] = Field(None, ge=1, description="节点超时时间（秒）")
    max_retry_count: Optional[int] = Field(None, ge=0, description="节点最大重试次数")
    retry_interval_seconds: Optional[int] = Field(None, ge=1, description="重试间隔（秒）")
    error_handling: Optional[ErrorHandling] = Field(None, description="错误处理策略")
    is_optional: Optional[bool] = Field(None, description="是否为可选节点")


class WorkflowNodeInDB(WorkflowNodeBase):
    """数据库中的工作流节点Schema"""
    id: int
    workflow_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowNode(WorkflowNodeInDB):
    """工作流节点完整Schema"""
    pass


# ============================================
# 工作流连接Schema
# ============================================

class WorkflowConnectionBase(BaseModel):
    """工作流连接基础Schema"""
    source_node_id: int = Field(..., description="源节点ID")
    target_node_id: int = Field(..., description="目标节点ID")
    connection_type: ConnectionType = Field(ConnectionType.SUCCESS, description="连接类型")
    condition_expression: Optional[str] = Field(None, description="条件表达式（用于conditional类型）")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="连接配置参数")


class WorkflowConnectionCreate(WorkflowConnectionBase):
    """创建工作流连接Schema"""
    workflow_id: int = Field(..., description="所属工作流ID")


class WorkflowConnectionUpdate(BaseModel):
    """更新工作流连接Schema"""
    connection_type: Optional[ConnectionType] = Field(None, description="连接类型")
    condition_expression: Optional[str] = Field(None, description="条件表达式")
    connection_config: Optional[Dict[str, Any]] = Field(None, description="连接配置参数")


class WorkflowConnectionInDB(WorkflowConnectionBase):
    """数据库中的工作流连接Schema"""
    id: int
    workflow_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowConnection(WorkflowConnectionInDB):
    """工作流连接完整Schema"""
    pass


# ============================================
# 工作流实例Schema
# ============================================

class WorkflowInstanceBase(BaseModel):
    """工作流实例基础Schema"""
    instance_name: Optional[str] = Field(None, max_length=200, description="实例名称")
    priority: Priority = Field(Priority.NORMAL, description="实例优先级")
    input_data: Optional[Dict[str, Any]] = Field(None, description="工作流输入数据")
    scheduled_time: datetime = Field(..., description="计划执行时间")
    triggered_by: TriggerType = Field(..., description="触发方式")
    triggered_by_user: Optional[int] = Field(None, description="触发用户ID")
    parent_instance_id: Optional[int] = Field(None, description="父工作流实例ID")


class WorkflowInstanceCreate(WorkflowInstanceBase):
    """创建工作流实例Schema"""
    workflow_id: int = Field(..., description="工作流定义ID")


class WorkflowInstanceUpdate(BaseModel):
    """更新工作流实例Schema"""
    instance_name: Optional[str] = Field(None, max_length=200, description="实例名称")
    status: Optional[InstanceStatus] = Field(None, description="实例状态")
    priority: Optional[Priority] = Field(None, description="实例优先级")
    output_data: Optional[Dict[str, Any]] = Field(None, description="工作流输出数据")
    context_data: Optional[Dict[str, Any]] = Field(None, description="工作流上下文数据")
    current_node_id: Optional[int] = Field(None, description="当前执行节点ID")
    error_message: Optional[str] = Field(None, description="错误信息")


class WorkflowInstanceInDB(WorkflowInstanceBase):
    """数据库中的工作流实例Schema"""
    id: int
    instance_id: str
    workflow_id: int
    workflow_version: Optional[str]
    status: InstanceStatus
    output_data: Optional[Dict[str, Any]]
    context_data: Optional[Dict[str, Any]]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    duration_seconds: Optional[int]
    current_node_id: Optional[int]
    retry_count: int
    max_retry_count: int
    error_message: Optional[str]
    created_by_scheduler: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowInstance(WorkflowInstanceInDB):
    """工作流实例完整Schema"""
    pass


# ============================================
# 工作流节点实例Schema
# ============================================

class WorkflowNodeInstanceBase(BaseModel):
    """工作流节点实例基础Schema"""
    input_data: Optional[Dict[str, Any]] = Field(None, description="节点输入数据")
    scheduled_time: datetime = Field(..., description="计划执行时间")


class WorkflowNodeInstanceCreate(WorkflowNodeInstanceBase):
    """创建工作流节点实例Schema"""
    workflow_instance_id: int = Field(..., description="工作流实例ID")
    node_id: int = Field(..., description="节点定义ID")


class WorkflowNodeInstanceUpdate(BaseModel):
    """更新工作流节点实例Schema"""
    status: Optional[InstanceStatus] = Field(None, description="节点实例状态")
    output_data: Optional[Dict[str, Any]] = Field(None, description="节点输出数据")
    context_data: Optional[Dict[str, Any]] = Field(None, description="节点上下文数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    assigned_executor_node: Optional[str] = Field(None, description="分配的执行器节点ID")


class WorkflowNodeInstanceInDB(WorkflowNodeInstanceBase):
    """数据库中的工作流节点实例Schema"""
    id: int
    instance_id: str
    workflow_instance_id: int
    node_id: int
    node_name: str
    node_type: str
    status: InstanceStatus
    output_data: Optional[Dict[str, Any]]
    context_data: Optional[Dict[str, Any]]
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    duration_seconds: Optional[int]
    retry_count: int
    max_retry_count: int
    error_message: Optional[str]
    executor_group: Optional[str]
    assigned_executor_node: Optional[str]
    task_instance_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowNodeInstance(WorkflowNodeInstanceInDB):
    """工作流节点实例完整Schema"""
    pass


# ============================================
# 工作流调度Schema
# ============================================

class WorkflowScheduleBase(BaseModel):
    """工作流调度基础Schema"""
    schedule_name: str = Field(..., max_length=100, description="调度名称")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔秒数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    timezone: str = Field("UTC", max_length=50, description="时区")
    is_enabled: bool = Field(True, description="是否启用")
    max_instances: int = Field(1, ge=1, description="最大并发实例数")
    misfire_policy: MisfirePolicy = Field(MisfirePolicy.FIRE_ONCE, description="错过执行策略")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="调度配置参数")
    input_data: Optional[Dict[str, Any]] = Field(None, description="调度时的默认输入数据")


class WorkflowScheduleCreate(WorkflowScheduleBase):
    """创建工作流调度Schema"""
    workflow_id: int = Field(..., description="工作流定义ID")


class WorkflowScheduleUpdate(BaseModel):
    """更新工作流调度Schema"""
    schedule_name: Optional[str] = Field(None, max_length=100, description="调度名称")
    schedule_type: Optional[ScheduleType] = Field(None, description="调度类型")
    cron_expression: Optional[str] = Field(None, max_length=100, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, ge=1, description="间隔秒数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    timezone: Optional[str] = Field(None, max_length=50, description="时区")
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    max_instances: Optional[int] = Field(None, ge=1, description="最大并发实例数")
    misfire_policy: Optional[MisfirePolicy] = Field(None, description="错过执行策略")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="调度配置参数")
    input_data: Optional[Dict[str, Any]] = Field(None, description="调度时的默认输入数据")


class WorkflowScheduleInDB(WorkflowScheduleBase):
    """数据库中的工作流调度Schema"""
    id: int
    workflow_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowSchedule(WorkflowScheduleInDB):
    """工作流调度完整Schema"""
    pass


# ============================================
# 复合Schema和响应Schema
# ============================================

class WorkflowWithNodes(Workflow):
    """包含节点的工作流Schema"""
    nodes: List[WorkflowNode] = Field(default_factory=list, description="工作流节点列表")
    connections: List[WorkflowConnection] = Field(default_factory=list, description="工作流连接列表")


class WorkflowInstanceWithNodes(WorkflowInstance):
    """包含节点实例的工作流实例Schema"""
    node_instances: List[WorkflowNodeInstance] = Field(default_factory=list, description="节点实例列表")


class WorkflowExecutionStatus(BaseModel):
    """工作流执行状态Schema"""
    workflow_instance_id: int = Field(..., description="工作流实例ID")
    instance_id: str = Field(..., description="实例唯一标识")
    workflow_name: str = Field(..., description="工作流名称")
    workflow_display_name: Optional[str] = Field(None, description="工作流显示名称")
    workflow_status: InstanceStatus = Field(..., description="工作流状态")
    priority: Priority = Field(..., description="优先级")
    scheduled_time: datetime = Field(..., description="计划执行时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    retry_count: int = Field(..., description="重试次数")
    triggered_by: TriggerType = Field(..., description="触发方式")
    triggered_by_username: Optional[str] = Field(None, description="触发用户名")
    total_nodes: int = Field(..., description="总节点数")
    completed_nodes: int = Field(..., description="已完成节点数")
    failed_nodes: int = Field(..., description="失败节点数")
    running_nodes: int = Field(..., description="运行中节点数")
    
    model_config = ConfigDict(from_attributes=True)


class NodeExecutionStats(BaseModel):
    """节点执行统计Schema"""
    node_id: int = Field(..., description="节点ID")
    node_name: str = Field(..., description="节点名称")
    node_type: NodeType = Field(..., description="节点类型")
    workflow_name: str = Field(..., description="工作流名称")
    total_executions: int = Field(..., description="总执行次数")
    success_count: int = Field(..., description="成功次数")
    failure_count: int = Field(..., description="失败次数")
    avg_duration_seconds: Optional[float] = Field(None, description="平均执行时长（秒）")
    max_duration_seconds: Optional[int] = Field(None, description="最大执行时长（秒）")
    min_duration_seconds: Optional[int] = Field(None, description="最小执行时长（秒）")
    
    model_config = ConfigDict(from_attributes=True)


# ============================================
# 查询参数Schema
# ============================================

class WorkflowQueryParams(BaseQueryParams):
    """工作流查询参数Schema"""
    name: Optional[str] = Field(None, description="工作流名称（模糊搜索）")
    workflow_status: Optional[WorkflowStatus] = Field(None, description="工作流状态")
    workflow_category: Optional[str] = Field(None, description="工作流分类")
    project_id: Optional[int] = Field(None, description="项目ID")
    created_by: Optional[int] = Field(None, description="创建者ID")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_system: Optional[bool] = Field(None, description="是否为系统工作流")


class WorkflowInstanceQueryParams(BaseQueryParams):
    """工作流实例查询参数Schema"""
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    status: Optional[InstanceStatus] = Field(None, description="实例状态")
    priority: Optional[Priority] = Field(None, description="优先级")
    triggered_by: Optional[TriggerType] = Field(None, description="触发方式")
    triggered_by_user: Optional[int] = Field(None, description="触发用户ID")
    scheduled_start: Optional[datetime] = Field(None, description="计划开始时间（起始）")
    scheduled_end: Optional[datetime] = Field(None, description="计划开始时间（结束）")


class WorkflowNodeInstanceQueryParams(BaseQueryParams):
    """工作流节点实例查询参数Schema"""
    workflow_instance_id: Optional[int] = Field(None, description="工作流实例ID")
    node_id: Optional[int] = Field(None, description="节点ID")
    status: Optional[InstanceStatus] = Field(None, description="节点实例状态")
    node_type: Optional[NodeType] = Field(None, description="节点类型")


# ============================================
# 响应Schema
# ============================================

class WorkflowListResponse(PaginatedResponse):
    """工作流列表响应Schema"""
    items: List[Workflow] = Field(..., description="工作流列表")


class WorkflowInstanceListResponse(PaginatedResponse):
    """工作流实例列表响应Schema"""
    items: List[WorkflowInstance] = Field(..., description="工作流实例列表")


class WorkflowNodeInstanceListResponse(PaginatedResponse):
    """工作流节点实例列表响应Schema"""
    items: List[WorkflowNodeInstance] = Field(..., description="工作流节点实例列表")


class WorkflowExecutionStatusListResponse(PaginatedResponse):
    """工作流执行状态列表响应Schema"""
    items: List[WorkflowExecutionStatus] = Field(..., description="工作流执行状态列表")


class NodeExecutionStatsListResponse(PaginatedResponse):
    """节点执行统计列表响应Schema"""
    items: List[NodeExecutionStats] = Field(..., description="节点执行统计列表")


# ============================================
# 操作Schema
# ============================================

class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求Schema"""
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    priority: Priority = Field(Priority.NORMAL, description="执行优先级")
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间（默认为当前时间）")


class WorkflowCopyRequest(BaseModel):
    """工作流复制请求Schema"""
    new_workflow_name: str = Field(..., max_length=100, description="新工作流名称")
    new_display_name: Optional[str] = Field(None, max_length=200, description="新工作流显示名称")
    copy_schedules: bool = Field(False, description="是否复制调度配置")
    target_project_id: Optional[int] = Field(None, description="目标项目ID")


class WorkflowImportRequest(BaseModel):
    """工作流导入请求Schema"""
    workflow_data: Dict[str, Any] = Field(..., description="工作流数据")
    target_project_id: Optional[int] = Field(None, description="目标项目ID")
    overwrite_existing: bool = Field(False, description="是否覆盖已存在的工作流")


class WorkflowExportResponse(BaseModel):
    """工作流导出响应Schema"""
    workflow_data: Dict[str, Any] = Field(..., description="工作流数据")
    export_time: datetime = Field(..., description="导出时间")
    version: str = Field(..., description="导出格式版本")