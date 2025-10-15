#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据资源中心服务层
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func, desc, asc, text, select
from datetime import datetime, timedelta
import logging

from app.models.data_resource import (
    DataResource,
    DataResourceCategory,
    DataResourcePermission,
    DataResourceAccessLog,
    DataResourceFavorite,
    DataResourceQueryHistory,
    DataResourceTag,
    DataResourceTagRelation,
    ResourceType,
    ResourceStatus,
    PermissionType,
    AccessType,
    AccessStatus
)
from app.models.datasource import Datasource
from app.schemas.data_resource import (
    DataResourceCreate,
    DataResourceUpdate,
    DataResourceSearchRequest,
    DataResourceQueryRequest,
    DataResourcePermissionCreate,
    DataResourceCategoryCreate,
    DataResourceTagCreate
)
from app.core.exceptions import (
    BusinessError,
    AuthorizationError,
    NotFoundError
)
from app.services.datasource import DatasourceService
from app.utils.query_executor import QueryExecutor
from app.models.user import User

logger = logging.getLogger(__name__)


class DataResourceService:
    """数据资源服务类"""
    
    def __init__(self, db: AsyncSession):
        """初始化数据资源服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.datasource_service = DatasourceService(db)
        self.query_executor = QueryExecutor()
    
    async def create_resource(self, resource_data: DataResourceCreate, user_id: int) -> DataResource:
        """创建数据资源
        
        Args:
            resource_data: 资源创建数据
            user_id: 用户ID
            
        Returns:
            创建的数据资源
            
        Raises:
            BusinessException: 业务异常
        """
        try:
            logger.info(f"开始创建数据资源，用户ID: {user_id}, 资源名称: {resource_data.name}")
            
            # 验证数据源是否存在
            logger.info(f"验证数据源，ID: {resource_data.datasource_id}")
            datasource = await self.datasource_service.get_datasource(resource_data.datasource_id)
            if not datasource:
                logger.error(f"数据源不存在，ID: {resource_data.datasource_id}")
                raise BusinessError("数据源不存在")
            logger.info(f"数据源验证通过: {datasource.name}")
            
            # 验证资源类型与数据源类型匹配
            logger.info(f"验证资源类型: {resource_data.resource_type}")
            if resource_data.resource_type == ResourceType.DORIS_TABLE:
                if not resource_data.database_name or not resource_data.table_name:
                    logger.error(f"Doris表资源缺少必要参数，database_name: {resource_data.database_name}, table_name: {resource_data.table_name}")
                    raise BusinessError("Doris表资源必须指定数据库名和表名")
            elif resource_data.resource_type == ResourceType.ELASTICSEARCH_INDEX:
                if not resource_data.index_name:
                    logger.error(f"Elasticsearch资源缺少索引名")
                    raise BusinessError("Elasticsearch资源必须指定索引名")
            logger.info("资源类型验证通过")
            
            # 检查资源名称是否重复
            logger.info(f"检查资源名称是否重复: {resource_data.name}")
            existing_query = select(DataResource).where(
                DataResource.name == resource_data.name
            )
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()
            if existing:
                logger.error(f"资源名称已存在: {resource_data.name}")
                raise BusinessError("资源名称已存在")
            logger.info("资源名称检查通过")
            
            # 获取表结构信息
            logger.info("开始获取表结构信息")
            schema_info = self._get_resource_schema(datasource, resource_data)
            logger.info(f"表结构信息获取完成，列数: {len(schema_info.get('columns', []))}")
            
            # 创建资源
            logger.info("开始创建资源对象")
            resource_dict = resource_data.model_dump()
            resource_dict.update({
                "schema_info": schema_info,
                "created_by": user_id
            })
            resource = DataResource(**resource_dict)
            logger.info(f"资源对象创建完成: {resource.name}")
            
            logger.info("添加资源到数据库会话")
            self.db.add(resource)
            logger.info("执行flush获取资源ID")
            await self.db.flush()  # 获取resource.id但不提交事务
            logger.info(f"资源ID获取成功: {resource.id}")
            
            # 给创建者分配管理员权限
            logger.info(f"开始分配管理员权限，资源ID: {resource.id}, 用户ID: {user_id}")
            permission_granted = await self._grant_permission(
                resource.id,
                user_id,
                PermissionType.ADMIN,
                user_id
            )
            
            if not permission_granted:
                logger.error("分配管理员权限失败")
                raise BusinessError("分配管理员权限失败")
            logger.info("管理员权限分配成功")
            
            # 统一提交事务
            logger.info("开始提交事务")
            await self.db.commit()
            logger.info("事务提交成功")
            
            # 预加载关联数据
            await self.db.refresh(resource, ['datasource', 'category'])
            
            # 重新查询资源以获取完整数据
            result = await self.db.execute(
                select(DataResource)
                .options(
                    selectinload(DataResource.category),
                    selectinload(DataResource.datasource)
                )
                .where(DataResource.id == resource.id)
            )
            fresh_resource = result.scalar_one()
            
            logger.info(f"用户 {user_id} 创建了数据资源 {fresh_resource.id}")
            return fresh_resource
            
        except BusinessError:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建数据资源失败: {str(e)}")
            raise BusinessError(f"创建数据资源失败: {str(e)}")
    
    async def get_resource_by_id(self, resource_id: int, user_id: int) -> Optional[DataResource]:
        """根据ID获取数据资源
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            
        Returns:
            数据资源或None
        """
        query = select(DataResource).options(
            selectinload(DataResource.category).selectinload(DataResourceCategory.children),
            selectinload(DataResource.datasource),
            selectinload(DataResource.tag_relations).selectinload(DataResourceTagRelation.tag)
        ).where(DataResource.id == resource_id)
        
        result = await self.db.execute(query)
        resource = result.scalar_one_or_none()
        
        if not resource:
            return None
        
        # 检查权限
        if not await self._check_resource_permission(resource_id, user_id, PermissionType.READ):
            if not resource.is_public:
                return None
        
        return resource
    
    async def update_resource(self, resource_id: int, resource_data: DataResourceUpdate, user_id: int) -> DataResource:
        """更新数据资源
        
        Args:
            resource_id: 资源ID
            resource_data: 更新数据
            user_id: 用户ID
            
        Returns:
            更新后的数据资源
            
        Raises:
            ResourceNotFoundException: 资源不存在
            PermissionDeniedException: 权限不足
        """
        # 使用异步查询
        result = await self.db.execute(
            select(DataResource).where(DataResource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        
        if not resource:
            raise NotFoundError("数据资源不存在")
        
        # 检查权限
        if not await self._check_resource_permission(resource_id, user_id, PermissionType.WRITE):
            raise AuthorizationError("没有权限修改此资源")
        
        try:
            # 更新字段
            update_data = resource_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                # 特殊处理 tags 字段
                if field == 'tags':
                    if value == 'null' or value == 'None':
                        value = None
                    elif isinstance(value, str) and value.lower() == 'null':
                        value = None
                setattr(resource, field, value)
            
            resource.updated_by = user_id
            
            await self.db.commit()
            logger.info(f"用户 {user_id} 更新了数据资源 {resource_id}")
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新数据资源失败: {str(e)}")
            raise BusinessError(f"更新数据资源失败: {str(e)}")
        
        # 重新查询资源以预加载关联对象，避免 MissingGreenlet 错误
        result = await self.db.execute(
            select(DataResource)
            .options(
                selectinload(DataResource.category).selectinload(DataResourceCategory.children),
                selectinload(DataResource.datasource),
                selectinload(DataResource.tag_relations).selectinload(DataResourceTagRelation.tag)
            )
            .where(DataResource.id == resource_id)
        )
        updated_resource = result.scalar_one()
        
        return updated_resource
    
    async def delete_resource(self, resource_id: int, user_id: int) -> bool:
        """删除数据资源
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
            
        Raises:
            ResourceNotFoundException: 资源不存在
            PermissionDeniedException: 权限不足
        """
        # 使用异步查询
        result = await self.db.execute(
            select(DataResource).where(DataResource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        
        if not resource:
            raise NotFoundError("数据资源不存在")
        
        # 检查权限
        if not await self._check_resource_permission(resource_id, user_id, PermissionType.ADMIN):
            raise AuthorizationError("没有权限删除此资源")
        
        try:
            await self.db.delete(resource)
            await self.db.commit()
            
            logger.info(f"用户 {user_id} 删除了数据资源 {resource_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除数据资源失败: {str(e)}")
            raise BusinessError(f"删除数据资源失败: {str(e)}")
    
    async def search_resources(self, search_request: DataResourceSearchRequest, user_id: int) -> Tuple[List[DataResource], int]:
        """搜索数据资源
        
        Args:
            search_request: 搜索请求
            user_id: 用户ID
            
        Returns:
            资源列表和总数
        """
        query = select(DataResource).options(
            selectinload(DataResource.category).selectinload(DataResourceCategory.children),
            selectinload(DataResource.datasource),
            selectinload(DataResource.tag_relations).selectinload(DataResourceTagRelation.tag)
        )
        
        # 权限过滤：只显示有权限的资源或公开资源
        permission_subquery = select(DataResourcePermission.resource_id).filter(
            and_(
                DataResourcePermission.user_id == user_id,
                DataResourcePermission.is_active == True,
                or_(
                    DataResourcePermission.expires_at.is_(None),
                    DataResourcePermission.expires_at > datetime.now()
                )
            )
        )
        permission_filter = or_(
            DataResource.is_public == True,
            DataResource.id.in_(permission_subquery)
        )
        query = query.where(permission_filter)
        
        # 关键词搜索
        if search_request.keyword:
            keyword_filter = or_(
                DataResource.name.ilike(f"%{search_request.keyword}%"),
                DataResource.display_name.ilike(f"%{search_request.keyword}%"),
                DataResource.description.ilike(f"%{search_request.keyword}%")
            )
            query = query.where(keyword_filter)
        
        # 分类过滤
        if search_request.category_id:
            query = query.where(DataResource.category_id == search_request.category_id)
        
        # 资源类型过滤
        if search_request.resource_type:
            query = query.where(DataResource.resource_type == search_request.resource_type)
        
        # 数据源过滤
        if search_request.datasource_id:
            query = query.where(DataResource.datasource_id == search_request.datasource_id)
        
        # 状态过滤
        if search_request.status:
            query = query.where(DataResource.status == search_request.status)
        
        # 创建者过滤
        if search_request.created_by:
            query = query.where(DataResource.created_by == search_request.created_by)
        
        # 日期范围过滤
        if search_request.date_from:
            query = query.where(DataResource.created_at >= search_request.date_from)
        if search_request.date_to:
            query = query.where(DataResource.created_at <= search_request.date_to)
        
        # 标签过滤
        if search_request.tags:
            tag_subquery = select(DataResourceTagRelation.resource_id).join(
                DataResourceTag
            ).where(
                DataResourceTag.name.in_(search_request.tags)
            )
            query = query.where(DataResource.id.in_(tag_subquery))
        
        # 排序
        if search_request.sort_by:
            sort_column = getattr(DataResource, search_request.sort_by, None)
            if sort_column:
                if search_request.sort_order == "asc":
                    query = query.order_by(asc(sort_column))
                else:
                    query = query.order_by(desc(sort_column))
        
        # 获取总数
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页
        offset = (search_request.page - 1) * search_request.size
        query = query.offset(offset).limit(search_request.size)
        
        # 执行查询
        result = await self.db.execute(query)
        resources = result.scalars().all()
        
        return resources, total
    
    async def query_resource_data(self, resource_id: int, query_request: DataResourceQueryRequest, user_id: int) -> Dict[str, Any]:
        """查询数据资源数据
        
        Args:
            resource_id: 资源ID
            query_request: 查询请求
            user_id: 用户ID
            
        Returns:
            查询结果
            
        Raises:
            ResourceNotFoundException: 资源不存在
            PermissionDeniedException: 权限不足
        """
        # 使用异步查询
        result = await self.db.execute(
            select(DataResource).where(DataResource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        
        if not resource:
            raise NotFoundError("数据资源不存在")
        
        # 检查权限
        if not await self._check_resource_permission(resource_id, user_id, PermissionType.READ):
            if not resource.is_public:
                raise AuthorizationError("没有权限访问此资源")
        
        start_time = datetime.now()
        
        try:
            # 执行查询
            result = self.query_executor.execute_query(
                resource.datasource,
                query_request.sql,
                query_request.params,
                query_request.limit,
                query_request.offset
            )
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 记录访问日志
            await self._log_access(
                resource_id,
                user_id,
                AccessType.QUERY,
                query_request.sql,
                query_request.params,
                len(result["data"]),
                execution_time,
                AccessStatus.SUCCESS
            )
            
            # 更新统计信息
            resource.query_count += 1
            resource.last_accessed_at = datetime.now()
            await self.db.commit()
            
            # 保存查询历史
            if query_request.save_query:
                await self._save_query_history(
                    resource_id,
                    user_id,
                    query_request.query_name,
                    query_request.sql,
                    query_request.params,
                    len(result["data"]),
                    execution_time
                )
            
            result["execution_time"] = execution_time
            return result
            
        except Exception as e:
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # 记录错误日志
            await self._log_access(
                resource_id,
                user_id,
                AccessType.QUERY,
                query_request.sql,
                query_request.params,
                0,
                execution_time,
                AccessStatus.FAILED,
                str(e)
            )
            
            logger.error(f"查询数据资源 {resource_id} 失败: {str(e)}")
            raise BusinessError(f"查询失败: {str(e)}")
    
    async def get_resource_schema(self, resource_id: int, user_id: int) -> Dict[str, Any]:
        """获取数据资源结构
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            
        Returns:
            资源结构信息
        """
        # 使用异步查询
        result = await self.db.execute(
            select(DataResource).where(DataResource.id == resource_id)
        )
        resource = result.scalar_one_or_none()
        
        if not resource:
            raise NotFoundError("数据资源不存在")
        
        # 检查权限
        if not await self._check_resource_permission(resource_id, user_id, PermissionType.READ):
            if not resource.is_public:
                raise AuthorizationError("没有权限访问此资源")
        
        try:
            # 记录访问日志
            await self._log_access(
                resource_id,
                user_id,
                AccessType.SCHEMA,
                None,
                None,
                0,
                0,
                AccessStatus.SUCCESS
            )
            
            return resource.schema_info or {}
            
        except Exception as e:
            logger.error(f"获取资源结构失败: {str(e)}")
            raise BusinessError(f"获取资源结构失败: {str(e)}")
    
    async def preview_resource_data(self, resource_id: int, user_id: int, limit: int = 100) -> Dict[str, Any]:
        """预览数据资源数据
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            limit: 限制条数
            
        Returns:
            预览数据
        """
        resource = self.db.query(DataResource).filter(DataResource.id == resource_id).first()
        if not resource:
            raise NotFoundError("数据资源不存在")
        
        # 检查权限
        if not self._check_resource_permission(resource_id, user_id, PermissionType.READ):
            if not resource.is_public:
                raise AuthorizationError("没有权限访问此资源")
        
        try:
            # 构建预览SQL
            if resource.resource_type == ResourceType.DORIS_TABLE:
                sql = f"SELECT * FROM {resource.database_name}.{resource.table_name} LIMIT {limit}"
            else:
                # Elasticsearch预览逻辑
                sql = f"SELECT * FROM {resource.index_name} LIMIT {limit}"
            
            result = self.query_executor.execute_query(
                resource.datasource,
                sql,
                None,
                limit,
                0
            )
            
            # 记录访问日志
            await self._log_access(
                resource_id,
                user_id,
                AccessType.PREVIEW,
                sql,
                None,
                len(result["data"]),
                0,
                AccessStatus.SUCCESS
            )
            
            # 更新统计信息
            resource.view_count += 1
            resource.last_accessed_at = datetime.now()
            await self.db.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"预览数据资源 {resource_id} 失败: {str(e)}")
            raise BusinessError(f"预览失败: {str(e)}")
    
    async def grant_permission(self, resource_id: int, permission_data: DataResourcePermissionCreate, granter_id: int) -> bool:
        """授予权限
        
        Args:
            resource_id: 资源ID
            permission_data: 权限数据
            granter_id: 授权者ID
            
        Returns:
            是否成功
        """
        # 检查授权者权限
        if not await self._check_resource_permission(resource_id, granter_id, PermissionType.ADMIN):
            raise AuthorizationError("没有权限授予此资源的权限")
        
        return await self._grant_permission(
            resource_id,
            permission_data.user_id,
            permission_data.permission_type,
            granter_id,
            permission_data.expires_at,
            permission_data.notes
        )
    
    async def _check_resource_permission(self, resource_id: int, user_id: int, required_permission: PermissionType) -> bool:
        """检查资源权限
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            required_permission: 所需权限
            
        Returns:
            是否有权限
        """
        # 系统管理员直接拥有所有权限
        try:
            user_result = await self.db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user and getattr(user, "is_admin", False):
                return True
        except Exception:
            pass

        # 资源创建者默认拥有管理权限
        try:
            owner_result = await self.db.execute(
                select(DataResource.created_by).where(DataResource.id == resource_id)
            )
            owner_id = owner_result.scalar_one_or_none()
            if owner_id and owner_id == user_id:
                return True
        except Exception:
            pass
        query = select(DataResourcePermission).where(
            and_(
                DataResourcePermission.resource_id == resource_id,
                DataResourcePermission.user_id == user_id,
                DataResourcePermission.is_active == True,
                or_(
                    DataResourcePermission.expires_at.is_(None),
                    DataResourcePermission.expires_at > datetime.now()
                )
            )
        )
        
        result = await self.db.execute(query)
        permission = result.scalar_one_or_none()
        
        if not permission:
            return False
        
        # 权限级别检查
        permission_levels = {
            PermissionType.READ: 1,
            PermissionType.WRITE: 2,
            PermissionType.ADMIN: 3
        }
        
        return permission_levels.get(permission.permission_type, 0) >= permission_levels.get(required_permission, 0)
    
    async def _grant_permission(self, resource_id: int, user_id: int, permission_type: PermissionType, 
                        granter_id: int, expires_at: Optional[datetime] = None, notes: Optional[str] = None) -> bool:
        """授予权限
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            permission_type: 权限类型
            granter_id: 授权者ID
            expires_at: 过期时间
            notes: 备注
            
        Returns:
            是否成功
        """
        try:
            # 检查是否已有权限
            existing_query = select(DataResourcePermission).where(
                and_(
                    DataResourcePermission.resource_id == resource_id,
                    DataResourcePermission.user_id == user_id,
                    DataResourcePermission.is_active == True
                )
            )
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()
            
            if existing:
                # 更新现有权限
                existing.permission_type = permission_type
                existing.expires_at = expires_at
                existing.notes = notes
                existing.granted_by = granter_id
                existing.granted_at = datetime.now()
            else:
                # 创建新权限
                permission = DataResourcePermission(
                    resource_id=resource_id,
                    user_id=user_id,
                    permission_type=permission_type,
                    granted_by=granter_id,
                    expires_at=expires_at,
                    notes=notes
                )
                self.db.add(permission)
            
            # 不在这里提交事务，由外层方法统一管理
            return True
            
        except Exception as e:
            logger.error(f"授予权限失败: {str(e)}")
            return False
    
    async def _log_access(self, resource_id: int, user_id: int, access_type: AccessType,
                   query_sql: Optional[str] = None, query_params: Optional[Dict] = None,
                   result_count: Optional[int] = None, execution_time: Optional[int] = None,
                   status: AccessStatus = AccessStatus.SUCCESS, error_message: Optional[str] = None):
        """记录访问日志
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            access_type: 访问类型
            query_sql: 查询SQL
            query_params: 查询参数
            result_count: 结果数量
            execution_time: 执行时间
            status: 状态
            error_message: 错误信息
        """
        try:
            log = DataResourceAccessLog(
                resource_id=resource_id,
                user_id=user_id,
                access_type=access_type,
                query_sql=query_sql,
                query_params=query_params,
                result_count=result_count,
                execution_time=execution_time,
                status=status,
                error_message=error_message
            )
            self.db.add(log)
            await self.db.commit()
        except Exception as e:
            logger.error(f"记录访问日志失败: {str(e)}")
    
    async def _save_query_history(self, resource_id: int, user_id: int, query_name: Optional[str],
                           query_sql: str, query_params: Optional[Dict], result_count: int, execution_time: int):
        """保存查询历史
        
        Args:
            resource_id: 资源ID
            user_id: 用户ID
            query_name: 查询名称
            query_sql: 查询SQL
            query_params: 查询参数
            result_count: 结果数量
            execution_time: 执行时间
        """
        try:
            history = DataResourceQueryHistory(
                resource_id=resource_id,
                user_id=user_id,
                query_name=query_name,
                query_sql=query_sql,
                query_params=query_params,
                result_count=result_count,
                execution_time=execution_time,
                is_saved=True
            )
            self.db.add(history)
            await self.db.commit()
        except Exception as e:
            logger.error(f"保存查询历史失败: {str(e)}")
    
    def _get_resource_schema(self, datasource: Datasource, resource_data: DataResourceCreate) -> Dict[str, Any]:
        """获取资源结构信息
        
        Args:
            datasource: 数据源
            resource_data: 资源数据
            
        Returns:
            结构信息
        """
        try:
            if resource_data.resource_type == ResourceType.DORIS_TABLE:
                # 获取Doris表结构
                sql = f"DESCRIBE {resource_data.database_name}.{resource_data.table_name}"
            else:
                # 获取Elasticsearch索引结构
                sql = f"DESCRIBE {resource_data.index_name}"
            
            result = self.query_executor.execute_query(datasource, sql)
            return {
                "columns": result.get("columns", []),
                "table_name": resource_data.table_name or resource_data.index_name,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"获取资源结构失败: {str(e)}")
            return {}
    
    # ==================== 标签管理相关方法 ====================
    
    async def get_tags(self, search: Optional[str] = None, page: int = 1, page_size: int = 20) -> Tuple[List[DataResourceTag], int]:
        """获取标签列表
        
        Args:
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            标签列表和总数
        """
        try:
            logger.info(f"获取标签列表，搜索: {search}, 页码: {page}, 每页: {page_size}")
            
            # 构建查询
            query = select(DataResourceTag)
            count_query = select(func.count(DataResourceTag.id))
            
            # 搜索条件
            if search:
                search_pattern = f"%{search}%"
                search_condition = or_(
                    DataResourceTag.name.like(search_pattern),
                    DataResourceTag.description.like(search_pattern)
                )
                query = query.where(search_condition)
                count_query = count_query.where(search_condition)
            
            # 获取总数
            count_result = await self.db.execute(count_query)
            total = count_result.scalar() or 0
            
            # 分页和排序
            query = query.order_by(desc(DataResourceTag.usage_count), DataResourceTag.name)
            query = query.offset((page - 1) * page_size).limit(page_size)
            
            # 执行查询
            result = await self.db.execute(query)
            tags = result.scalars().all()
            
            logger.info(f"获取标签列表成功，返回 {len(tags)} 个标签，总数: {total}")
            return list(tags), total
            
        except Exception as e:
            logger.error(f"获取标签列表失败: {str(e)}")
            raise BusinessError(f"获取标签列表失败: {str(e)}")
    
    async def get_tag_by_id(self, tag_id: int) -> Optional[DataResourceTag]:
        """根据ID获取标签
        
        Args:
            tag_id: 标签ID
            
        Returns:
            标签对象
        """
        try:
            logger.info(f"获取标签详情，ID: {tag_id}")
            
            query = select(DataResourceTag).where(DataResourceTag.id == tag_id)
            result = await self.db.execute(query)
            tag = result.scalar_one_or_none()
            
            if not tag:
                logger.warning(f"标签不存在，ID: {tag_id}")
                return None
                
            logger.info(f"获取标签详情成功: {tag.name}")
            return tag
            
        except Exception as e:
            logger.error(f"获取标签详情失败: {str(e)}")
            raise BusinessError(f"获取标签详情失败: {str(e)}")
    
    async def create_tag(self, tag_data: DataResourceTagCreate, user_id: int) -> DataResourceTag:
        """创建标签
        
        Args:
            tag_data: 标签创建数据
            user_id: 用户ID
            
        Returns:
            创建的标签
        """
        try:
            logger.info(f"创建标签，用户ID: {user_id}, 标签名: {tag_data.name}")
            
            # 检查标签名是否重复
            existing_query = select(DataResourceTag).where(DataResourceTag.name == tag_data.name)
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()
            if existing:
                logger.error(f"标签名已存在: {tag_data.name}")
                raise BusinessError("标签名已存在")
            
            # 创建标签
            tag_dict = tag_data.model_dump()
            tag_dict.update({
                "created_by": user_id,
                "usage_count": 0
            })
            tag = DataResourceTag(**tag_dict)
            
            self.db.add(tag)
            await self.db.commit()
            await self.db.refresh(tag)
            
            logger.info(f"标签创建成功，ID: {tag.id}, 名称: {tag.name}")
            return tag
            
        except BusinessError:
            raise
        except Exception as e:
            logger.error(f"创建标签失败: {str(e)}")
            await self.db.rollback()
            raise BusinessError(f"创建标签失败: {str(e)}")
    
    async def update_tag(self, tag_id: int, tag_data: Dict[str, Any], user_id: int) -> DataResourceTag:
        """更新标签
        
        Args:
            tag_id: 标签ID
            tag_data: 更新数据
            user_id: 用户ID
            
        Returns:
            更新后的标签
        """
        try:
            logger.info(f"更新标签，ID: {tag_id}, 用户ID: {user_id}")
            
            # 获取标签
            tag = await self.get_tag_by_id(tag_id)
            if not tag:
                raise NotFoundError("标签不存在")
            
            # 如果更新名称，检查是否重复
            if "name" in tag_data and tag_data["name"] != tag.name:
                existing_query = select(DataResourceTag).where(
                    and_(
                        DataResourceTag.name == tag_data["name"],
                        DataResourceTag.id != tag_id
                    )
                )
                result = await self.db.execute(existing_query)
                existing = result.scalar_one_or_none()
                if existing:
                    logger.error(f"标签名已存在: {tag_data['name']}")
                    raise BusinessError("标签名已存在")
            
            # 更新标签
            for key, value in tag_data.items():
                if hasattr(tag, key):
                    setattr(tag, key, value)
            
            tag.updated_by = user_id
            tag.updated_at = datetime.now()
            
            await self.db.commit()
            await self.db.refresh(tag)
            
            logger.info(f"标签更新成功，ID: {tag.id}, 名称: {tag.name}")
            return tag
            
        except (BusinessError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"更新标签失败: {str(e)}")
            await self.db.rollback()
            raise BusinessError(f"更新标签失败: {str(e)}")
    
    async def delete_tag(self, tag_id: int, user_id: int) -> bool:
        """删除标签
        
        Args:
            tag_id: 标签ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"删除标签，ID: {tag_id}, 用户ID: {user_id}")
            
            # 获取标签
            tag = await self.get_tag_by_id(tag_id)
            if not tag:
                raise NotFoundError("标签不存在")
            
            # 检查是否有关联的资源
            relation_query = select(func.count(DataResourceTagRelation.id)).where(
                DataResourceTagRelation.tag_id == tag_id
            )
            result = await self.db.execute(relation_query)
            relation_count = result.scalar() or 0
            
            if relation_count > 0:
                logger.error(f"标签仍有 {relation_count} 个关联资源，无法删除")
                raise BusinessError(f"标签仍有 {relation_count} 个关联资源，无法删除")
            
            # 删除标签
            await self.db.delete(tag)
            await self.db.commit()
            
            logger.info(f"标签删除成功，ID: {tag_id}")
            return True
            
        except (BusinessError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"删除标签失败: {str(e)}")
            await self.db.rollback()
            raise BusinessError(f"删除标签失败: {str(e)}")
    
    async def toggle_tag_status(self, tag_id: int, user_id: int) -> DataResourceTag:
        """切换标签状态
        
        Args:
            tag_id: 标签ID
            user_id: 用户ID
            
        Returns:
            更新后的标签
        """
        try:
            logger.info(f"切换标签状态，ID: {tag_id}, 用户ID: {user_id}")
            
            # 获取标签
            tag = await self.get_tag_by_id(tag_id)
            if not tag:
                raise NotFoundError("标签不存在")
            
            # 切换状态：active <-> disabled
            from app.models.data_resource import TagStatus
            new_status = TagStatus.DISABLED if tag.status == TagStatus.ACTIVE else TagStatus.ACTIVE
            
            # 更新标签状态
            tag.status = new_status
            tag.updated_by = user_id
            tag.updated_at = func.now()
            
            # 提交更改
            await self.db.commit()
            await self.db.refresh(tag)
            
            logger.info(f"标签状态切换成功，ID: {tag.id}, 新状态: {new_status.value}")
            return tag
            
        except (BusinessError, NotFoundError):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"切换标签状态失败: {str(e)}")
            raise BusinessError(f"切换标签状态失败: {str(e)}")
    
    async def batch_delete_tags(self, tag_ids: List[int], user_id: int) -> Dict[str, Any]:
        """批量删除标签
        
        Args:
            tag_ids: 标签ID列表
            user_id: 用户ID
            
        Returns:
            删除结果统计
        """
        try:
            logger.info(f"批量删除标签，IDs: {tag_ids}, 用户ID: {user_id}")
            
            success_count = 0
            failed_count = 0
            failed_tags = []
            
            for tag_id in tag_ids:
                try:
                    await self.delete_tag(tag_id, user_id)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    failed_tags.append({
                        "id": tag_id,
                        "error": str(e)
                    })
                    logger.warning(f"删除标签失败，ID: {tag_id}, 错误: {str(e)}")
            
            result = {
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_tags": failed_tags,
                "total": len(tag_ids)
            }
            
            logger.info(f"批量删除标签完成，成功: {success_count}, 失败: {failed_count}")
            return result
            
        except Exception as e:
            logger.error(f"批量删除标签失败: {str(e)}")
            raise BusinessError(f"批量删除标签失败: {str(e)}")
    
    async def get_tag_usage_stats(self, tag_id: int) -> Dict[str, Any]:
        """获取标签使用统计
        
        Args:
            tag_id: 标签ID
            
        Returns:
            使用统计信息
        """
        try:
            logger.info(f"获取标签使用统计，ID: {tag_id}")
            
            # 获取标签
            tag = await self.get_tag_by_id(tag_id)
            if not tag:
                raise NotFoundError("标签不存在")
            
            # 获取关联的资源数量
            resource_query = select(func.count(DataResourceTagRelation.resource_id)).where(
                DataResourceTagRelation.tag_id == tag_id
            )
            result = await self.db.execute(resource_query)
            resource_count = result.scalar() or 0
            
            # 获取关联的资源列表（最近的10个）
            recent_resources_query = (
                select(DataResource.id, DataResource.name, DataResource.display_name)
                .join(DataResourceTagRelation, DataResource.id == DataResourceTagRelation.resource_id)
                .where(DataResourceTagRelation.tag_id == tag_id)
                .order_by(desc(DataResourceTagRelation.created_at))
                .limit(10)
            )
            result = await self.db.execute(recent_resources_query)
            recent_resources = [
                {
                    "id": row.id,
                    "name": row.name,
                    "display_name": row.display_name
                }
                for row in result.fetchall()
            ]
            
            stats = {
                "tag_id": tag_id,
                "tag_name": tag.name,
                "resource_count": resource_count,
                "usage_count": tag.usage_count,
                "recent_resources": recent_resources,
                "created_at": tag.created_at.isoformat() if tag.created_at else None,
                "updated_at": tag.updated_at.isoformat() if tag.updated_at else None
            }
            
            logger.info(f"获取标签使用统计成功，资源数量: {resource_count}")
            return stats
            
        except (BusinessError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"获取标签使用统计失败: {str(e)}")
            raise BusinessError(f"获取标签使用统计失败: {str(e)}")