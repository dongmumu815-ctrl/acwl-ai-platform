from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import BaseQueryParams, BaseListResponse

# ============================================
# 执行器相关枚举
# ============================================

class GroupType(str, Enum):
    """执行器分组类型枚举"""
    DEFAULT = "DEFAULT"  # 匹配数据库中的大写值
    COMPUTE = "compute"
    GPU = "GPU"  # 匹配数据库中的大写值
    MEMORY_INTENSIVE = "MEMORY_INTENSIVE"  # 匹配数据库中的大写值
    CPU_INTENSIVE = "CPU_INTENSIVE"  # 匹配数据库中的大写值
    IO_INTENSIVE = "io_intensive"
    CUSTOM = "custom"

class LoadBalanceStrategy(str, Enum):
    """负载均衡策略枚举"""
    ROUND_ROBIN = "ROUND_ROBIN"
    LEAST_CONNECTIONS = "LEAST_CONNECTIONS"
    LEAST_LOAD = "LEAST_LOAD"
    RANDOM = "RANDOM"
    WEIGHTED = "WEIGHTED"
    CONSISTENT_HASH = "CONSISTENT_HASH"

class ExecutorStatus(str, Enum):
    """执行器节点状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    MAINTENANCE = "maintenance"
    ERROR = "error"

# ============================================
# 执行器分组相关Schema
# ============================================

class ExecutorGroupBase(BaseModel):
    """执行器分组基础Schema"""
    group_name: str = Field(..., description="分组名称")
    group_display_name: Optional[str] = Field(None, description="分组显示名称")
    group_description: Optional[str] = Field(None, description="分组描述")
    group_type: GroupType = Field(GroupType.DEFAULT, description="分组类型")
    load_balance_strategy: LoadBalanceStrategy = Field(LoadBalanceStrategy.ROUND_ROBIN, description="负载均衡策略")
    max_concurrent_tasks: int = Field(10, description="最大并发任务数")
    is_active: bool = Field(True, description="是否激活")
    
    # 配置信息
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    
    # 扩展信息
    tags: Optional[List[str]] = Field(None, description="标签")
    group_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class ExecutorGroupCreate(ExecutorGroupBase):
    """创建执行器分组Schema"""
    pass

class ExecutorGroupUpdate(BaseModel):
    """更新执行器分组Schema"""
    group_display_name: Optional[str] = None
    group_description: Optional[str] = None
    group_type: Optional[GroupType] = None
    load_balance_strategy: Optional[LoadBalanceStrategy] = None
    max_concurrent_tasks: Optional[int] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    group_metadata: Optional[Dict[str, Any]] = None

class ExecutorGroupInDB(ExecutorGroupBase):
    """数据库中的执行器分组Schema"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ExecutorGroup(ExecutorGroupInDB):
    """执行器分组Schema"""
    pass

# ============================================
# 执行器节点相关Schema
# ============================================

class ExecutorNodeBase(BaseModel):
    """执行器节点基础Schema"""
    node_name: str = Field(..., description="节点名称")
    host_ip: str = Field(..., description="主机IP地址")
    port: int = Field(..., description="端口")
    status: ExecutorStatus = Field(ExecutorStatus.OFFLINE, description="节点状态")
    version: Optional[str] = Field(None, description="节点版本")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="节点能力配置")
    resource_info: Optional[Dict[str, Any]] = Field(None, description="资源信息")
    current_load: int = Field(0, description="当前负载")
    max_concurrent_tasks: int = Field(5, description="最大并发任务数")
    tags: Optional[List[str]] = Field(None, description="标签")
    node_metadata: Optional[Dict[str, Any]] = Field(None, description="节点元数据")

class ExecutorNodeCreate(ExecutorNodeBase):
    """创建执行器节点Schema"""
    group_id: int = Field(..., description="分组ID")
    node_id: Optional[str] = Field(None, description="节点ID，如果不提供将自动生成")

class ExecutorNodeUpdate(BaseModel):
    """更新执行器节点Schema"""
    node_name: Optional[str] = None
    host_ip: Optional[str] = None
    port: Optional[int] = None
    status: Optional[ExecutorStatus] = None
    version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    resource_info: Optional[Dict[str, Any]] = None
    current_load: Optional[int] = None
    max_concurrent_tasks: Optional[int] = None
    node_metadata: Optional[Dict[str, Any]] = None

class ExecutorNodeInDB(ExecutorNodeBase):
    """数据库中的执行器节点Schema"""
    id: int
    node_id: str
    group_id: int
    last_heartbeat: Optional[datetime] = None
    registration_time: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ExecutorNode(ExecutorNodeInDB):
    """执行器节点Schema"""
    pass

# ============================================
# 执行器节点管理相关Schema
# ============================================

class ExecutorNodeHeartbeat(BaseModel):
    """执行器节点心跳Schema"""
    status: Optional[ExecutorStatus] = Field(None, description="节点状态")
    current_load: Optional[int] = Field(None, description="当前负载")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")
    version: Optional[str] = Field(None, description="节点版本")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="节点能力配置")
    node_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class ExecutorNodeStatusUpdate(BaseModel):
    """执行器节点状态更新Schema"""
    status: ExecutorStatus = Field(..., description="新状态")
    reason: Optional[str] = Field(None, description="状态变更原因")
    node_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class ExecutorNodeStatus(BaseModel):
    """执行器节点状态详情Schema"""
    node_id: str = Field(..., description="节点ID")
    node_name: str = Field(..., description="节点名称")
    status: ExecutorStatus = Field(..., description="节点状态")
    is_healthy: bool = Field(..., description="是否健康")
    current_load: int = Field(..., description="当前负载")
    max_concurrent_tasks: int = Field(..., description="最大并发任务数")
    running_tasks: int = Field(..., description="运行中任务数")
    last_heartbeat: Optional[datetime] = Field(None, description="最后心跳时间")
    uptime_seconds: Optional[int] = Field(None, description="运行时长（秒）")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")

# ============================================
# 集群健康和性能指标Schema
# ============================================

class ClusterHealth(BaseModel):
    """集群健康状态Schema"""
    total_nodes: int = Field(..., description="总节点数")
    online_nodes: int = Field(..., description="在线节点数")
    offline_nodes: int = Field(..., description="离线节点数")
    busy_nodes: int = Field(..., description="繁忙节点数")
    idle_nodes: int = Field(..., description="空闲节点数")
    total_capacity: int = Field(..., description="总容量")
    used_capacity: int = Field(..., description="已用容量")
    utilization_rate: float = Field(..., description="利用率")
    avg_load: float = Field(..., description="平均负载")
    health_score: float = Field(..., description="健康评分")

class ClusterMetrics(BaseModel):
    """集群性能指标Schema"""
    timestamp: datetime = Field(..., description="时间戳")
    nodes: List[Dict[str, Any]] = Field(..., description="节点指标列表")
    summary: Dict[str, Any] = Field(..., description="汇总指标")

# ============================================
# 查询参数和响应Schema
# ============================================

class ExecutorGroupQueryParams(BaseQueryParams):
    """执行器分组查询参数Schema"""
    group_name: Optional[str] = Field(None, description="分组名称")
    group_type: Optional[GroupType] = Field(None, description="分组类型")
    is_active: Optional[bool] = Field(None, description="是否激活")

class ExecutorNodeQueryParams(BaseQueryParams):
    """执行器节点查询参数Schema"""
    group_id: Optional[int] = Field(None, description="分组ID")
    node_name: Optional[str] = Field(None, description="节点名称")
    status: Optional[ExecutorStatus] = Field(None, description="节点状态")
    include_offline: bool = Field(True, description="是否包含离线节点")

# ============================================
# 列表响应Schema
# ============================================

class ExecutorGroupListResponse(BaseListResponse):
    """执行器分组列表响应Schema"""
    items: List[ExecutorGroup] = Field(..., description="执行器分组列表")

class ExecutorNodeListResponse(BaseListResponse):
    """执行器节点列表响应Schema"""
    items: List[ExecutorNode] = Field(..., description="执行器节点列表")