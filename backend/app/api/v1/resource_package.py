"""资源包API路由"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, text, select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.response import success_response
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.resource_package import (
    ResourcePackage, ResourcePackagePermission, 
    ResourcePackageQueryHistory, ResourcePackageTag
)
from app.schemas.resource_package import (
    ResourcePackageCreate, ResourcePackageUpdate, ResourcePackage as ResourcePackageSchema,
    ResourcePackageResponse, ResourcePackageListResponse, ResourcePackageSearchRequest,
    ResourcePackageQueryRequest, ResourcePackageQueryResponse,
    PermissionType, QueryStatus, PackageType
)
from app.services.data_resource_service import DataResourceService
from app.services.elasticsearch_service import ElasticsearchService
import json
import time
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)

router = APIRouter()


class ResourcePackageService:
    """资源包服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_resource_service = DataResourceService(db)
        self.es_service = ElasticsearchService()
    
    async def create_package(self, package_data: ResourcePackageCreate, user_id: int) -> ResourcePackage:
        """创建资源包"""
        # 检查名称是否重复
        existing_query = select(ResourcePackage).where(
            and_(
                ResourcePackage.name == package_data.name,
                ResourcePackage.created_by == user_id
            )
        )
        result = await self.db.execute(existing_query)
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="资源包名称已存在")
        
        # 创建资源包
        db_package = ResourcePackage(
            name=package_data.name,
            description=package_data.description,
            type=package_data.type,
            datasource_id=package_data.datasource_id,
            resource_id=package_data.resource_id,
            template_id=package_data.template_id,
            template_type=package_data.template_type,
            dynamic_params=package_data.dynamic_params,
            is_active=package_data.is_active,
            created_by=user_id
        )
        
        self.db.add(db_package)
        await self.db.flush()
        
        # 添加标签
        if package_data.tags:
            for tag_name in package_data.tags:
                tag = ResourcePackageTag(
                    package_id=db_package.id,
                    tag_name=tag_name.strip()
                )
                self.db.add(tag)
        
        # 给创建者添加管理权限
        permission = ResourcePackagePermission(
            package_id=db_package.id,
            user_id=user_id,
            permission_type=PermissionType.ADMIN,
            granted_by=user_id
        )
        self.db.add(permission)
        
        await self.db.commit()
        
        # 重新查询以获取完整的关联数据
        from sqlalchemy.orm import selectinload
        query = select(ResourcePackage).options(
            selectinload(ResourcePackage.tags),
            selectinload(ResourcePackage.permissions)
        ).where(ResourcePackage.id == db_package.id)
        result = await self.db.execute(query)
        refreshed_package = result.scalar_one()
        
        return refreshed_package
    
    async def get_package(self, package_id: int, user_id: int) -> ResourcePackage:
        """获取资源包详情"""
        query = select(ResourcePackage).options(
            selectinload(ResourcePackage.tags),
            selectinload(ResourcePackage.permissions),
            selectinload(ResourcePackage.datasource),
            selectinload(ResourcePackage.resource),
            selectinload(ResourcePackage.creator)
        ).where(ResourcePackage.id == package_id)
        result = await self.db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(status_code=404, detail="资源包不存在")
        
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.READ):
            raise HTTPException(status_code=403, detail="无权限访问此资源包")
        
        return package
    
    async def update_package(self, package_id: int, package_data: ResourcePackageUpdate, user_id: int) -> ResourcePackage:
        """更新资源包"""
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.WRITE):
            raise HTTPException(status_code=403, detail="无权限修改此资源包")
        
        query = select(ResourcePackage).where(ResourcePackage.id == package_id)
        result = await self.db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(status_code=404, detail="资源包不存在")
        
        # 更新基本信息
        if package_data.name is not None:
            package.name = package_data.name
        if package_data.description is not None:
            package.description = package_data.description
        if package_data.template_id is not None:
            package.template_id = package_data.template_id
        if package_data.template_type is not None:
            package.template_type = package_data.template_type
        if package_data.dynamic_params is not None:
            package.dynamic_params = package_data.dynamic_params
        if package_data.is_active is not None:
            package.is_active = package_data.is_active
        
        package.updated_at = datetime.utcnow()
        
        # 更新标签
        if package_data.tags is not None:
            # 删除旧标签
            delete_tags_query = select(ResourcePackageTag).where(
                ResourcePackageTag.package_id == package_id
            )
            old_tags_result = await self.db.execute(delete_tags_query)
            old_tags = old_tags_result.scalars().all()
            for tag in old_tags:
                await self.db.delete(tag)
            
            # 添加新标签
            for tag_name in package_data.tags:
                tag = ResourcePackageTag(
                    package_id=package_id,
                    tag_name=tag_name.strip()
                )
                self.db.add(tag)
        
        await self.db.commit()
        await self.db.refresh(package)
        return package
    
    async def delete_package(self, package_id: int, user_id: int):
        """删除资源包"""
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.ADMIN):
            raise HTTPException(status_code=403, detail="无权限删除此资源包")
        
        query = select(ResourcePackage).where(ResourcePackage.id == package_id)
        result = await self.db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(status_code=404, detail="资源包不存在")
        
        # 删除相关数据
        # 删除标签
        tags_query = select(ResourcePackageTag).where(ResourcePackageTag.package_id == package_id)
        tags_result = await self.db.execute(tags_query)
        tags = tags_result.scalars().all()
        for tag in tags:
            await self.db.delete(tag)
        
        # 删除权限
        permissions_query = select(ResourcePackagePermission).where(
            ResourcePackagePermission.package_id == package_id
        )
        permissions_result = await self.db.execute(permissions_query)
        permissions = permissions_result.scalars().all()
        for permission in permissions:
            await self.db.delete(permission)
        
        # 删除查询历史
        history_query = select(ResourcePackageQueryHistory).where(
            ResourcePackageQueryHistory.package_id == package_id
        )
        history_result = await self.db.execute(history_query)
        histories = history_result.scalars().all()
        for history in histories:
            await self.db.delete(history)
        
        # 删除资源包
        await self.db.delete(package)
        await self.db.commit()
    
    async def search_packages(self, search_req: ResourcePackageSearchRequest, user_id: int) -> ResourcePackageListResponse:
        """搜索资源包"""
        # 构建基础查询
        query = select(ResourcePackage)
        
        # 权限过滤：只显示用户有权限访问的资源包
        accessible_packages_query = select(ResourcePackagePermission.package_id).where(
            ResourcePackagePermission.user_id == user_id
        )
        accessible_result = await self.db.execute(accessible_packages_query)
        accessible_package_ids = [row[0] for row in accessible_result.fetchall()]
        
        if accessible_package_ids:
            query = query.where(ResourcePackage.id.in_(accessible_package_ids))
        else:
            # 如果没有任何权限，返回空结果
            return ResourcePackageListResponse(
                items=[],
                total=0,
                page=search_req.page,
                size=search_req.size
            )
        
        # 添加搜索条件
        conditions = []
        
        if search_req.keyword:
            keyword_condition = or_(
                ResourcePackage.name.ilike(f"%{search_req.keyword}%"),
                ResourcePackage.description.ilike(f"%{search_req.keyword}%")
            )
            conditions.append(keyword_condition)
        
        if search_req.type:
            conditions.append(ResourcePackage.type == search_req.type)
        
        if search_req.datasource_id:
            conditions.append(ResourcePackage.datasource_id == search_req.datasource_id)
        
        if search_req.is_active is not None:
            conditions.append(ResourcePackage.is_active == search_req.is_active)
        
        if search_req.created_by:
            conditions.append(ResourcePackage.created_by == search_req.created_by)
        
        # 标签过滤
        if search_req.tags:
            tag_packages_query = select(ResourcePackageTag.package_id).where(
                ResourcePackageTag.tag_name.in_(search_req.tags)
            )
            tag_result = await self.db.execute(tag_packages_query)
            tag_package_ids = [row[0] for row in tag_result.fetchall()]
            if tag_package_ids:
                conditions.append(ResourcePackage.id.in_(tag_package_ids))
            else:
                # 如果指定了标签但没有匹配的资源包，返回空结果
                return ResourcePackageListResponse(
                    items=[],
                    total=0,
                    page=search_req.page,
                    size=search_req.size
                )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 计算总数
        count_query = select(func.count(ResourcePackage.id)).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 排序
        if search_req.sort_by:
            if search_req.sort_by == "created_at":
                order_column = ResourcePackage.created_at
            elif search_req.sort_by == "updated_at":
                order_column = ResourcePackage.updated_at
            elif search_req.sort_by == "name":
                order_column = ResourcePackage.name
            else:
                order_column = ResourcePackage.created_at
            
            if search_req.sort_order and search_req.sort_order.lower() == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        else:
            query = query.order_by(ResourcePackage.created_at.desc())
        
        # 分页
        offset = (search_req.page - 1) * search_req.size
        query = query.offset(offset).limit(search_req.size)
        
        # 预加载关联数据
        query = query.options(
            selectinload(ResourcePackage.tags),
            selectinload(ResourcePackage.permissions)
        )
        
        # 执行查询
        result = await self.db.execute(query)
        packages = result.scalars().all()
        
        return ResourcePackageListResponse(
            items=packages,
            total=total,
            page=search_req.page,
            size=search_req.size
        )
    

    
    async def query_package(self, package_id: int, query_req: ResourcePackageQueryRequest, user_id: int) -> ResourcePackageQueryResponse:
        """执行资源包查询"""
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.EXECUTE):
            raise HTTPException(status_code=403, detail="无权限执行此资源包查询")
        
        query = select(ResourcePackage).where(ResourcePackage.id == package_id)
        result = await self.db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(status_code=404, detail="资源包不存在")
        
        if not package.is_active:
            raise HTTPException(status_code=400, detail="资源包已禁用")
        
        start_time = time.time()
        generated_query = None
        result_count = 0
        status = QueryStatus.SUCCESS
        error_message = None
        
        try:
            if package.type == PackageType.SQL:
                query_result = await self._execute_sql_query(package, query_req)
            elif package.type == PackageType.ELASTICSEARCH:
                query_result = await self._execute_es_query(package, query_req)
            else:
                raise HTTPException(status_code=400, detail="不支持的资源包类型")
            
            generated_query = query_result["query"]
            result_count = len(query_result["data"])
            
        except Exception as e:
            status = QueryStatus.ERROR
            error_message = str(e)
            query_result = {
                "data": [],
                "total": 0,
                "query": None
            }
            logger.error(f"资源包查询失败: {e}")
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # 记录查询历史
        await self._record_query_history(
            package_id, user_id, query_req.dynamic_params,
            generated_query, result_count, execution_time,
            status, error_message
        )
        
        return ResourcePackageQueryResponse(
            data=query_result["data"],
            total=query_result["total"],
            generated_query=generated_query,
            execution_time=execution_time,
            status=status,
            error_message=error_message
        )
    
    async def _execute_sql_query(self, package: ResourcePackage, query_req: ResourcePackageQueryRequest) -> Dict[str, Any]:
        """执行SQL查询"""
        # 获取SQL查询模板
        template = package.template
        if not template:
            raise HTTPException(status_code=400, detail="未找到关联的SQL查询模板")
        
        # 获取模板的查询内容
        template_query = template.query
        if not template_query:
            raise HTTPException(status_code=400, detail="查询模板内容为空")
        
        # 合并参数：资源包动态参数 + 请求参数
        effective_params = package.get_effective_params(query_req.dynamic_params)
        
        # 处理分页参数
        if query_req.limit:
            effective_params['limit'] = query_req.limit
        if query_req.offset:
            effective_params['offset'] = query_req.offset
        
        # 使用模板引擎渲染查询
        try:
            from jinja2 import Template
            jinja_template = Template(template_query)
            rendered_query = jinja_template.render(**effective_params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"查询模板渲染失败: {str(e)}")
        
        # 执行查询
        try:
            # 使用数据资源服务执行查询
            query_result = await self.data_resource_service.execute_sql_query(
                package.datasource_id, rendered_query, effective_params
            )
            
            return {
                "data": query_result.get("data", []),
                "total": len(query_result.get("data", [])),
                "query": rendered_query
            }
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")
    
    async def _execute_es_query(self, package: ResourcePackage, query_req: ResourcePackageQueryRequest) -> Dict[str, Any]:
        """执行Elasticsearch查询"""
        # 获取查询模板
        if not package.template:
            raise HTTPException(status_code=400, detail="资源包未配置查询模板")
        
        # 获取查询内容
        query_content = package.get_query_content()
        if not query_content:
            raise HTTPException(status_code=400, detail="查询模板内容为空")
        
        # 合并动态参数
        effective_params = package.get_effective_params(query_req.dynamic_params)
        
        # 渲染查询模板
        try:
            template = Template(query_content)
            rendered_query = template.render(**effective_params)
            
            # 解析为JSON
            query_body = json.loads(rendered_query)
            
        except json.JSONDecodeError as e:
            logger.error(f"ES查询模板JSON解析失败: {e}")
            raise HTTPException(status_code=400, detail=f"查询模板JSON格式错误: {str(e)}")
        except Exception as e:
            logger.error(f"ES查询模板渲染失败: {e}")
            raise HTTPException(status_code=400, detail=f"查询模板渲染失败: {str(e)}")
        
        # 添加分页参数
        if query_req.limit:
            query_body["size"] = query_req.limit
        if query_req.offset:
            query_body["from"] = query_req.offset
        
        # 执行查询
        try:
            # 从模板参数中获取索引名
            index_name = effective_params.get("index_name")
            if not index_name:
                raise HTTPException(status_code=400, detail="查询模板缺少索引名参数")
            
            result = await self.es_service.search(index_name, query_body)
            
            return {
                "data": [hit["_source"] for hit in result.get("hits", {}).get("hits", [])],
                "total": result.get("hits", {}).get("total", {}).get("value", 0),
                "query": json.dumps(query_body, ensure_ascii=False, indent=2)
            }
        except Exception as e:
            logger.error(f"ES查询执行失败: {e}")
            raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")

    
    async def _check_permission(self, package_id: int, user_id: int, required_permission: PermissionType) -> bool:
        """检查用户权限"""
        query = select(ResourcePackagePermission).where(
            and_(
                ResourcePackagePermission.package_id == package_id,
                ResourcePackagePermission.user_id == user_id
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
        
        user_level = permission_levels.get(permission.permission_type, 0)
        required_level = permission_levels.get(required_permission, 0)
        
        return user_level >= required_level
    
    async def _record_query_history(self, package_id: int, user_id: int, dynamic_params: Dict[str, Any],
                            generated_query: Optional[str], result_count: int, execution_time: int,
                            status: QueryStatus, error_message: Optional[str] = None):
        """记录查询历史"""
        history = ResourcePackageQueryHistory(
            package_id=package_id,
            user_id=user_id,
            dynamic_params=dynamic_params,
            generated_query=generated_query,
            result_count=result_count,
            execution_time=execution_time,
            status=status,
            error_message=error_message
        )
        
        self.db.add(history)
        await self.db.commit()


# API路由
@router.post("/", response_model=ResourcePackageSchema)
async def create_resource_package(
    package_data: ResourcePackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建资源包"""
    service = ResourcePackageService(db)
    return await service.create_package(package_data, current_user.id)


@router.get("/{package_id}", response_model=ResourcePackageResponse)
async def get_resource_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取资源包详情"""
    service = ResourcePackageService(db)
    return await service.get_package(package_id, current_user.id)


@router.put("/{package_id}", response_model=ResourcePackageSchema)
async def update_resource_package(
    package_id: int,
    package_data: ResourcePackageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新资源包"""
    service = ResourcePackageService(db)
    return await service.update_package(package_id, package_data, current_user.id)


@router.delete("/{package_id}")
async def delete_resource_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除资源包"""
    service = ResourcePackageService(db)
    await service.delete_package(package_id, current_user.id)
    return {"message": "资源包删除成功"}


@router.post("/search")
async def search_resource_packages(
    search_req: ResourcePackageSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """搜索资源包"""
    service = ResourcePackageService(db)
    result = await service.search_packages(search_req, current_user.id)
    return success_response(
        data=result.model_dump(),
        message="查询成功"
    )



@router.post("/{package_id}/query", response_model=ResourcePackageQueryResponse)
async def query_resource_package(
    package_id: int,
    query_req: ResourcePackageQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行资源包查询"""
    service = ResourcePackageService(db)
    return await service.query_package(package_id, query_req, current_user.id)


@router.get("/{package_id}/history")
async def get_query_history(
    package_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取查询历史"""
    service = ResourcePackageService(db)
    
    # 检查权限
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限访问此资源包")
    
    # 构建查询
    query = select(ResourcePackageQueryHistory).where(
        ResourcePackageQueryHistory.package_id == package_id
    ).order_by(ResourcePackageQueryHistory.created_at.desc())
    
    # 计算总数
    count_query = select(func.count(ResourcePackageQueryHistory.id)).where(
        ResourcePackageQueryHistory.package_id == package_id
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # 分页
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)
    
    # 执行查询
    result = await db.execute(query)
    histories = result.scalars().all()
    
    return {
        "items": histories,
        "total": total,
        "page": page,
        "size": size
    }