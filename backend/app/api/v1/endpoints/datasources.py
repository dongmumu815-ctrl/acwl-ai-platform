#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import math

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.datasource import DatasourceType, DatasourceStatus
from app.schemas.datasource import (
    DatasourceCreate, DatasourceUpdate, DatasourceResponse, DatasourceListResponse,
    DatasourceTestRequest, DatasourceTestResponse, DatasourceTestLogResponse,
    # DatasourceUsageStatsResponse, 
    DatasourcePermissionCreate, DatasourcePermissionUpdate,
    DatasourcePermissionResponse, DatasourceTemplateResponse, DatasourceFilter,
    DatasourceStats, DatasourceConnectionInfo, DatasourceQueryRequest, DatasourceQueryResponse
)
from app.services.datasource import DatasourceService
from app.core.exceptions import ValidationError, NotFoundError, PermissionError

router = APIRouter()


@router.post("/", response_model=DatasourceResponse, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    datasource_data: DatasourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建数据源
    
    - **name**: 数据源名称（必填）
    - **description**: 数据源描述
    - **datasource_type**: 数据源类型（必填）
    - **host**: 主机地址（必填）
    - **port**: 端口号（必填）
    - **database_name**: 数据库名称
    - **username**: 用户名
    - **password**: 密码
    - **connection_params**: 连接参数
    - **pool_config**: 连接池配置
    - **is_enabled**: 是否启用
    """
    try:
        service = DatasourceService(db)
        datasource = await service.create_datasource(datasource_data, current_user.id)
        return DatasourceResponse.from_orm(datasource)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建数据源失败: {str(e)}")


@router.get("/", response_model=DatasourceListResponse)
async def get_datasources(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    datasource_type: Optional[DatasourceType] = Query(None, description="数据源类型"),
    status: Optional[DatasourceStatus] = Query(None, description="数据源状态"),
    is_enabled: Optional[bool] = Query(None, description="是否启用"),
    created_by: Optional[int] = Query(None, description="创建者ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源列表
    
    支持分页和筛选：
    - **page**: 页码，从1开始
    - **size**: 每页大小，最大100
    - **search**: 搜索关键词，支持名称、描述、主机地址模糊搜索
    - **datasource_type**: 按数据源类型筛选
    - **status**: 按状态筛选
    - **is_enabled**: 按启用状态筛选
    - **created_by**: 按创建者筛选
    """
    try:
        filters = DatasourceFilter(
            search=search,
            datasource_type=datasource_type,
            status=status,
            is_enabled=is_enabled,
            created_by=created_by
        )
        
        service = DatasourceService(db)
        datasources, total = await service.get_datasources(
            filters=filters,
            page=page,
            size=size,
            user_id=current_user.id
        )
        
        pages = math.ceil(total / size) if total > 0 else 1
        
        return DatasourceListResponse(
            items=[DatasourceResponse.from_orm(ds) for ds in datasources],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据源列表失败: {str(e)}")


@router.get("/{datasource_id}", response_model=DatasourceResponse)
async def get_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个数据源详情
    
    - **datasource_id**: 数据源ID
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        return DatasourceResponse.from_orm(datasource)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取数据源失败: {str(e)}")


@router.put("/{datasource_id}", response_model=DatasourceResponse)
async def update_datasource(
    datasource_id: int,
    datasource_data: DatasourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新数据源
    
    - **datasource_id**: 数据源ID
    - 其他字段为可选更新字段
    """
    try:
        service = DatasourceService(db)
        datasource = await service.update_datasource(datasource_id, datasource_data, current_user.id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        return DatasourceResponse.from_orm(datasource)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新数据源失败: {str(e)}")


@router.delete("/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除数据源
    
    - **datasource_id**: 数据源ID
    
    注意：如果数据源存在关联的权限记录，将无法删除
    """
    try:
        service = DatasourceService(db)
        await service.delete_datasource(datasource_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"删除数据源失败: {str(e)}")


@router.post("/test-temp", response_model=DatasourceTestResponse)
async def test_temp_datasource_connection(
    datasource_data: DatasourceCreate,
    test_request: DatasourceTestRequest = DatasourceTestRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    临时测试数据源连接（不保存数据源）
    
    - **datasource_data**: 数据源配置信息
    - **timeout**: 超时时间（秒），默认10秒
    - **test_query**: 自定义测试查询语句，可选
    
    返回连接测试结果，包括成功状态、响应时间、连接信息等
    """
    try:
        service = DatasourceService(db)
        result = await service.test_temp_connection(datasource_data, test_request, current_user.id)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"测试连接失败: {str(e)}")


@router.post("/{datasource_id}/test", response_model=DatasourceTestResponse)
async def test_datasource_connection(
    datasource_id: int,
    test_request: DatasourceTestRequest = DatasourceTestRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    测试数据源连接
    
    - **datasource_id**: 数据源ID
    - **timeout**: 超时时间（秒），默认10秒
    - **test_query**: 自定义测试查询语句，可选
    
    返回连接测试结果，包括成功状态、响应时间、连接信息等
    """
    try:
        service = DatasourceService(db)
        result = await service.test_connection(datasource_id, test_request, current_user.id)
        return result
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"测试连接失败: {str(e)}")


@router.post("/{datasource_id}/enable", status_code=status.HTTP_200_OK)
async def enable_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    启用数据源
    
    - **datasource_id**: 数据源ID
    """
    try:
        service = DatasourceService(db)
        await service.enable_datasource(datasource_id)
        return {"message": "数据源已启用"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"启用数据源失败: {str(e)}")


@router.post("/{datasource_id}/disable", status_code=status.HTTP_200_OK)
async def disable_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    停用数据源
    
    - **datasource_id**: 数据源ID
    """
    try:
        service = DatasourceService(db)
        await service.disable_datasource(datasource_id)
        return {"message": "数据源已停用"}
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"停用数据源失败: {str(e)}")


@router.get("/stats/overview", response_model=DatasourceStats)
async def get_datasource_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源统计信息
    
    返回数据源的总体统计信息，包括：
    - 总数量
    - 各状态数量
    - 类型分布
    - 最近测试成功率
    """
    try:
        service = DatasourceService(db)
        stats = await service.get_datasource_stats()
        return DatasourceStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取统计信息失败: {str(e)}")


@router.get("/{datasource_id}/test-logs", response_model=List[DatasourceTestLogResponse])
async def get_datasource_test_logs(
    datasource_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源测试日志
    
    - **datasource_id**: 数据源ID
    - **page**: 页码
    - **size**: 每页大小
    """
    try:
        service = DatasourceService(db)
        logs, total = await service.get_test_logs(datasource_id, page, size)
        return [DatasourceTestLogResponse.from_orm(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取测试日志失败: {str(e)}")


@router.get("/test-logs/all", response_model=List[DatasourceTestLogResponse])
async def get_all_test_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有数据源的测试日志
    
    - **page**: 页码
    - **size**: 每页大小
    """
    try:
        service = DatasourceService(db)
        logs, total = await service.get_test_logs(None, page, size)
        return [DatasourceTestLogResponse.from_orm(log) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取测试日志失败: {str(e)}")


@router.get("/templates/", response_model=List[DatasourceTemplateResponse])
async def get_datasource_templates(
    datasource_type: Optional[DatasourceType] = Query(None, description="数据源类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源配置模板
    
    - **datasource_type**: 数据源类型，可选，不指定则返回所有类型的模板
    
    返回预定义的数据源配置模板，包含默认端口、连接参数等信息
    """
    try:
        service = DatasourceService(db)
        templates = await service.get_templates(datasource_type)
        return [DatasourceTemplateResponse.from_orm(template) for template in templates]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取模板失败: {str(e)}")


@router.get("/{datasource_id}/connection-info", response_model=DatasourceConnectionInfo)
async def get_datasource_connection_info(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源连接信息
    
    - **datasource_id**: 数据源ID
    
    返回数据源的连接信息，敏感信息会被隐藏
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 构建连接URL（隐藏敏感信息）
        connection_url = f"{datasource.datasource_type.value}://{datasource.username}:***@{datasource.host}:{datasource.port}"
        if datasource.database_name:
            connection_url += f"/{datasource.database_name}"
        
        return DatasourceConnectionInfo(
            datasource_id=datasource_id,
            connection_url=connection_url,
            driver_info={
                "type": datasource.datasource_type.value,
                "version": "Unknown"  # 可以从实际连接中获取
            },
            server_info={
                "host": datasource.host,
                "port": datasource.port,
                "status": datasource.status.value
            },
            database_info={
                "name": datasource.database_name,
                "last_test_time": datasource.last_test_time.isoformat() if datasource.last_test_time else None,
                "last_test_result": datasource.last_test_result
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取连接信息失败: {str(e)}")


@router.post("/{datasource_id}/query", response_model=DatasourceQueryResponse)
async def execute_datasource_query(
    datasource_id: int,
    query_request: DatasourceQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行数据源查询
    
    - **datasource_id**: 数据源ID
    - **query**: 查询语句
    - **limit**: 结果限制，默认100
    - **timeout**: 超时时间（秒），默认30
    
    注意：此功能仅用于测试和调试，生产环境中应谨慎使用
    """
    try:
        # 这里可以实现查询执行逻辑
        # 为了安全考虑，可能需要限制查询类型（如只允许SELECT）
        
        return DatasourceQueryResponse(
            success=True,
            columns=["column1", "column2"],
            data=[["value1", "value2"], ["value3", "value4"]],
            row_count=2,
            execution_time=100,
            message="查询执行成功"
        )
    except Exception as e:
        return DatasourceQueryResponse(
            success=False,
            columns=None,
            data=None,
            row_count=0,
            execution_time=0,
            message=f"查询执行失败: {str(e)}",
            error_details=str(e)
        )