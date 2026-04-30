#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调任务CRUD操作
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, desc, select
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid

from app.models.fine_tuning import FineTuningJob, FineTuningStatus, FineTuningMethod
from app.models.model import Model
from app.schemas.fine_tuning import FineTuningJobCreate, FineTuningJobUpdate
from app.core.security import encrypt_datasource_password, decrypt_datasource_password


def generate_job_id() -> str:
    """生成唯一的任务ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"ft_{timestamp}_{unique_id}"


def create_fine_tuning_job(
    db: Session,
    job_in: FineTuningJobCreate,
    creator_id: int
) -> FineTuningJob:
    """
    创建新的微调任务
    """
    db_job = FineTuningJob(
        job_name=job_in.job_name,
        job_id=generate_job_id(),
        base_model_name=job_in.base_model_name,
        model_type=job_in.model_type,
        template=job_in.template,
        fine_tuned_model_name=job_in.fine_tuned_model_name,
        method=FineTuningMethod(job_in.method) if isinstance(job_in.method, str) else job_in.method,
        dataset_name=job_in.dataset_name,
        dataset_path=job_in.dataset_path,
        training_params=job_in.training_params,
        server_id=job_in.server_id,
        server_ip=job_in.server_ip,
        ssh_port=job_in.ssh_port,
        ssh_username=job_in.ssh_username,
        ssh_password=job_in.ssh_password,
        conda_env=job_in.conda_env,
        total_epochs=job_in.total_epochs,
        output_path=job_in.output_path,
        remarks=job_in.remarks,
        torch_dtype=job_in.torch_dtype,
        max_length=job_in.max_length,
        gradient_accumulation_steps=job_in.gradient_accumulation_steps,
        learning_rate=job_in.learning_rate,
        eval_steps=job_in.eval_steps,
        use_chat_template=job_in.use_chat_template,
        task_type=job_in.task_type,
        num_labels=job_in.num_labels,
        cuda_devices=job_in.cuda_devices,
        status=FineTuningStatus.PENDING,
        created_by=creator_id
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


async def async_create_fine_tuning_job(
    db: AsyncSession,
    job_in: FineTuningJobCreate,
    creator_id: int
) -> FineTuningJob:
    """
    异步创建新的微调任务
    """
    ssh_password_encrypted = None
    if job_in.ssh_password:
        ssh_password_encrypted = encrypt_datasource_password(job_in.ssh_password)

    db_job = FineTuningJob(
        job_name=job_in.job_name,
        job_id=generate_job_id(),
        base_model_name=job_in.base_model_name,
        model_type=job_in.model_type,
        template=job_in.template,
        fine_tuned_model_name=job_in.fine_tuned_model_name,
        method=FineTuningMethod(job_in.method) if isinstance(job_in.method, str) else job_in.method,
        dataset_name=job_in.dataset_name,
        dataset_path=job_in.dataset_path,
        training_params=job_in.training_params,
        server_id=job_in.server_id,
        server_ip=job_in.server_ip,
        ssh_port=job_in.ssh_port,
        ssh_username=job_in.ssh_username,
        ssh_password=ssh_password_encrypted,
        conda_env=job_in.conda_env,
        total_epochs=job_in.total_epochs,
        output_path=job_in.output_path,
        remarks=job_in.remarks,
        torch_dtype=job_in.torch_dtype,
        max_length=job_in.max_length,
        gradient_accumulation_steps=job_in.gradient_accumulation_steps,
        learning_rate=job_in.learning_rate,
        eval_steps=job_in.eval_steps,
        use_chat_template=job_in.use_chat_template,
        task_type=job_in.task_type,
        num_labels=job_in.num_labels,
        cuda_devices=job_in.cuda_devices,
        status=FineTuningStatus.PENDING,
        created_by=creator_id
    )

    db.add(db_job)
    await db.commit()
    await db.refresh(db_job)
    return db_job


def get_fine_tuning_job(db: Session, job_id: int) -> Optional[FineTuningJob]:
    """
    根据ID获取微调任务
    """
    return db.query(FineTuningJob).filter(
        FineTuningJob.id == job_id
    ).first()


def get_fine_tuning_job_by_job_id(db: Session, job_id: str) -> Optional[FineTuningJob]:
    """
    根据job_id获取微调任务
    """
    return db.query(FineTuningJob).filter(
        FineTuningJob.job_id == job_id
    ).first()


async def async_get_fine_tuning_job(db: AsyncSession, job_id: int) -> Optional[FineTuningJob]:
    """
    异步根据ID获取微调任务
    """
    result = await db.execute(
        select(FineTuningJob).where(FineTuningJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def async_get_fine_tuning_job_by_job_id(db: AsyncSession, job_id: str) -> Optional[FineTuningJob]:
    """
    异步根据job_id获取微调任务
    """
    result = await db.execute(
        select(FineTuningJob).where(FineTuningJob.job_id == job_id)
    )
    return result.scalar_one_or_none()


def get_fine_tuning_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[FineTuningStatus] = None,
    method: Optional[FineTuningMethod] = None,
    base_model_name: Optional[str] = None,
    created_by: Optional[int] = None,
    search: Optional[str] = None
) -> Tuple[List[FineTuningJob], int]:
    """
    获取微调任务列表
    """
    query = db.query(FineTuningJob)

    filters = []
    if status:
        filters.append(FineTuningJob.status == status)
    if method:
        filters.append(FineTuningJob.method == method)
    if base_model_name:
        filters.append(FineTuningJob.base_model_name == base_model_name)
    if created_by:
        filters.append(FineTuningJob.created_by == created_by)
    if search:
        filters.append(
            or_(
                FineTuningJob.job_name.ilike(f"%{search}%"),
                FineTuningJob.job_id.ilike(f"%{search}%"),
                FineTuningJob.fine_tuned_model_name.ilike(f"%{search}%"),
                FineTuningJob.base_model_name.ilike(f"%{search}%")
            )
        )

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    jobs = query.order_by(desc(FineTuningJob.created_at)).offset(skip).limit(limit).all()

    return jobs, total


async def async_get_fine_tuning_jobs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    status: Optional[FineTuningStatus] = None,
    method: Optional[FineTuningMethod] = None,
    base_model_name: Optional[str] = None,
    created_by: Optional[int] = None,
    search: Optional[str] = None
) -> Tuple[List[FineTuningJob], int]:
    """
    异步获取微调任务列表
    """
    filters = []
    if status:
        filters.append(FineTuningJob.status == status)
    if method:
        filters.append(FineTuningJob.method == method)
    if base_model_name:
        filters.append(FineTuningJob.base_model_name == base_model_name)
    if created_by:
        filters.append(FineTuningJob.created_by == created_by)
    if search:
        filters.append(
            or_(
                FineTuningJob.job_name.ilike(f"%{search}%"),
                FineTuningJob.job_id.ilike(f"%{search}%"),
                FineTuningJob.fine_tuned_model_name.ilike(f"%{search}%"),
                FineTuningJob.base_model_name.ilike(f"%{search}%")
            )
        )

    query = select(FineTuningJob)
    count_query = select(func.count(FineTuningJob.id))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(desc(FineTuningJob.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return jobs, total


def update_fine_tuning_job(
    db: Session,
    job_id: int,
    job_in: FineTuningJobUpdate
) -> Optional[FineTuningJob]:
    """
    更新微调任务
    """
    job = db.query(FineTuningJob).filter(FineTuningJob.id == job_id).first()
    if not job:
        return None

    update_data = job_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


async def async_update_fine_tuning_job(
    db: AsyncSession,
    job_id: int,
    job_in: FineTuningJobUpdate
) -> Optional[FineTuningJob]:
    """
    异步更新微调任务
    """
    result = await db.execute(
        select(FineTuningJob).where(FineTuningJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return None

    update_data = job_in.model_dump(exclude_unset=True)

    if 'ssh_password' in update_data and update_data['ssh_password']:
        update_data['ssh_password'] = encrypt_datasource_password(update_data['ssh_password'])

    for field, value in update_data.items():
        setattr(job, field, value)

    await db.commit()
    await db.refresh(job)
    return job


def update_fine_tuning_job_status(
    db: Session,
    job_id: int,
    status: FineTuningStatus,
    error_message: Optional[str] = None,
    progress: Optional[int] = None,
    current_epoch: Optional[int] = None
) -> Optional[FineTuningJob]:
    """
    更新微调任务状态
    """
    job = db.query(FineTuningJob).filter(FineTuningJob.job_id == job_id).first()
    if not job:
        return None

    job.status = status
    if error_message is not None:
        job.error_message = error_message
    if progress is not None:
        job.progress = progress
    if current_epoch is not None:
        job.current_epoch = current_epoch

    if status == FineTuningStatus.RUNNING and job.started_at is None:
        job.started_at = datetime.now()
    elif status in [FineTuningStatus.COMPLETED, FineTuningStatus.FAILED, FineTuningStatus.CANCELLED]:
        job.completed_at = datetime.now()

    db.commit()
    db.refresh(job)
    return job


async def async_update_fine_tuning_job_status(
    db: AsyncSession,
    job_id: str,
    status: FineTuningStatus,
    error_message: Optional[str] = None,
    progress: Optional[int] = None,
    current_epoch: Optional[int] = None,
    log_file: Optional[str] = None,
    output_path: Optional[str] = None,
    model_size: Optional[int] = None
) -> Optional[FineTuningJob]:
    """
    异步更新微调任务状态
    """
    result = await db.execute(
        select(FineTuningJob).where(FineTuningJob.job_id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return None

    job.status = status
    if error_message is not None:
        job.error_message = error_message
    if progress is not None:
        job.progress = progress
    if current_epoch is not None:
        job.current_epoch = current_epoch
    if log_file is not None:
        job.log_file = log_file
    if output_path is not None:
        job.output_path = output_path
    if model_size is not None:
        job.model_size = model_size

    if status == FineTuningStatus.RUNNING and job.started_at is None:
        job.started_at = datetime.now()
    elif status in [FineTuningStatus.COMPLETED, FineTuningStatus.FAILED, FineTuningStatus.CANCELLED]:
        job.completed_at = datetime.now()

    await db.commit()
    await db.refresh(job)
    return job


def delete_fine_tuning_job(db: Session, job_id: int) -> bool:
    """
    删除微调任务
    """
    job = db.query(FineTuningJob).filter(FineTuningJob.id == job_id).first()
    if not job:
        return False

    if job.status == FineTuningStatus.RUNNING:
        return False

    db.delete(job)
    db.commit()
    return True


async def async_delete_fine_tuning_job(db: AsyncSession, job_id: int) -> bool:
    """
    异步删除微调任务
    """
    result = await db.execute(
        select(FineTuningJob).where(FineTuningJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        return False

    if job.status == FineTuningStatus.RUNNING:
        return False

    await db.delete(job)
    await db.commit()
    return True


def get_fine_tuning_stats(db: Session) -> Dict[str, int]:
    """
    获取微调任务统计
    """
    total = db.query(func.count(FineTuningJob.id)).scalar()
    pending = db.query(func.count(FineTuningJob.id)).filter(
        FineTuningJob.status == FineTuningStatus.PENDING
    ).scalar()
    running = db.query(func.count(FineTuningJob.id)).filter(
        FineTuningJob.status == FineTuningStatus.RUNNING
    ).scalar()
    completed = db.query(func.count(FineTuningJob.id)).filter(
        FineTuningJob.status == FineTuningStatus.COMPLETED
    ).scalar()
    failed = db.query(func.count(FineTuningJob.id)).filter(
        FineTuningJob.status == FineTuningStatus.FAILED
    ).scalar()
    cancelled = db.query(func.count(FineTuningJob.id)).filter(
        FineTuningJob.status == FineTuningStatus.CANCELLED
    ).scalar()

    return {
        "total_jobs": total,
        "pending_jobs": pending,
        "running_jobs": running,
        "completed_jobs": completed,
        "failed_jobs": failed,
        "cancelled_jobs": cancelled
    }


async def async_get_fine_tuning_stats(db: AsyncSession) -> Dict[str, int]:
    """
    异步获取微调任务统计
    """
    total_result = await db.execute(select(func.count(FineTuningJob.id)))
    total = total_result.scalar()

    pending_result = await db.execute(
        select(func.count(FineTuningJob.id)).where(FineTuningJob.status == FineTuningStatus.PENDING)
    )
    pending = pending_result.scalar()

    running_result = await db.execute(
        select(func.count(FineTuningJob.id)).where(FineTuningJob.status == FineTuningStatus.RUNNING)
    )
    running = running_result.scalar()

    completed_result = await db.execute(
        select(func.count(FineTuningJob.id)).where(FineTuningJob.status == FineTuningStatus.COMPLETED)
    )
    completed = completed_result.scalar()

    failed_result = await db.execute(
        select(func.count(FineTuningJob.id)).where(FineTuningJob.status == FineTuningStatus.FAILED)
    )
    failed = failed_result.scalar()

    cancelled_result = await db.execute(
        select(func.count(FineTuningJob.id)).where(FineTuningJob.status == FineTuningStatus.CANCELLED)
    )
    cancelled = cancelled_result.scalar()

    return {
        "total_jobs": total,
        "pending_jobs": pending,
        "running_jobs": running,
        "completed_jobs": completed,
        "failed_jobs": failed,
        "cancelled_jobs": cancelled
    }