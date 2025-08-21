from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from .base import BaseQueryParams
from .executor import ExecutorGroup, ExecutorNode, ExecutorGroupQueryParams, ExecutorNodeQueryParams, ExecutorGroupListResponse, ExecutorNodeListResponse, ClusterHealth, ClusterMetrics
from .scheduler import SchedulerNode, SchedulerNodeQueryParams, SchedulerNodeListResponse, SchedulerClusterStatus

# 枚举类定义
class TaskType(str, Enum):
    """任务类型"""
    DATA_SYNC = "data_sync"
    MODEL_TRAIN = "model_train"
    DATA_ANALYSIS = "data_analysis"
    MODEL_INFERENCE = "model_inference"
    DATA_PREPROCESSING = "data_preprocessing"
    MODEL_EVALUATION = "model_evaluation"
    DATA_VISUALIZATION = "data_visualization"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    CUSTOM = "custom"

class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(str, Enum):
    """任务状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"

class InstanceStatus(str, Enum):
    """实例状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"

class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"



class TriggerType(str, Enum):
    """触发类型"""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    DEPENDENCY = "dependency"
    EVENT = "event"
    API = "api"

class ScheduleType(str, Enum):
    """调度类型"""
    ONCE = "once"
    CRON = "cron"
    INTERVAL = "interval"
    DEPENDENCY = "dependency"

# ============================================
# 任务定义相关Schema
# ============================================

class TaskDefinitionBase(BaseModel):
    """任务定义基础Schema"""
    task_name: str = Field(..., description="任务名称")
    task_display_name: Optional[str] = Field(None, description="任务显示名称")
    task_description: Optional[str] = Field(None, description="任务描述")
    task_type: TaskType = Field(..., description="任务类型")
    task_category: Optional[str] = Field(None, description="任务分类")
    task_version: str = Field("1.0.0", description="任务版本")
    task_status: TaskStatus = Field(TaskStatus.DRAFT, description="任务状态")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="优先级")
    
    # 关联信息
    project_id: Optional[int] = Field(None, description="项目ID")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    workflow_node_id: Optional[int] = Field(None, description="工作流节点ID")
    template_id: Optional[int] = Field(None, description="模板ID")
    
    # 执行配置
    executor_group_id: Optional[int] = Field(None, description="执行器分组ID")
    max_retry_count: int = Field(3, description="最大重试次数")
    timeout_seconds: Optional[int] = Field(None, description="超时时间（秒）")
    
    # 任务内容
    task_content: Optional[Dict[str, Any]] = Field(None, description="任务内容")
    input_schema: Optional[Dict[str, Any]] = Field(None, description="输入参数Schema")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="输出结果Schema")
    
    # 标识
    is_template: bool = Field(False, description="是否为模板")
    is_system: bool = Field(False, description="是否为系统任务")
    
    # 扩展信息
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TaskDefinitionCreate(TaskDefinitionBase):
    """创建任务定义Schema"""
    pass

class TaskDefinitionUpdate(BaseModel):
    """更新任务定义Schema"""
    task_display_name: Optional[str] = None
    task_description: Optional[str] = None
    task_category: Optional[str] = None
    task_version: Optional[str] = None
    task_status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    
    executor_group_id: Optional[int] = None
    max_retry_count: Optional[int] = None
    timeout_seconds: Optional[int] = None
    
    task_content: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskDefinitionInDB(TaskDefinitionBase):
    """数据库中的任务定义Schema"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TaskDefinition(TaskDefinitionInDB):
    """任务定义Schema"""
    pass

# ============================================
# 任务模板相关Schema
# ============================================

class TaskTemplateBase(BaseModel):
    """任务模板基础Schema"""
    template_name: str = Field(..., description="模板名称")
    template_display_name: Optional[str] = Field(None, description="模板显示名称")
    template_description: Optional[str] = Field(None, description="模板描述")
    template_category: Optional[str] = Field(None, description="模板分类")
    template_version: str = Field("1.0.0", description="模板版本")
    
    task_type: TaskType = Field(..., description="任务类型")
    
    # 模板内容
    template_content: Dict[str, Any] = Field(..., description="模板内容")
    default_config: Optional[Dict[str, Any]] = Field(None, description="默认配置")
    parameter_schema: Optional[Dict[str, Any]] = Field(None, description="参数Schema")
    
    # 标识
    is_system: bool = Field(False, description="是否为系统模板")
    is_active: bool = Field(True, description="是否激活")
    
    # 扩展信息
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TaskTemplateCreate(TaskTemplateBase):
    """创建任务模板Schema"""
    pass

class TaskTemplateUpdate(BaseModel):
    """更新任务模板Schema"""
    template_display_name: Optional[str] = None
    template_description: Optional[str] = None
    template_category: Optional[str] = None
    template_version: Optional[str] = None
    
    template_content: Optional[Dict[str, Any]] = None
    default_config: Optional[Dict[str, Any]] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskTemplateInDB(TaskTemplateBase):
    """数据库中的任务模板Schema"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TaskTemplate(TaskTemplateInDB):
    """任务模板Schema"""
    pass

# ============================================
# 任务依赖相关Schema
# ============================================

class TaskDependencyBase(BaseModel):
    """任务依赖基础Schema"""
    dependency_task_id: int = Field(..., description="依赖任务ID")
    dependency_type: str = Field("success", description="依赖类型")
    dependency_condition: Optional[str] = Field(None, description="依赖条件")
    is_required: bool = Field(True, description="是否必需")

class TaskDependencyCreate(TaskDependencyBase):
    """创建任务依赖Schema"""
    pass

class TaskDependencyUpdate(BaseModel):
    """更新任务依赖Schema"""
    dependency_type: Optional[str] = None
    dependency_condition: Optional[str] = None
    is_required: Optional[bool] = None

class TaskDependencyInDB(TaskDependencyBase):
    """数据库中的任务依赖Schema"""
    id: int
    task_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TaskDependency(TaskDependencyInDB):
    """任务依赖Schema"""
    pass



# ============================================
# 任务调度相关Schema
# ============================================

class TaskScheduleBase(BaseModel):
    """任务调度基础Schema"""
    schedule_name: str = Field(..., description="调度名称")
    schedule_description: Optional[str] = Field(None, description="调度描述")
    schedule_type: ScheduleType = Field(..., description="调度类型")
    cron_expression: Optional[str] = Field(None, description="Cron表达式")
    interval_seconds: Optional[int] = Field(None, description="间隔秒数")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    is_active: bool = Field(True, description="是否激活")
    
    # 配置信息
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")

class TaskScheduleCreate(TaskScheduleBase):
    """创建任务调度Schema"""
    task_definition_id: int = Field(..., description="任务定义ID")

class TaskScheduleUpdate(BaseModel):
    """更新任务调度Schema"""
    schedule_description: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None

class TaskScheduleInDB(TaskScheduleBase):
    """数据库中的任务调度Schema"""
    id: int
    task_definition_id: int
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TaskSchedule(TaskScheduleInDB):
    """任务调度Schema"""
    pass

# ============================================
# 任务实例相关Schema
# ============================================

class TaskInstanceBase(BaseModel):
    """任务实例基础Schema"""
    instance_id: str = Field(..., description="实例ID")
    instance_name: Optional[str] = Field(None, description="实例名称")
    task_version: str = Field(..., description="任务版本")
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="优先级")
    status: InstanceStatus = Field(InstanceStatus.PENDING, description="状态")
    
    # 输入输出
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    output_data: Optional[Dict[str, Any]] = Field(None, description="输出数据")
    
    # 时间信息
    scheduled_time: datetime = Field(..., description="计划执行时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    
    # 执行信息
    executor_node_id: Optional[int] = Field(None, description="执行器节点ID")
    retry_count: int = Field(0, description="重试次数")
    
    # 触发信息
    triggered_by: TriggerType = Field(..., description="触发方式")
    triggered_by_user: Optional[int] = Field(None, description="触发用户ID")
    
    # 扩展信息
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TaskInstanceCreate(TaskInstanceBase):
    """创建任务实例Schema"""
    task_definition_id: int = Field(..., description="任务定义ID")

class TaskInstanceUpdate(BaseModel):
    """更新任务实例Schema"""
    status: Optional[InstanceStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    executor_node_id: Optional[int] = None
    retry_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskInstanceInDB(TaskInstanceBase):
    """数据库中的任务实例Schema"""
    id: int
    task_definition_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TaskInstance(TaskInstanceInDB):
    """任务实例Schema"""
    pass

# ============================================
# 任务执行相关Schema
# ============================================

class TaskExecutionBase(BaseModel):
    """任务执行基础Schema"""
    execution_id: str = Field(..., description="执行ID")
    status: ExecutionStatus = Field(..., description="执行状态")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    
    # 执行结果
    exit_code: Optional[int] = Field(None, description="退出码")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 资源使用
    cpu_usage: Optional[float] = Field(None, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, description="内存使用量")
    
    # 扩展信息
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TaskExecutionUpdate(BaseModel):
    """更新任务执行Schema"""
    status: Optional[ExecutionStatus] = None
    end_time: Optional[datetime] = None
    exit_code: Optional[int] = None
    error_message: Optional[str] = None
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskExecutionInDB(TaskExecutionBase):
    """数据库中的任务执行Schema"""
    id: int
    task_instance_id: int
    executor_node_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class TaskExecution(TaskExecutionInDB):
    """任务执行Schema"""
    pass

# ============================================
# 任务日志相关Schema
# ============================================

class TaskLogBase(BaseModel):
    """任务日志基础Schema"""
    log_level: LogLevel = Field(..., description="日志级别")
    log_message: str = Field(..., description="日志消息")
    log_source: Optional[str] = Field(None, description="日志来源")
    log_time: datetime = Field(..., description="日志时间")
    
    # 扩展信息
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TaskLogCreate(TaskLogBase):
    """创建任务日志Schema"""
    task_instance_id: int = Field(..., description="任务实例ID")
    task_execution_id: Optional[int] = Field(None, description="任务执行ID")

class TaskLogInDB(TaskLogBase):
    """数据库中的任务日志Schema"""
    id: int
    task_instance_id: int
    task_execution_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TaskLog(TaskLogInDB):
    """任务日志Schema"""
    pass

# ============================================
# 任务结果相关Schema
# ============================================

class TaskResultBase(BaseModel):
    """任务结果基础Schema"""
    result_type: str = Field(..., description="结果类型")
    result_data: Dict[str, Any] = Field(..., description="结果数据")
    result_size: Optional[int] = Field(None, description="结果大小")
    
    # 存储信息
    storage_path: Optional[str] = Field(None, description="存储路径")
    storage_type: Optional[str] = Field(None, description="存储类型")
    
    # 扩展信息
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class TaskResultCreate(TaskResultBase):
    """创建任务结果Schema"""
    task_instance_id: int = Field(..., description="任务实例ID")
    task_execution_id: Optional[int] = Field(None, description="任务执行ID")

class TaskResultInDB(TaskResultBase):
    """数据库中的任务结果Schema"""
    id: int
    task_instance_id: int
    task_execution_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class TaskResult(TaskResultInDB):
    """任务结果Schema"""
    pass

# ============================================
# 查询参数Schema
# ============================================

class BaseQueryParams(BaseModel):
    """基础查询参数"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: Optional[str] = Field(None, description="排序字段")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="排序方向")
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size

class TaskDefinitionQueryParams(BaseQueryParams):
    """任务定义查询参数"""
    task_name: Optional[str] = Field(None, description="任务名称")
    task_type: Optional[TaskType] = Field(None, description="任务类型")
    task_status: Optional[TaskStatus] = Field(None, description="任务状态")
    task_category: Optional[str] = Field(None, description="任务分类")
    project_id: Optional[int] = Field(None, description="项目ID")
    workflow_id: Optional[int] = Field(None, description="工作流ID")
    created_by: Optional[int] = Field(None, description="创建者ID")
    is_template: Optional[bool] = Field(None, description="是否为模板")
    is_system: Optional[bool] = Field(None, description="是否为系统任务")

class TaskTemplateQueryParams(BaseQueryParams):
    """任务模板查询参数"""
    template_name: Optional[str] = Field(None, description="模板名称")
    template_category: Optional[str] = Field(None, description="模板分类")
    task_type: Optional[TaskType] = Field(None, description="任务类型")
    is_system: Optional[bool] = Field(None, description="是否为系统模板")
    is_active: Optional[bool] = Field(None, description="是否激活")



class TaskScheduleQueryParams(BaseQueryParams):
    """任务调度查询参数"""
    schedule_name: Optional[str] = Field(None, description="调度名称")
    schedule_type: Optional[ScheduleType] = Field(None, description="调度类型")
    task_definition_id: Optional[int] = Field(None, description="任务定义ID")
    is_active: Optional[bool] = Field(None, description="是否激活")

class TaskInstanceQueryParams(BaseQueryParams):
    """任务实例查询参数"""
    task_definition_id: Optional[int] = Field(None, description="任务定义ID")
    status: Optional[InstanceStatus] = Field(None, description="状态")
    priority: Optional[TaskPriority] = Field(None, description="优先级")
    triggered_by: Optional[TriggerType] = Field(None, description="触发方式")
    triggered_by_user: Optional[int] = Field(None, description="触发用户ID")
    scheduled_start: Optional[datetime] = Field(None, description="计划开始时间")
    scheduled_end: Optional[datetime] = Field(None, description="计划结束时间")

class TaskExecutionQueryParams(BaseQueryParams):
    """任务执行查询参数"""
    task_instance_id: Optional[int] = Field(None, description="任务实例ID")
    status: Optional[ExecutionStatus] = Field(None, description="执行状态")
    executor_node_id: Optional[int] = Field(None, description="执行器节点ID")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

class TaskLogQueryParams(BaseQueryParams):
    """任务日志查询参数"""
    log_level: Optional[LogLevel] = Field(None, description="日志级别")
    log_source: Optional[str] = Field(None, description="日志来源")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")

# ============================================
# 响应Schema
# ============================================

class BaseListResponse(BaseModel):
    """基础列表响应"""
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")

class TaskDefinitionListResponse(BaseListResponse):
    """任务定义列表响应"""
    items: List[TaskDefinition] = Field(..., description="任务定义列表")

class TaskTemplateListResponse(BaseListResponse):
    """任务模板列表响应"""
    items: List[TaskTemplate] = Field(..., description="任务模板列表")



class TaskScheduleListResponse(BaseListResponse):
    """任务调度列表响应"""
    items: List[TaskSchedule] = Field(..., description="任务调度列表")

class TaskInstanceListResponse(BaseListResponse):
    """任务实例列表响应"""
    items: List[TaskInstance] = Field(..., description="任务实例列表")

class TaskExecutionListResponse(BaseListResponse):
    """任务执行列表响应"""
    items: List[TaskExecution] = Field(..., description="任务执行列表")

class TaskLogListResponse(BaseListResponse):
    """任务日志列表响应"""
    items: List[TaskLog] = Field(..., description="任务日志列表")

# ============================================
# 操作相关Schema
# ============================================

class TaskExecuteRequest(BaseModel):
    """任务执行请求"""
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="优先级")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    scheduled_time: Optional[datetime] = Field(None, description="计划执行时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

# ============================================
# 统计相关Schema
# ============================================

class TaskExecutionStats(BaseModel):
    """任务执行统计"""
    task_definition_id: int = Field(..., description="任务定义ID")
    task_name: str = Field(..., description="任务名称")
    task_type: str = Field(..., description="任务类型")
    total_executions: int = Field(..., description="总执行次数")
    success_count: int = Field(..., description="成功次数")
    failure_count: int = Field(..., description="失败次数")
    avg_duration_seconds: Optional[float] = Field(None, description="平均执行时长（秒）")
    max_duration_seconds: Optional[float] = Field(None, description="最大执行时长（秒）")
    min_duration_seconds: Optional[float] = Field(None, description="最小执行时长（秒）")

class TaskExecutionStatsListResponse(BaseListResponse):
    """任务执行统计列表响应"""
    items: List[TaskExecutionStats] = Field(..., description="任务执行统计列表")

class TaskExecutionStatus(BaseModel):
    """任务执行状态"""
    task_instance_id: int = Field(..., description="任务实例ID")
    instance_id: str = Field(..., description="实例ID")
    task_name: str = Field(..., description="任务名称")
    task_display_name: Optional[str] = Field(None, description="任务显示名称")
    task_status: str = Field(..., description="任务状态")
    priority: str = Field(..., description="优先级")
    scheduled_time: datetime = Field(..., description="计划时间")
    actual_start_time: Optional[datetime] = Field(None, description="实际开始时间")
    actual_end_time: Optional[datetime] = Field(None, description="实际结束时间")
    duration_seconds: Optional[int] = Field(None, description="执行时长（秒）")
    retry_count: int = Field(..., description="重试次数")
    triggered_by: str = Field(..., description="触发方式")
    triggered_by_username: Optional[str] = Field(None, description="触发用户名")

class TaskExecutionStatusListResponse(BaseListResponse):
    """任务执行状态列表响应"""
    items: List[TaskExecutionStatus] = Field(..., description="任务执行状态列表")