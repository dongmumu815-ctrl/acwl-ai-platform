#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多数据库API端点
提供多数据库管理和CRUD操作的REST接口
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import logging

from app.services.multi_db_service import (
    RawQueryService, 
    DatabaseSwitchService,
    execute_sql
)
from app.core.multi_db_config import DatabaseConfig, DatabaseType, multi_db_config
from app.core.multi_db_manager import get_multi_db_manager
from app.core.db_router import get_smart_router, RoutingContext

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic模型定义
class DatabaseConfigCreate(BaseModel):
    """创建数据库配置的请求模型"""
    name: str = Field(..., description="数据库配置名称")
    type: DatabaseType = Field(..., description="数据库类型")
    host: str = Field(..., description="数据库主机")
    port: int = Field(..., description="数据库端口")
    username: str = Field(..., description="数据库用户名")
    password: str = Field(..., description="数据库密码")
    database: str = Field(..., description="数据库名称")
    charset: str = Field(default="utf8mb4", description="字符集")
    pool_size: int = Field(default=10, description="连接池大小")
    max_overflow: int = Field(default=20, description="最大溢出连接数")
    business_tags: List[str] = Field(default=[], description="业务标签")
    is_primary: bool = Field(default=False, description="是否为主数据库")


class DatabaseConfigUpdate(BaseModel):
    """更新数据库配置的请求模型"""
    host: Optional[str] = Field(None, description="数据库主机")
    port: Optional[int] = Field(None, description="数据库端口")
    username: Optional[str] = Field(None, description="数据库用户名")
    password: Optional[str] = Field(None, description="数据库密码")
    database: Optional[str] = Field(None, description="数据库名称")
    charset: Optional[str] = Field(None, description="字符集")
    pool_size: Optional[int] = Field(None, description="连接池大小")
    max_overflow: Optional[int] = Field(None, description="最大溢出连接数")
    business_tags: Optional[List[str]] = Field(None, description="业务标签")
    is_active: Optional[bool] = Field(None, description="是否激活")


class SQLQueryRequest(BaseModel):
    """SQL查询请求模型"""
    query: str = Field(..., description="SQL查询语句")
    params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    business_tag: Optional[str] = Field(None, description="业务标签")
    db_name: Optional[str] = Field(None, description="指定数据库名称")


class BatchSQLQueryRequest(BaseModel):
    """批量SQL查询请求模型"""
    queries: List[Dict[str, Any]] = Field(..., description="查询列表")
    business_tag: Optional[str] = Field(None, description="业务标签")
    db_name: Optional[str] = Field(None, description="指定数据库名称")


class DatabaseResponse(BaseModel):
    """数据库信息响应模型"""
    name: str
    type: str
    host: str
    port: int
    database: str
    business_tags: List[str]
    is_primary: bool
    is_active: bool


class QueryResponse(BaseModel):
    """查询响应模型"""
    success: bool
    data: Any
    message: Optional[str] = None
    affected_rows: Optional[int] = None


# 数据库配置管理端点
@router.get("/databases", response_model=Dict[str, DatabaseResponse])
async def get_all_databases():
    """
    获取所有数据库配置
    
    Returns:
        Dict[str, DatabaseResponse]: 数据库配置字典
    """
    try:
        databases_info = await DatabaseSwitchService.get_available_databases()
        
        response = {}
        for db_name, db_info in databases_info.items():
            response[db_name] = DatabaseResponse(**db_info)
        
        return response
    except Exception as e:
        logger.error(f"获取数据库配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取数据库配置失败: {str(e)}")


@router.post("/databases", response_model=Dict[str, str])
async def create_database_config(config: DatabaseConfigCreate):
    """
    创建新的数据库配置
    
    Args:
        config: 数据库配置
        
    Returns:
        Dict[str, str]: 创建结果
    """
    try:
        # 创建数据库配置对象
        db_config = DatabaseConfig(
            name=config.name,
            type=config.type,
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            database=config.database,
            charset=config.charset,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            business_tags=config.business_tags,
            is_primary=config.is_primary
        )
        
        # 添加到多数据库管理器
        db_manager = await get_multi_db_manager()
        success = await db_manager.add_database(db_config)
        
        if success:
            return {"message": f"数据库配置创建成功: {config.name}"}
        else:
            raise HTTPException(status_code=400, detail="数据库配置创建失败")
            
    except Exception as e:
        logger.error(f"创建数据库配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建数据库配置失败: {str(e)}")


@router.put("/databases/{db_name}", response_model=Dict[str, str])
async def update_database_config(db_name: str, config: DatabaseConfigUpdate):
    """
    更新数据库配置
    
    Args:
        db_name: 数据库名称
        config: 更新的配置
        
    Returns:
        Dict[str, str]: 更新结果
    """
    try:
        # 获取现有配置
        existing_config = multi_db_config.get_database(db_name)
        if not existing_config:
            raise HTTPException(status_code=404, detail=f"未找到数据库配置: {db_name}")
        
        # 更新配置
        update_data = config.dict(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(existing_config, key):
                setattr(existing_config, key, value)
        
        # 保存配置
        multi_db_config.save_config()
        
        # 重新初始化连接管理器
        db_manager = await get_multi_db_manager()
        await db_manager.remove_database(db_name)
        await db_manager.add_database(existing_config)
        
        return {"message": f"数据库配置更新成功: {db_name}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新数据库配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新数据库配置失败: {str(e)}")


@router.delete("/databases/{db_name}", response_model=Dict[str, str])
async def delete_database_config(db_name: str):
    """
    删除数据库配置
    
    Args:
        db_name: 数据库名称
        
    Returns:
        Dict[str, str]: 删除结果
    """
    try:
        db_manager = await get_multi_db_manager()
        success = await db_manager.remove_database(db_name)
        
        if success:
            return {"message": f"数据库配置删除成功: {db_name}"}
        else:
            raise HTTPException(status_code=400, detail="数据库配置删除失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除数据库配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除数据库配置失败: {str(e)}")


# 数据库连接测试端点
@router.get("/databases/{db_name}/test", response_model=Dict[str, bool])
async def test_database_connection(db_name: str):
    """
    测试指定数据库连接
    
    Args:
        db_name: 数据库名称
        
    Returns:
        Dict[str, bool]: 连接测试结果
    """
    try:
        result = await DatabaseSwitchService.test_database_connection(db_name)
        return {"connected": result}
    except Exception as e:
        logger.error(f"测试数据库连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试数据库连接失败: {str(e)}")


@router.get("/databases/test-all", response_model=Dict[str, bool])
async def test_all_database_connections():
    """
    测试所有数据库连接
    
    Returns:
        Dict[str, bool]: 所有数据库连接测试结果
    """
    try:
        results = await DatabaseSwitchService.test_all_connections()
        return results
    except Exception as e:
        logger.error(f"测试所有数据库连接失败: {e}")
        raise HTTPException(status_code=500, detail=f"测试所有数据库连接失败: {str(e)}")


# SQL查询端点
@router.post("/query", response_model=QueryResponse)
async def execute_sql_query(request: SQLQueryRequest):
    """
    执行SQL查询
    
    Args:
        request: SQL查询请求
        
    Returns:
        QueryResponse: 查询结果
    """
    try:
        result = await execute_sql(
            query=request.query,
            params=request.params,
            business_tag=request.business_tag,
            db_name=request.db_name
        )
        
        # 判断是否为写操作
        is_write_operation = any(keyword in request.query.upper() for keyword in ["INSERT", "UPDATE", "DELETE"])
        
        if is_write_operation:
            return QueryResponse(
                success=True,
                data=None,
                message="SQL执行成功",
                affected_rows=result if isinstance(result, int) else None
            )
        else:
            return QueryResponse(
                success=True,
                data=result,
                message="查询执行成功"
            )
            
    except Exception as e:
        logger.error(f"SQL查询执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"SQL查询执行失败: {str(e)}")


@router.post("/query/batch", response_model=List[QueryResponse])
async def execute_batch_sql_queries(request: BatchSQLQueryRequest):
    """
    批量执行SQL查询
    
    Args:
        request: 批量SQL查询请求
        
    Returns:
        List[QueryResponse]: 查询结果列表
    """
    try:
        results = await RawQueryService.execute_batch_queries(
            queries=request.queries,
            business_tag=request.business_tag,
            db_name=request.db_name
        )
        
        responses = []
        for i, result in enumerate(results):
            if result is not None:
                query_info = request.queries[i]
                query = query_info.get('query', '')
                is_write_operation = any(keyword in query.upper() for keyword in ["INSERT", "UPDATE", "DELETE"])
                
                if is_write_operation:
                    responses.append(QueryResponse(
                        success=True,
                        data=None,
                        message="SQL执行成功",
                        affected_rows=result if isinstance(result, int) else None
                    ))
                else:
                    responses.append(QueryResponse(
                        success=True,
                        data=result,
                        message="查询执行成功"
                    ))
            else:
                responses.append(QueryResponse(
                    success=False,
                    data=None,
                    message="查询执行失败"
                ))
        
        return responses
        
    except Exception as e:
        logger.error(f"批量SQL查询执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量SQL查询执行失败: {str(e)}")


# 路由信息端点
@router.get("/routing/info", response_model=Dict[str, Any])
async def get_routing_info():
    """
    获取路由器信息
    
    Returns:
        Dict[str, Any]: 路由器信息
    """
    try:
        router_instance = await get_smart_router()
        return router_instance.get_routing_info()
    except Exception as e:
        logger.error(f"获取路由信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取路由信息失败: {str(e)}")


@router.get("/databases/by-tag/{tag}", response_model=List[DatabaseResponse])
async def get_databases_by_tag(tag: str):
    """
    根据业务标签获取数据库列表
    
    Args:
        tag: 业务标签
        
    Returns:
        List[DatabaseResponse]: 数据库列表
    """
    try:
        db_configs = multi_db_config.get_databases_by_tag(tag)
        
        response = []
        for db_config in db_configs:
            response.append(DatabaseResponse(
                name=db_config.name,
                type=db_config.type.value,
                host=db_config.host,
                port=db_config.port,
                database=db_config.database,
                business_tags=db_config.business_tags,
                is_primary=db_config.is_primary,
                is_active=db_config.is_active
            ))
        
        return response
    except Exception as e:
        logger.error(f"根据标签获取数据库失败: {e}")
        raise HTTPException(status_code=500, detail=f"根据标签获取数据库失败: {str(e)}")


# 便捷查询端点
@router.get("/query/simple")
async def simple_query(
    sql: str = Query(..., description="SQL查询语句"),
    db_name: Optional[str] = Query(None, description="数据库名称"),
    business_tag: Optional[str] = Query(None, description="业务标签")
):
    """
    简单SQL查询（GET方式）
    
    Args:
        sql: SQL查询语句
        db_name: 数据库名称
        business_tag: 业务标签
        
    Returns:
        Any: 查询结果
    """
    try:
        # 只允许SELECT查询
        if not sql.strip().upper().startswith('SELECT'):
            raise HTTPException(status_code=400, detail="只允许SELECT查询")
        
        result = await execute_sql(
            query=sql,
            business_tag=business_tag,
            db_name=db_name
        )
        
        return {
            "success": True,
            "data": result,
            "message": "查询执行成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"简单查询执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")


# 健康检查端点
@router.get("/health")
async def health_check():
    """
    多数据库服务健康检查
    
    Returns:
        Dict[str, Any]: 健康状态
    """
    try:
        # 测试所有数据库连接
        connection_results = await DatabaseSwitchService.test_all_connections()
        
        # 获取路由器信息
        router_instance = await get_smart_router()
        routing_info = router_instance.get_routing_info()
        
        # 计算健康状态
        total_dbs = len(connection_results)
        healthy_dbs = sum(1 for connected in connection_results.values() if connected)
        health_percentage = (healthy_dbs / total_dbs * 100) if total_dbs > 0 else 0
        
        return {
            "status": "healthy" if health_percentage >= 80 else "degraded" if health_percentage >= 50 else "unhealthy",
            "total_databases": total_dbs,
            "healthy_databases": healthy_dbs,
            "health_percentage": health_percentage,
            "connection_status": connection_results,
            "routing_info": routing_info
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }