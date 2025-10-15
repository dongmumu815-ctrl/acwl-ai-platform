#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据资源中心API路由
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from app.core.database import get_db
from app.core.response import success_response
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.schemas.data_resource import (
    DataResourceCreate,
    DataResourceUpdate,
    DataResourceResponse,
    DataResourceListResponse,
    DataResourceSearchRequest,
    DataResourceQueryRequest,
    DataResourceQueryResponse,
    DataResourceSchemaResponse,
    DataResourcePreviewResponse,
    DataResourcePermissionCreate,
    DataResourcePermissionResponse,
    DataResourceCategoryCreate,
    DataResourceCategoryResponse,
    DataResourceTagCreate,
    DataResourceTagResponse,
    DataResourceStatisticsResponse,
    BatchOperationRequest,
    BatchOperationResponse
)
from app.services.data_resource_service import DataResourceService
from app.core.response import success_response, error_response
from app.core.exceptions import BusinessError, AuthorizationError, NotFoundError

router = APIRouter(prefix="/data-resources", tags=["数据资源中心"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=DataResourceResponse, status_code=HTTP_201_CREATED)
async def create_resource(
    resource_data: DataResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建数据资源
    
    Args:
        resource_data: 资源创建数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的数据资源
    """
    try:
        service = DataResourceService(db)
        resource = await service.create_resource(resource_data, current_user.id)
        return resource
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建数据资源失败")


@router.get("/", response_model=DataResourceListResponse)
async def search_resources(
    keyword: Optional[str] = Query(None, description="关键词"),
    category_id: Optional[int] = Query(None, description="分类ID"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    datasource_id: Optional[int] = Query(None, description="数据源ID"),
    tags: Optional[str] = Query(None, description="标签，逗号分隔"),
    is_public: Optional[bool] = Query(None, description="是否公开"),
    status: Optional[str] = Query(None, description="状态"),
    created_by: Optional[int] = Query(None, description="创建者ID"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索数据资源
    
    Args:
        keyword: 关键词
        category_id: 分类ID
        resource_type: 资源类型
        datasource_id: 数据源ID
        tags: 标签
        is_public: 是否公开
        status: 状态
        created_by: 创建者ID
        sort_by: 排序字段
        sort_order: 排序方向
        page: 页码
        size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        资源列表
    """
    try:
        # 构建搜索请求
        search_request = DataResourceSearchRequest(
            keyword=keyword if keyword else None,
            category_id=category_id,
            resource_type=resource_type if resource_type else None,
            datasource_id=datasource_id,
            tags=tags.split(",") if tags else None,
            is_public=is_public,
            status=status if status else None,
            created_by=created_by,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        service = DataResourceService(db)
        resources, total = await service.search_resources(search_request, current_user.id)
        
        # 计算分页信息
        pages = (total + size - 1) // size
        
        # 使用自定义序列化方法处理标签信息
        resource_items = [
            DataResourceResponse.from_orm_with_tags(resource)
            for resource in resources
        ]
        
        result = DataResourceListResponse(
            items=resource_items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
        return success_response(data=result, message="查询成功")
        
    except Exception as e:
        import traceback
        print(f"查询数据资源失败: {str(e)}")
        print(f"错误详情: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"查询数据资源失败: {str(e)}")


@router.get("/{resource_id}")
async def get_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据资源详情
    
    Args:
        resource_id: 资源ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        数据资源详情
    """
    try:
        service = DataResourceService(db)
        resource = await service.get_resource_by_id(resource_id, current_user.id)
        
        if not resource:
            raise HTTPException(status_code=404, detail="数据资源不存在")
        
        # 使用自定义方法，确保标签信息正确序列化到 tag_list
        resource_response = DataResourceResponse.from_orm_with_tags(resource)
        return success_response(data=resource_response, message="获取数据资源成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据资源失败，资源ID: {resource_id}, 用户ID: {current_user.id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取数据资源失败: {str(e)}")


@router.put("/{resource_id}", response_model=DataResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: DataResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新数据资源
    
    Args:
        resource_id: 资源ID
        resource_data: 更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的数据资源
    """
    try:
        service = DataResourceService(db)
        resource = await service.update_resource(resource_id, resource_data, current_user.id)
        # 使用自定义方法，确保标签信息正确序列化到 tag_list
        resource_response = DataResourceResponse.from_orm_with_tags(resource)
        return success_response(data=resource_response, message="数据资源更新成功")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新数据资源失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新数据资源失败: {str(e)}")


@router.delete("/{resource_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除数据资源
    
    Args:
        resource_id: 资源ID
        db: 数据库会话
        current_user: 当前用户
    """
    try:
        service = DataResourceService(db)
        await service.delete_resource(resource_id, current_user.id)
        return success_response(message="数据资源删除成功")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="删除数据资源失败")


@router.post("/{resource_id}/query", response_model=DataResourceQueryResponse)
async def query_resource_data(
    resource_id: int,
    query_request: DataResourceQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询数据资源数据
    
    Args:
        resource_id: 资源ID
        query_request: 查询请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        查询结果
    """
    try:
        service = DataResourceService(db)
        result = await service.query_resource_data(resource_id, query_request, current_user.id)
        return success_response(data=result, message="查询成功")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except BusinessError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="查询数据失败")


@router.get("/{resource_id}/schema", response_model=DataResourceSchemaResponse)
async def get_resource_schema(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据资源结构
    
    Args:
        resource_id: 资源ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        资源结构信息
    """
    try:
        service = DataResourceService(db)
        schema_info = await service.get_resource_schema(resource_id, current_user.id)
        return success_response(data=schema_info, message="获取结构成功")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取资源结构失败")


@router.get("/{resource_id}/preview", response_model=DataResourcePreviewResponse)
async def preview_resource_data(
    resource_id: int,
    limit: int = Query(100, ge=1, le=1000, description="限制条数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """预览数据资源数据
    
    Args:
        resource_id: 资源ID
        limit: 限制条数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        预览数据
    """
    try:
        service = DataResourceService(db)
        result = await service.preview_resource_data(resource_id, current_user.id, limit)
        return success_response(data=result, message="预览成功")
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="预览数据失败")


@router.post("/{resource_id}/permissions", response_model=DataResourcePermissionResponse, status_code=HTTP_201_CREATED)
async def grant_permission(
    resource_id: int,
    permission_data: DataResourcePermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """授予资源权限
    
    Args:
        resource_id: 资源ID
        permission_data: 权限数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        权限信息
    """
    try:
        permission_data.resource_id = resource_id
        service = DataResourceService(db)
        success = await service.grant_permission(resource_id, permission_data, current_user.id)
        
        if success:
            return success_response(message="权限授予成功")
        else:
            raise HTTPException(status_code=400, detail="权限授予失败")
            
    except AuthorizationError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="授予权限失败")


@router.get("/{resource_id}/permissions", response_model=List[DataResourcePermissionResponse])
async def get_resource_permissions(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资源权限列表
    
    Args:
        resource_id: 资源ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        权限列表
    """
    try:
        # 这里需要实现获取权限列表的逻辑
        # service = DataResourceService(db)
        # permissions = service.get_resource_permissions(resource_id, current_user.id)
        permissions = []  # 临时返回空列表
        return success_response(data=permissions, message="查询成功")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取权限列表失败")


@router.post("/{resource_id}/favorite")
async def toggle_favorite(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换收藏状态
    
    Args:
        resource_id: 资源ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        # 这里需要实现收藏功能的逻辑
        # service = DataResourceService(db)
        # is_favorited = service.toggle_favorite(resource_id, current_user.id)
        is_favorited = True  # 临时返回
        
        message = "已收藏" if is_favorited else "已取消收藏"
        return success_response(data={"is_favorited": is_favorited}, message=message)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="操作失败")


# 分类相关接口
@router.get("/categories/", response_model=List[DataResourceCategoryResponse])
async def get_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资源分类列表
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        分类列表
    """
    try:
        # 这里需要实现获取分类列表的逻辑
        categories = []  # 临时返回空列表
        return success_response(data=categories, message="查询成功")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取分类列表失败")


@router.post("/categories/", response_model=DataResourceCategoryResponse, status_code=HTTP_201_CREATED)
async def create_category(
    category_data: DataResourceCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建资源分类
    
    Args:
        category_data: 分类数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的分类
    """
    try:
        # 这里需要实现创建分类的逻辑
        # service = DataResourceService(db)
        # category = service.create_category(category_data, current_user.id)
        return success_response(message="分类创建成功")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建分类失败")


# 标签相关接口
@router.get("/tags/", response_model=List[DataResourceTagResponse])
async def get_tags(
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资源标签列表
    
    Args:
        search: 搜索关键词
        page: 页码
        page_size: 每页数量
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        标签列表
    """
    try:
        service = DataResourceService(db)
        tags, total = await service.get_tags(search=search, page=page, page_size=page_size)
        
        # 转换为响应格式
        tag_list = [
            {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color,
                "description": tag.description,
                "status": tag.status.value if tag.status else "active",
                "usage_count": tag.usage_count,
                "created_at": tag.created_at.isoformat() if tag.created_at else None,
                "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
                "created_by": tag.created_by,
                "updated_by": tag.updated_by
            }
            for tag in tags
        ]
        
        return success_response(
            data={
                "list": tag_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            message="查询成功"
        )
        
    except Exception as e:
        logger.error(f"获取标签列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签列表失败: {str(e)}")


@router.post("/tags/", response_model=DataResourceTagResponse, status_code=HTTP_201_CREATED)
async def create_tag(
    tag_data: DataResourceTagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建资源标签
    
    Args:
        tag_data: 标签数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        创建的标签
    """
    try:
        service = DataResourceService(db)
        tag = await service.create_tag(tag_data, current_user.id)
        
        tag_response = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "status": tag.status.value if hasattr(tag.status, 'value') else (tag.status or "active"),
            "usage_count": tag.usage_count,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
            "created_by": tag.created_by,
            "updated_by": tag.updated_by
        }
        
        return success_response(data=tag_response, message="标签创建成功")
        
    except BusinessError as e:
        logger.error(f"创建标签失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建标签失败: {str(e)}")


@router.get("/tags/{tag_id}", response_model=DataResourceTagResponse)
async def get_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标签详情
    
    Args:
        tag_id: 标签ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        标签详情
    """
    try:
        service = DataResourceService(db)
        tag = await service.get_tag_by_id(tag_id)
        
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        
        tag_response = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "status": tag.status.value if tag.status else "active",
            "usage_count": tag.usage_count,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
            "created_by": tag.created_by,
            "updated_by": tag.updated_by
        }
        
        return success_response(data=tag_response, message="获取标签详情成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取标签详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签详情失败: {str(e)}")


@router.put("/tags/{tag_id}", response_model=DataResourceTagResponse)
async def update_tag(
    tag_id: int,
    tag_data: DataResourceTagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新标签
    
    Args:
        tag_id: 标签ID
        tag_data: 标签更新数据
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的标签
    """
    try:
        service = DataResourceService(db)
        tag_dict = tag_data.model_dump(exclude_unset=True)
        tag = await service.update_tag(tag_id, tag_dict, current_user.id)
        
        tag_response = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "usage_count": tag.usage_count,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
            "updated_by": tag.updated_by
        }
        
        return success_response(data=tag_response, message="标签更新成功")
        
    except (BusinessError, NotFoundError) as e:
        logger.error(f"更新标签失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新标签失败: {str(e)}")


@router.delete("/tags/{tag_id}", status_code=HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除标签
    
    Args:
        tag_id: 标签ID
        db: 数据库会话
        current_user: 当前用户
    """
    try:
        service = DataResourceService(db)
        await service.delete_tag(tag_id, current_user.id)
        
    except (BusinessError, NotFoundError) as e:
        logger.error(f"删除标签失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"删除标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除标签失败: {str(e)}")


@router.post("/tags/{tag_id}/toggle-status", response_model=DataResourceTagResponse)
async def toggle_tag_status(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """切换标签状态
    
    Args:
        tag_id: 标签ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        更新后的标签
    """
    try:
        service = DataResourceService(db)
        tag = await service.toggle_tag_status(tag_id, current_user.id)
        
        tag_response = {
            "id": tag.id,
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "status": tag.status.value if tag.status else "active",
            "usage_count": tag.usage_count,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None,
            "created_by": tag.created_by,
            "updated_by": tag.updated_by
        }
        
        return success_response(data=tag_response, message="标签状态切换成功")
        
    except (BusinessError, NotFoundError) as e:
        logger.error(f"切换标签状态失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"切换标签状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"切换标签状态失败: {str(e)}")


@router.post("/tags/batch-delete", response_model=BatchOperationResponse)
async def batch_delete_tags(
    request: BatchOperationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量删除标签
    
    Args:
        request: 批量操作请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        批量操作结果
    """
    try:
        service = DataResourceService(db)
        result = await service.batch_delete_tags(request.ids, current_user.id)
        
        return success_response(
            data=result,
            message=f"批量删除完成，成功: {result['success_count']}, 失败: {result['failed_count']}"
        )
        
    except Exception as e:
        logger.error(f"批量删除标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除标签失败: {str(e)}")


@router.get("/tags/{tag_id}/usage-stats")
async def get_tag_usage_stats(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取标签使用统计
    
    Args:
        tag_id: 标签ID
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        标签使用统计
    """
    try:
        service = DataResourceService(db)
        stats = await service.get_tag_usage_stats(tag_id)
        
        return success_response(data=stats, message="获取标签使用统计成功")
        
    except (BusinessError, NotFoundError) as e:
        logger.error(f"获取标签使用统计失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取标签使用统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取标签使用统计失败: {str(e)}")


# 统计相关接口
@router.get("/statistics", response_model=DataResourceStatisticsResponse)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取数据资源统计信息
    
    Args:
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        统计信息
    """
    try:
        # 这里需要实现统计功能的逻辑
        # service = DataResourceService(db)
        # statistics = service.get_statistics(current_user.id)
        statistics = {
            "total_resources": 0,
            "doris_resources": 0,
            "es_resources": 0,
            "public_resources": 0,
            "private_resources": 0,
            "total_views": 0,
            "total_queries": 0,
            "active_users": 0,
            "category_stats": [],
            "tag_stats": [],
            "recent_activities": []
        }
        return success_response(data=statistics, message="查询成功")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取统计信息失败")


# 批量操作接口
@router.post("/batch", response_model=BatchOperationResponse)
async def batch_operation(
    operation_request: BatchOperationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """批量操作数据资源
    
    Args:
        operation_request: 操作请求
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        操作结果
    """
    try:
        # 这里需要实现批量操作的逻辑
        # service = DataResourceService(db)
        # result = service.batch_operation(operation_request, current_user.id)
        result = {
            "success_count": 0,
            "failed_count": 0,
            "success_ids": [],
            "failed_items": [],
            "message": "批量操作完成"
        }
        return success_response(data=result, message="批量操作完成")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="批量操作失败")