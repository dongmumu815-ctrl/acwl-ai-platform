#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境管理CRUD操作
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from fastapi import HTTPException

from app.models.environment import Environment
from app.schemas.environment import EnvironmentCreate, EnvironmentUpdate


class EnvironmentCRUD:
    """环境CRUD操作类"""

    async def create(
        self,
        db: AsyncSession,
        obj_in: EnvironmentCreate,
        created_by: Optional[int] = None
    ) -> Environment:
        # 检查名称是否已存在
        existing = await self.get_by_name(db, obj_in.name)
        if existing:
            raise HTTPException(status_code=400, detail="环境名称已存在")

        db_obj = Environment(
            **obj_in.dict(),
            created_by=created_by
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, env_id: int) -> Optional[Environment]:
        result = await db.execute(
            select(Environment).where(Environment.id == env_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Environment]:
        result = await db.execute(
            select(Environment).where(Environment.name == name)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> tuple[List[Environment], int]:
        conditions = []
        if search:
            conditions.append(
                or_(
                    Environment.name.contains(search),
                    Environment.description.contains(search)
                )
            )

        query = select(Environment)
        if conditions:
            query = query.where(and_(*conditions))

        count_query = select(func.count(Environment.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Environment.updated_at.desc(), Environment.name).offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()
        return list(items), total

    async def update(self, db: AsyncSession, db_obj: Environment, obj_in: EnvironmentUpdate) -> Environment:
        # 检查名称重复
        if obj_in.name and obj_in.name != db_obj.name:
            existing = await self.get_by_name(db, obj_in.name)
            if existing and existing.id != db_obj.id:
                raise HTTPException(status_code=400, detail=f"环境名称 '{obj_in.name}' 已存在")

        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, env_id: int) -> bool:
        db_obj = await self.get(db, env_id)
        if not db_obj:
            return False
        await db.delete(db_obj)
        await db.commit()
        return True


environment_crud = EnvironmentCRUD()