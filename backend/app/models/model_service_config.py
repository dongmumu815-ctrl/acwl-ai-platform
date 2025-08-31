#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型服务配置数据库模型
用于管理各种AI服务提供商的接口配置
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DECIMAL, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class ModelServiceProvider(str, Enum):
    """模型服务提供商枚举"""
    OPENAI = "openai"
    CLAUDE = "claude"
    QWEN = "qwen"  # 通义千问
    DOUBAO = "doubao"  # 豆包
    GEMINI = "gemini"  # Google Gemini
    OLLAMA = "ollama"  # 本地Ollama
    VLLM = "vllm"  # 本地vLLM
    CUSTOM = "custom"  # 自定义服务


class ModelServiceConfig(Base):
    """
    模型服务配置表
    用于存储各种AI服务提供商的接口配置信息
    """
    __tablename__ = "acwl_model_service_configs"
    
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    name = Column(String(100), unique=True, nullable=False, index=True, comment="服务配置名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    provider = Column(String(50), nullable=False, index=True, comment="服务提供商")
    model_type = Column(String(50), default="chat", comment="模型类型")
    model_name = Column(String(100), nullable=False, comment="模型名称")
    
    # API配置
    api_endpoint = Column(String(500), comment="API端点URL")
    api_key = Column(String(500), comment="API密钥")
    api_version = Column(String(20), comment="API版本")
    
    # 模型参数
    max_tokens = Column(Integer, default=4096, comment="最大token数")
    temperature = Column(DECIMAL(3, 2), default=0.7, comment="温度参数")
    top_p = Column(DECIMAL(3, 2), default=0.9, comment="top_p参数")
    frequency_penalty = Column(DECIMAL(3, 2), default=0.0, comment="频率惩罚")
    presence_penalty = Column(DECIMAL(3, 2), default=0.0, comment="存在惩罚")
    
    # 请求配置
    timeout = Column(Integer, default=30, comment="请求超时时间(秒)")
    retry_count = Column(Integer, default=3, comment="重试次数")
    extra_config = Column(Text, comment="额外配置(JSON格式)")
    
    # 状态字段
    is_active = Column(Boolean, default=True, index=True, comment="是否启用")
    is_default = Column(Boolean, default=False, index=True, comment="是否为默认配置")
    description = Column(Text, comment="配置描述")
    
    # 审计字段
    created_by = Column(Integer, ForeignKey("acwl_users.id", ondelete="SET NULL"), comment="创建者ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<ModelServiceConfig(id={self.id}, name='{self.name}', provider='{self.provider}')>"
    
    @property
    def provider_display_name(self) -> str:
        """获取提供商的显示名称"""
        provider_names = {
            ModelServiceProvider.OPENAI: "OpenAI",
            ModelServiceProvider.CLAUDE: "Anthropic Claude",
            ModelServiceProvider.QWEN: "通义千问",
            ModelServiceProvider.DOUBAO: "豆包",
            ModelServiceProvider.GEMINI: "Google Gemini",
            ModelServiceProvider.OLLAMA: "Ollama",
            ModelServiceProvider.VLLM: "vLLM",
            ModelServiceProvider.CUSTOM: "自定义服务"
        }
        return provider_names.get(self.provider, self.provider)
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "provider": self.provider,
            "provider_display_name": self.provider_display_name,
            "model_type": self.model_type,
            "model_name": self.model_name,
            "api_endpoint": self.api_endpoint,
            "api_version": self.api_version,
            "max_tokens": self.max_tokens,
            "temperature": float(self.temperature) if self.temperature else None,
            "top_p": float(self.top_p) if self.top_p else None,
            "frequency_penalty": float(self.frequency_penalty) if self.frequency_penalty else None,
            "presence_penalty": float(self.presence_penalty) if self.presence_penalty else None,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "extra_config": self.extra_config,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def to_agent_option(self) -> dict:
        """转换为Agent配置选项格式"""
        return {
            "label": self.display_name,
            "value": self.name,
            "model_id": self.id,
            "description": self.description,
            "provider": self.provider,
            "provider_display_name": self.provider_display_name,
            "model_name": self.model_name
        }