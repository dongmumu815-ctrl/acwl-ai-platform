#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调任务相关数据模型
"""

from sqlalchemy import Integer, String, Text, Boolean, TIMESTAMP, JSON, Enum, ForeignKey, BigInteger, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, TYPE_CHECKING
from enum import Enum as PyEnum
from datetime import datetime

from app.core.database import Base, TimestampMixin, UserMixin

if TYPE_CHECKING:
    from .user import User
    from .model import Model


class FineTuningMethod(str, PyEnum):
    """微调方法枚举"""
    LORA = "lora"
    QLORA = "qlora"
    FULL = "full"
    ADAPTOR = "adaptor"


class FineTuningStatus(str, PyEnum):
    """微调任务状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FineTuningJob(Base, TimestampMixin, UserMixin):
    """微调任务表"""
    __tablename__ = "acwl_fine_tuning_jobs"
    __table_args__ = {"comment": "微调任务表，存储模型微调任务的配置和状态"}

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="微调任务ID，自增主键"
    )

    job_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="微调任务名称"
    )

    job_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="任务唯一标识符，用于SSH远程调用"
    )

    base_model_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="基础模型名称 (ModelScope ID，如 Qwen/Qwen2.5-0.5B-Instruct)"
    )

    model_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="模型类型 (如 qwen2, llama2)"
    )

    template: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="模板类型 (如 qwen2_5)"
    )

    fine_tuned_model_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="微调后的模型名称"
    )

    method: Mapped[FineTuningMethod] = mapped_column(
        Enum(FineTuningMethod, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        comment="微调方法：lora, qlora, full, adaptor"
    )

    status: Mapped[FineTuningStatus] = mapped_column(
        Enum(FineTuningStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=FineTuningStatus.PENDING,
        comment="任务状态"
    )

    dataset_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="训练数据集名称"
    )

    dataset_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="训练数据集路径"
    )

    system_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="系统提示词"
    )

    training_params: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="训练参数JSON字符串"
    )

    server_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("acwl_servers.id", ondelete="SET NULL"),
        nullable=True,
        comment="执行的GPU服务器ID"
    )

    server_ip: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="服务器IP地址"
    )

    ssh_port: Mapped[int] = mapped_column(
        Integer,
        default=22,
        comment="SSH端口"
    )

    ssh_username: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="SSH用户名"
    )

    ssh_password: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="SSH密码（加密存储）"
    )

    conda_env: Mapped[str] = mapped_column(
        String(100),
        default="msswift",
        comment="Conda环境名称"
    )

    log_file: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="训练日志文件路径"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )

    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="训练进度百分比(0-100)"
    )

    current_epoch: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="当前训练轮次"
    )

    total_epochs: Mapped[int] = mapped_column(
        Integer,
        default=3,
        comment="总训练轮次"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="训练开始时间"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP,
        nullable=True,
        comment="训练完成时间"
    )

    output_path: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="微调模型输出路径"
    )

    model_size: Mapped[Optional[BigInteger]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="微调后模型大小(字节)"
    )

    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="备注"
    )

    torch_dtype: Mapped[Optional[str]] = mapped_column(
        String(20),
        default="bfloat16",
        comment="数据类型 (bfloat16, float16, float32)"
    )

    max_length: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=1024,
        comment="最大序列长度"
    )

    split_dataset_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        default=0,
        comment="验证集拆分比例"
    )

    gradient_accumulation_steps: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=16,
        comment="梯度累积步数"
    )

    lora_rank: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=8,
        comment="LoRA rank"
    )

    lora_alpha: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=32,
        comment="LoRA alpha"
    )

    learning_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        default=1e-4,
        comment="学习率"
    )

    eval_steps: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=500,
        comment="评估步数"
    )

    use_chat_template: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="是否使用chat模板"
    )

    task_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="任务类型 (seq_cls 等)"
    )

    num_labels: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="标签数量 (用于分类任务)"
    )

    cuda_devices: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CUDA可见设备，如: 0,1,2,3"
    )

    model_status: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        default="stopped",
        comment="模型服务状态: stopped, running"
    )

    model_service_port: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=7860,
        comment="模型服务端口"
    )

    model_service_pid: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="模型服务进程PID"
    )

    def __repr__(self) -> str:
        return f"<FineTuningJob(id={self.id}, job_name='{self.job_name}', status='{self.status}')>"