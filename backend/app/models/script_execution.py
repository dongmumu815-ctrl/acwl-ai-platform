#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本执行记录数据模型
"""

from sqlalchemy import Integer, String, Boolean, Text, Enum as SQLEnum, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from typing import List, Optional

from app.core.database import Base, TimestampMixin

class ScriptExecutionStatus(str, Enum):
    """脚本执行状态枚举"""
    pending = "pending"        # 等待执行
    running = "running"        # 执行中
    completed = "completed"    # 执行完成（全部成功）
    partial_failed = "partial_failed" # 部分失败
    failed = "failed"          # 执行失败（全部失败）

class ScriptDetailStatus(str, Enum):
    """单台服务器脚本执行状态枚举"""
    pending = "pending"    # 等待执行
    running = "running"    # 执行中
    success = "success"    # 执行成功
    failed = "failed"      # 执行失败
    timeout = "timeout"    # 执行超时

class ScriptExecutionRecord(Base, TimestampMixin):
    """脚本执行记录主表"""
    
    __tablename__ = "acwl_script_execution_records"
    __table_args__ = {"comment": "脚本批量执行记录主表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="记录ID"
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="执行标题/脚本名称"
    )
    
    script_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="脚本内容"
    )
    
    executor_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_users.id"),
        nullable=False,
        comment="执行人ID"
    )
    
    status: Mapped[ScriptExecutionStatus] = mapped_column(
        SQLEnum(ScriptExecutionStatus),
        default=ScriptExecutionStatus.pending,
        nullable=False,
        comment="总体执行状态"
    )
    
    total_servers: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="目标服务器总数"
    )
    
    success_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="成功数量"
    )
    
    fail_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="失败数量"
    )
    
    # 关联
    details: Mapped[List["ScriptExecutionDetail"]] = relationship(
        "ScriptExecutionDetail",
        back_populates="record",
        cascade="all, delete-orphan"
    )

class ScriptExecutionDetail(Base, TimestampMixin):
    """脚本执行详情表（每台服务器的执行情况）"""
    
    __tablename__ = "acwl_script_execution_details"
    __table_args__ = {"comment": "脚本执行详情表"}
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="详情ID"
    )
    
    record_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_script_execution_records.id"),
        nullable=False,
        comment="关联的主记录ID"
    )
    
    server_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("acwl_servers.id"),
        nullable=False,
        comment="目标服务器ID"
    )
    
    server_name: Mapped[str] = mapped_column(
        String(100),
        comment="服务器名称快照"
    )
    
    server_ip: Mapped[str] = mapped_column(
        String(45),
        comment="服务器IP快照"
    )
    
    status: Mapped[ScriptDetailStatus] = mapped_column(
        SQLEnum(ScriptDetailStatus),
        default=ScriptDetailStatus.pending,
        nullable=False,
        comment="执行状态"
    )
    
    exit_code: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="脚本退出码"
    )
    
    stdout: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="标准输出"
    )
    
    stderr: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="标准错误"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="系统错误信息（如SSH连接失败）"
    )
    
    start_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="开始执行时间"
    )
    
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        comment="结束执行时间"
    )
    
    # 关联
    record: Mapped["ScriptExecutionRecord"] = relationship(
        "ScriptExecutionRecord",
        back_populates="details"
    )
