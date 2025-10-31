#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型管理API端点
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import os
import shutil
from datetime import datetime
import asyncio
import subprocess
import zipfile
import tempfile
import urllib.parse

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logger import logger
from app.models.user import User
from app.models.model import Model, ModelType, DownloadStatus
from app.schemas.common import PaginatedResponse, IDResponse
from app.api.v1.endpoints.auth import get_current_active_user

# 导入MinIO服务（必需）
try:
    from app.services.minio_service import minio_service
except ImportError as e:
    raise ImportError(f"MinIO服务是必需的，请检查配置: {e}")

router = APIRouter()


@router.get("/stats", summary="获取模型统计数据")
async def get_model_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型统计数据，包括总数、激活数、未激活数和总大小"""
    
    # 查询总模型数
    total_count_query = select(func.count(Model.id))
    total_count_result = await db.execute(total_count_query)
    total_count = total_count_result.scalar() or 0
    
    # 查询激活模型数
    active_count_query = select(func.count(Model.id)).where(Model.is_active == True)
    active_count_result = await db.execute(active_count_query)
    active_count = active_count_result.scalar() or 0
    
    # 计算未激活模型数
    inactive_count = total_count - active_count
    
    # 查询总大小
    total_size_query = select(func.sum(Model.model_size))
    total_size_result = await db.execute(total_size_query)
    total_size = total_size_result.scalar() or 0
    
    return {
        "total_count": total_count,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "total_size": total_size
    }


@router.get("/", summary="获取模型列表")
async def get_models(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    model_type: Optional[ModelType] = Query(None, description="模型类型"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型列表"""
        
    # 构建查询
    query = select(Model)
    
    # 搜索条件
    if search:
        query = query.where(
            Model.name.contains(search) |
            Model.description.contains(search)
        )
    
    # 类型筛选
    if model_type:
        query = query.where(Model.model_type == model_type)
    
    # 激活状态筛选
    if is_active is not None:
        query = query.where(Model.is_active == is_active)
    
    # 获取总数
    count_query = select(func.count(Model.id))
    if search:
        count_query = count_query.where(
            Model.name.contains(search) |
            Model.description.contains(search)
        )
    if model_type:
        count_query = count_query.where(Model.model_type == model_type)
    if is_active is not None:
        count_query = count_query.where(Model.is_active == is_active)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页查询
    offset = (page - 1) * size
    query = query.offset(offset).limit(size).order_by(Model.created_at.desc())
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 序列化模型数据
    model_items = []
    for model in models:
        model_dict = {
            "id": model.id,
            "name": model.name,
            "version": model.version,
            "description": model.description,
            "model_type": model.model_type,
            "model_size": model.model_size,
            "framework": model.framework,
            "local_path": model.local_path,
            "is_active": model.is_active,
            "download_status": model.download_status,
            "download_progress": model.download_progress,
            "download_error": model.download_error,
            "created_at": model.created_at,
            "updated_at": model.updated_at
        }
        model_items.append(model_dict)
    
    return PaginatedResponse(
        items=model_items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/{model_id}", summary="获取模型详情")
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型详情"""
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    # 序列化模型数据
    return {
        "id": model.id,
        "name": model.name,
        "version": model.version,
        "description": model.description,
        "model_type": model.model_type,
        "model_size": model.model_size,
        "framework": model.framework,
        "local_path": model.local_path,
        "is_active": model.is_active,
        "created_at": model.created_at,
        "updated_at": model.updated_at
    }


@router.post("/", summary="创建模型")
async def create_model(
    # 这里需要定义模型创建的schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """创建模型"""
    # TODO: 实现模型创建逻辑
    return IDResponse(id=1, message="模型创建成功")


@router.put("/{model_id}", summary="更新模型")
async def update_model(
    model_id: int,
    # 这里需要定义模型更新的schema
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新模型"""
    # TODO: 实现模型更新逻辑
    return {"message": "模型更新成功"}


@router.get("/{model_id}/download", summary="直接下载模型文件流")
async def get_download_url(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    直接下载模型文件流
    
    统一的下载接口，支持MinIO和本地文件的流式下载
    """
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    if not model.local_path:
        raise ValidationError("模型文件路径不存在")
    
    from fastapi.responses import FileResponse, StreamingResponse
    
    try:
        print(f"🚀 开始下载模型文件: {model.name} v{model.version}")
        
        # 检查是否为MinIO路径
        if model.local_path.startswith("minio://"):
            # 解析MinIO路径
            path_parts = model.local_path.replace("minio://", "").split("/", 2)
            if len(path_parts) < 3:
                raise ValidationError("MinIO路径格式错误")
            
            object_path = path_parts[2]
            
            # 检查MinIO中的文件是否存在并获取文件信息
            try:
                stat_info = minio_service.client.stat_object(minio_service.bucket_name, object_path)
                file_size = stat_info.size
                logger.info(f"MinIO文件信息 - 路径: {object_path}, 大小: {file_size} 字节")
            except Exception as e:
                logger.error(f"MinIO文件不存在或无法访问: {object_path}, 错误: {str(e)}")
                raise NotFoundError("MinIO中的模型文件不存在")
            
            # 从MinIO流式下载文件
            try:
                response = minio_service.client.get_object(minio_service.bucket_name, object_path)
                filename = f"{model.name}-{model.version}.zip"
                
                def iter_file():
                    try:
                        # 使用较大的块大小提高传输效率
                        chunk_size = 64 * 1024  # 64KB
                        while True:
                            data = response.read(chunk_size)
                            if not data:
                                break
                            yield data
                    except Exception as e:
                        logger.error(f"MinIO文件流式读取错误: {str(e)}")
                        raise
                    finally:
                        try:
                            response.close()
                            response.release_conn()
                        except:
                            pass
                
                # 正确编码文件名以支持中文字符
                encoded_filename = urllib.parse.quote(filename, safe='')
                headers = {
                    "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                    "Content-Length": str(file_size),
                    "Accept-Ranges": "bytes"
                }
                
                logger.info(f"开始流式传输MinIO文件: {filename}, 大小: {file_size} 字节")
                
                return StreamingResponse(
                    iter_file(),
                    media_type='application/zip',
                    headers=headers
                )
                
            except Exception as e:
                logger.error(f"MinIO文件下载失败: {str(e)}")
                raise ValidationError(f"文件下载失败: {str(e)}")
        
        # 检查本地文件是否存在
        elif os.path.exists(model.local_path):
            # 返回本地文件
            filename = f"{model.name}-{model.version}.zip"
            # 正确编码文件名以支持中文字符
            encoded_filename = urllib.parse.quote(filename, safe='')
            headers = {
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
            return FileResponse(
                path=model.local_path,
                media_type='application/zip',
                headers=headers
            )
        
        else:
            raise ValidationError("模型文件不存在")
                
    except ValidationError:
        raise
    except Exception as e:
        print(f"模型文件下载失败: {str(e)}")
        raise ValidationError(f"模型文件下载失败: {str(e)}")


@router.delete("/{model_id}", summary="删除模型")
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除模型（仅管理员）"""
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    # 检查是否有关联的部署记录
    from app.models.deployment import Deployment
    deployment_result = await db.execute(
        select(Deployment).where(Deployment.model_id == model_id)
    )
    deployments = deployment_result.scalars().all()
    
    if deployments:
        # 如果有关联的部署记录，提供详细信息
        deployment_names = [d.deployment_name for d in deployments]
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无法删除该模型，因为它正在被以下部署使用：{', '.join(deployment_names)}。请先删除或修改这些部署后再删除模型。"
        )
    
    try:
        # 删除模型文件（如果存在）
        if model.local_path:
            try:
                if model.local_path.startswith("minio://"):
                    # 删除MinIO中的文件
                    # 解析MinIO路径
                    path_parts = model.local_path.replace("minio://", "").split("/", 2)
                    if len(path_parts) >= 3:
                        bucket_name = path_parts[1]
                        object_path = path_parts[2]
                        
                        # 删除MinIO对象
                        minio_service.client.remove_object(bucket_name, object_path)
                        print(f"已删除MinIO文件: {model.local_path}")
                    else:
                        print(f"警告：MinIO路径格式错误: {model.local_path}")
                elif os.path.exists(model.local_path):
                    # 删除本地文件
                    if os.path.isfile(model.local_path):
                        os.remove(model.local_path)
                    elif os.path.isdir(model.local_path):
                        shutil.rmtree(model.local_path)
                    print(f"已删除本地文件: {model.local_path}")
            except Exception as file_error:
                # 文件删除失败不影响数据库删除，只记录警告
                print(f"警告：删除模型文件失败: {file_error}")
        
        await db.delete(model)
        await db.commit()
        return {"message": "模型删除成功"}
    except Exception as e:
        await db.rollback()
        error_msg = str(e)
        
        # 检查是否是外键约束错误
        if "foreign key constraint" in error_msg.lower() or "fk_" in error_msg.lower():
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法删除该模型，因为它正在被其他资源引用。请先解除相关引用后再删除。"
            )
        else:
            # 其他错误
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除模型时发生错误: {error_msg}"
            )


@router.post("/upload", summary="上传模型")
async def upload_model(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    version: str = Form(...),
    model_type: ModelType = Form(...),
    description: str = Form(None),
    base_model: str = Form(None),
    framework: str = Form(None),
    parameters: int = Form(None),
    quantization: str = Form(None),
    source_url: str = Form(None),
    upload_type: str = Form("file", description="上传类型：file(文件上传) 或 download(源地址下载)"),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> IDResponse:
    """上传模型文件或通过源地址下载"""
    
    # 检查模型名称和版本是否已存在
    existing_model = await db.execute(
        select(Model).where(Model.name == name, Model.version == version)
    )
    if existing_model.scalar_one_or_none():
        raise ValidationError(f"模型 {name}:{version} 已存在")
    
    # 验证上传类型和参数
    if upload_type == "file":
        if not file:
            raise ValidationError("文件上传模式必须提供文件")
        
        # 验证文件类型
        if not file.filename:
            raise ValidationError("文件名不能为空")
        
        # 检查文件扩展名
        if not file.filename.lower().endswith('.zip'):
            raise ValidationError("只支持上传 .zip 格式的文件")
        
        # 检查文件MIME类型
        allowed_content_types = [
            'application/zip',
            'application/x-zip-compressed',
            'application/x-zip',
            'application/octet-stream'  # 某些浏览器可能发送这个类型
        ]
        if file.content_type and file.content_type not in allowed_content_types:
            raise ValidationError(f"不支持的文件类型: {file.content_type}，只支持 .zip 格式")
        
    elif upload_type == "download":
        if not source_url:
            raise ValidationError("源地址下载模式必须提供源地址")
    else:
        raise ValidationError("上传类型必须是 'file' 或 'download'")
    
    local_path = None
    file_size = None
    download_status = DownloadStatus.UPLOADED
    
    if upload_type == "file":
        # 文件上传模式 - 强制使用MinIO存储，支持分片上传
        try:
            import tempfile
            import os
            import zipfile
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # 保存上传的文件到临时位置
                file_content = await file.read()
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # 验证zip文件格式
            try:
                with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                    # 尝试读取zip文件信息，如果不是有效的zip文件会抛出异常
                    zip_ref.testzip()
                logger.info(f"✅ ZIP文件格式验证通过: {file.filename}")
            except zipfile.BadZipFile:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise ValidationError("上传的文件不是有效的ZIP格式")
            except Exception as e:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise ValidationError(f"ZIP文件验证失败: {str(e)}")
            
            try:
                # 使用增强的MinIO服务进行分片上传
                object_path = await minio_service.upload_model_file(
                    file_path=temp_file_path,
                    model_name=name,
                    model_version=version,
                    filename=file.filename,
                    progress_callback=None  # 可以添加进度回调
                )
                
                # 设置MinIO路径
                local_path = minio_service.get_object_url(object_path)
                file_size = len(file_content)
                
                logger.info(f"✅ 模型文件上传成功: {local_path}")
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
        except Exception as e:
            logger.error(f"MinIO分片上传失败: {str(e)}")
            raise ValidationError(f"MinIO分片上传失败: {str(e)}")
        download_status = DownloadStatus.UPLOADED
    else:
        # 源地址下载模式
        download_status = DownloadStatus.PENDING
    
    # 创建模型记录
    new_model = Model(
        name=name,
        version=version,
        description=description,
        base_model=base_model,
        model_type=model_type,
        model_size=file_size,
        parameters=parameters,
        framework=framework,
        quantization=quantization,
        source_url=source_url,
        local_path=local_path,
        download_status=download_status,
        download_progress=0 if upload_type == "download" else None,
        is_active=upload_type == "file"  # 文件上传立即激活，下载完成后激活
    )
    
    db.add(new_model)
    await db.commit()
    await db.refresh(new_model)
    
    # 如果是下载模式，启动后台下载任务
    if upload_type == "download":
        background_tasks.add_task(download_model_from_source, new_model.id, source_url)
        return IDResponse(id=new_model.id, message="模型下载任务已启动")
    
    return IDResponse(id=new_model.id, message="模型上传成功")





# 克隆功能已暂时禁用
# @router.post("/{model_id}/clone", summary="克隆模型")
# async def clone_model(
#     model_id: int,
#     request_data: dict,
#     current_user: User = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db)
# ) -> IDResponse:
#     """克隆模型"""
#     
#     # 获取新模型名称
#     name = request_data.get("name")
#     if not name:
#         raise ValidationError("模型名称不能为空")
#     
#     # 获取原模型
#     result = await db.execute(select(Model).where(Model.id == model_id))
#     original_model = result.scalar_one_or_none()
#     
#     if not original_model:
#         raise NotFoundError("原模型不存在")
#     
#     # 检查新名称是否已存在
#     existing_model = await db.execute(
#         select(Model).where(Model.name == name, Model.version == original_model.version)
#     )
#     if existing_model.scalar_one_or_none():
#         raise ValidationError(f"模型 {name}:{original_model.version} 已存在")
#     
#     # 创建克隆模型
#     cloned_model = Model(
#         name=name,
#         version=original_model.version,
#         description=f"克隆自 {original_model.name}",
#         base_model=original_model.base_model,
#         model_type=original_model.model_type,
#         model_size=original_model.model_size,
#         parameters=original_model.parameters,
#         framework=original_model.framework,
#         quantization=original_model.quantization,
#         source_url=original_model.source_url,
#         local_path=original_model.local_path,  # 共享同一个文件
#         is_active=False  # 克隆的模型默认不激活
#     )
#     
#     db.add(cloned_model)
#     await db.commit()
#     await db.refresh(cloned_model)
#     
#     return IDResponse(id=cloned_model.id, message="模型克隆成功")


@router.patch("/{model_id}/status", summary="切换模型状态")
async def toggle_model_status(
    model_id: int,
    request_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """激活或停用模型"""
    
    # 获取激活状态
    is_active = request_data.get("is_active")
    if is_active is None:
        raise ValidationError("is_active参数不能为空")
    
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    model.is_active = is_active
    await db.commit()
    
    status_text = "激活" if is_active else "停用"
    return {"message": f"模型{status_text}成功"}


@router.get("/stats", summary="获取模型统计信息")
async def get_model_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型统计信息"""
    
    # 总模型数
    total_result = await db.execute(select(func.count(Model.id)))
    total = total_result.scalar()
    
    # 激活模型数
    active_result = await db.execute(
        select(func.count(Model.id)).where(Model.is_active == True)
    )
    active = active_result.scalar()
    
    # 总存储大小
    size_result = await db.execute(
        select(func.sum(Model.model_size)).where(Model.model_size.isnot(None))
    )
    total_size = size_result.scalar() or 0
    
    return {
        "total": total,
        "active": active,
        "training": 0,  # 训练中的模型需要从其他表获取
        "totalSize": total_size
    }


@router.get("/available-for-agents", summary="获取可用于Agent的模型列表")
async def get_available_models_for_agents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取可用于Agent配置的模型列表
    只返回激活状态的LLM类型模型，格式化为前端下拉选择所需的格式
    """
    
    # 查询激活的LLM模型
    query = select(Model).where(
        Model.is_active == True,
        Model.model_type == ModelType.LLM
    ).order_by(Model.name, Model.version)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    # 格式化为前端下拉选择所需的格式
    available_models = []
    for model in models:
        # 生成显示标签和值
        label = f"{model.name}"
        if model.version:
            label += f" ({model.version})"
        
        value = f"{model.name}"
        if model.version:
            value += f":{model.version}"
        
        available_models.append({
            "label": label,
            "value": value,
            "model_id": model.id,
            "description": model.description
        })
    
    return available_models


async def download_model_from_source(model_id: int, source_url: str):
    """异步下载模型的后台任务"""
    from app.core.database import get_db_context
    
    async with get_db_context() as db:
        try:
            # 获取模型记录
            result = await db.execute(select(Model).where(Model.id == model_id))
            model = result.scalar_one_or_none()
            if not model:
                return
            
            # 更新状态为下载中
            model.download_status = DownloadStatus.DOWNLOADING
            model.download_progress = 0
            await db.commit()
            
            # 创建临时下载目录
            download_dir = f"/tmp/models/{model.name}-{model.version}"
            os.makedirs(download_dir, exist_ok=True)
            
            # 使用 modelscope download 命令下载模型
            cmd = [
                "modelscope", "download", 
                "--model", source_url,
                "--local_dir", download_dir
            ]
            
            # 启动下载进程
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # 等待下载完成
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 下载成功，更新进度到50%
                model.download_progress = 50
                await db.commit()
                
                # 压缩模型文件到临时目录
                zip_filename = f"{model.name}-{model.version}.zip"
                zip_path = os.path.join("/tmp", zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(download_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, download_dir)
                            zipf.write(file_path, arcname)
                
                # 压缩完成，更新进度到75%
                model.download_progress = 75
                await db.commit()
                
                # 获取文件大小
                file_size = os.path.getsize(zip_path)
                
                # 生成MinIO对象路径
                minio_object_path = f"models/{model.name}/{model.version}/compressed/{zip_filename}"
                
                # 分片上传到MinIO
                await minio_service.upload_file_with_progress(
                    file_path=zip_path,
                    object_name=minio_object_path,
                    content_type='application/zip',
                    progress_callback=None  # 可以添加进度回调
                )
                
                # 上传完成，更新模型记录
                model.download_status = DownloadStatus.COMPLETED
                model.download_progress = 100
                model.local_path = minio_service.get_object_url(minio_object_path)
                model.model_size = file_size
                model.is_active = True
                model.download_error = None
                
                # 清理临时文件
                shutil.rmtree(download_dir, ignore_errors=True)
                if os.path.exists(zip_path):
                    os.remove(zip_path)
                
                print(f"✅ 模型 {model.name} v{model.version} 下载、压缩、上传完成")
                
            else:
                # 下载失败
                error_msg = stderr.decode() if stderr else "下载失败"
                model.download_status = DownloadStatus.FAILED
                model.download_error = error_msg
                
                # 清理临时目录
                shutil.rmtree(download_dir, ignore_errors=True)
            
            await db.commit()
            
        except Exception as e:
            # 处理异常
            try:
                model.download_status = DownloadStatus.FAILED
                model.download_error = str(e)
                await db.commit()
                
                # 清理临时文件
                if 'download_dir' in locals():
                    shutil.rmtree(download_dir, ignore_errors=True)
                if 'zip_path' in locals() and os.path.exists(zip_path):
                    os.remove(zip_path)
                    
                print(f"❌ 模型下载失败: {str(e)}")
            except:
                pass


@router.get("/{model_id}/download-status", summary="获取模型下载状态")
async def get_download_status(
    model_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取模型下载状态和进度"""
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    return {
        "id": model.id,
        "name": model.name,
        "version": model.version,
        "download_status": model.download_status,
        "download_progress": model.download_progress,
        "download_error": model.download_error,
        "is_active": model.is_active
    }


@router.post("/{model_id}/retry-download", summary="重新下载模型")
async def retry_download_model(
    model_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重新下载失败的模型"""
    
    # 获取模型记录
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    
    if not model:
        raise NotFoundError("模型不存在")
    
    # 检查模型是否可以重新下载
    if model.download_status not in [DownloadStatus.FAILED]:
        raise ValidationError("只有下载失败的模型才能重新下载")
    
    if not model.source_url:
        raise ValidationError("模型没有源地址，无法重新下载")
    
    # 重置下载状态
    model.download_status = DownloadStatus.PENDING
    model.download_progress = 0
    model.download_error = None
    model.is_active = False
    
    await db.commit()
    
    # 启动后台下载任务
    background_tasks.add_task(download_model_from_source, model.id, model.source_url)
    
    return {"message": "重新下载任务已启动"}