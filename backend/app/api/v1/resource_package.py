"""资源包API路由"""

from datetime import datetime, timedelta
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
    ResourcePackageQueryHistory, ResourcePackageTag, ResourcePackageFile
)
from app.models.datasource import Datasource
from app.schemas.resource_package import (
    ResourcePackageCreate, ResourcePackageUpdate, ResourcePackage as ResourcePackageSchema,
    ResourcePackageResponse, ResourcePackageListResponse, ResourcePackageSearchRequest,
    ResourcePackageQueryRequest, ResourcePackageQueryResponse,
    PermissionType, QueryStatus, PackageType
)
from app.services.data_resource_service import DataResourceService
from app.services.elasticsearch_service import ElasticsearchService
from app.services.excel_service import ExcelService
from app.core.config import settings
from minio import Minio
from minio.error import S3Error
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
        logger.info(f"=== 开始创建资源包 ===")
        logger.info(f"用户ID: {user_id}")
        logger.info(f"资源包数据: {package_data.dict()}")
        
        try:
            # 检查名称是否重复
            logger.info(f"检查资源包名称是否重复: {package_data.name}")
            existing_query = select(ResourcePackage).where(
                and_(
                    ResourcePackage.name == package_data.name,
                    ResourcePackage.created_by == user_id
                )
            )
            result = await self.db.execute(existing_query)
            existing = result.scalar_one_or_none()
            if existing:
                logger.warning(f"资源包名称已存在: {package_data.name}")
                raise HTTPException(status_code=400, detail="资源包名称已存在")
            
            logger.info("名称检查通过，开始创建资源包实例")
            
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
                is_lock=package_data.is_lock,
                created_by=user_id
            )
            
            logger.info(f"资源包实例创建完成，准备添加到数据库")
            logger.info(f"资源包属性: name={db_package.name}, type={db_package.type}, is_lock={db_package.is_lock}")
            
            self.db.add(db_package)
            logger.info("资源包已添加到会话，准备flush")
            
            await self.db.flush()
            logger.info(f"数据库flush完成，资源包ID: {db_package.id}")
            
            # 添加标签
            if package_data.tags:
                logger.info(f"开始添加标签: {package_data.tags}")
                for tag_name in package_data.tags:
                    tag = ResourcePackageTag(
                        package_id=db_package.id,
                        tag_name=tag_name.strip()
                    )
                    self.db.add(tag)
                    logger.info(f"添加标签: {tag_name.strip()}")
            else:
                logger.info("没有标签需要添加")
            
            # 给创建者添加管理权限
            logger.info("开始添加管理权限")
            permission = ResourcePackagePermission(
                package_id=db_package.id,
                user_id=user_id,
                permission_type=PermissionType.ADMIN,
                granted_by=user_id
            )
            self.db.add(permission)
            logger.info(f"管理权限已添加: package_id={db_package.id}, user_id={user_id}")
            
            logger.info("准备提交事务")
            await self.db.commit()
            logger.info("事务提交成功")
            
        except Exception as e:
            logger.error(f"创建资源包失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"错误堆栈: {traceback.format_exc()}")
            await self.db.rollback()
            raise HTTPException(status_code=500, detail=f"创建资源包失败: {str(e)}")
    
        # 重新查询以获取完整的关联数据
        logger.info("开始重新查询资源包以获取完整数据")
        try:
            from sqlalchemy.orm import selectinload
            query = select(ResourcePackage).options(
                selectinload(ResourcePackage.tags),
                selectinload(ResourcePackage.permissions)
            ).where(ResourcePackage.id == db_package.id)
            result = await self.db.execute(query)
            refreshed_package = result.scalar_one()
            
            logger.info(f"资源包创建成功! ID: {refreshed_package.id}, 名称: {refreshed_package.name}")
            logger.info(f"=== 资源包创建完成 ===")
            
            return refreshed_package
        except Exception as e:
            logger.error(f"重新查询资源包失败: {e}")
            raise HTTPException(status_code=500, detail=f"重新查询资源包失败: {str(e)}")
    
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
        
        # # 检查权限
        # if not await self._check_permission(package_id, user_id, PermissionType.READ):
        #     raise HTTPException(status_code=403, detail="无权限访问此资源包")

        
        #   // 页面访问权限：资源中心查询
        #   permission: 'data:resource_center:query',
        #   strictPermission: true,
        
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
        # 支持更新删除锁定状态（0 可删除，1 禁止删除）
        if package_data.is_lock is not None:
            package.is_lock = package_data.is_lock
        
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
        # 为避免异步会话下的懒加载导致序列化抛错（MissingGreenlet），
        # 重新查询并使用 selectinload 预加载关联数据后再返回
        reload_query = (
            select(ResourcePackage)
            .options(
                selectinload(ResourcePackage.tags),
                selectinload(ResourcePackage.permissions)
            )
            .where(ResourcePackage.id == package_id)
        )
        reload_result = await self.db.execute(reload_query)
        updated_package = reload_result.scalar_one_or_none()
        return updated_package
    
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
        
        if search_req.is_lock is not None:
            conditions.append(ResourcePackage.is_lock == search_req.is_lock)
        
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
        
        # 计算总数 - 基于相同的查询条件计算资源包总数
        count_query = select(func.count(ResourcePackage.id))
        
        # 应用相同的权限过滤
        if accessible_package_ids:
            count_query = count_query.where(ResourcePackage.id.in_(accessible_package_ids))
        else:
            total = 0
        
        # 应用相同的搜索条件
        if conditions and accessible_package_ids:
            count_query = count_query.where(and_(*conditions))
        
        if accessible_package_ids:
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()
        else:
            total = 0
        
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
    logger.info(f"=== 收到创建资源包请求 ===")
    logger.info(f"当前用户: {current_user.id} ({current_user.username})")
    logger.info(f"请求数据: {package_data.dict()}")
    
    try:
        service = ResourcePackageService(db)
        logger.info("ResourcePackageService 实例创建成功")
        
        result = await service.create_package(package_data, current_user.id)
        logger.info(f"资源包创建成功，返回结果: ID={result.id}")
        
        return result
    except HTTPException as he:
        logger.error(f"HTTP异常: {he.status_code} - {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"创建资源包端点异常: {e}")
        logger.error(f"异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"异常堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


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


@router.post("/{package_id}/download")
async def download_resource_package(
    package_id: int,
    query_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载资源包Excel文件"""
    service = ResourcePackageService(db)
    
    # 检查权限
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限访问此资源包")
    
    try:
        excel_service = ExcelService()
        result = await excel_service.generate_and_upload_excel(
            package_id=package_id,
            query_data=query_data,
            db=db
        )
        
        if result["status"] == "no_new_data":
            return success_response(
                data={"has_new_data": False},
                message=result["message"]
            )
        
        return success_response(
            data={
                "has_new_data": True,
                "download_url": result["download_url"],
                "filename": result["filename"],
                "minio_path": result["minio_path"]
            },
            message="Excel文件生成成功"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"下载资源包失败: {e}")
        raise HTTPException(status_code=500, detail="下载失败，请稍后重试")


@router.post("/{package_id}/generate-excel")
async def generate_excel_for_package(
    package_id: int,
    query_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成Excel并上传到MinIO（更新excel_time与download_url）"""
    service = ResourcePackageService(db)
    
    # 权限检查
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限访问此资源包")
    
    try:
        excel_service = ExcelService()
        result = await excel_service.generate_and_upload_excel(
            package_id=package_id,
            query_data=query_data,
            db=db
        )
        
        if result["status"] == "no_new_data":
            return success_response(
                data={"has_new_data": False},
                message=result["message"]
            )
        
        return success_response(
            data={
                "has_new_data": True,
                "download_url": result["download_url"],
                "filename": result["filename"],
                "minio_path": result["minio_path"]
            },
            message="Excel文件生成成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"生成Excel失败: {e}")
        raise HTTPException(status_code=500, detail="生成失败，请稍后重试")


@router.post("/{package_id}/download-latest")
async def download_latest_resource_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取最新资源包的预签名下载链接，并更新download_time"""
    service = ResourcePackageService(db)
    
    # 权限检查
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限访问此资源包")
    
    # 获取资源包
    result = await db.execute(select(ResourcePackage).where(ResourcePackage.id == package_id))
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(status_code=404, detail="资源包不存在")
    
    if not package.download_url:
        return success_response(data={"has_file": False}, message="尚未生成Excel文件")
    
    # 解析MinIO对象路径
    try:
        prefix = f"minio://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET_NAME}/"
        if package.download_url.startswith(prefix):
            object_path = package.download_url[len(prefix):]
        else:
            # 兜底：尝试从URL最后的路径段作为对象名
            object_path = package.download_url.split('/')[-1]
        
        minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            region=settings.MINIO_REGION
        )
        
        presigned_url = minio_client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=object_path,
            expires=timedelta(seconds=3600)
        )
        
        # 更新下载时间
        package.download_time = datetime.now()
        await db.commit()
        
        return success_response(
            data={
                "has_file": True,
                "download_url": presigned_url,
                "object_path": object_path,
                "excel_time": package.excel_time,
                "download_time": package.download_time
            },
            message="下载链接生成成功"
        )
    except S3Error as e:
        logger.error(f"获取预签名链接失败: {e}")
        raise HTTPException(status_code=500, detail="获取下载链接失败")


@router.get("/{package_id}/files")
async def list_resource_package_files(
    package_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """列出资源包历史生成的Excel文件"""
    service = ResourcePackageService(db)
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限访问此资源包")

    # 统计总数
    total_result = await db.execute(
        select(func.count(ResourcePackageFile.id)).where(ResourcePackageFile.package_id == package_id)
    )
    total = total_result.scalar()

    # 查询分页数据
    offset = (page - 1) * size
    query = (
        select(ResourcePackageFile)
        .where(ResourcePackageFile.package_id == package_id)
        .order_by(ResourcePackageFile.generated_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await db.execute(query)
    files = result.scalars().all()

    items = [
        {
            "id": f.id,
            "filename": f.filename,
            "object_path": f.object_path,
            "generated_at": f.generated_at,
        }
        for f in files
    ]

    return success_response(
        data={"items": items, "total": total, "page": page, "size": size},
        message="历史文件列表获取成功",
    )


@router.post("/{package_id}/files/{file_id}/download")
async def download_resource_package_file(
    package_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """下载指定历史Excel文件，返回预签名URL"""
    service = ResourcePackageService(db)
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限访问此资源包")

    # 获取文件记录
    result = await db.execute(
        select(ResourcePackageFile).where(
            and_(
                ResourcePackageFile.id == file_id,
                ResourcePackageFile.package_id == package_id,
            )
        )
    )
    file_rec = result.scalar_one_or_none()
    if not file_rec:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 生成预签名URL
    minio_client = Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
        region=settings.MINIO_REGION,
    )

    try:
        presigned_url = minio_client.presigned_get_object(
            bucket_name=settings.MINIO_BUCKET_NAME,
            object_name=file_rec.object_path,
            expires=timedelta(seconds=3600),
        )
    except S3Error as e:
        logger.error(f"生成预签名链接失败: {e}")
        raise HTTPException(status_code=500, detail="获取下载链接失败")

    # 更新下载时间（与最新下载保持一致）
    pkg_result = await db.execute(select(ResourcePackage).where(ResourcePackage.id == package_id))
    package = pkg_result.scalar_one_or_none()
    if package:
        package.download_time = datetime.now()
        await db.commit()

    return success_response(
        data={
            "has_file": True,
            "download_url": presigned_url,
            "object_path": file_rec.object_path,
            "filename": file_rec.filename,
            "generated_at": file_rec.generated_at,
        },
        message="下载链接生成成功",
    )