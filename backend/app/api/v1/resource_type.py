#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源类型管理 API 路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.resource_type import (
    ResourceTypeCreate,
    ResourceTypeUpdate,
    ResourceTypeResponse,
)
from app.services.resource_type_service import ResourceTypeService
from app.core.response import success_response, paginated_response, error_response

router = APIRouter(prefix="/data-resource-types", tags=["资源类型管理"]) 


@router.post("/create")
async def create_resource_type(payload: ResourceTypeCreate, db: AsyncSession = Depends(get_db)):
    try:
        obj = await ResourceTypeService.create_type(db, payload)
        # 提交事务，确保数据持久化，并避免后续属性访问触发异步加载问题
        await db.commit()
        return success_response(
            data=ResourceTypeResponse.model_validate({
                "id": obj.id,
                "name": obj.name,
                "describe": obj.describe,
                "metadata": obj.meta,
                "create_time": obj.create_time,
                "update_time": obj.update_time,
            })
        )
    except ValueError as e:
        return error_response(message=str(e))


# 将 /list 放在动态路由 /{type_id} 之前，避免被错误匹配
@router.get("/list")
async def list_resource_types(
    page: int = 1,
    page_size: int = 10,
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    items, total, current_page = await ResourceTypeService.list_types(
        db=db,
        page=page,
        page_size=page_size,
        name=name,
    )
    # 将 ORM 对象转换为可序列化的 dict 列表
    payload_items = [
        {
            "id": obj.id,
            "name": obj.name,
            "describe": obj.describe,
            "metadata": obj.meta,
            "create_time": obj.create_time,
            "update_time": obj.update_time,
        }
        for obj in items
    ]

    return paginated_response(
        items=payload_items,
        total=total,
        page=current_page,
        size=page_size,
    )


@router.get("/{type_id}")
async def get_resource_type(type_id: str, db: AsyncSession = Depends(get_db)):
    obj = await ResourceTypeService.get_type(db, type_id)
    if not obj:
        return error_response(message="资源类型不存在")
    return success_response(
        data=ResourceTypeResponse.model_validate({
            "id": obj.id,
            "name": obj.name,
            "describe": obj.describe,
            "metadata": obj.meta,
            "create_time": obj.create_time,
            "update_time": obj.update_time,
        })
    )


@router.put("/{type_id}")
async def update_resource_type(type_id: str, payload: ResourceTypeUpdate, db: AsyncSession = Depends(get_db)):
    obj = await ResourceTypeService.update_type(db, type_id, payload)
    if not obj:
        return error_response(message="资源类型不存在")
    # 提交事务，确保更新生效，并加载 server 默认的 update_time
    await db.commit()
    return success_response(
        data=ResourceTypeResponse.model_validate({
            "id": obj.id,
            "name": obj.name,
            "describe": obj.describe,
            "metadata": obj.meta,
            "create_time": obj.create_time,
            "update_time": obj.update_time,
        })
    )


@router.delete("/{type_id}")
async def delete_resource_type(type_id: str, db: AsyncSession = Depends(get_db)):
    ok = await ResourceTypeService.delete_type(db, type_id)
    if not ok:
        return error_response(message="资源类型不存在")
    # 提交事务，确保删除生效
    await db.commit()
    return success_response(message="删除成功")