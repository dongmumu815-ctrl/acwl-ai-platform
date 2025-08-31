#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent相关Schema定义
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.agent import AgentStatus, AgentType, ToolType
from pydantic import BaseModel
from app.schemas.common import PaginatedResponse


# ============================================
# 基础Schema
# ============================================

class AgentBase(BaseModel):
    """Agent基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent名称")
    description: Optional[str] = Field(None, description="Agent描述")
    agent_type: AgentType = Field(AgentType.CUSTOM, description="Agent类型")
    status: AgentStatus = Field(AgentStatus.DRAFT, description="Agent状态")
    model_service_config_id: int = Field(..., gt=0, description="使用的模型服务配置ID")
    instruction_set_id: Optional[int] = Field(None, gt=0, description="关联的指令集ID")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    user_prompt_template: Optional[str] = Field(None, description="用户提示词模板")
    model_params: Optional[Dict[str, Any]] = Field(None, description="模型配置参数")
    tools: Optional[List[str]] = Field(None, description="可用工具列表")
    tool_config: Optional[Dict[str, Any]] = Field(None, description="工具配置参数")
    memory_enabled: bool = Field(False, description="是否启用记忆功能")
    memory_config: Optional[Dict[str, Any]] = Field(None, description="记忆配置参数")
    is_public: bool = Field(False, description="是否公开可用")
    allowed_users: Optional[List[int]] = Field(None, description="允许使用的用户ID列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class AgentCreate(AgentBase):
    """创建Agent Schema"""
    pass


class AgentUpdate(BaseModel):
    """更新Agent Schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Agent名称")
    description: Optional[str] = Field(None, description="Agent描述")
    agent_type: Optional[AgentType] = Field(None, description="Agent类型")
    status: Optional[AgentStatus] = Field(None, description="Agent状态")
    model_service_config_id: Optional[int] = Field(None, gt=0, description="使用的模型服务配置ID")
    instruction_set_id: Optional[int] = Field(None, gt=0, description="关联的指令集ID")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    user_prompt_template: Optional[str] = Field(None, description="用户提示词模板")
    model_params: Optional[Dict[str, Any]] = Field(None, description="模型配置参数")
    tools: Optional[List[str]] = Field(None, description="可用工具列表")
    tool_config: Optional[Dict[str, Any]] = Field(None, description="工具配置参数")
    memory_enabled: Optional[bool] = Field(None, description="是否启用记忆功能")
    memory_config: Optional[Dict[str, Any]] = Field(None, description="记忆配置参数")
    is_public: Optional[bool] = Field(None, description="是否公开可用")
    allowed_users: Optional[List[int]] = Field(None, description="允许使用的用户ID列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="额外元数据")


class AgentInDB(AgentBase):
    """数据库中的Agent Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    usage_count: int
    last_used_at: Optional[datetime]
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime


class AgentResponse(AgentInDB):
    """Agent响应Schema"""
    # 关联数据
    model_name: Optional[str] = Field(None, description="模型名称")
    creator_name: Optional[str] = Field(None, description="创建者名称")
    updater_name: Optional[str] = Field(None, description="更新者名称")


class AgentListItem(BaseModel):
    """Agent列表项Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str]
    agent_type: AgentType
    status: AgentStatus
    model_service_config_id: int
    model_name: Optional[str] = Field(None, description="模型名称")
    is_public: bool
    usage_count: int
    last_used_at: Optional[datetime]
    created_by: Optional[int]
    creator_name: Optional[str] = Field(None, description="创建者名称")
    created_at: datetime
    updated_at: datetime
    tags: Optional[List[str]]


class AgentListResponse(PaginatedResponse):
    """Agent列表响应Schema"""
    items: List[AgentListItem]


# ============================================
# 查询参数Schema
# ============================================

class AgentQueryParams(BaseModel):
    """Agent查询参数Schema"""
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词（名称或描述）")
    agent_type: Optional[AgentType] = Field(None, description="Agent类型")
    status: Optional[AgentStatus] = Field(None, description="Agent状态")
    model_service_config_id: Optional[int] = Field(None, description="模型服务配置ID")
    is_public: Optional[bool] = Field(None, description="是否公开")
    created_by: Optional[int] = Field(None, description="创建者ID")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    order_by: Optional[str] = Field("created_at", description="排序字段")
    order_desc: bool = Field(True, description="是否降序")


# ============================================
# Agent工具相关Schema
# ============================================

class AgentToolBase(BaseModel):
    """Agent工具基础Schema"""
    name: str = Field(..., min_length=1, max_length=100, description="工具名称")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="工具描述")
    tool_type: ToolType = Field(..., description="工具类型")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置参数Schema")
    default_config: Optional[Dict[str, Any]] = Field(None, description="默认配置")
    is_enabled: bool = Field(True, description="是否启用")
    is_builtin: bool = Field(False, description="是否内置工具")


class AgentToolCreate(AgentToolBase):
    """创建Agent工具Schema"""
    pass


class AgentToolUpdate(BaseModel):
    """更新Agent工具Schema"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="工具描述")
    tool_type: Optional[ToolType] = Field(None, description="工具类型")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="配置参数Schema")
    default_config: Optional[Dict[str, Any]] = Field(None, description="默认配置")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class AgentToolResponse(AgentToolBase):
    """Agent工具响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime


class AgentToolListResponse(PaginatedResponse):
    """Agent工具列表响应Schema"""
    items: List[AgentToolResponse]


# ============================================
# Agent会话相关Schema
# ============================================

class AgentConversationBase(BaseModel):
    """Agent会话基础Schema"""
    agent_id: int = Field(..., gt=0, description="Agent ID")
    session_id: str = Field(..., min_length=1, max_length=100, description="会话标识符")
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    context: Optional[Dict[str, Any]] = Field(None, description="会话上下文")


class AgentConversationCreate(AgentConversationBase):
    """创建Agent会话Schema"""
    pass


class AgentConversationUpdate(BaseModel):
    """更新Agent会话Schema"""
    title: Optional[str] = Field(None, max_length=200, description="会话标题")
    context: Optional[Dict[str, Any]] = Field(None, description="会话上下文")
    is_active: Optional[bool] = Field(None, description="是否活跃")


class AgentConversationResponse(AgentConversationBase):
    """Agent会话响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # 关联数据
    agent_name: Optional[str] = Field(None, description="Agent名称")
    user_name: Optional[str] = Field(None, description="用户名称")
    message_count: Optional[int] = Field(None, description="消息数量")


class AgentConversationListResponse(PaginatedResponse):
    """Agent会话列表响应Schema"""
    items: List[AgentConversationResponse]


# ============================================
# Agent消息相关Schema
# ============================================

class AgentMessageBase(BaseModel):
    """Agent消息基础Schema"""
    role: str = Field(..., description="消息角色（user/assistant/system）")
    content: str = Field(..., description="消息内容")
    content_type: str = Field("text", description="内容类型（text/image/file等）")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="消息元数据")


class AgentMessageCreate(AgentMessageBase):
    """创建Agent消息Schema"""
    conversation_id: int = Field(..., gt=0, description="会话ID")


class AgentMessageResponse(AgentMessageBase):
    """Agent消息响应Schema"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    conversation_id: int
    tokens_used: Optional[int]
    processing_time: Optional[float]
    created_at: datetime


class AgentMessageListResponse(PaginatedResponse):
    """Agent消息列表响应Schema"""
    items: List[AgentMessageResponse]


# ============================================
# Agent聊天相关Schema
# ============================================

class AgentChatRequest(BaseModel):
    """Agent聊天请求Schema"""
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID，如果不提供则创建新会话")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")
    images: Optional[List[str]] = Field(None, description="图片数据列表（Base64编码）")
    stream: bool = Field(False, description="是否流式响应")


class AgentChatResponse(BaseModel):
    """Agent聊天响应Schema"""
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="Agent回复")
    tokens_used: Optional[int] = Field(None, description="使用的token数量")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="智能体元数据")


# ============================================
# Agent统计相关Schema
# ============================================

class AgentStatsResponse(BaseModel):
    """Agent统计响应Schema"""
    total_agents: int = Field(..., description="总Agent数量")
    active_agents: int = Field(..., description="活跃Agent数量")
    total_conversations: int = Field(..., description="总会话数量")
    total_messages: int = Field(..., description="总消息数量")
    popular_agents: List[AgentListItem] = Field(..., description="热门Agent列表")
    recent_conversations: List[AgentConversationResponse] = Field(..., description="最近会话列表")


# ============================================
# Agent配置相关Schema
# ============================================

class ModelConfigSchema(BaseModel):
    """模型配置Schema"""
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, le=8192, description="最大token数")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p参数")
    top_k: Optional[int] = Field(None, ge=1, description="Top-k参数")
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="频率惩罚")
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="存在惩罚")
    stop_sequences: Optional[List[str]] = Field(None, description="停止序列")


class MemoryConfigSchema(BaseModel):
    """记忆配置Schema"""
    max_history: Optional[int] = Field(None, ge=1, le=100, description="最大历史记录数")
    summary_threshold: Optional[int] = Field(None, ge=1, description="摘要阈值")
    enable_summary: Optional[bool] = Field(None, description="是否启用摘要")
    memory_type: Optional[str] = Field(None, description="记忆类型")


class AgentConfigValidationResponse(BaseModel):
    """Agent配置验证响应Schema"""
    is_valid: bool = Field(..., description="配置是否有效")
    errors: List[str] = Field(..., description="错误信息列表")
    warnings: List[str] = Field(..., description="警告信息列表")