#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源类型 Service 层
"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.models import DataResourceType
from app.schemas.resource_type import ResourceTypeCreate, ResourceTypeUpdate
from app.core.response import error_response
from app.core.id_generator import generate_snowflake_id


class ResourceTypeService:
    """资源类型业务逻辑封装"""

    @staticmethod
    async def create_type(db: AsyncSession, data: ResourceTypeCreate) -> DataResourceType:
        # 名称重复校验（可选）
        if data.name:
            stmt = select(DataResourceType).where(DataResourceType.name == data.name)
            exists = (await db.execute(stmt)).scalar_one_or_none()
            if exists:
                raise ValueError("资源类型名称已存在")

        new_obj = DataResourceType(
            id=generate_snowflake_id(),
            name=data.name,
            describe=data.describe,
            meta=data.metadata,
        )
        db.add(new_obj)
        await db.flush()  # 获取自增或默认字段
        # 刷新对象以加载服务端默认值（例如 create_time / update_time），避免异步懒加载触发 MissingGreenlet
        await db.refresh(new_obj)
        return new_obj

    @staticmethod
    async def get_type(db: AsyncSession, type_id: str) -> Optional[DataResourceType]:
        stmt = select(DataResourceType).where(DataResourceType.id == type_id)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def update_type(db: AsyncSession, type_id: str, data: ResourceTypeUpdate) -> Optional[DataResourceType]:
        obj = await ResourceTypeService.get_type(db, type_id)
        if not obj:
            return None

        if data.name is not None:
            obj.name = data.name
        if data.describe is not None:
            obj.describe = data.describe
        if data.metadata is not None:
            obj.meta = data.metadata

        await db.flush()
        # 刷新对象以加载服务端更新的默认值（例如 update_time）
        await db.refresh(obj)
        return obj

    @staticmethod
    async def delete_type(db: AsyncSession, type_id: str) -> bool:
        obj = await ResourceTypeService.get_type(db, type_id)
        if not obj:
            return False
        await db.delete(obj)
        await db.flush()
        return True

    @staticmethod
    async def list_types(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        name: Optional[str] = None,
    ) -> Tuple[List[DataResourceType], int, int]:
        stmt = select(DataResourceType)
        if name:
            # 同时按名称和描述进行模糊匹配
            stmt = stmt.where(
                or_(
                    DataResourceType.name.like(f"%{name}%"),
                    DataResourceType.describe.like(f"%{name}%")
                )
            )

        # 排序：更新时间优先，其次创建时间
        stmt = stmt.order_by(
            desc(DataResourceType.update_time),
            desc(DataResourceType.create_time),
        )

        total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

        # 分页
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = (await db.execute(stmt)).scalars().all()
        return result, total, page