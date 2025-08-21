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
    ip_address: str = Field(..., description="服务器IP地址", max_length=45)
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
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('无效的IP地址格式')
        return v
    
    @validator('ssh_port')
    def validate_ssh_port(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('SSH端口必须在1-65535之间')
        return v


class ServerUpdate(BaseModel):
    """更新服务器模型"""
    name: Optional[str] = Field(None, description="服务器名称")
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