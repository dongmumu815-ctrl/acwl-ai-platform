#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型服务配置CRUD操作
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from app.models.model_service_config import ModelServiceConfig, ModelServiceProvider
from app.schemas.model_service_config import (
    ModelServiceConfigCreate,
    ModelServiceConfigUpdate,
    ModelServiceConfigForAgent
)


class ModelServiceConfigCRUD:
    """模型服务配置CRUD操作类"""
    
    async def create(
        self,
        db: AsyncSession,
        obj_in: ModelServiceConfigCreate,
        created_by: Optional[int] = None
    ) -> ModelServiceConfig:
        """
        创建模型服务配置
        
        Args:
            db: 数据库会话
            obj_in: 创建数据
            created_by: 创建者ID
            
        Returns:
            创建的模型服务配置对象
        """
        # 检查名称是否已存在
        existing = await self.get_by_name(db, obj_in.name)
        if existing:
            raise HTTPException(status_code=400, detail="配置名称已存在")
        
        # 如果设置为默认配置，先取消其他默认配置
        if obj_in.is_default:
            await self._clear_default_configs(db)
        
        # 创建新配置
        db_obj = ModelServiceConfig(
            **obj_in.dict(),
            created_by=created_by
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get(
        self,
        db: AsyncSession,
        config_id: int
    ) -> Optional[ModelServiceConfig]:
        """
        根据ID获取模型服务配置
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            
        Returns:
            模型服务配置对象或None
        """
        result = await db.execute(
            select(ModelServiceConfig)
            .options(selectinload(ModelServiceConfig.creator))
            .where(ModelServiceConfig.id == config_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[ModelServiceConfig]:
        """
        根据名称获取模型服务配置
        
        Args:
            db: 数据库会话
            name: 配置名称
            
        Returns:
            模型服务配置对象或None
        """
        result = await db.execute(
            select(ModelServiceConfig)
            .where(ModelServiceConfig.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        provider: Optional[ModelServiceProvider] = None,
        is_active: Optional[bool] = None
    ) -> tuple[List[ModelServiceConfig], int]:
        """
        获取模型服务配置列表
        
        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            search: 搜索关键词
            provider: 服务提供商
            is_active: 是否激活
            
        Returns:
            (配置列表, 总数)
        """
        # 构建查询条件
        conditions = []
        
        if search:
            conditions.append(
                or_(
                    ModelServiceConfig.name.contains(search),
                    ModelServiceConfig.display_name.contains(search),
                    ModelServiceConfig.description.contains(search)
                )
            )
        
        if provider:
            conditions.append(ModelServiceConfig.provider == provider)
        
        if is_active is not None:
            conditions.append(ModelServiceConfig.is_active == is_active)
        
        # 构建查询
        query = select(ModelServiceConfig).options(
            selectinload(ModelServiceConfig.creator)
        )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 获取总数
        count_query = select(func.count(ModelServiceConfig.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 获取数据
        query = query.order_by(
            ModelServiceConfig.is_default.desc(),
            ModelServiceConfig.provider,
            ModelServiceConfig.name
        ).offset(skip).limit(limit)
        
        result = await db.execute(query)
        configs = result.scalars().all()
        
        return list(configs), total
    
    async def update(
        self,
        db: AsyncSession,
        db_obj: ModelServiceConfig,
        obj_in: ModelServiceConfigUpdate
    ) -> ModelServiceConfig:
        """
        更新模型服务配置
        
        Args:
            db: 数据库会话
            db_obj: 数据库对象
            obj_in: 更新数据
            
        Returns:
            更新后的模型服务配置对象
            
        Raises:
            HTTPException: 当配置名称已存在时抛出400错误
        """
        # 检查名称是否重复（如果要更新名称）
        if obj_in.name and obj_in.name != db_obj.name:
            existing_config = await self.get_by_name(db, obj_in.name)
            if existing_config and existing_config.id != db_obj.id:
                raise HTTPException(
                    status_code=400,
                    detail=f"配置名称 '{obj_in.name}' 已存在"
                )
        
        # 如果设置为默认配置，先取消其他默认配置
        if obj_in.is_default:
            await self._clear_default_configs(db, exclude_id=db_obj.id)
        
        # 更新字段
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(
        self,
        db: AsyncSession,
        config_id: int
    ) -> bool:
        """
        删除模型服务配置
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            
        Returns:
            是否删除成功
            
        Raises:
            HTTPException: 当配置被Agent引用时抛出400错误
        """
        db_obj = await self.get(db, config_id)
        if not db_obj:
            return False
        
        try:
            await db.delete(db_obj)
            await db.commit()
            return True
        except IntegrityError as e:
            await db.rollback()
            # 检查是否是外键约束错误
            error_msg = str(e.orig)
            if "fk_agents_model_service_config" in error_msg or "FOREIGN KEY" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail="无法删除该模型服务配置，因为有Agent正在使用此配置。请先修改相关Agent的配置后再删除。"
                )
            else:
                # 其他数据库完整性错误
                raise HTTPException(
                    status_code=400,
                    detail="删除失败，该配置可能被其他资源引用"
                )
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"删除模型服务配置时发生错误: {str(e)}"
            )
    
    async def get_active_configs(
        self,
        db: AsyncSession
    ) -> List[ModelServiceConfig]:
        """
        获取所有激活的模型服务配置
        
        Args:
            db: 数据库会话
            
        Returns:
            激活的配置列表
        """
        result = await db.execute(
            select(ModelServiceConfig)
            .where(ModelServiceConfig.is_active == True)
            .order_by(
                ModelServiceConfig.is_default.desc(),
                ModelServiceConfig.provider,
                ModelServiceConfig.name
            )
        )
        return list(result.scalars().all())
    
    async def get_for_agents(
        self,
        db: AsyncSession
    ) -> List[ModelServiceConfigForAgent]:
        """
        获取用于Agent配置的模型服务列表
        
        Args:
            db: 数据库会话
            
        Returns:
            格式化的配置列表
        """
        configs = await self.get_active_configs(db)
        return [config.to_agent_option() for config in configs]
    
    async def get_default_config(
        self,
        db: AsyncSession
    ) -> Optional[ModelServiceConfig]:
        """
        获取默认模型服务配置
        
        Args:
            db: 数据库会话
            
        Returns:
            默认配置或None
        """
        result = await db.execute(
            select(ModelServiceConfig)
            .where(
                and_(
                    ModelServiceConfig.is_active == True,
                    ModelServiceConfig.is_default == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def get_stats(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        获取模型服务配置统计信息
        
        Args:
            db: 数据库会话
            
        Returns:
            统计信息字典
        """
        # 总数统计
        total_result = await db.execute(
            select(func.count(ModelServiceConfig.id))
        )
        total = total_result.scalar()
        
        # 激活数统计
        active_result = await db.execute(
            select(func.count(ModelServiceConfig.id))
            .where(ModelServiceConfig.is_active == True)
        )
        active = active_result.scalar()
        
        # 按提供商分组统计
        provider_result = await db.execute(
            select(
                ModelServiceConfig.provider,
                func.count(ModelServiceConfig.id)
            )
            .group_by(ModelServiceConfig.provider)
        )
        by_provider = {row[0]: row[1] for row in provider_result.fetchall()}
        
        # 默认配置
        default_config = await self.get_default_config(db)
        default_config_data = None
        if default_config:
            default_config_data = default_config.to_agent_option()
        
        return {
            "total_count": total,
            "active_count": active,
            "inactive_count": total - active,
            "provider_stats": by_provider
        }
    
    async def toggle_status(
        self,
        db: AsyncSession,
        config_id: int,
        is_active: bool
    ) -> Optional[ModelServiceConfig]:
        """
        切换配置激活状态
        
        Args:
            db: 数据库会话
            config_id: 配置ID
            is_active: 是否激活
            
        Returns:
            更新后的配置对象或None
        """
        db_obj = await self.get(db, config_id)
        if not db_obj:
            return None
        
        db_obj.is_active = is_active
        
        # 如果停用的是默认配置，需要取消默认状态
        if not is_active and db_obj.is_default:
            db_obj.is_default = False
        
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def _clear_default_configs(
        self,
        db: AsyncSession,
        exclude_id: Optional[int] = None
    ) -> None:
        """
        清除其他默认配置
        
        Args:
            db: 数据库会话
            exclude_id: 排除的配置ID
        """
        query = select(ModelServiceConfig).where(
            ModelServiceConfig.is_default == True
        )
        
        if exclude_id:
            query = query.where(ModelServiceConfig.id != exclude_id)
        
        result = await db.execute(query)
        configs = result.scalars().all()
        
        for config in configs:
            config.is_default = False
        
        await db.commit()


# 创建CRUD实例
model_service_config_crud = ModelServiceConfigCRUD()