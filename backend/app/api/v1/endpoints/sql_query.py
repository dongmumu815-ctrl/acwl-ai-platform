#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQL查询模板API接口
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.services.sql_query_template import SQLQueryTemplateService
from app.core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Pydantic模型定义
class SQLTemplateRequest(BaseModel):
    """SQL查询模板请求模型"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    datasourceId: int = Field(..., description="数据源ID")
    dataResourceId: Optional[int] = Field(None, description="数据资源ID")
    query: str = Field(..., description="SQL查询语句")
    tags: Optional[List[str]] = Field([], description="标签")
    config: Optional[dict] = Field({}, description="查询条件配置信息")
    is_template: bool = Field(True, description="是否为模板")

class SQLTemplateResponse(BaseModel):
    """SQL查询模板响应模型"""
    id: int
    name: str
    description: Optional[str]
    datasource_id: int
    data_resource_id: Optional[int]
    created_by: int
    query: str
    tags: Optional[List[str]]
    config: Optional[dict]
    is_template: bool
    created_at: str
    updated_at: str

@router.post("/templates")
async def save_sql_query_template(
    request: SQLTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    保存SQL查询模板
    """
    try:
        service = SQLQueryTemplateService(db)
        
        # 保存模板
        template = await service.create_template(
            name=request.name,
            description=request.description,
            datasource_id=request.datasourceId,
            data_resource_id=request.dataResourceId,
            query=request.query,
            created_by=current_user.id,
            tags=request.tags,
            config=request.config,
            is_template=request.is_template
        )
        
        logger.info(f"用户 {current_user.id} 保存了SQL查询模板: {template.name}")
        
        return {
            "success": True,
            "message": "SQL查询模板保存成功",
            "data": {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "datasource_id": template.datasource_id,
                "created_by": template.created_by,
                "query": template.query,
                "tags": template.tags,
                "config": template.config,  # 添加配置字段
                "is_template": template.is_template,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"保存SQL查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存SQL查询模板失败: {str(e)}"
        )

@router.get("/templates")
async def get_sql_query_templates(
    datasource_id: Optional[int] = Query(None, description="数据源ID"),
    data_resource_id: Optional[int] = Query(None, description="数据资源ID"),
    isTemplate: Optional[bool] = Query(None, description="是否为模板"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取SQL查询模板列表
    支持通过数据源ID或数据资源ID进行查询
    """
    # 验证参数：至少需要提供datasource_id或data_resource_id之一
    if not datasource_id and not data_resource_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="必须提供datasource_id或data_resource_id参数之一"
        )
    
    try:
        service = SQLQueryTemplateService(db)
        
        # 获取用户的模板列表
        templates = await service.get_templates(
            datasource_id=datasource_id,
            data_resource_id=data_resource_id,
            created_by=current_user.id,
            is_template=isTemplate
        )
        
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "datasource_id": template.datasource_id,
                "data_resource_id": template.data_resource_id,
                "created_by": template.created_by,
                "query": template.query,
                "tags": template.tags,
                "config": template.config,  # 添加配置字段
                "is_template": template.is_template,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": template_list
        }
        
    except Exception as e:
        logger.error(f"获取SQL查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取SQL查询模板失败: {str(e)}"
        )

@router.get("/templates/{template_id}")
async def get_sql_query_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个SQL查询模板
    """
    try:
        service = SQLQueryTemplateService(db)
        
        template = await service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SQL查询模板不存在"
            )
        
        # 检查权限（只能查看自己的模板）
        if template.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此模板"
            )
        
        return {
            "success": True,
            "data": {
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "datasource_id": template.datasource_id,
                "created_by": template.created_by,
                "query": template.query,
                "tags": template.tags,
                "config": template.config,  # 添加配置字段
                "is_template": template.is_template,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取SQL查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取SQL查询模板失败: {str(e)}"
        )

@router.put("/templates/{template_id}")
async def update_sql_query_template(
    template_id: int,
    request: SQLTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新SQL查询模板
    """
    try:
        service = SQLQueryTemplateService(db)
        
        # 检查模板是否存在
        template = await service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SQL查询模板不存在"
            )
        
        # 检查权限（只能修改自己的模板）
        if template.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此模板"
            )
        
        # 更新模板数据
        updated_template = await service.update_template(
            template_id=template_id,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            datasource_id=request.datasourceId,
            data_resource_id=request.dataResourceId,
            query=request.query,
            tags=request.tags,
            config=request.config,
            is_template=request.is_template
        )
        
        logger.info(f"用户 {current_user.id} 更新了SQL查询模板: {updated_template.name}")
        
        return {
            "success": True,
            "message": "SQL查询模板更新成功",
            "data": {
                "id": updated_template.id,
                "name": updated_template.name,
                "description": updated_template.description,
                "datasource_id": updated_template.datasource_id,
                "created_by": updated_template.created_by,
                "query": updated_template.query,
                "tags": updated_template.tags,
                "config": updated_template.config,  # 添加配置字段
                "is_template": updated_template.is_template,
                "created_at": updated_template.created_at.isoformat(),
                "updated_at": updated_template.updated_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新SQL查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新SQL查询模板失败: {str(e)}"
        )

@router.delete("/templates/{template_id}")
async def delete_sql_query_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除SQL查询模板
    """
    try:
        service = SQLQueryTemplateService(db)
        
        # 检查模板是否存在
        template = await service.get_template_by_id(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SQL查询模板不存在"
            )
        
        # 检查权限（只能删除自己的模板）
        if template.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此模板"
            )
        
        # 删除模板
        await service.delete_template(template_id)
        
        logger.info(f"用户 {current_user.id} 删除了SQL查询模板: {template.name}")
        
        return {
            "success": True,
            "message": "SQL查询模板删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除SQL查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除SQL查询模板失败: {str(e)}"
        )

@router.get("/templates/search")
async def search_sql_query_templates(
    keyword: str = Query(..., description="搜索关键词"),
    datasource_id: Optional[int] = Query(None, description="数据源ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    搜索SQL查询模板
    """
    try:
        service = SQLQueryTemplateService(db)
        
        # 搜索模板
        templates = await service.search_templates(
            keyword=keyword,
            datasource_id=datasource_id,
            user_id=current_user.id
        )
        
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.id,
                "name": template.name,
                "description": template.description,
                "datasource_id": template.datasource_id,
                "created_by": template.created_by,
                "query": template.query,
                "tags": template.tags,
                "is_template": template.is_template,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "data": template_list
        }
        
    except Exception as e:
        logger.error(f"搜索SQL查询模板失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索SQL查询模板失败: {str(e)}"
        )