"""
增强安全性的资源包查询API接口
为ResourcePackageQueryPage.vue页面提供安全的查询服务
"""

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
    ResourcePackageQueryRequest, ResourcePackageQueryResponse,
    PermissionType, QueryStatus, PackageType
)
from app.services.data_resource_service import DataResourceService
from app.services.datasource import DatasourceService
from app.services.elasticsearch_service import ElasticsearchService
from app.utils.sql_security import SQLSecurityValidator
from app.services.sql_dynamic_modifier import SQLDynamicModifier
from jinja2 import Template
import json
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SecureResourcePackageService:
    """增强安全性的资源包查询服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sql_validator = SQLSecurityValidator()
        self.sql_modifier = SQLDynamicModifier()
        self.data_resource_service = DataResourceService(db)
        self.datasource_service = DatasourceService(db)
        self.es_service = ElasticsearchService()

    async def secure_query_package(
        self, 
        package_id: int, 
        query_req: ResourcePackageQueryRequest, 
        user_id: int
    ) -> ResourcePackageQueryResponse:
        """
        执行增强安全性的资源包查询
        
        Args:
            package_id: 资源包ID
            query_req: 查询请求参数
            user_id: 用户ID
            
        Returns:
            ResourcePackageQueryResponse: 查询响应结果
            
        Raises:
            HTTPException: 权限不足、资源包不存在等错误
        """
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.READ):
            raise HTTPException(status_code=403, detail="无权限执行此资源包查询")
        
        # 获取资源包信息
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
            logger.info(f"开始执行资源包查询，包ID: {package_id}, 类型: {package.type}")
            if package.type == PackageType.SQL:
                query_result = await self._execute_secure_sql_query(package, query_req, user_id)
            elif package.type == PackageType.ELASTICSEARCH:
                query_result = await self._execute_es_query(package, query_req)
            else:
                raise HTTPException(status_code=400, detail="不支持的资源包类型")
            
            generated_query = query_result["query"]
            result_count = len(query_result["data"])
            logger.info(f"****执行的SQL查询****\n{generated_query}\n****SQL查询结束****")
            logger.info(f"查询结果数量: {result_count}")
            
        except Exception as e:
            status = QueryStatus.ERROR
            error_message = str(e)
            query_result = {
                "data": [],
                "total": 0,
                "query": None
            }
            logger.error(f"资源包查询失败: {e}")
            logger.error(f"异常类型: {type(e).__name__}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        execution_time = int((time.time() - start_time) * 1000)
        
        # 记录查询历史
        await self._record_query_history(
            package_id, user_id, query_req.dynamic_params,
            generated_query, result_count, execution_time,
            status, error_message
        )
        
        return ResourcePackageQueryResponse(
            success=status == QueryStatus.SUCCESS,
            columns=query_result.get("columns", []),
            data=query_result["data"],
            total_count=query_result["total"],
            generated_query=generated_query,
            execution_time=execution_time,
            error_message=error_message
        )

    async def _execute_secure_sql_query(
        self, 
        package: ResourcePackage, 
        query_req: ResourcePackageQueryRequest,
        user_id: int
    ) -> Dict[str, Any]:
        """
        执行增强安全性的SQL查询
        
        Args:
            package: 资源包对象
            query_req: 查询请求参数
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 查询结果
            
        Raises:
            HTTPException: SQL安全检查失败或查询执行失败
        """
        # 获取SQL查询模板
        logger.info(f"获取模板，模板ID: {package.template_id}, 模板类型: {package.template_type}")
        template = package.template
        if not template:
            logger.error(f"未找到关联的SQL查询模板，模板ID: {package.template_id}")
            raise HTTPException(status_code=400, detail="未找到关联的SQL查询模板")
        
        logger.info(f"模板查询内容: {template.query}")
        logger.info(f"动态参数: {query_req.dynamic_params}")
        
        # 获取模板配置
        template_config = {}
        if hasattr(template, 'config') and template.config:
            try:
                template_config = json.loads(template.config) if isinstance(template.config, str) else template.config
            except Exception as e:
                logger.warning(f"解析模板配置失败: {e}")
                template_config = {}
        
        logger.info(f"模板配置: {template_config}")
        
        # 使用SQL动态修改器处理SQL
        try:
            rendered_sql = self.sql_modifier.modify_sql_by_params(
                template.query, 
                template_config, 
                query_req.dynamic_params
            )
            logger.info(f"处理后的SQL: {rendered_sql}")
        except Exception as e:
            logger.error(f"SQL动态修改失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"SQL动态修改失败: {str(e)}")
        
        # 增强安全性检查
        try:
            # 1. 基础SQL安全检查（包含查询类型检查）
            validation_result = self.sql_validator.validate_query(rendered_sql)
            if not validation_result["is_safe"]:
                error_message = validation_result.get("error_message", "SQL查询包含不安全的操作")
                raise HTTPException(
                    status_code=400, 
                    detail=f"SQL查询包含不安全的操作: {error_message}"
                )
            
            # 2. 清理和优化SQL
            cleaned_sql = self.sql_validator.sanitize_query(rendered_sql)
            
            # 3. 准备分页参数
            limit = min(query_req.limit or 1000, 10000)  # 最大限制10000条
            offset = query_req.offset or 0
            
            # 不在这里添加LIMIT，让datasource_service处理分页
            final_sql = cleaned_sql
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"SQL安全检查失败: {str(e)}"
            )
        
        # 执行查询
        try:
            # 获取数据源对象
            datasource = await self.datasource_service.get_datasource(package.datasource_id)
            if not datasource:
                raise HTTPException(
                    status_code=404,
                    detail=f"数据源不存在，ID: {package.datasource_id}"
                )
            
            # 使用datasource_service执行查询，启用分页功能
            result = await self.datasource_service.execute_query(
                datasource=datasource,
                query=final_sql,
                limit=limit,
                offset=offset,
                enable_pagination=True,
                timeout=30
            )
            
            return {
                "data": result.get("data", []),
                "total": result.get("total_count", result.get("row_count", 0)),  # 优先使用total_count
                "columns": result.get("columns", []),
                "query": final_sql
            }
            
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"查询执行失败: {str(e)}"
            )

    async def _execute_es_query(
        self, 
        package: ResourcePackage, 
        query_req: ResourcePackageQueryRequest
    ) -> Dict[str, Any]:
        """
        执行Elasticsearch查询
        
        Args:
            package: 资源包对象
            query_req: 查询请求参数
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        # 获取ES查询模板
        template = package.template
        if not template:
            raise HTTPException(status_code=400, detail="未找到关联的ES查询模板")
        
        try:
            # 渲染ES查询模板
            jinja_template = Template(template.content)
            rendered_query = jinja_template.render(**query_req.dynamic_params)
            
            # 解析为JSON
            es_query = json.loads(rendered_query)
            
            # 添加大小限制
            limit = min(query_req.limit or 1000, 10000)
            es_query["size"] = limit
            
            # 执行ES查询
            result = await self.es_service.search(
                package.datasource_id,
                es_query
            )
            
            return {
                "data": result.get("hits", []),
                "total": result.get("total", 0),
                "query": json.dumps(es_query, ensure_ascii=False, indent=2)
            }
            
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400, 
                detail=f"ES查询模板格式错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"ES查询执行失败: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"ES查询执行失败: {str(e)}"
            )

    async def _check_permission(
        self, 
        package_id: int, 
        user_id: int, 
        required_permission: PermissionType
    ) -> bool:
        """
        检查用户权限（支持权限层级关系）
        
        权限层级关系：
        - admin: 包含所有权限（read, write, admin）
        - write: 包含读写权限（read, write）
        - read: 仅包含读权限（read）
        
        Args:
            package_id: 资源包ID
            user_id: 用户ID
            required_permission: 所需权限类型
            
        Returns:
            bool: 是否有权限
        """
        # 定义权限层级关系
        permission_hierarchy = {
            PermissionType.READ: [PermissionType.READ, PermissionType.WRITE, PermissionType.ADMIN],
            PermissionType.WRITE: [PermissionType.WRITE, PermissionType.ADMIN],
            PermissionType.ADMIN: [PermissionType.ADMIN]
        }
        
        # 获取满足条件的权限类型列表
        allowed_permissions = permission_hierarchy.get(required_permission, [])
        
        # 查询用户是否拥有任何满足条件的权限
        query = select(ResourcePackagePermission).where(
            and_(
                ResourcePackagePermission.package_id == package_id,
                ResourcePackagePermission.user_id == user_id,
                ResourcePackagePermission.permission_type.in_(allowed_permissions),
                ResourcePackagePermission.is_active == True
            )
        )
        result = await self.db.execute(query)
        permission = result.scalar_one_or_none()
        
        return permission is not None

    async def _record_query_history(
        self, 
        package_id: int, 
        user_id: int, 
        dynamic_params: Dict[str, Any],
        generated_query: Optional[str], 
        result_count: int, 
        execution_time: int,
        status: QueryStatus, 
        error_message: Optional[str] = None
    ):
        """
        记录查询历史
        
        Args:
            package_id: 资源包ID
            user_id: 用户ID
            dynamic_params: 动态参数
            generated_query: 生成的查询语句
            result_count: 结果数量
            execution_time: 执行时间(毫秒)
            status: 查询状态
            error_message: 错误信息
        """
        history = ResourcePackageQueryHistory(
            package_id=package_id,
            user_id=user_id,
            dynamic_params=dynamic_params,
            generated_query=generated_query,
            result_count=result_count,
            execution_time=execution_time,
            status=status,
            error_message=error_message,
            created_at=datetime.utcnow()
        )
        
        self.db.add(history)
        await self.db.commit()


@router.post("/{package_id}/secure-query", response_model=ResourcePackageQueryResponse)
async def secure_query_resource_package(
    package_id: int,
    query_req: ResourcePackageQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    执行增强安全性的资源包查询
    
    这个接口专为ResourcePackageQueryPage.vue页面设计，
    提供比原有接口更强的安全性保障：
    
    1. 强化的SQL安全检查
    2. 查询类型限制（仅允许SELECT）
    3. 危险关键词过滤
    4. 查询结果数量限制
    5. 详细的查询历史记录
    
    Args:
        package_id: 资源包ID
        query_req: 查询请求参数
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        ResourcePackageQueryResponse: 查询响应结果
    """
    service = SecureResourcePackageService(db)
    result = await service.secure_query_package(package_id, query_req, current_user.id)
    return success_response(data=result)


@router.get("/{package_id}/query-history")
async def get_secure_query_history(
    package_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取安全查询历史记录
    
    Args:
        package_id: 资源包ID
        page: 页码
        size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        
    Returns:
        查询历史记录列表
    """
    service = SecureResourcePackageService(db)
    
    # 检查权限
    if not await service._check_permission(package_id, current_user.id, PermissionType.READ):
        raise HTTPException(status_code=403, detail="无权限查看此资源包的查询历史")
    
    # 查询历史记录
    offset = (page - 1) * size
    query = select(ResourcePackageQueryHistory).where(
        ResourcePackageQueryHistory.package_id == package_id
    ).order_by(ResourcePackageQueryHistory.created_at.desc()).offset(offset).limit(size)
    
    result = await db.execute(query)
    histories = result.scalars().all()
    
    # 统计总数
    count_query = select(func.count(ResourcePackageQueryHistory.id)).where(
        ResourcePackageQueryHistory.package_id == package_id
    )
    count_result = await db.execute(count_query)
    total = count_result.scalar()
    
    return success_response(data={
        "items": [
            {
                "id": h.id,
                "user_id": h.user_id,
                "query_params": h.query_params,
                "generated_query": h.generated_query,
                "result_count": h.result_count,
                "execution_time": h.execution_time,
                "status": h.status,
                "error_message": h.error_message,
                "created_at": h.created_at.isoformat()
            }
            for h in histories
        ],
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    })