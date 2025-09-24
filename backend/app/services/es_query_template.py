#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ES查询模板服务
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.es_query_template import ESQueryTemplate
from app.models.user import User
from app.models.datasource import Datasource
from app.core.logger import get_logger

logger = get_logger(__name__)


class ESQueryTemplateService:
    """ES查询模板服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_template(
        self,
        name: str,
        description: Optional[str],
        datasource_id: int,
        data_resource_id: Optional[int],
        indices: List[str],
        query: Dict[str, Any],
        tags: Optional[List[str]],
        is_template: bool,
        created_by: int,
        condition_lock_types: Optional[Dict[str, str]] = None,
        condition_ranges: Optional[Dict[str, Dict[str, Any]]] = None,
        allowed_operators: Optional[Dict[str, List[str]]] = None
    ) -> ESQueryTemplate:
        """
        创建ES查询模板
        
        Args:
            name: 模板名称
            description: 模板描述
            datasource_id: 数据源ID
            data_resource_id: 数据资源ID
            indices: ES索引列表
            query: 查询DSL或可视化查询配置
            tags: 标签列表
            is_template: 是否为模板
            created_by: 创建者用户ID
            condition_lock_types: 条件锁定类型配置
            condition_ranges: 条件值范围限制配置
            allowed_operators: 允许的操作符配置
            
        Returns:
            创建的ES查询模板对象
        """
        try:
            # 添加调试日志，确认参数传递
            logger.info(f"创建ES查询模板 - 参数信息: name={name}, datasource_id={datasource_id}, data_resource_id={data_resource_id}, created_by={created_by}")
            
            # 验证数据源是否存在
            datasource_stmt = select(Datasource).where(Datasource.id == datasource_id)
            datasource_result = await self.db.execute(datasource_stmt)
            datasource = datasource_result.scalar_one_or_none()
            
            if not datasource:
                raise ValueError(f"数据源ID {datasource_id} 不存在")
            
            # 创建模板对象
            template = ESQueryTemplate(
                name=name,
                description=description,
                datasource_id=datasource_id,
                data_resource_id=data_resource_id,
                indices=indices or [],
                query=query,
                tags=tags or [],
                is_template=is_template,
                created_by=created_by,
                condition_lock_types=condition_lock_types,
                condition_ranges=condition_ranges,
                allowed_operators=allowed_operators
            )
            
            # 添加调试日志，确认模板对象的data_resource_id值
            logger.info(f"创建的模板对象 - data_resource_id: {template.data_resource_id}")
            
            self.db.add(template)
            await self.db.commit()
            await self.db.refresh(template)
            
            # 添加调试日志，确认保存后的data_resource_id值
            logger.info(f"ES查询模板创建成功: {template.id} - {template.name}, 保存后的data_resource_id: {template.data_resource_id}")
            return template
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建ES查询模板失败: {str(e)}")
            raise
    
    async def get_templates(
        self,
        datasource_id: Optional[int] = None,
        data_resource_id: Optional[int] = None,
        created_by: Optional[int] = None,
        is_template: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        indices: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ESQueryTemplate]:
        """
        获取ES查询模板列表
        
        Args:
            datasource_id: 数据源ID过滤
            data_resource_id: 数据资源ID过滤
            created_by: 创建者ID过滤
            is_template: 是否为模板过滤
            tags: 标签过滤
            indices: 索引名称列表过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            ES查询模板列表
        """
        try:
            # 构建查询条件
            conditions = []
            
            if datasource_id is not None:
                conditions.append(ESQueryTemplate.datasource_id == datasource_id)
            
            if data_resource_id is not None:
                conditions.append(ESQueryTemplate.data_resource_id == data_resource_id)
            
            if created_by is not None:
                conditions.append(ESQueryTemplate.created_by == created_by)
            
            if is_template is not None:
                conditions.append(ESQueryTemplate.is_template == is_template)
            
            # 标签过滤（包含任一标签）
            if tags:
                tag_conditions = []
                for tag in tags:
                    tag_conditions.append(ESQueryTemplate.tags.contains([tag]))
                conditions.append(or_(*tag_conditions))
            
            # 索引过滤（模板的索引列表包含任一指定索引）
            if indices:
                index_conditions = []
                for index in indices:
                    index_conditions.append(ESQueryTemplate.indices.contains([index]))
                conditions.append(or_(*index_conditions))
            
            # 构建查询语句
            stmt = (
                select(ESQueryTemplate)
                .options(
                    selectinload(ESQueryTemplate.creator),
                    selectinload(ESQueryTemplate.datasource)
                )
                .where(and_(*conditions) if conditions else True)
                .order_by(ESQueryTemplate.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            
            result = await self.db.execute(stmt)
            templates = result.scalars().all()
            
            logger.info(f"获取ES查询模板列表成功，共 {len(templates)} 条")
            return list(templates)
            
        except Exception as e:
            logger.error(f"获取ES查询模板列表失败: {str(e)}")
            raise
    
    async def get_template_by_id(self, template_id: int) -> Optional[ESQueryTemplate]:
        """
        根据ID获取ES查询模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            ES查询模板对象或None
        """
        try:
            stmt = (
                select(ESQueryTemplate)
                .options(
                    selectinload(ESQueryTemplate.creator),
                    selectinload(ESQueryTemplate.datasource)
                )
                .where(ESQueryTemplate.id == template_id)
            )
            
            result = await self.db.execute(stmt)
            template = result.scalar_one_or_none()
            
            if template:
                logger.info(f"获取ES查询模板成功: {template.id} - {template.name}")
            else:
                logger.warning(f"ES查询模板不存在: {template_id}")
            
            return template
            
        except Exception as e:
            logger.error(f"获取ES查询模板失败: {str(e)}")
            raise
    
    async def update_template(
        self,
        template_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        data_resource_id: Optional[int] = None,
        indices: Optional[List[str]] = None,
        query: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[ESQueryTemplate]:
        """
        更新ES查询模板
        
        Args:
            template_id: 模板ID
            name: 新的模板名称
            description: 新的模板描述
            data_resource_id: 新的数据资源ID
            indices: 新的索引列表
            query: 新的查询配置
            tags: 新的标签列表
            
        Returns:
            更新后的ES查询模板对象或None
        """
        try:
            template = await self.get_template_by_id(template_id)
            if not template:
                return None
            
            # 更新字段
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if data_resource_id is not None:
                template.data_resource_id = data_resource_id
            if indices is not None:
                template.indices = indices
            if query is not None:
                template.query = query
            if tags is not None:
                template.tags = tags
            
            await self.db.commit()
            await self.db.refresh(template)
            
            logger.info(f"ES查询模板更新成功: {template.id} - {template.name}")
            return template
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新ES查询模板失败: {str(e)}")
            raise
    
    async def delete_template(self, template_id: int) -> bool:
        """
        删除ES查询模板
        
        Args:
            template_id: 模板ID
            
        Returns:
            是否删除成功
        """
        try:
            template = await self.get_template_by_id(template_id)
            if not template:
                logger.warning(f"要删除的ES查询模板不存在: {template_id}")
                return False
            
            await self.db.delete(template)
            await self.db.commit()
            
            logger.info(f"ES查询模板删除成功: {template_id} - {template.name}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除ES查询模板失败: {str(e)}")
            raise
    
    async def search_templates(
        self,
        keyword: str,
        datasource_id: Optional[int] = None,
        created_by: Optional[int] = None,
        limit: int = 50
    ) -> List[ESQueryTemplate]:
        """
        搜索ES查询模板
        
        Args:
            keyword: 搜索关键词（在名称和描述中搜索）
            datasource_id: 数据源ID过滤
            created_by: 创建者ID过滤
            limit: 限制数量
            
        Returns:
            匹配的ES查询模板列表
        """
        try:
            # 构建搜索条件
            conditions = [
                or_(
                    ESQueryTemplate.name.ilike(f"%{keyword}%"),
                    ESQueryTemplate.description.ilike(f"%{keyword}%")
                )
            ]
            
            if datasource_id is not None:
                conditions.append(ESQueryTemplate.datasource_id == datasource_id)
            
            if created_by is not None:
                conditions.append(ESQueryTemplate.created_by == created_by)
            
            # 构建查询语句
            stmt = (
                select(ESQueryTemplate)
                .options(
                    selectinload(ESQueryTemplate.creator),
                    selectinload(ESQueryTemplate.datasource)
                )
                .where(and_(*conditions))
                .order_by(ESQueryTemplate.created_at.desc())
                .limit(limit)
            )
            
            result = await self.db.execute(stmt)
            templates = result.scalars().all()
            
            logger.info(f"搜索ES查询模板成功，关键词: {keyword}，共 {len(templates)} 条")
            return list(templates)
            
        except Exception as e:
            logger.error(f"搜索ES查询模板失败: {str(e)}")
            raise