#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent模型定义
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
from enum import Enum

from app.core.database import Base


class AgentStatus(str, Enum):
    """Agent状态枚举"""
    ACTIVE = "ACTIVE"          # 激活
    INACTIVE = "INACTIVE"      # 未激活
    DRAFT = "DRAFT"            # 草稿
    ARCHIVED = "ARCHIVED"      # 已归档


class AgentType(str, Enum):
    """Agent类型枚举"""
    CHAT = "CHAT"              # 聊天助手
    CODE = "CODE"              # 代码助手
    DOCUMENT = "DOCUMENT"      # 文档助手
    ANALYSIS = "ANALYSIS"      # 分析助手
    WORKFLOW = "WORKFLOW"      # 工作流助手
    REVIEW = "REVIEW"          # 审读助手
    CUSTOM = "CUSTOM"          # 自定义


class ToolType(str, Enum):
    """工具类型枚举"""
    CODE_EXECUTOR = "code_executor"                    # 代码执行器
    SYNTAX_CHECKER = "syntax_checker"                  # 语法检查器
    DOCUMENTATION_GENERATOR = "documentation_generator" # 文档生成器
    DOCUMENT_PARSER = "document_parser"                # 文档解析器
    SUMMARIZER = "summarizer"                          # 摘要生成器
    KEYWORD_EXTRACTOR = "keyword_extractor"            # 关键词提取器
    LANGUAGE_DETECTOR = "language_detector"            # 语言检测器
    TRANSLATOR = "translator"                          # 翻译器
    GRAMMAR_CHECKER = "grammar_checker"                # 语法检查器
    WEB_SEARCH = "web_search"                          # 网络搜索
    FILE_READER = "file_reader"                        # 文件读取器
    DATABASE_QUERY = "database_query"                  # 数据库查询
    API_CALLER = "api_caller"                          # API调用器
    CUSTOM = "custom"                                  # 自定义工具


class Agent(Base):
    """Agent模型"""
    __tablename__ = "acwl_agents"
    __table_args__ = {"comment": "AI Agent表，存储智能代理的配置和信息"}

    # 基本信息
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Agent ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Agent名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Agent描述"
    )
    
    agent_type: Mapped[AgentType] = mapped_column(
        SQLEnum(AgentType),
        nullable=False,
        default=AgentType.CUSTOM,
        comment="Agent类型"
    )
    
    status: Mapped[AgentStatus] = mapped_column(
        SQLEnum(AgentStatus),
        nullable=False,
        default=AgentStatus.DRAFT,
        comment="Agent状态"
    )
    
    # 模型服务配置
    model_service_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_model_service_configs.id"),
        nullable=False,
        comment="使用的模型服务配置ID"
    )
    
    instruction_set_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("instruction_sets.id"),
        nullable=True,
        comment="关联的指令集ID"
    )
    
    # 提示词配置
    system_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="系统提示词"
    )
    
    user_prompt_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="用户提示词模板"
    )
    
    # 模型参数配置
    model_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="模型配置参数（temperature、max_tokens等）"
    )
    
    # 工具配置
    tools: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="可用工具列表"
    )
    
    tool_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="工具配置参数"
    )
    
    # 高级配置
    memory_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否启用记忆功能"
    )
    
    memory_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="记忆配置参数"
    )
    
    # 权限和访问控制
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否公开可用"
    )
    
    allowed_users: Mapped[Optional[List[int]]] = mapped_column(
        JSON,
        nullable=True,
        comment="允许使用的用户ID列表"
    )
    
    # 使用统计
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="使用次数"
    )
    
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="最后使用时间"
    )
    
    # 元数据
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签列表"
    )
    
    meta_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="额外元数据"
    )
    
    # 审计字段
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=True,
        comment="创建者ID"
    )
    
    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=True,
        comment="最后更新者ID"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )
    
    # 关联关系
    model_service_config: Mapped["ModelServiceConfig"] = relationship(
        "ModelServiceConfig",
        foreign_keys=[model_service_config_id],
        lazy="select"
    )
    
    instruction_set: Mapped[Optional["InstructionSet"]] = relationship(
        "InstructionSet",
        foreign_keys=[instruction_set_id],
        lazy="select"
    )
    
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="select"
    )
    
    updater: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[updated_by],
        lazy="select"
    )
    
    # Agent会话关联
    conversations: Mapped[List["AgentConversation"]] = relationship(
        "AgentConversation",
        back_populates="agent",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name='{self.name}', type='{self.agent_type}', status='{self.status}')>"


class AgentConversation(Base):
    """Agent会话模型"""
    __tablename__ = "acwl_agent_conversations"
    __table_args__ = {"comment": "Agent会话表，存储用户与Agent的对话记录"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="会话ID，自增主键"
    )
    
    agent_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_agents.id"),
        nullable=False,
        comment="Agent ID"
    )
    
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=False,
        comment="用户ID"
    )
    
    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="会话标识符"
    )
    
    title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="会话标题"
    )
    
    context: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="会话上下文"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否活跃"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )
    
    # 关联关系
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="conversations"
    )
    
    user: Mapped["User"] = relationship(
        "User",
        lazy="select"
    )
    
    messages: Mapped[List["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<AgentConversation(id={self.id}, agent_id={self.agent_id}, user_id={self.user_id})>"


class AgentMessage(Base):
    """Agent消息模型"""
    __tablename__ = "acwl_agent_messages"
    __table_args__ = {"comment": "Agent消息表，存储对话中的具体消息"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="消息ID，自增主键"
    )
    
    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_agent_conversations.id"),
        nullable=False,
        comment="会话ID"
    )
    
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="消息角色（user/assistant/system）"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容"
    )
    
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
        comment="内容类型（text/image/file等）"
    )
    
    meta_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="消息元数据"
    )
    
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="使用的token数量"
    )
    
    processing_time: Mapped[Optional[float]] = mapped_column(
        nullable=True,
        comment="处理时间（秒）"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    
    # 关联关系
    conversation: Mapped["AgentConversation"] = relationship(
        "AgentConversation",
        back_populates="messages"
    )
    
    def __repr__(self) -> str:
        return f"<AgentMessage(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"


class AgentTool(Base):
    """Agent工具模型"""
    __tablename__ = "acwl_agent_tools"
    __table_args__ = {"comment": "Agent工具表，存储可用的工具定义"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="工具ID，自增主键"
    )
    
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="工具名称"
    )
    
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="工具描述"
    )
    
    tool_type: Mapped[ToolType] = mapped_column(
        SQLEnum(ToolType),
        nullable=False,
        comment="工具类型"
    )
    
    config_schema: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="配置参数Schema"
    )
    
    default_config: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="默认配置"
    )
    
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否启用"
    )
    
    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否内置工具"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        comment="创建时间"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        comment="更新时间"
    )
    
    def __repr__(self) -> str:
        return f"<AgentTool(id={self.id}, name='{self.name}', type='{self.tool_type}')>"