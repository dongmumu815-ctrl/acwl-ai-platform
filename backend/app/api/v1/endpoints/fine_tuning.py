#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微调任务管理API端点
"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from typing import List, Optional
import asyncio
import paramiko
from datetime import datetime

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError, FineTuningError
from app.core.logger import logger
from app.core.security import decrypt_datasource_password
from app.models.user import User
from app.models.fine_tuning import FineTuningJob, FineTuningStatus, FineTuningMethod
from app.schemas.fine_tuning import (
    FineTuningJobCreate,
    FineTuningJobUpdate,
    FineTuningJobResponse,
    FineTuningJobListResponse,
    FineTuningJobStatusResponse,
    FineTuningStatsResponse,
    FineTuningJobStartRequest,
    DatasetUploadRequest,
    DatasetUploadResponse,
)
from app.crud.fine_tuning import (
    create_fine_tuning_job,
    async_create_fine_tuning_job,
    get_fine_tuning_job,
    async_get_fine_tuning_job,
    get_fine_tuning_job_by_job_id,
    async_get_fine_tuning_job_by_job_id,
    get_fine_tuning_jobs,
    async_get_fine_tuning_jobs,
    update_fine_tuning_job,
    async_update_fine_tuning_job,
    update_fine_tuning_job_status,
    async_update_fine_tuning_job_status,
    delete_fine_tuning_job,
    async_delete_fine_tuning_job,
    get_fine_tuning_stats,
    async_get_fine_tuning_stats,
)
from app.api.v1.endpoints.auth import get_current_active_user
from sqlalchemy import select

router = APIRouter()


def get_decrypted_password(encrypted_password: str | None) -> str:
    """解密密码"""
    if not encrypted_password:
        return ""
    return decrypt_datasource_password(encrypted_password)


def job_to_response(job: FineTuningJob) -> FineTuningJobResponse:
    """将数据库模型转换为响应模型"""
    ssh_password_decrypted = None
    if job.ssh_password:
        ssh_password_decrypted = decrypt_datasource_password(job.ssh_password)

    return FineTuningJobResponse(
        id=job.id,
        job_id=job.job_id,
        job_name=job.job_name,
        base_model_name=job.base_model_name,
        model_type=job.model_type,
        template=job.template,
        fine_tuned_model_name=job.fine_tuned_model_name,
        method=job.method,
        status=job.status,
        dataset_name=job.dataset_name,
        dataset_path=job.dataset_path,
        training_params=job.training_params,
        server_id=job.server_id,
        server_ip=job.server_ip,
        ssh_port=job.ssh_port,
        ssh_username=job.ssh_username,
        ssh_password=ssh_password_decrypted,
        conda_env=job.conda_env,
        log_file=job.log_file,
        error_message=job.error_message,
        progress=job.progress,
        current_epoch=job.current_epoch,
        total_epochs=job.total_epochs,
        started_at=job.started_at,
        completed_at=job.completed_at,
        output_path=job.output_path,
        model_size=job.model_size,
        remarks=job.remarks,
        torch_dtype=job.torch_dtype,
        max_length=job.max_length,
        gradient_accumulation_steps=job.gradient_accumulation_steps,
        learning_rate=job.learning_rate,
        eval_steps=job.eval_steps,
        use_chat_template=job.use_chat_template,
        task_type=job.task_type,
        num_labels=job.num_labels,
        cuda_devices=job.cuda_devices,
        split_dataset_ratio=job.split_dataset_ratio,
        lora_rank=job.lora_rank,
        lora_alpha=job.lora_alpha,
        model_status=job.model_status,
        model_service_port=job.model_service_port,
        model_service_pid=job.model_service_pid,
        created_at=job.created_at,
        updated_at=job.updated_at,
        created_by=job.created_by,
    )


@router.get("/stats", summary="获取微调任务统计")
async def get_fine_tuning_stats_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微调任务统计数据"""
    stats = await async_get_fine_tuning_stats(db)
    return FineTuningStatsResponse(**stats)


@router.post("/upload-dataset", summary="上传数据集到远程训练服务器")
async def upload_dataset_to_server(
    request: DatasetUploadRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    将数据集管理中的数据集上传到远程训练服务器
    """
    from app.services.minio_service import MinIOService
    from app.models.dataset import Dataset
    from sqlalchemy import select

    result = await db.execute(
        select(Dataset).where(
            Dataset.id == request.dataset_id,
            Dataset.created_by == current_user.id
        )
    )
    dataset = result.scalar_one_or_none()

    if not dataset:
        raise NotFoundError(f"数据集 {request.dataset_id} 不存在")

    if not dataset.storage_path:
        raise ValidationError("该数据集没有关联的文件")

    remote_base_path = "/data/modelscope/ms-swift/dataset"
    filename = request.target_filename or f"dataset_{dataset.id}_{dataset.name}"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=request.server_ip,
            port=request.ssh_port,
            username=request.ssh_username,
            password=request.ssh_password,
            timeout=30
        )

        sftp = client.open_sftp()

        remote_dir = remote_base_path
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            sftp.mkdir(remote_dir)

        remote_path = f"{remote_dir}/{filename}"

        if dataset.storage_path.startswith("minio://"):
            minio_service = MinIOService()
            path_parts = dataset.storage_path.replace("minio://", "").split("/", 1)
            if len(path_parts) < 2:
                raise ValidationError("MinIO路径格式错误")

            prefix = path_parts[1]
            objects = minio_service.client.list_objects(minio_service.bucket_name, prefix=prefix, recursive=True)
            files = list(objects)

            if not files:
                raise ValidationError("数据集中没有找到文件")

            for obj in files:
                response = minio_service.client.get_object(minio_service.bucket_name, obj.object_name)
                file_data = response.read()
                response.close()

                fname = obj.object_name.split("/")[-1]
                file_remote_path = f"{remote_dir}/{fname}"

                with sftp.file(file_remote_path, "wb") as f:
                    f.write(file_data)

                file_size = len(file_data)

            sftp.close()
            client.close()

            return DatasetUploadResponse(
                success=True,
                dataset_path=f"{remote_dir}/{files[0].object_name.split('/')[-1]}",
                filename=files[0].object_name.split("/")[-1],
                file_size=file_size
            )

        else:
            with open(dataset.storage_path, "rb") as f:
                file_data = f.read()

            with sftp.file(remote_path, "wb") as f:
                f.write(file_data)

            sftp.close()
            client.close()

            return DatasetUploadResponse(
                success=True,
                dataset_path=remote_path,
                filename=filename,
                file_size=len(file_data)
            )

    except Exception as e:
        logger.error(f"上传数据集到远程服务器失败: {e}")
        raise FineTuningError(f"上传失败: {str(e)}")


@router.post("/upload-dataset-file", summary="上传本地数据集文件到远程训练服务器")
async def upload_dataset_file_to_server(
    file: UploadFile = File(...),
    server_ip: str = Form(...),
    ssh_port: int = Form(22),
    ssh_username: str = Form(...),
    ssh_password: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    将本地上传的数据集文件上传到远程训练服务器
    """
    remote_base_path = "/data/modelscope/ms-swift/dataset"
    filename = file.filename or "uploaded_dataset.jsonl"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=server_ip,
            port=ssh_port,
            username=ssh_username,
            password=ssh_password,
            timeout=30
        )

        sftp = client.open_sftp()

        remote_dir = remote_base_path
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            sftp.mkdir(remote_dir)

        remote_path = f"{remote_dir}/{filename}"

        file_data = await file.read()

        with sftp.file(remote_path, "wb") as f:
            f.write(file_data)

        sftp.close()
        client.close()

        return {
            "success": True,
            "dataset_path": remote_path,
            "filename": filename,
            "file_size": len(file_data)
        }

    except Exception as e:
        logger.error(f"上传本地数据集文件到远程服务器失败: {e}")
        raise FineTuningError(f"上传失败: {str(e)}")


@router.get("/", summary="获取微调任务列表")
async def get_fine_tuning_jobs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[FineTuningStatus] = Query(None, description="任务状态"),
    method: Optional[str] = Query(None, description="微调方法"),
    base_model_name: Optional[str] = Query(None, description="基础模型名称"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微调任务列表"""
    skip = (page - 1) * size
    method_enum = FineTuningMethod(method) if method else None
    jobs, total = await async_get_fine_tuning_jobs(
        db,
        skip=skip,
        limit=size,
        status=status,
        method=method_enum,
        base_model_name=base_model_name,
        search=search
    )

    if status is None or status == FineTuningStatus.RUNNING:
        for job in jobs:
            if job.status == FineTuningStatus.RUNNING and job.log_file:
                try:
                    asyncio.create_task(update_single_job_progress(job.job_id))
                except RuntimeError:
                    asyncio.get_event_loop().run_in_executor(None, update_single_job_progress_sync, job.job_id)

    items = [job_to_response(job) for job in jobs]
    pages = (total + size - 1) // size if total > 0 else 0

    return FineTuningJobListResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


async def update_single_job_progress(job_id: str):
    """异步更新单个任务进度"""
    import paramiko
    import re
    from app.core.database import AsyncSessionLocal
    from app.models.fine_tuning import FineTuningStatus
    from app.crud.fine_tuning import async_get_fine_tuning_job_by_job_id, async_update_fine_tuning_job_status

    logger.info(f"[ASYNC] Updating progress for job_id: {job_id}")

    async with AsyncSessionLocal() as db:
        job = await async_get_fine_tuning_job_by_job_id(db, job_id)
        if not job:
            logger.warning(f"[ASYNC] Job not found: {job_id}")
            return

        if job.status != FineTuningStatus.RUNNING:
            return

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            password = get_decrypted_password(job.ssh_password)
            client.connect(
                hostname=job.server_ip,
                port=job.ssh_port,
                username=job.ssh_username,
                password=password,
                timeout=30
            )
            sftp = client.open_sftp()

            epoch_info = None
            log_content = ""
            swift_output_path = None

            if job.output_path:
                logging_file = f"{job.output_path}/logging.jsonl"
                try:
                    with sftp.file(logging_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            log_content += f"logging.jsonl: {last_line}\n"
                            epoch_info = parse_epoch_from_log([last_line])
                except IOError:
                    pass

            try:
                with sftp.file(job.log_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        for line in lines:
                            log_content += f"log_file: {line.strip()}\n"

                        if not swift_output_path:
                            match = re.search(r"\[INFO:swift\]\s*output_dir:\s*(.+)", "".join(lines))
                            if match:
                                swift_output_path = match.group(1).strip()
            except IOError:
                pass

            if swift_output_path and not epoch_info:
                logging_file = f"{swift_output_path}/logging.jsonl"
                try:
                    with sftp.file(logging_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            epoch_info = parse_epoch_from_log([last_line])
                except IOError:
                    pass

            sftp.close()
            client.close()

            if epoch_info:
                current_epoch = epoch_info.get("current_epoch", 1)
                progress = epoch_info.get("progress", 0)
                await async_update_fine_tuning_job_status(
                    db, job_id, FineTuningStatus.RUNNING,
                    progress=progress,
                    current_epoch=current_epoch,
                    output_path=swift_output_path
                )
                logger.info(f"[ASYNC] Updated job {job_id}: progress={progress}, epoch={current_epoch}")

            if "train_runtime" in log_content or "train_samples_per_second" in log_content:
                await async_update_fine_tuning_job_status(
                    db, job_id, FineTuningStatus.COMPLETED, progress=100,
                    current_epoch=job.total_epochs
                )
                logger.info(f"[ASYNC] Job {job_id} completed")

            if "ERROR" in log_content or "Traceback" in log_content:
                await async_update_fine_tuning_job_status(
                    db, job_id, FineTuningStatus.FAILED, error_message="训练出错"
                )
                logger.info(f"[ASYNC] Job {job_id} failed")

        except Exception as e:
            logger.warning(f"[ASYNC] Failed to update job {job_id}: {e}")


def update_single_job_progress_sync(job_id: str):
    """同步更新单个任务进度"""
    import paramiko
    import re
    from app.core.database import SessionLocal
    from app.models.fine_tuning import FineTuningJob, FineTuningStatus

    logger.info(f"[SYNC] Updating progress for job_id: {job_id}")

    with SessionLocal() as db:
        job = db.query(FineTuningJob).filter(FineTuningJob.job_id == job_id).first()
        if not job:
            logger.warning(f"[SYNC] Job not found: {job_id}")
            return

        if job.status != FineTuningStatus.RUNNING:
            return

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            password = get_decrypted_password(job.ssh_password)
            client.connect(
                hostname=job.server_ip,
                port=job.ssh_port,
                username=job.ssh_username,
                password=password,
                timeout=30
            )
            sftp = client.open_sftp()

            epoch_info = None
            log_content = ""
            swift_output_path = None

            if job.output_path:
                logging_file = f"{job.output_path}/logging.jsonl"
                try:
                    with sftp.file(logging_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            log_content += f"logging.jsonl: {last_line}\n"
                            epoch_info = parse_epoch_from_log([last_line])
                except IOError:
                    pass

            try:
                with sftp.file(job.log_file, "r") as f:
                    lines = f.readlines()
                    if lines:
                        for line in lines:
                            log_content += f"log_file: {line.strip()}\n"

                        if not swift_output_path:
                            match = re.search(r"\[INFO:swift\]\s*output_dir:\s*(.+)", "".join(lines))
                            if match:
                                swift_output_path = match.group(1).strip()
            except IOError:
                pass

            if swift_output_path and not epoch_info:
                logging_file = f"{swift_output_path}/logging.jsonl"
                try:
                    with sftp.file(logging_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            last_line = lines[-1].strip()
                            epoch_info = parse_epoch_from_log([last_line])
                except IOError:
                    pass

            sftp.close()
            client.close()

            if epoch_info:
                current_epoch = epoch_info.get("current_epoch", 1)
                progress = epoch_info.get("progress", 0)
                job.progress = progress
                job.current_epoch = current_epoch
                if swift_output_path:
                    job.output_path = swift_output_path
                db.commit()
                logger.info(f"[SYNC] Updated job {job_id}: progress={progress}, epoch={current_epoch}")

            if "train_runtime" in log_content or "train_samples_per_second" in log_content:
                job.status = FineTuningStatus.COMPLETED
                job.progress = 100
                job.current_epoch = job.total_epochs
                job.completed_at = datetime.now()
                db.commit()
                logger.info(f"[SYNC] Job {job_id} completed")

            if "ERROR" in log_content or "Traceback" in log_content:
                job.status = FineTuningStatus.FAILED
                job.error_message = "训练出错"
                job.completed_at = datetime.now()
                db.commit()
                logger.info(f"[SYNC] Job {job_id} failed")

        except Exception as e:
            logger.warning(f"[SYNC] Failed to update job {job_id}: {e}")


@router.get("/{job_id}", summary="获取微调任务详情")
async def get_fine_tuning_job_endpoint(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取微调任务详情"""
    job = await async_get_fine_tuning_job(db, job_id)
    if not job:
        raise NotFoundError(f"微调任务 {job_id} 不存在")
    return job_to_response(job)


@router.post("/", summary="创建微调任务")
async def create_fine_tuning_job_endpoint(
    job_in: FineTuningJobCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建新的微调任务"""
    job = await async_create_fine_tuning_job(db, job_in, current_user.id)

    return {
        "id": job.id,
        "job_id": job.job_id,
        "message": "微调任务创建成功"
    }


@router.put("/{job_id}", summary="更新微调任务")
async def update_fine_tuning_job_endpoint(
    job_id: int,
    job_in: FineTuningJobUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新微调任务"""
    job = await async_update_fine_tuning_job(db, job_id, job_in)
    if not job:
        raise NotFoundError(f"微调任务 {job_id} 不存在")
    return job_to_response(job)


@router.delete("/{job_id}", summary="删除微调任务")
async def delete_fine_tuning_job_endpoint(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除微调任务"""
    success = await async_delete_fine_tuning_job(db, job_id)
    if not success:
        raise HTTPException(status_code=400, detail="无法删除运行中的任务或任务不存在")
    return {"message": "删除成功"}


@router.post("/start", summary="启动微调任务")
async def start_fine_tuning_job_endpoint(
    request: FineTuningJobStartRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """启动微调任务（异步执行）"""
    job = await async_get_fine_tuning_job(db, request.job_id)
    if not job:
        raise NotFoundError(f"微调任务 {request.job_id} 不存在")

    if job.status not in [FineTuningStatus.PENDING, FineTuningStatus.FAILED]:
        raise FineTuningError(f"任务状态为 {job.status}，无法启动")

    await async_update_fine_tuning_job_status(db, job.job_id, FineTuningStatus.QUEUED)

    background_tasks.add_task(run_fine_tuning_async, job.job_id, db, background_tasks)

    return {"message": "任务已加入队列", "job_id": job.job_id}


@router.get("/{job_id}/logs", summary="获取微调任务日志")
async def get_fine_tuning_job_logs_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微调任务日志"""
    job = await async_get_fine_tuning_job_by_job_id(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    log_content = None
    if job.log_file:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            password = get_decrypted_password(job.ssh_password)
            client.connect(
                hostname=job.server_ip,
                port=job.ssh_port,
                username=job.ssh_username,
                password=password,
                timeout=30
            )
            sftp = client.open_sftp()
            try:
                with sftp.file(job.log_file, "r") as f:
                    lines = f.readlines()
                    log_content = "".join(lines[-200:]) if len(lines) > 200 else "".join(lines)
            except IOError as e:
                log_content = f"无法读取日志: {str(e)}"
            finally:
                sftp.close()
                client.close()
        except Exception as e:
            logger.warning(f"读取日志文件失败: {e}")
            log_content = f"无法读取日志: {str(e)}"
    else:
        log_content = "日志文件尚未生成"

    return {"job_id": job.job_id, "log_content": log_content}


@router.get("/{job_id}/curves", summary="获取训练曲线数据")
async def get_fine_tuning_job_curves_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取训练曲线数据"""
    job = await async_get_fine_tuning_job_by_job_id(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    import json

    curves_data = {
        "loss": [],
        "acc": [],
        "token_acc": [],
        "learning_rate": [],
        "grad_norm": [],
        "epoch": []
    }

    output_path = job.output_path

    if not output_path and job.log_file:
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            password = get_decrypted_password(job.ssh_password)
            client.connect(
                hostname=job.server_ip,
                port=job.ssh_port,
                username=job.ssh_username,
                password=password,
                timeout=30
            )
            sftp = client.open_sftp()
            try:
                with sftp.file(job.log_file, "r") as f:
                    lines = f.readlines()
                    log_text = "".join(lines)
                    match = re.search(r"\[INFO:swift\]\s*output_dir:\s*(.+)", log_text)
                    if match:
                        output_path = match.group(1).strip()
            finally:
                sftp.close()
                client.close()
        except Exception as e:
            logger.warning(f"读取日志文件获取output_path失败: {e}")

    if output_path:
        logging_file = f"{output_path}/logging.jsonl"
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            password = get_decrypted_password(job.ssh_password)
            client.connect(
                hostname=job.server_ip,
                port=job.ssh_port,
                username=job.ssh_username,
                password=password,
                timeout=30
            )
            sftp = client.open_sftp()
            try:
                with sftp.file(logging_file, "r") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        try:
                            data = json.loads(line.strip())
                            step = data.get("global_step/max_steps", str(i))
                            if "/" in step:
                                step_num = int(step.split("/")[0])
                            else:
                                step_num = i + 1

                            if "loss" in data and data["loss"] is not None:
                                curves_data["loss"].append({"step": step_num, "value": float(data["loss"])})
                            if "acc" in data and data["acc"] is not None:
                                curves_data["acc"].append({"step": step_num, "value": float(data["acc"])})
                            if "token_acc" in data and data["token_acc"] is not None:
                                curves_data["token_acc"].append({"step": step_num, "value": float(data["token_acc"])})
                            if "learning_rate" in data and data["learning_rate"] is not None:
                                curves_data["learning_rate"].append({"step": step_num, "value": float(data["learning_rate"])})
                            if "grad_norm" in data and data["grad_norm"] is not None:
                                curves_data["grad_norm"].append({"step": step_num, "value": float(data["grad_norm"])})
                            if "epoch" in data and data["epoch"] is not None:
                                curves_data["epoch"].append({"step": step_num, "value": float(data["epoch"])})
                        except (json.JSONDecodeError, ValueError, KeyError):
                            continue
            except IOError as e:
                logger.warning(f"读取训练曲线文件失败: {e}")
            finally:
                sftp.close()
                client.close()
        except Exception as e:
            logger.warning(f"连接服务器获取训练曲线失败: {e}")

    return {"job_id": job.job_id, "curves": curves_data}


@router.get("/{job_id}/status", summary="获取微调任务状态")
async def get_fine_tuning_job_status_endpoint(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取微调任务状态和日志"""
    job = await async_get_fine_tuning_job_by_job_id(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    log_content = None
    if job.log_file:
        try:
            with open(job.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                log_content = "".join(lines[-100:]) if len(lines) > 100 else "".join(lines)
        except Exception as e:
            logger.warning(f"读取日志文件失败: {e}")
            log_content = f"无法读取日志: {str(e)}"

    return FineTuningJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        current_epoch=job.current_epoch,
        total_epochs=job.total_epochs,
        error_message=job.error_message,
        log_content=log_content
    )


@router.post("/{job_id}/cancel", summary="取消微调任务")
async def cancel_fine_tuning_job_endpoint(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """取消正在运行的微调任务"""
    job = await async_get_fine_tuning_job(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    if job.status == FineTuningStatus.RUNNING:
        try:
            await cancel_remote_training(job)
        except Exception as e:
            logger.error(f"取消远程训练失败: {e}")

    await async_update_fine_tuning_job_status(db, job.job_id, FineTuningStatus.CANCELLED)
    return {"message": "任务已取消"}


@router.post("/{job_id}/start-model", summary="启动微调模型服务")
async def start_model_service_endpoint(
    job_id: int,
    port: int = Form(8060, description="服务端口"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """启动微调后的模型服务"""
    job = await async_get_fine_tuning_job(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    if job.status != FineTuningStatus.COMPLETED:
        raise ValidationError("任务未完成，无法启动模型服务")

    if job.model_status == "running":
        return {"message": "模型服务已在运行", "model_status": "running", "port": job.model_service_port}

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        password = get_decrypted_password(job.ssh_password)
        client.connect(job.server_ip, job.ssh_port or 22, job.ssh_username, password)

        base_model = job.base_model_name
        output_path = job.output_path or f"/data/modelscope/output/{job.fine_tuned_model_name or job.job_name}"

        cuda_prefix = f"CUDA_VISIBLE_DEVICES={job.cuda_devices}" if job.cuda_devices else ""
        conda_path = "/data/softs/miniconda3/bin/activate"
        conda_env = job.conda_env or "msswift"

        log_dir = f"/data/modelscope/ms-swift/logs"
        log_file = f"{log_dir}/model_service_{job.job_id}.log"
        pid_file = f"/data/modelscope/ms-swift/logs/model_service_{job.job_id}.pid"

        target_port = port
        max_port_attempts = 10
        port_attempt = 0

        while port_attempt < max_port_attempts:
            check_port_cmd = f"lsof -i :{target_port} 2>/dev/null | grep -v COMMAND | wc -l"
            stdin_check, stdout_check, stderr_check = client.exec_command(check_port_cmd)
            port_in_use = int(stdout_check.read().decode().strip()) > 0

            if not port_in_use:
                port = target_port
                logger.info(f"[DEBUG] Found available port: {port}")
                break

            logger.warning(f"[DEBUG] Port {target_port} is in use, trying next port")
            target_port += 1
            port_attempt += 1
        else:
            raise FineTuningError(f"无法找到可用端口，已尝试 {max_port_attempts} 个端口")

        is_lora = job.method in ["lora", "qlora"]

        if is_lora:
            stdin, stdout, stderr = client.exec_command(f"ls -d {output_path}/checkpoint-* 2>/dev/null | sort -V | tail -1")
            checkpoint_path = stdout.read().decode().strip()
            if checkpoint_path:
                model_arg = f"--adapters {checkpoint_path}"
                logger.info(f"[DEBUG] LoRA adapter path: {checkpoint_path}")
            else:
                model_arg = f"--adapters {output_path}"
                logger.warning(f"[DEBUG] No checkpoint found, using output_path: {output_path}")
        else:
            model_arg = f"--model {output_path}"

        if cuda_prefix:
            command = f"cd {log_dir} && export {cuda_prefix} && source {conda_path} {conda_env} && nohup swift deploy {model_arg} --port {port} > {log_file} 2>&1 & echo $! > {pid_file}"
        else:
            command = f"cd {log_dir} && source {conda_path} {conda_env} && nohup swift deploy {model_arg} --port {port} > {log_file} 2>&1 & echo $! > {pid_file}"

        logger.info(f"[DEBUG] Starting model service with command: {command}")

        transport = client.get_transport()
        transport.set_keepalive(30)

        channel = transport.open_session()
        channel.exec_command(command)

        job.model_status = "running"
        job.model_service_port = port
        job.model_service_pid = None
        await db.commit()

        return {
            "message": "模型服务启动成功",
            "model_status": "running",
            "port": port,
            "log_file": log_file
        }
    except Exception as e:
        logger.error(f"启动模型服务失败: {str(e)}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise FineTuningError(f"启动模型服务失败: {str(e)}")


@router.post("/{job_id}/stop-model", summary="停止微调模型服务")
async def stop_model_service_endpoint(
    job_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """停止微调后的模型服务"""
    job = await async_get_fine_tuning_job(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    if job.model_status != "running":
        return {"message": "模型服务未运行", "model_status": job.model_status}

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        password = get_decrypted_password(job.ssh_password)
        client.connect(job.server_ip, job.ssh_port or 22, job.ssh_username, password)

        port = job.model_service_port or 8060
        pid_file = f"/data/modelscope/ms-swift/logs/model_service_{job.job_id}.pid"

        def check_and_kill():
            check_cmd = f"lsof -i :{port} 2>/dev/null | grep -v COMMAND | awk '{{print $2}}' | sort -u"
            stdin_c, stdout_c, stderr_c = client.exec_command(check_cmd)
            pids = stdout_c.read().decode().strip()
            if pids:
                kill_cmd = f"kill -9 {pids} 2>/dev/null || true"
                client.exec_command(kill_cmd)
                return True
            return False

        logger.info(f"[DEBUG] Stop command: killing processes on port {port}")
        still_running = check_and_kill()
        if still_running:
            import time
            time.sleep(1)
            still_running = check_and_kill()

        if still_running:
            logger.warning(f"[DEBUG] Failed to kill processes on port {port}")
        else:
            logger.info(f"[DEBUG] Successfully killed processes on port {port}")

        client.close()

        job.model_status = "stopped"
        job.model_service_pid = None
        await db.commit()

        return {"message": "模型服务已停止", "model_status": "stopped"}
    except Exception as e:
        logger.error(f"停止模型服务失败: {e}")
        raise FineTuningError(f"停止模型服务失败: {str(e)}")


class ModelChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


@router.post("/{job_id}/chat", summary="与微调模型对话")
async def chat_with_model_endpoint(
    job_id: int,
    request: ModelChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """与部署的微调模型进行对话"""
    import aiohttp

    job = await async_get_fine_tuning_job(db, job_id)
    if not job:
        raise NotFoundError(f"任务 {job_id} 不存在")

    if job.model_status != "running":
        raise ValidationError("模型服务未运行，请先启动模型服务")

    base_url = f"http://{job.server_ip}:{job.model_service_port}"

    try:
        async with aiohttp.ClientSession() as session:
            models_resp = await session.get(f"{base_url}/v1/models", timeout=aiohttp.ClientTimeout(total=10))
            if models_resp.status == 200:
                models_data = await models_resp.json()
                model_name = models_data.get("data", [{}])[0].get("id", job.base_model_name)
                logger.info(f"[DEBUG] 获取到模型名称: {model_name}")
            else:
                model_name = job.base_model_name
                logger.warning(f"[DEBUG] 获取模型列表失败，使用默认: {model_name}")
    except Exception as e:
        model_name = job.base_model_name
        logger.warning(f"[DEBUG] 获取模型列表异常: {e}，使用默认: {model_name}")

    endpoints = [
        f"{base_url}/v1/chat/completions",
    ]

    messages = []
    if request.system_prompt or job.system_prompt:
        messages.append({
            "role": "system",
            "content": request.system_prompt or job.system_prompt
        })
    messages.append({"role": "user", "content": request.message})

    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    logger.info(f"[DEBUG] Chat request payload: {payload}")

    last_error = None
    for url in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {
                            "response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                            "usage": result.get("usage", {}),
                            "model_status": "running"
                        }
                    else:
                        error_text = await resp.text()
                        last_error = f"状态码 {resp.status}: {error_text}"
                        logger.warning(f"[DEBUG] 尝试端点 {url} 失败: {last_error}")
                        continue
        except aiohttp.ClientError as e:
            last_error = str(e)
            logger.warning(f"[DEBUG] 尝试端点 {url} 失败: {last_error}")
            continue

    logger.error(f"[DEBUG] 所有端点尝试失败，最后错误: {last_error}")
    raise HTTPException(status_code=503, detail=f"模型服务响应错误: {last_error}")


async def run_fine_tuning_async(job_id: str, db: AsyncSession, background_tasks: BackgroundTasks):
    """异步执行微调任务的内部函数"""
    from app.core.database import AsyncSessionLocal
    logger.info(f"[DEBUG] run_fine_tuning_async started for job_id: {job_id}")

    async with AsyncSessionLocal() as session:
        job = await async_get_fine_tuning_job_by_job_id(session, job_id)
        if not job:
            logger.error(f"任务 {job_id} 不存在")
            return

        await async_update_fine_tuning_job_status(session, job.job_id, FineTuningStatus.PREPARING)

        try:
            logger.info(f"[DEBUG] run_fine_tuning_async: calling execute_training_on_server for job_id: {job_id}")
            await execute_training_on_server(job, session)
            await session.commit()
            logger.info(f"[DEBUG] run_fine_tuning_async: execute_training_on_server completed, refreshing job data")
            await session.refresh(job)
            logger.info(f"[DEBUG] run_fine_tuning_async: job status={job.status}, log_file={job.log_file}")
            if not job.log_file:
                logger.warning(f"[DEBUG] run_fine_tuning_async: log_file is still None, aborting progress update")
                return
            logger.info(f"[DEBUG] run_fine_tuning_async: adding update_training_progress for job_id: {job_id}")
            background_tasks.add_task(update_training_progress, job_id)
        except Exception as e:
            logger.error(f"微调任务 {job_id} 执行失败: {e}")
            await async_update_fine_tuning_job_status(
                session, job.job_id, FineTuningStatus.FAILED, error_message=str(e)
            )


async def execute_training_on_server(job: FineTuningJob, db: AsyncSession):
    """在远程服务器上执行训练"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    await async_update_fine_tuning_job_status(db, job.job_id, FineTuningStatus.RUNNING)

    executor = ThreadPoolExecutor(max_workers=1)

    def _run_ssh_training():
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            if not job.server_ip or not job.ssh_username:
                raise FineTuningError("服务器信息不完整")

            password = get_decrypted_password(job.ssh_password)

            client.connect(
                hostname=job.server_ip,
                port=job.ssh_port,
                username=job.ssh_username,
                password=password,
                timeout=30
            )

            swift_args = build_swift_args(job)
            log_dir = f"/home/{job.ssh_username}/training_logs"
            log_file = f"{log_dir}/{job.job_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"

            mkdir_cmd = f"mkdir -p {log_dir}"
            client.exec_command(mkdir_cmd)

            conda_env = job.conda_env or "msswift"
            conda_path = "/data/softs/miniconda3/bin/activate"
            logger.info(f"[DEBUG] Using conda activate: '{conda_path}' for environment: '{conda_env}'")

            cuda_prefix = f"CUDA_VISIBLE_DEVICES={job.cuda_devices}" if job.cuda_devices else ""
            swift_args = build_swift_args(job)

            if cuda_prefix:
                command = f"cd {log_dir} && nohup bash -c 'export {cuda_prefix}; source {conda_path} {conda_env}; swift sft {swift_args}' > {log_file} 2>&1 &"
            else:
                command = f"cd {log_dir} && nohup bash -c 'source {conda_path} {conda_env}; swift sft {swift_args}' > {log_file} 2>&1 &"
            logger.info(f"[DEBUG] Executing command: {command}")

            client.exec_command(command)
            client.close()
            return log_file
        except Exception as e:
            client.close()
            raise FineTuningError(f"SSH执行失败: {str(e)}")

    loop = asyncio.get_event_loop()
    try:
        log_file = await loop.run_in_executor(executor, _run_ssh_training)
        await async_update_fine_tuning_job_status(
            db, job.job_id, FineTuningStatus.RUNNING, log_file=log_file
        )
    except Exception as e:
        raise FineTuningError(f"SSH执行失败: {str(e)}")
    finally:
        executor.shutdown(wait=False)


async def cancel_remote_training(job: FineTuningJob):
    """取消远程服务器上的训练任务"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        password = get_decrypted_password(job.ssh_password)
        client.connect(
            hostname=job.server_ip,
            port=job.ssh_port,
            username=job.ssh_username,
            password=password,
            timeout=30
        )

        kill_cmd = f"pkill -f 'run_ms_swift_training.sh.*{job.job_id}'"
        client.exec_command(kill_cmd)

    except Exception as e:
        logger.error(f"取消远程训练失败: {e}")
    finally:
        client.close()


async def update_training_progress(job_id: str):
    """更新训练进度（从日志文件解析 swift 输出路径并读取 logging.jsonl）"""
    from app.core.database import AsyncSessionLocal

    logger.info(f"[DEBUG] update_training_progress started for job_id: {job_id}")

    async with AsyncSessionLocal() as db:
        job = await async_get_fine_tuning_job_by_job_id(db, job_id)
        if not job:
            logger.warning(f"[DEBUG] update_training_progress: job not found for job_id: {job_id}")
            return

        import time
        import re
        max_wait_time = 3600 * 24
        start_time = time.time()

        swift_output_path = None

        while time.time() - start_time < max_wait_time:
            logger.info(f"[DEBUG] update_training_progress loop iteration for job_id: {job_id}, status={job.status}, log_file={job.log_file}")
            if job.status == FineTuningStatus.CANCELLED:
                break

            if not job.log_file:
                logger.info(f"[DEBUG] update_training_progress: log_file is None, waiting...")
                await asyncio.sleep(30)
                job = await async_get_fine_tuning_job_by_job_id(db, job_id)
                if not job:
                    break
                continue

            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                password = get_decrypted_password(job.ssh_password)
                client.connect(
                    hostname=job.server_ip,
                    port=job.ssh_port,
                    username=job.ssh_username,
                    password=password,
                    timeout=30
                )
                sftp = client.open_sftp()

                epoch_info = None
                log_content = ""

                if job.output_path:
                    logging_file = f"{job.output_path}/logging.jsonl"
                    try:
                        with sftp.file(logging_file, "r") as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-1].strip()
                                log_content += f"logging.jsonl: {last_line}\n"
                                epoch_info = parse_epoch_from_log([last_line])
                    except IOError:
                        pass

                try:
                    with sftp.file(job.log_file, "r") as f:
                        lines = f.readlines()
                        if lines:
                            for line in lines:
                                log_content += f"log_file: {line.strip()}\n"

                            if not swift_output_path:
                                match = re.search(r"\[INFO:swift\]\s*output_dir:\s*(.+)", "".join(lines))
                                if match:
                                    swift_output_path = match.group(1).strip()
                                    logger.info(f"[DEBUG] Found swift output path: {swift_output_path}")

                            if not epoch_info:
                                epoch_info = parse_epoch_from_log(lines)
                except IOError:
                    pass

                if swift_output_path and not epoch_info:
                    logging_file = f"{swift_output_path}/logging.jsonl"
                    try:
                        with sftp.file(logging_file, "r") as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-1].strip()
                                log_content += f"logging.jsonl: {last_line}\n"
                                epoch_info = parse_epoch_from_log([last_line])
                    except IOError:
                        pass

                sftp.close()
                client.close()

                if epoch_info:
                    current_epoch = epoch_info.get("current_epoch", 1)
                    progress = epoch_info.get("progress", 0)
                    await async_update_fine_tuning_job_status(
                        db, job_id, FineTuningStatus.RUNNING,
                        progress=progress,
                        current_epoch=current_epoch,
                        output_path=swift_output_path
                    )
                elif swift_output_path:
                    await async_update_fine_tuning_job_status(
                        db, job_id, FineTuningStatus.RUNNING,
                        output_path=swift_output_path
                    )

                if "train_runtime" in log_content or "train_samples_per_second" in log_content:
                    await async_update_fine_tuning_job_status(
                        db, job_id, FineTuningStatus.COMPLETED, progress=100
                    )
                    break

                if "ERROR" in log_content or "Traceback" in log_content:
                    await async_update_fine_tuning_job_status(
                        db, job_id, FineTuningStatus.FAILED, error_message="训练出错"
                    )
                    break

            except Exception as e:
                logger.warning(f"更新进度失败: {e}")

            await asyncio.sleep(30)
            job = await async_get_fine_tuning_job_by_job_id(db, job_id)
            if not job:
                break


def build_swift_args(job: FineTuningJob) -> str:
    """构建 ms-swift 训练参数"""
    args = [
        f"--model '{job.base_model_name}'",
        f"--model_type '{job.model_type or 'qwen2'}'",
        f"--template '{job.template or 'qwen2_5'}'",
        f"--dataset '{job.dataset_path or job.dataset_name}'",
        f"--torch_dtype 'bfloat16'",
        f"--max_length '{job.max_length or 1024}'",
        f"--split_dataset_ratio '{job.split_dataset_ratio if job.split_dataset_ratio is not None else 0}'",
        f"--learning_rate '{job.learning_rate or 1e-4}'",
        f"--gradient_accumulation_steps '{job.gradient_accumulation_steps or 16}'",
        f"--eval_steps '{job.eval_steps or 500}'",
        f"--lora_rank '{job.lora_rank or 8}'",
        f"--lora_alpha '{job.lora_alpha or 32}'",
        f"--num_train_epochs '{job.total_epochs}'",
        f"--use_chat_template 'True'",
        f"--ignore_args_error True"
    ]

    if job.task_type:
        args.append(f"--task_type '{job.task_type}'")
    if job.num_labels:
        args.append(f"--num_labels '{job.num_labels}'")
    if job.system_prompt:
        args.append(f"--system '{job.system_prompt}'")

    method_map = {
        FineTuningMethod.LORA: "lora",
        FineTuningMethod.QLORA: "qlora",
        FineTuningMethod.FULL: "full",
    }
    sft_type = method_map.get(job.method, "lora")
    args.append(f"--sft_type '{sft_type}'")

    if job.training_params:
        import json
        try:
            user_params = json.loads(job.training_params)
            for key, value in user_params.items():
                if key not in ["model", "model_type", "template", "dataset", "sft_type"]:
                    args.append(f"--{key} '{value}'")
        except json.JSONDecodeError:
            pass

    return " ".join(args)


def parse_epoch_from_log(lines: List[str]) -> Optional[dict]:
    """从日志中解析训练进度（支持 logging.jsonl JSON 格式）"""
    import re
    import json

    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue

        try:
            if line.startswith("{"):
                data = json.loads(line)
                epoch_val = data.get("epoch")
                global_step = data.get("global_step/max_steps", "")

                if isinstance(global_step, str) and "/" in global_step:
                    current, total = global_step.split("/")
                    current = int(current)
                    total = int(total)
                    if epoch_val is not None:
                        return {"current_epoch": int(float(epoch_val)), "progress": int(current * 100 / total) if total > 0 else 0}
                    else:
                        return {"current_epoch": 0, "progress": int(current * 100 / total) if total > 0 else 0}
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

        if "epoch" in line.lower() or "step" in line.lower():
            try:
                epoch_match = re.search(r"['\"]epoch['\"]:\s*['\"]?(\d+\.?\d*)/(\d+)", line, re.IGNORECASE)
                if epoch_match:
                    current = float(epoch_match.group(1))
                    total = int(epoch_match.group(2))
                    progress = int(current / total * 100) if total > 0 else 0
                    return {"current_epoch": int(current), "progress": progress}

                step_match = re.search(r"global_step/max_steps['\"]?:\s*['\"]?(\d+)/(\d+)", line, re.IGNORECASE)
                if step_match:
                    current = int(step_match.group(1))
                    total = int(step_match.group(2))
                    return {"current_epoch": int(current), "progress": int(current * 100 / total) if total > 0 else 0}

                train_match = re.search(r"Train:\s*(\d+)%+\|", line, re.IGNORECASE)
                if train_match:
                    progress = int(train_match.group(1))
                    return {"current_epoch": 0, "progress": progress}
            except Exception:
                pass
    return None


def extract_error_from_log(lines: List[str]) -> str:
    """从日志中提取错误信息"""
    for line in reversed(lines):
        if "ERROR" in line.upper() or "错误" in line or "失败" in line:
            return line.strip()
    return "未知错误"