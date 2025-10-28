#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from typing import List, Optional
import math

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.datasource import DatasourceType, DatasourceStatus
from app.schemas.datasource import (
    DatasourceCreate, DatasourceUpdate, DatasourceResponse, DatasourceListResponse,
    DatasourceTestRequest, DatasourceTestResponse, DatasourceTestLogResponse,
    DatasourceFilter, DatasourcePermissionCreate, DatasourcePermissionUpdate,
    DatasourcePermissionResponse, DatasourceTemplateResponse, DatasourceFilter,
    DatasourceStats, DatasourceConnectionInfo, DatasourceQueryRequest, DatasourceQueryResponse
)
from app.services.datasource import DatasourceService
from app.core.exceptions import ValidationError, NotFoundError, PermissionError
from app.core.response import success_response

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


@router.get("/")
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
        
        result = DatasourceListResponse(
            items=[DatasourceResponse.from_orm(ds) for ds in datasources],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
        return success_response(data=result, message="查询成功")
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
    import time
    import re
    from sqlalchemy import text
    
    start_time = time.time()
    
    try:
        # 获取数据源信息
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            return DatasourceQueryResponse(
                success=False,
                columns=None,
                data=None,
                row_count=0,
                execution_time=0,
                message="数据源不存在",
                error_details=f"数据源ID {datasource_id} 不存在"
            )
        
        # 检查数据源状态
        if not datasource.is_enabled:
            return DatasourceQueryResponse(
                success=False,
                columns=None,
                data=None,
                row_count=0,
                execution_time=0,
                message="数据源已禁用",
                error_details="数据源当前处于禁用状态"
            )
        
        # 安全检查：只允许SELECT查询
        query_upper = query_request.query.strip().upper()
        if not query_upper.startswith('SELECT'):
            return DatasourceQueryResponse(
                success=False,
                columns=None,
                data=None,
                row_count=0,
                execution_time=0,
                message="只允许执行SELECT查询",
                error_details="出于安全考虑，只允许执行SELECT查询语句"
            )
        
        # 检查是否包含危险关键词
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return DatasourceQueryResponse(
                    success=False,
                    columns=None,
                    data=None,
                    row_count=0,
                    execution_time=0,
                    message=f"查询包含禁止的关键词: {keyword}",
                    error_details=f"出于安全考虑，不允许在查询中使用 {keyword} 关键词"
                )
        
        # 执行查询
        result = await service.execute_query(
            datasource=datasource,
            query=query_request.query,
            limit=query_request.limit,
            timeout=query_request.timeout
        )
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return DatasourceQueryResponse(
            success=True,
            columns=result.get('columns', []),
            data=result.get('data', []),
            row_count=result.get('row_count', 0),
            execution_time=execution_time,
            message="查询执行成功"
        )
        
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        error_message = str(e)
        
        # 记录错误日志
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"数据源查询执行失败 - 数据源ID: {datasource_id}, 错误: {error_message}")
        
        return DatasourceQueryResponse(
            success=False,
            columns=None,
            data=None,
            row_count=0,
            execution_time=execution_time,
            message=f"查询执行失败: {error_message}",
            error_details=error_message
        )


@router.get("/{datasource_id}/tables/")
async def get_datasource_tables(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源的表/视图/索引列表
    
    - **datasource_id**: 数据源ID
    
    对于Elasticsearch：直接返回索引列表
    对于关系型数据库：需要先通过schemas API获取Schema，再通过schemas/{schema_name}/tables API获取表列表
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 根据数据源类型返回不同结果
        if datasource.datasource_type == DatasourceType.ELASTICSEARCH:
            # ES直接返回索引列表
            tables = await service._get_elasticsearch_indices(datasource)
            return {"success": True, "data": tables, "message": "获取索引列表成功"}
        else:
            # 关系型数据库需要先选择Schema
            return {
                "success": False, 
                "data": [], 
                "message": "关系型数据库需要先选择Schema，请使用 /api/v1/datasources/{datasource_id}/schemas/ 获取Schema列表，然后使用 /api/v1/datasources/{datasource_id}/schemas/{schema_name}/tables/ 获取表列表"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取表列表失败: {str(e)}")


@router.get("/{datasource_id}/schemas/")
async def get_datasource_schemas(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源的Schema列表
    
    - **datasource_id**: 数据源ID
    
    返回数据源中所有可用的Schema信息
    """
    try:
        service = DatasourceService(db)
        schemas = await service.get_datasource_schemas(datasource_id)
        
        return {"success": True, "data": schemas, "message": "获取Schema列表成功"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取Schema列表失败: {str(e)}")


@router.get("/{datasource_id}/schemas/{schema_name}/tables/")
async def get_datasource_tables_by_schema(
    datasource_id: int,
    schema_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定数据源指定Schema下的表和视图列表
    
    - **datasource_id**: 数据源ID
    - **schema_name**: Schema名称
    
    返回指定Schema中所有可用的表和视图信息
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 调用服务层方法获取指定Schema下的表列表
        tables = await service.get_datasource_tables_by_schema(datasource_id, schema_name)
        
        return {"success": True, "data": tables, "message": f"获取Schema '{schema_name}' 下的表列表成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取Schema下表列表失败: {str(e)}")


@router.get("/{datasource_id}/schemas/{schema_name}/tables/{table_name}/fields/")
async def get_datasource_table_fields(
    datasource_id: int,
    schema_name: str,
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定数据源指定Schema下指定表的字段列表
    
    - **datasource_id**: 数据源ID
    - **schema_name**: Schema名称
    - **table_name**: 表名称
    
    返回指定表中所有字段的详细信息
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 调用服务层方法获取指定表的字段列表
        fields = await service.get_datasource_table_fields(datasource_id, schema_name, table_name)
        
        return {"success": True, "data": fields, "message": f"获取表 '{table_name}' 的字段列表成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取表字段列表失败: {str(e)}")


@router.get("/{datasource_id}/stats/")
async def get_elasticsearch_cluster_stats(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Elasticsearch集群统计信息
    
    - **datasource_id**: 数据源ID
    
    返回集群健康、节点、分片和索引总体统计
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        if datasource.datasource_type != DatasourceType.ELASTICSEARCH:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该数据源不是Elasticsearch类型")
        
        timeout = datasource.connection_params.get('timeout', 30) if datasource.connection_params else 30
        max_retries = datasource.connection_params.get('max_retries', 3) if datasource.connection_params else 3
        
        from elasticsearch import AsyncElasticsearch
        
        if datasource.username and datasource.password:
            es = AsyncElasticsearch(
                [{
                    'scheme': 'http',
                    'host': datasource.host,
                    'port': datasource.port
                }],
                basic_auth=(datasource.username, datasource.password),
                request_timeout=timeout,
                max_retries=max_retries,
                retry_on_timeout=True,
                verify_certs=False
            )
        else:
            es = AsyncElasticsearch(
                [{
                    'scheme': 'http',
                    'host': datasource.host,
                    'port': datasource.port
                }],
                request_timeout=timeout,
                max_retries=max_retries,
                retry_on_timeout=True,
                verify_certs=False
            )
        
        try:
            health = await es.cluster.health()
            cluster_stats = await es.cluster.stats()
            indices_stats = cluster_stats.get('indices', {})
            documents = indices_stats.get('docs', {})
            store = indices_stats.get('store', {})
            
            def format_size(num_bytes: int) -> str:
                try:
                    b = int(num_bytes or 0)
                except Exception:
                    b = 0
                for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                    if b < 1024.0:
                        return f"{b:.1f}{unit}" if unit != 'B' else f"{b}B"
                    b /= 1024.0
                return f"{b:.1f}PB"
            
            data = {
                "clusterName": health.get('cluster_name') or cluster_stats.get('cluster_name'),
                "status": health.get('status'),
                "nodeCount": health.get('number_of_nodes', 0),
                "dataNodeCount": health.get('number_of_data_nodes', 0),
                "activeShards": health.get('active_shards', 0),
                "relocatingShards": health.get('relocating_shards', 0),
                "initializingShards": health.get('initializing_shards', 0),
                "unassignedShards": health.get('unassigned_shards', 0),
                "indices": {
                    "count": indices_stats.get('count', 0),
                    "docsCount": documents.get('count', 0),
                    "storeSize": format_size(store.get('size_in_bytes', 0))
                }
            }
            return success_response(data=data, message="获取集群统计信息成功")
        finally:
            await es.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取集群统计信息失败: {str(e)}")


@router.get("/{datasource_id}/tables/")
async def get_datasource_tables(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源的表/视图/索引列表
    
    - **datasource_id**: 数据源ID
    
    对于Elasticsearch：直接返回索引列表
    对于关系型数据库：需要先通过schemas API获取Schema，再通过schemas/{schema_name}/tables API获取表列表
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 根据数据源类型返回不同结果
        if datasource.datasource_type == DatasourceType.ELASTICSEARCH:
            # ES直接返回索引列表
            tables = await service._get_elasticsearch_indices(datasource)
            return {"success": True, "data": tables, "message": "获取索引列表成功"}
        else:
            # 关系型数据库需要先选择Schema
            return {
                "success": False, 
                "data": [], 
                "message": "关系型数据库需要先选择Schema，请使用 /api/v1/datasources/{datasource_id}/schemas/ 获取Schema列表，然后使用 /api/v1/datasources/{datasource_id}/schemas/{schema_name}/tables/ 获取表列表"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取表列表失败: {str(e)}")


@router.get("/{datasource_id}/schemas/")
async def get_datasource_schemas(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取数据源的Schema列表
    
    - **datasource_id**: 数据源ID
    
    返回数据源中所有可用的Schema信息
    """
    try:
        service = DatasourceService(db)
        schemas = await service.get_datasource_schemas(datasource_id)
        
        return {"success": True, "data": schemas, "message": "获取Schema列表成功"}
        
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取Schema列表失败: {str(e)}")


@router.get("/{datasource_id}/schemas/{schema_name}/tables/")
async def get_datasource_tables_by_schema(
    datasource_id: int,
    schema_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定数据源指定Schema下的表和视图列表
    
    - **datasource_id**: 数据源ID
    - **schema_name**: Schema名称
    
    返回指定Schema中所有可用的表和视图信息
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 调用服务层方法获取指定Schema下的表列表
        tables = await service.get_datasource_tables_by_schema(datasource_id, schema_name)
        
        return {"success": True, "data": tables, "message": f"获取Schema '{schema_name}' 下的表列表成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取Schema下表列表失败: {str(e)}")


@router.get("/{datasource_id}/schemas/{schema_name}/tables/{table_name}/fields/")
async def get_datasource_table_fields(
    datasource_id: int,
    schema_name: str,
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定数据源指定Schema下指定表的字段列表
    
    - **datasource_id**: 数据源ID
    - **schema_name**: Schema名称
    - **table_name**: 表名称
    
    返回指定表中所有字段的详细信息
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        
        # 调用服务层方法获取指定表的字段列表
        fields = await service.get_datasource_table_fields(datasource_id, schema_name, table_name)
        
        return {"success": True, "data": fields, "message": f"获取表 '{table_name}' 的字段列表成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取表字段列表失败: {str(e)}")


@router.get("/{datasource_id}/tables/{index_name}/stats/")
async def get_elasticsearch_index_stats(
    datasource_id: int,
    index_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取Elasticsearch指定索引的统计信息
    
    - **datasource_id**: 数据源ID
    - **index_name**: 索引名称
    
    返回索引的健康、状态、文档数量、存储大小等信息
    """
    try:
        service = DatasourceService(db)
        datasource = await service.get_datasource(datasource_id)
        
        if not datasource:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"数据源 ID {datasource_id} 不存在")
        if datasource.datasource_type != DatasourceType.ELASTICSEARCH:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该数据源不是Elasticsearch类型")
        
        # 读取连接参数
        timeout = datasource.connection_params.get('timeout', 30) if datasource.connection_params else 30
        max_retries = datasource.connection_params.get('max_retries', 3) if datasource.connection_params else 3
        
        # 延迟导入，避免非ES路径不必要依赖
        from elasticsearch import AsyncElasticsearch
        
        # 创建ES客户端（适配 8.x）
        if datasource.username and datasource.password:
            es = AsyncElasticsearch(
                [{
                    'scheme': 'http',
                    'host': datasource.host,
                    'port': datasource.port
                }],
                basic_auth=(datasource.username, datasource.password),
                request_timeout=timeout,
                max_retries=max_retries,
                retry_on_timeout=True,
                verify_certs=False
            )
        else:
            es = AsyncElasticsearch(
                [{
                    'scheme': 'http',
                    'host': datasource.host,
                    'port': datasource.port
                }],
                request_timeout=timeout,
                max_retries=max_retries,
                retry_on_timeout=True,
                verify_certs=False
            )
        
        try:
            # 使用 cat indices 获取统计（JSON 格式）
            indices = await es.cat.indices(index=index_name, format='json')
            if not indices:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"索引 {index_name} 不存在")
            index_info = indices[0]
            
            def to_int(v, default=0):
                try:
                    return int(v)
                except Exception:
                    return default
            
            stats = {
                "health": index_info.get("health"),
                "status": index_info.get("status"),
                "index": index_info.get("index"),
                "uuid": index_info.get("uuid"),
                "pri": to_int(index_info.get("pri")),
                "rep": to_int(index_info.get("rep")),
                # 兼容不同版本字段命名
                "docsCount": to_int(index_info.get("docs.count", index_info.get("docs"))),
                "docsDeleted": to_int(index_info.get("docs.deleted")),
                "storeSize": index_info.get("store.size"),
                "priStoreSize": index_info.get("pri.store.size")
            }
            
            return success_response(data=stats, message="获取索引统计信息成功")
        finally:
            await es.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"获取索引统计信息失败: {str(e)}")