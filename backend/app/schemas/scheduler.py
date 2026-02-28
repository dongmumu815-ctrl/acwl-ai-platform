from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from .base import BaseQueryParams, BaseListResponse

# ============================================
# 调度器相关枚举
# ============================================

class SchedulerRole(str, Enum):
    """调度器角色枚举"""
    LEADER = "leader"
    FOLLOWER = "follower"
    CANDIDATE = "candidate"

class SchedulerStatus(str, Enum):
    """调度器状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    STARTING = "starting"
    STANDBY = "standby"
    RUNNING = "running"
    ACTIVE = "active"

# ============================================
# 调度器节点相关Schema
# ============================================

class SchedulerNodeBase(BaseModel):
    """调度器节点基础Schema"""
    node_name: str = Field(..., description="节点名称")
    host_ip: str = Field(..., description="主机IP地址")
    port: int = Field(..., description="端口")
    version: Optional[str] = Field(None, description="调度器版本")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="节点能力配置")
    resource_info: Optional[Dict[str, Any]] = Field(None, description="资源信息")
    node_metadata: Optional[Dict[str, Any]] = Field(None, description="节点元数据")

class SchedulerNodeCreate(SchedulerNodeBase):
    """创建调度器节点Schema"""
    node_id: Optional[str] = Field(None, description="节点ID，如果不提供将自动生成")

class SchedulerNodeUpdate(BaseModel):
    """更新调度器节点Schema"""
    node_name: Optional[str] = None
    host_ip: Optional[str] = None
    port: Optional[int] = None
    version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    resource_info: Optional[Dict[str, Any]] = None
    node_metadata: Optional[Dict[str, Any]] = None

class SchedulerNodeInDB(SchedulerNodeBase):
    """数据库中的调度器节点Schema"""
    id: int
    node_id: str
    role: SchedulerRole
    status: SchedulerStatus
    last_heartbeat: Optional[datetime] = None
    registration_time: datetime
    leader_election_time: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class SchedulerNode(SchedulerNodeInDB):
    """调度器节点Schema"""
    pass

# ============================================
# 调度器节点管理相关Schema
# ============================================

class SchedulerNodeHeartbeat(BaseModel):
    """调度器节点心跳Schema"""
    status: Optional[SchedulerStatus] = Field(None, description="节点状态")
    role: Optional[SchedulerRole] = Field(None, description="节点角色")
    resource_usage: Optional[Dict[str, Any]] = Field(None, description="资源使用情况")
    version: Optional[str] = Field(None, description="节点版本")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="节点能力配置")
    node_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class SchedulerNodeStatusUpdate(BaseModel):
    """调度器节点状态更新Schema"""
    status: SchedulerStatus = Field(..., description="新状态")
    reason: Optional[str] = Field(None, description="状态变更原因")
    node_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

# ============================================
# 调度器集群状态Schema
# ============================================

class SchedulerClusterStatus(BaseModel):
    """调度器集群状态Schema"""
    total_nodes: int = Field(..., description="总节点数")
    online_nodes: int = Field(..., description="在线节点数")
    leader_node_id: Optional[str] = Field(None, description="Leader节点ID")
    leader_node_name: Optional[str] = Field(None, description="Leader节点名称")
    leader_election_time: Optional[datetime] = Field(None, description="Leader选举时间")
    cluster_health: str = Field(..., description="集群健康状态")
    nodes: List[SchedulerNode] = Field(..., description="节点列表")

# ============================================
# 调度器锁相关Schema
# ============================================

class SchedulerLockBase(BaseModel):
    """调度器锁基础Schema"""
    lock_name: str = Field(..., description="锁名称")
    lock_type: str = Field(..., description="锁类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    description: Optional[str] = Field(None, description="锁描述")
    timeout_seconds: Optional[int] = Field(None, description="超时时间（秒）")
    lock_metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class SchedulerLockCreate(SchedulerLockBase):
    """创建调度器锁Schema"""
    pass

class SchedulerLockUpdate(BaseModel):
    """更新调度器锁Schema"""
    description: Optional[str] = None
    timeout_seconds: Optional[int] = None
    lock_metadata: Optional[Dict[str, Any]] = None

class SchedulerLockInDB(SchedulerLockBase):
    """数据库中的调度器锁Schema"""
    id: int
    lock_id: str
    owner_node_id: str
    acquired_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

class SchedulerLock(SchedulerLockInDB):
    """调度器锁Schema"""
    pass

# ============================================
# 查询参数和响应Schema
# ============================================

class SchedulerNodeQueryParams(BaseQueryParams):
    """调度器节点查询参数Schema"""
    node_name: Optional[str] = Field(None, description="节点名称")
    role: Optional[SchedulerRole] = Field(None, description="节点角色")
    status: Optional[SchedulerStatus] = Field(None, description="节点状态")
    include_offline: bool = Field(True, description="是否包含离线节点")

class SchedulerLockQueryParams(BaseQueryParams):
    """调度器锁查询参数Schema"""
    lock_name: Optional[str] = Field(None, description="锁名称")
    lock_type: Optional[str] = Field(None, description="锁类型")
    owner_node_id: Optional[str] = Field(None, description="拥有者节点ID")
    is_active: Optional[bool] = Field(None, description="是否激活")

# ============================================
# 列表响应Schema
# ============================================

class SchedulerNodeListResponse(BaseListResponse):
    """调度器节点列表响应Schema"""
    items: List[SchedulerNode] = Field(..., description="调度器节点列表")

class SchedulerLockListResponse(BaseListResponse):
    """调度器锁列表响应Schema"""
    items: List[SchedulerLock] = Field(..., description="调度器锁列表")