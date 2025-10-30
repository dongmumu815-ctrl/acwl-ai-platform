#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器相关的Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.models.server import ServerType, ServerStatus


class ServerType(str, Enum):
    """服务器类型枚举"""
    physical = "physical"  # 物理机
    virtual = "virtual"    # 虚拟机
    cloud = "cloud"        # 云服务器


class ServerStatus(str, Enum):
    """服务器状态枚举"""
    online = "online"          # 在线
    offline = "offline"        # 离线
    maintenance = "maintenance" # 维护中


class ServerBase(BaseModel):
    """服务器基础模型"""
    name: str = Field(..., description="服务器名称", max_length=100)
    ip_address: str = Field(..., description="服务器地址（IP或域名）", max_length=253)
    ssh_port: int = Field(default=22, description="SSH端口")
    ssh_username: Optional[str] = Field(None, description="SSH用户名", max_length=50)
    ssh_key_path: Optional[str] = Field(None, description="SSH密钥路径")
    ssh_password: Optional[str] = Field(None, description="SSH密码（加密存储）", max_length=255)
    server_type: ServerType = Field(..., description="服务器类型")
    os_info: Optional[str] = Field(None, description="操作系统信息", max_length=100)
    status: ServerStatus = Field(default=ServerStatus.offline, description="服务器状态")
    total_memory: Optional[str] = Field(None, description="总内存", max_length=50)
    total_storage: Optional[str] = Field(None, description="总存储空间", max_length=50)
    total_cpu_cores: Optional[int] = Field(None, description="总CPU核心数")


class ServerCreate(ServerBase):
    """创建服务器模型"""
    ssh_password: Optional[str] = Field(None, description="SSH密码")
    
    @validator('ip_address')
    def validate_ip_address(cls, v):
        import re
        import ipaddress
        v = (v or '').strip()
        if not v:
            raise ValueError('请输入地址')
        if v.lower() == 'localhost':
            return v
        # 协议/路径不允许
        if '://' in v or '/' in v:
            raise ValueError('请输入主机名（IP或域名），不要包含协议或路径')
        # 先尝试作为 IP（支持 IPv4/IPv6）
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass
        # 如果包含冒号但不是 IPv6，可能是端口，拒绝（端口应使用独立字段）
        if ':' in v and not re.fullmatch(r'[0-9a-fA-F:]+', v):
            raise ValueError('请不要在地址中包含端口')
        # 主机名（允许单标签或 FQDN），每个标签 1-63，总长 <= 253
        hostname_pattern = re.compile(r'^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)(?:\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?))*$')
        if hostname_pattern.fullmatch(v):
            return v
        raise ValueError('无效的地址格式（需为IP或域名）')
    
    @validator('ssh_port')
    def validate_ssh_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('SSH端口必须在1-65535之间')
        return v


class ServerUpdate(BaseModel):
    """更新服务器模型"""
    name: Optional[str] = Field(None, description="服务器名称")
    ip_address: Optional[str] = Field(None, description="服务器IP地址")
    ssh_port: Optional[int] = Field(None, description="SSH端口")
    ssh_username: Optional[str] = Field(None, description="SSH用户名")
    ssh_key_path: Optional[str] = Field(None, description="SSH密钥路径")
    ssh_password: Optional[str] = Field(None, description="SSH密码")
    server_type: Optional[ServerType] = Field(None, description="服务器类型")
    os_info: Optional[str] = Field(None, description="操作系统信息")
    status: Optional[ServerStatus] = Field(None, description="服务器状态")
    total_memory: Optional[str] = Field(None, description="总内存")
    total_storage: Optional[str] = Field(None, description="总存储空间")
    total_cpu_cores: Optional[int] = Field(None, description="总CPU核心数")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        import re
        import ipaddress
        if v is None:
            return v
        v = v.strip()
        if not v:
            return v
        if v.lower() == 'localhost':
            return v
        if '://' in v or '/' in v:
            raise ValueError('请输入主机名（IP或域名），不要包含协议或路径')
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass
        if ':' in v and not re.fullmatch(r'[0-9a-fA-F:]+', v):
            raise ValueError('请不要在地址中包含端口')
        hostname_pattern = re.compile(r'^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)(?:\.(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?))*$')
        if hostname_pattern.fullmatch(v):
            return v
        raise ValueError('无效的地址格式（需为IP或域名）')

    @validator('ssh_port')
    def validate_ssh_port(cls, v):
        if v is None:
            return v
        if not 1 <= v <= 65535:
            raise ValueError('SSH端口必须在1-65535之间')
        return v


class GPUResourceResponse(BaseModel):
    """GPU资源响应模型"""
    id: int
    server_id: int
    gpu_name: str
    gpu_type: Optional[str]
    memory_size: Optional[str]
    cuda_version: Optional[str]
    device_id: Optional[str]
    is_available: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServerResponse(ServerBase):
    """服务器响应模型"""
    id: int
    status: ServerStatus
    created_at: datetime
    updated_at: datetime
    gpu_resources: Optional[List[GPUResourceResponse]] = None
    
    class Config:
        from_attributes = True


class ServerStatusResponse(BaseModel):
    """服务器状态响应模型"""
    server_id: int
    status: ServerStatus
    cpu_usage: Optional[float] = Field(None, description="CPU使用率（百分比）")
    memory_usage: Optional[float] = Field(None, description="内存使用率（百分比）")
    disk_usage: Optional[float] = Field(None, description="磁盘使用率（百分比）")
    gpu_usage: Optional[List[float]] = Field(None, description="GPU使用率列表")
    uptime: Optional[str] = Field(None, description="运行时间")
    last_updated: Optional[str] = Field(None, description="最后更新时间")


class GPUResourceCreate(BaseModel):
    """创建GPU资源模型"""
    server_id: int
    gpu_name: str
    gpu_type: Optional[str] = None
    memory_size: Optional[str] = None
    cuda_version: Optional[str] = None
    device_id: Optional[str] = None
    is_available: bool = True


class GPUResourceUpdate(BaseModel):
    """更新GPU资源模型"""
    gpu_name: Optional[str] = None
    gpu_type: Optional[str] = None
    memory_size: Optional[str] = None
    cuda_version: Optional[str] = None
    device_id: Optional[str] = None
    is_available: Optional[bool] = None


class ServerListResponse(BaseModel):
    """服务器列表响应模型"""
    id: int
    name: str
    ip_address: str
    server_type: ServerType
    status: ServerStatus
    os_info: Optional[str]
    total_memory: Optional[str]
    total_cpu_cores: Optional[int]
    gpu_count: int = 0  # GPU数量
    deployment_count: int = 0  # 部署数量
    created_at: datetime
    
    class Config:
        from_attributes = True


class ServerMetricsResponse(BaseModel):
    """服务器监控指标响应模型"""
    id: int
    server_id: int
    cpu_usage: Optional[float] = Field(None, description="CPU使用率（百分比）")
    memory_usage: Optional[float] = Field(None, description="内存使用率（百分比）")
    disk_usage: Optional[float] = Field(None, description="磁盘使用率（百分比）")
    network_in: Optional[float] = Field(None, description="网络入流量（MB/s）")
    network_out: Optional[float] = Field(None, description="网络出流量（MB/s）")
    gpu_metrics: Optional[dict] = Field(None, description="GPU监控指标")
    timestamp: datetime = Field(..., description="监控时间戳")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DeploymentServerInfo(BaseModel):
    """部署时的服务器信息"""
    id: int
    name: str
    ip_address: str
    status: ServerStatus
    available_gpus: List[GPUResourceResponse]
    
    class Config:
        from_attributes = True