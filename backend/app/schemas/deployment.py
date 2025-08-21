#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署相关的Pydantic schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.deployment import DeploymentType, DeploymentStatus
from app.schemas.server import DeploymentServerInfo


class DeploymentBase(BaseModel):
    """部署基础模型"""
    deployment_name: str = Field(..., description="部署名称")
    deployment_type: DeploymentType = Field(..., description="部署类型")
    model_id: int = Field(..., description="关联的模型ID")
    server_id: Optional[int] = Field(None, description="部署服务器ID")
    max_concurrent_requests: Optional[int] = Field(None, description="最大并发请求数")
    restart_policy: str = Field("no", description="重启策略：no, always, on-failure等")
    config: Optional[Dict[str, Any]] = Field(None, description="部署配置，如资源分配等")
    gpu_config: Optional[Dict[str, Any]] = Field(None, description="GPU配置，如设备ID列表、显存限制等")
    runtime_env: Optional[Dict[str, Any]] = Field(None, description="运行环境配置，如CUDA版本、Python环境等")


class DeploymentCreate(DeploymentBase):
    """创建部署请求模型"""
    gpu_ids: Optional[List[int]] = Field(None, description="GPU ID列表")
    
    class Config:
        schema_extra = {
            "example": {
                "deployment_name": "llama2-7b-vllm",
                "deployment_type": "vLLM",
                "model_id": 1,
                "server_id": 1,
                "max_concurrent_requests": 10,
                "restart_policy": "always",
                "gpu_ids": [1, 2],
                "config": {
                    "tensor_parallel_size": 2,
                    "max_model_len": 4096
                },
                "gpu_config": {
                    "memory_limit": "16GiB"
                },
                "runtime_env": {
                    "cuda_version": "11.8",
                    "python_version": "3.10"
                }
            }
        }


class DeploymentUpdate(BaseModel):
    """更新部署请求模型"""
    deployment_name: Optional[str] = Field(None, description="部署名称")
    max_concurrent_requests: Optional[int] = Field(None, description="最大并发请求数")
    restart_policy: Optional[str] = Field(None, description="重启策略")
    config: Optional[Dict[str, Any]] = Field(None, description="部署配置")
    gpu_config: Optional[Dict[str, Any]] = Field(None, description="GPU配置")
    runtime_env: Optional[Dict[str, Any]] = Field(None, description="运行环境配置")
    
    class Config:
        schema_extra = {
            "example": {
                "deployment_name": "llama2-7b-vllm-updated",
                "max_concurrent_requests": 20,
                "restart_policy": "on-failure",
                "config": {
                    "tensor_parallel_size": 4,
                    "max_model_len": 8192
                }
            }
        }


class DeploymentResponse(BaseModel):
    """部署响应模型"""
    id: int
    deployment_name: str
    deployment_type: DeploymentType
    model_id: int
    server_id: Optional[int]
    status: DeploymentStatus
    endpoint_url: Optional[str]
    deploy_path: Optional[str]
    config: Optional[Dict[str, Any]]
    gpu_config: Optional[Dict[str, Any]]
    runtime_env: Optional[Dict[str, Any]]
    restart_policy: str
    max_concurrent_requests: Optional[int]
    deployment_logs: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    updated_by: Optional[int]
    
    class Config:
        from_attributes = True


class DeploymentListResponse(BaseModel):
    """部署列表响应模型"""
    items: List[DeploymentResponse]
    total: int
    page: int
    size: int
    pages: int


class DeploymentGPUResponse(BaseModel):
    """部署GPU关联响应模型"""
    deployment_id: int
    gpu_id: int
    memory_limit: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DeploymentTemplateResponse(BaseModel):
    """部署模板响应模型"""
    id: int
    name: str
    description: Optional[str]
    deployment_type: DeploymentType
    template_config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int]
    updated_by: Optional[int]
    
    class Config:
        from_attributes = True


class DeploymentTemplateCreate(BaseModel):
    """创建部署模板请求模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    deployment_type: DeploymentType = Field(..., description="部署类型")
    template_config: Dict[str, Any] = Field(..., description="模板配置")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "vLLM标准配置",
                "description": "适用于大多数模型的vLLM标准部署配置",
                "deployment_type": "vLLM",
                "template_config": {
                    "tensor_parallel_size": 2,
                    "max_model_len": 4096,
                    "gpu_memory_utilization": 0.9
                }
            }
        }


class DeploymentTemplateUpdate(BaseModel):
    """更新部署模板请求模型"""
    name: Optional[str] = Field(None, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    template_config: Optional[Dict[str, Any]] = Field(None, description="模板配置")