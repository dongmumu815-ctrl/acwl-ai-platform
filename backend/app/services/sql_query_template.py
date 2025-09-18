from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.sql_query_template import SQLQueryTemplate
from app.models.datasource import Datasource
from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLQueryTemplateService:
    """
    SQL查询模板服务类
    处理SQL查询模板的业务逻辑
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    async def create_template(
        self,
        name: str,
        description: Optional[str],
        datasource_id: int,
        query: str,
        created_by: int,
        data_resource_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        is_template: bool = True
    ) -> SQLQueryTemplate:
        """
        创建SQL查询模板
        
        Args:
            name: 模板名称
            description: 模板描述
            datasource_id: 数据源ID
            query: SQL查询语句
            tags: 标签列表
            is_template: 是否为模板
            created_by: 创建者ID
            
        Returns:
            SQLQueryTemplate: 创建的模板对象
            
        Raises:
            ValueError: 当参数无效时
        """
        # 验证数据源是否存在
        datasource_stmt = select(Datasource).where(Datasource.id == datasource_id)
        datasource_result = await self.db.execute(datasource_stmt)
        datasource = datasource_result.scalar_one_or_none()
        
        if not datasource:
            raise ValueError(f"数据源ID {datasource_id} 不存在")
        
        # 创建模板对象
        template = SQLQueryTemplate(
            name=name,
            description=description,
            datasource_id=datasource_id,
            data_resource_id=data_resource_id,
            query=query,
            tags=tags or [],
            is_template=is_template,
            created_by=created_by
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        logger.info(f"创建SQL查询模板成功: {template.id} - {template.name}")
        return template
    
    async def get_templates(
        self,
        datasource_id: Optional[int] = None,
        data_resource_id: Optional[int] = None,
        created_by: Optional[int] = None,
        is_template: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SQLQueryTemplate]:
        """
        获取SQL查询模板列表
        
        Args:
            datasource_id: 数据源ID过滤
            data_resource_id: 数据资源ID过滤
            created_by: 创建者ID过滤
            is_template: 是否为模板过滤
            tags: 标签过滤
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[SQLQueryTemplate]: 模板列表
        """
        stmt = select(SQLQueryTemplate).options(
            selectinload(SQLQueryTemplate.datasource),
            selectinload(SQLQueryTemplate.creator)
        )
        
        # 添加过滤条件
        conditions = []
        
        if datasource_id is not None:
            conditions.append(SQLQueryTemplate.datasource_id == datasource_id)
        
        if data_resource_id is not None:
            conditions.append(SQLQueryTemplate.data_resource_id == data_resource_id)
        
        if created_by is not None:
            conditions.append(SQLQueryTemplate.created_by == created_by)
        
        if is_template is not None:
            conditions.append(SQLQueryTemplate.is_template == is_template)
        
        if tags:
            # 使用JSON查询匹配标签
            tag_conditions = []
            for tag in tags:
                tag_conditions.append(SQLQueryTemplate.tags.contains(tag))
            conditions.append(or_(*tag_conditions))
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 排序和分页
        stmt = stmt.order_by(desc(SQLQueryTemplate.updated_at))
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        templates = result.scalars().all()
        
        logger.info(f"获取SQL查询模板列表: {len(templates)} 条记录")
        return list(templates)
    
    async def get_template_by_id(
        self,
        template_id: int,
        user_id: Optional[int] = None
    ) -> Optional[SQLQueryTemplate]:
        """
        根据ID获取SQL查询模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID（用于权限检查）
            
        Returns:
            Optional[SQLQueryTemplate]: 模板对象或None
        """
        stmt = select(SQLQueryTemplate).options(
            selectinload(SQLQueryTemplate.datasource),
            selectinload(SQLQueryTemplate.creator)
        ).where(SQLQueryTemplate.id == template_id)
        
        if user_id is not None:
            stmt = stmt.where(SQLQueryTemplate.created_by == user_id)
        
        result = await self.db.execute(stmt)
        template = result.scalar_one_or_none()
        
        if template:
            logger.info(f"获取SQL查询模板: {template.id} - {template.name}")
        
        return template
    
    async def update_template(
        self,
        template_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        datasource_id: Optional[int] = None,
        data_resource_id: Optional[int] = None,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_template: Optional[bool] = None
    ) -> Optional[SQLQueryTemplate]:
        """
        更新SQL查询模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID（权限检查）
            name: 新的模板名称
            description: 新的模板描述
            datasource_id: 新的数据源ID
            data_resource_id: 新的数据资源ID
            query: 新的查询语句
            tags: 新的标签列表
            is_template: 是否为模板
            
        Returns:
            Optional[SQLQueryTemplate]: 更新后的模板对象或None
        """
        template = await self.get_template_by_id(template_id, user_id)
        
        if not template:
            return None
        
        # 更新字段
        if name is not None:
            template.name = name
        if description is not None:
            template.description = description
        if datasource_id is not None:
            template.datasource_id = datasource_id
        if data_resource_id is not None:
            template.data_resource_id = data_resource_id
        if query is not None:
            template.query = query
        if tags is not None:
            template.tags = tags
        if is_template is not None:
            template.is_template = is_template
        
        await self.db.commit()
        await self.db.refresh(template)
        
        logger.info(f"更新SQL查询模板: {template.id} - {template.name}")
        return template
    
    async def delete_template(
        self,
        template_id: int,
        user_id: int
    ) -> bool:
        """
        删除SQL查询模板
        
        Args:
            template_id: 模板ID
            user_id: 用户ID（权限检查）
            
        Returns:
            bool: 删除是否成功
        """
        template = await self.get_template_by_id(template_id, user_id)
        
        if not template:
            return False
        
        await self.db.delete(template)
        await self.db.commit()
        
        logger.info(f"删除SQL查询模板: {template_id}")
        return True
    
    async def search_templates(
        self,
        keyword: str,
        datasource_id: Optional[int] = None,
        created_by: Optional[int] = None,
        limit: int = 50
    ) -> List[SQLQueryTemplate]:
        """
        搜索SQL查询模板
        
        Args:
            keyword: 搜索关键词
            datasource_id: 数据源ID过滤
            created_by: 创建者ID过滤
            limit: 限制数量
            
        Returns:
            List[SQLQueryTemplate]: 搜索结果
        """
        stmt = select(SQLQueryTemplate).options(
            selectinload(SQLQueryTemplate.datasource),
            selectinload(SQLQueryTemplate.creator)
        )
        
        # 搜索条件
        search_conditions = [
            SQLQueryTemplate.name.contains(keyword),
            SQLQueryTemplate.description.contains(keyword),
            SQLQueryTemplate.query.contains(keyword)
        ]
        
        conditions = [or_(*search_conditions)]
        
        if datasource_id is not None:
            conditions.append(SQLQueryTemplate.datasource_id == datasource_id)
        
        if created_by is not None:
            conditions.append(SQLQueryTemplate.created_by == created_by)
        
        stmt = stmt.where(and_(*conditions))
        stmt = stmt.order_by(desc(SQLQueryTemplate.updated_at))
        stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        templates = result.scalars().all()
        
        logger.info(f"搜索SQL查询模板: 关键词'{keyword}', 找到 {len(templates)} 条记录")
        return list(templates)