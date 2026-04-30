#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调任务相关的Pydantic Schema
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

from app.models.fine_tuning import FineTuningMethod, FineTuningStatus


class FineTuningJobBase(BaseModel):
    """微调任务基础Schema"""
    job_name: str = Field(..., min_length=1, max_length=200, description="微调任务名称")
    base_model_name: str = Field(..., description="基础模型名称 (ModelScope ID，如 Qwen/Qwen2.5-0.5B-Instruct)")
    model_type: Optional[str] = Field(None, description="模型类型 (如 qwen2, llama2)")
    template: Optional[str] = Field(None, description="模板类型 (如 qwen2_5)")
    fine_tuned_model_name: Optional[str] = Field(None, max_length=200, description="微调后的模型名称")
    method: Literal["lora", "qlora", "full", "adaptor"] = Field(..., description="微调方法：lora, qlora, full, adaptor")
    dataset_name: str = Field(..., min_length=1, max_length=100, description="训练数据集名称")
    dataset_path: Optional[str] = Field(None, description="训练数据集路径")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    training_params: Optional[str] = Field(None, description="训练参数JSON字符串")
    server_id: Optional[int] = Field(None, description="执行的GPU服务器ID")
    server_ip: Optional[str] = Field(None, max_length=50, description="服务器IP地址")
    ssh_port: int = Field(22, description="SSH端口")
    ssh_username: Optional[str] = Field(None, max_length=100, description="SSH用户名")
    ssh_password: Optional[str] = Field(None, description="SSH密码（加密存储）")
    conda_env: str = Field("msswift", max_length=100, description="Conda环境名称")
    total_epochs: int = Field(3, ge=1, description="总训练轮次")
    output_path: Optional[str] = Field(None, description="微调模型输出路径")
    remarks: Optional[str] = Field(None, description="备注")
    torch_dtype: Optional[str] = Field("bfloat16", description="数据类型 (bfloat16, float16, float32)")
    max_length: Optional[int] = Field(1024, description="最大序列长度")
    split_dataset_ratio: Optional[float] = Field(0, ge=0, le=1, description="验证集拆分比例")
    gradient_accumulation_steps: Optional[int] = Field(16, description="梯度累积步数")
    learning_rate: Optional[float] = Field(1e-4, description="学习率")
    eval_steps: Optional[int] = Field(500, description="评估步数")
    lora_rank: Optional[int] = Field(8, description="LoRA rank")
    lora_alpha: Optional[int] = Field(32, description="LoRA alpha")
    use_chat_template: Optional[bool] = Field(True, description="是否使用chat模板")
    task_type: Optional[str] = Field(None, description="任务类型 (seq_cls 等)")
    num_labels: Optional[int] = Field(None, description="标签数量 (用于分类任务)")
    cuda_devices: Optional[str] = Field(None, description="CUDA可见设备，如: 0,1,2,3")
    model_status: Optional[str] = Field(None, description="模型服务状态: stopped, running")
    model_service_port: Optional[int] = Field(7860, description="模型服务端口")
    model_service_pid: Optional[int] = Field(None, description="模型服务进程PID")


class FineTuningJobCreate(FineTuningJobBase):
    """创建微调任务Schema"""
    ssh_password: Optional[str] = Field(None, description="SSH密码")


class FineTuningTrainingParams(BaseModel):
    """微调训练参数Schema"""
    lora_rank: int = Field(16, ge=1, description="LoRA rank")
    learning_rate: float = Field(1e-4, gt=0, description="学习率")
    batch_size: int = Field(16, ge=1, description="批次大小")
    num_train_epochs: int = Field(3, ge=1, description="训练轮次")
    fp16: bool = Field(True, description="是否使用FP16混合精度")
    gradient_accumulation_steps: int = Field(1, ge=1, description="梯度累积步数")
    max_grad_norm: float = Field(1.0, gt=0, description="梯度裁剪最大值")
    warmup_ratio: float = Field(0.1, ge=0, le=1, description="预热比例")
    weight_decay: float = Field(0.01, ge=0, description="权重衰减")
    logging_steps: int = Field(10, ge=1, description="日志打印步数")
    save_steps: int = Field(100, ge=1, description="模型保存步数")
    eval_steps: int = Field(100, ge=1, description="评估步数")
    save_total_limit: int = Field(2, ge=1, description="最多保存的模型 checkpoints 数量")


class FineTuningJobUpdate(BaseModel):
    """更新微调任务Schema"""
    job_name: Optional[str] = Field(None, min_length=1, max_length=200, description="微调任务名称")
    base_model_name: Optional[str] = Field(None, description="基础模型名称")
    model_type: Optional[str] = Field(None, description="模型类型")
    template: Optional[str] = Field(None, description="模板类型")
    fine_tuned_model_name: Optional[str] = Field(None, max_length=200, description="微调后的模型名称")
    method: Optional[Literal["lora", "qlora", "full", "adaptor"]] = Field(None, description="微调方法")
    dataset_name: Optional[str] = Field(None, min_length=1, max_length=100, description="训练数据集名称")
    dataset_path: Optional[str] = Field(None, description="训练数据集路径")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    training_params: Optional[str] = Field(None, description="训练参数JSON字符串")
    server_id: Optional[int] = Field(None, description="GPU服务器ID")
    server_ip: Optional[str] = Field(None, description="服务器IP地址")
    ssh_port: Optional[int] = Field(None, description="SSH端口")
    ssh_username: Optional[str] = Field(None, description="SSH用户名")
    ssh_password: Optional[str] = Field(None, description="SSH密码")
    conda_env: Optional[str] = Field(None, description="Conda环境名称")
    total_epochs: Optional[int] = Field(None, ge=1, description="总训练轮次")
    output_path: Optional[str] = Field(None, description="微调模型输出路径")
    remarks: Optional[str] = Field(None, description="备注")
    torch_dtype: Optional[str] = Field(None, description="数据类型")
    max_length: Optional[int] = Field(None, description="最大序列长度")
    split_dataset_ratio: Optional[float] = Field(None, ge=0, le=1, description="验证集拆分比例")
    gradient_accumulation_steps: Optional[int] = Field(None, description="梯度累积步数")
    learning_rate: Optional[float] = Field(None, description="学习率")
    eval_steps: Optional[int] = Field(None, description="评估步数")
    lora_rank: Optional[int] = Field(None, description="LoRA rank")
    lora_alpha: Optional[int] = Field(None, description="LoRA alpha")
    use_chat_template: Optional[bool] = Field(None, description="是否使用chat模板")
    task_type: Optional[str] = Field(None, description="任务类型")
    num_labels: Optional[int] = Field(None, description="标签数量")
    cuda_devices: Optional[str] = Field(None, description="CUDA可见设备")
    model_status: Optional[str] = Field(None, description="模型服务状态: stopped, running")
    model_service_port: Optional[int] = Field(None, description="模型服务端口")
    model_service_pid: Optional[int] = Field(None, description="模型服务进程PID")
    status: Optional[FineTuningStatus] = Field(None, description="任务状态")


class FineTuningJobInDB(FineTuningJobBase):
    """数据库中的微调任务Schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    status: FineTuningStatus
    progress: int = 0
    current_epoch: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    log_file: Optional[str] = None
    error_message: Optional[str] = None
    model_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None


class FineTuningJobResponse(FineTuningJobInDB):
    """微调任务响应Schema"""
    base_model_name: Optional[str] = Field(None, description="基础模型名称")
    base_model_version: Optional[str] = Field(None, description="基础模型版本")


class FineTuningJobListResponse(BaseModel):
    """微调任务列表响应Schema"""
    items: List[FineTuningJobResponse]
    total: int
    page: int
    size: int
    pages: int


class FineTuningJobSimpleResponse(BaseModel):
    """微调任务简化响应Schema"""
    id: int
    job_id: str
    job_name: str
    status: FineTuningStatus
    progress: int
    method: FineTuningMethod
    base_model_name: str
    created_at: datetime


class FineTuningJobStatusResponse(BaseModel):
    """微调任务状态响应Schema"""
    job_id: str
    status: FineTuningStatus
    progress: int
    current_epoch: Optional[int] = None
    total_epochs: int
    error_message: Optional[str] = None
    log_content: Optional[str] = Field(None, description="最新日志内容（最后N行）")


class FineTuningJobCancelRequest(BaseModel):
    """取消微调任务请求Schema"""
    job_id: str = Field(..., description="任务ID")


class FineTuningJobProgressUpdate(BaseModel):
    """微调任务进度更新Schema（内部使用）"""
    job_id: str
    progress: Optional[int] = None
    current_epoch: Optional[int] = None
    status: Optional[FineTuningStatus] = None
    log_line: Optional[str] = None
    error_message: Optional[str] = None


class FineTuningJobStartRequest(BaseModel):
    """启动微调任务请求Schema"""
    job_id: int = Field(..., description="微调任务数据库ID")


class FineTuningServerInfo(BaseModel):
    """微调任务服务器信息Schema"""
    server_id: int
    server_ip: str
    ssh_port: int
    ssh_username: str
    conda_env: str


class FineTuningStatsResponse(BaseModel):
    """微调任务统计响应Schema"""
    total_jobs: int
    pending_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    cancelled_jobs: int


class DatasetUploadRequest(BaseModel):
    """数据集上传请求Schema（用于从数据集管理选择已有数据集）"""
    server_ip: str = Field(..., description="目标服务器IP")
    ssh_port: int = Field(22, description="SSH端口")
    ssh_username: str = Field(..., description="SSH用户名")
    ssh_password: str = Field(..., description="SSH密码")
    dataset_id: int = Field(..., description="要上传的数据集ID")
    target_filename: Optional[str] = Field(None, description="目标文件名，不提供则使用原文件名")


class DatasetUploadResponse(BaseModel):
    """数据集上传响应Schema"""
    success: bool
    dataset_path: str = Field(..., description="数据集在服务器上的完整路径")
    filename: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")