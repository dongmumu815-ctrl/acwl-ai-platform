"""资源包服务类 - 重构版本

基于查询模板的资源包服务实现，避免数据冗余，提高一致性
"""

import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, text, select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.models.resource_package import (
    ResourcePackage, ResourcePackagePermission, 
    ResourcePackageQueryHistory, ResourcePackageTag
)
from app.models.sql_query_template import SQLQueryTemplate
from app.models.es_query_template import ESQueryTemplate
from app.models.user import User
from app.schemas.resource_package import (
    ResourcePackageCreate, ResourcePackageUpdate, ResourcePackage as ResourcePackageSchema,
    ResourcePackageListResponse, ResourcePackageSearchRequest,
    ResourcePackageQueryRequest, ResourcePackageQueryResponse,
    PermissionType, QueryStatus, PackageType
)
from app.services.data_resource_service import DataResourceService
from app.services.elasticsearch_service import ElasticsearchService
from app.core.exceptions import BusinessError

logger = logging.getLogger(__name__)


class ResourcePackageService:
    """资源包服务类 - 重构版本"""
    
    def __init__(self, db: AsyncSession):
        """初始化资源包服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.data_resource_service = DataResourceService(db)
        self.elasticsearch_service = ElasticsearchService()

    async def create_package(self, package_data: ResourcePackageCreate, user_id: int) -> ResourcePackageSchema:
        """创建资源包
        
        Args:
            package_data: 资源包创建数据
            user_id: 创建者ID
            
        Returns:
            ResourcePackageSchema: 创建的资源包信息
        """
        # 如果提供了模板ID，验证模板是否存在
        template = None
        if package_data.template_id is not None:
            template = await self._get_template(package_data.template_id, package_data.template_type)
            if not template:
                raise HTTPException(status_code=404, detail="关联的查询模板不存在")
            
            # 验证模板类型与资源包类型一致
            if package_data.template_type != package_data.type:
                raise HTTPException(status_code=400, detail="模板类型与资源包类型不匹配")
            
            # 验证数据源一致性
            if template.datasource_id != package_data.datasource_id:
                raise HTTPException(status_code=400, detail="模板的数据源与资源包数据源不匹配")
        
        # 创建资源包
        package = ResourcePackage(
            name=package_data.name,
            description=package_data.description,
            type=package_data.type,
            template_id=package_data.template_id,
            template_type=package_data.template_type,
            dynamic_params=package_data.dynamic_params,
            datasource_id=package_data.datasource_id,
            resource_id=package_data.resource_id,
            created_by=user_id
        )
        
        self.db.add(package)
        await self.db.commit()
        await self.db.refresh(package)
        
        # 为创建者添加管理员权限
        permission = ResourcePackagePermission(
            package_id=package.id,
            user_id=user_id,
            permission_type=PermissionType.ADMIN,
            granted_by=user_id
        )
        self.db.add(permission)
        await self.db.commit()
        
        return ResourcePackageSchema.model_validate(package)

    async def update_package(self, package_id: int, package_data: ResourcePackageUpdate, user_id: int) -> ResourcePackageSchema:
        """更新资源包
        
        Args:
            package_id: 资源包ID
            package_data: 更新数据
            user_id: 用户ID
            
        Returns:
            ResourcePackageSchema: 更新后的资源包信息
        """
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.WRITE):
            raise HTTPException(status_code=403, detail="无权限修改此资源包")
        
        query = select(ResourcePackage).where(ResourcePackage.id == package_id)
        result = await self.db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(status_code=404, detail="资源包不存在")
        
        # 如果更新了模板信息，需要验证
        if package_data.template_id and package_data.template_id != package.template_id:
            template = await self._get_template(package_data.template_id, package_data.template_type or package.template_type)
            if not template:
                raise HTTPException(status_code=404, detail="关联的查询模板不存在")
            
            if template.datasource_id != package.datasource_id:
                raise HTTPException(status_code=400, detail="模板的数据源与资源包数据源不匹配")
        
        # 更新字段
        for field, value in package_data.model_dump(exclude_unset=True).items():
            setattr(package, field, value)
        
        await self.db.commit()
        await self.db.refresh(package)
        
        return ResourcePackageSchema.model_validate(package)

    async def get_package(self, package_id: int, user_id: int) -> ResourcePackageSchema:
        """获取资源包详情
        
        Args:
            package_id: 资源包ID
            user_id: 用户ID
            
        Returns:
            ResourcePackageSchema: 资源包信息
        """
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.READ):
            raise HTTPException(status_code=403, detail="无权限访问此资源包")
        
        query = select(ResourcePackage).options(
            selectinload(ResourcePackage.datasource),
            selectinload(ResourcePackage.resource),
            selectinload(ResourcePackage.creator),
            selectinload(ResourcePackage.tags)
        ).where(ResourcePackage.id == package_id)
        
        result = await self.db.execute(query)
        package = result.scalar_one_or_none()
        
        if not package:
            raise HTTPException(status_code=404, detail="资源包不存在")
        
        return ResourcePackageSchema.model_validate(package)

    async def query_package(self, package_id: int, query_req: ResourcePackageQueryRequest, user_id: int) -> ResourcePackageQueryResponse:
        """执行资源包查询
        
        Args:
            package_id: 资源包ID
            query_req: 查询请求
            user_id: 用户ID
            
        Returns:
            ResourcePackageQueryResponse: 查询结果
        """
        # 检查权限
        if not await self._check_permission(package_id, user_id, PermissionType.READ):
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
            # 检查是否有关联的查询模板
            if package.template_id is None:
                raise HTTPException(status_code=400, detail="资源包未关联查询模板，无法执行查询")
            
            # 获取关联的查询模板
            template = await self._get_template(package.template_id, package.template_type)
            if not template:
                raise HTTPException(status_code=404, detail="关联的查询模板不存在")
            
            if package.template_type == PackageType.SQL:
                query_result = await self._execute_sql_query_with_template(package, template, query_req)
            elif package.template_type == PackageType.ELASTICSEARCH:
                query_result = await self._execute_es_query_with_template(package, template, query_req)
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
            success=status == QueryStatus.SUCCESS,
            columns=query_result.get("columns", []),
            data=query_result["data"],
            total_count=query_result["total"],
            generated_query=generated_query,
            execution_time=execution_time,
            error_message=error_message
        )



    async def _get_template(self, template_id: int, template_type: str) -> Union[SQLQueryTemplate, ESQueryTemplate, None]:
        """获取查询模板
        
        Args:
            template_id: 模板ID
            template_type: 模板类型
            
        Returns:
            Union[SQLQueryTemplate, ESQueryTemplate, None]: 查询模板
        """
        if template_type == 'sql':
            query = select(SQLQueryTemplate).where(SQLQueryTemplate.id == template_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        elif template_type == 'elasticsearch':
            query = select(ESQueryTemplate).where(ESQueryTemplate.id == template_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        return None

    async def _execute_sql_query_with_template(
        self, 
        package: ResourcePackage, 
        template: SQLQueryTemplate, 
        query_req: ResourcePackageQueryRequest
    ) -> Dict[str, Any]:
        """基于SQL模板执行查询
        
        Args:
            package: 资源包
            template: SQL查询模板
            query_req: 查询请求
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        # 获取模板的查询语句
        base_query = template.query
        
        # 获取模板配置
        template_config = template.config or {}
        
        # 合并资源包的动态参数
        effective_params = {}
        if template_config.get('dynamic_conditions'):
            for condition in template_config['dynamic_conditions']:
                param_key = condition.get('param_key')
                if param_key:
                    # 优先使用查询请求中的参数
                    if param_key in query_req.dynamic_params:
                        effective_params[param_key] = query_req.dynamic_params[param_key]
                    # 其次使用资源包的动态参数
                    elif package.dynamic_params and param_key in package.dynamic_params:
                        effective_params[param_key] = package.dynamic_params[param_key]
                    # 最后使用模板的默认值
                    elif condition.get('default_value') is not None:
                        effective_params[param_key] = condition['default_value']
                    # 如果是必需参数但没有值，抛出异常
                    elif condition.get('required', True):
                        raise HTTPException(status_code=400, detail=f"缺少必需参数: {param_key}")
        
        # 处理查询语句中的参数占位符
        processed_query = self._process_sql_parameters(base_query, effective_params)
        
        # 添加分页
        if query_req.limit:
            processed_query += f" LIMIT {query_req.limit}"
        if query_req.offset:
            processed_query += f" OFFSET {query_req.offset}"
        
        try:
            # 执行查询
            query_result = await self.data_resource_service.execute_sql_query(
                package.datasource_id, processed_query, effective_params
            )
            
            return {
                "data": query_result.get("data", []),
                "total": len(query_result.get("data", [])),
                "columns": query_result.get("columns", []),
                "query": processed_query
            }
        except Exception as e:
            logger.error(f"SQL查询执行失败: {e}")
            raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")

    async def _execute_es_query_with_template(
        self, 
        package: ResourcePackage, 
        template: ESQueryTemplate, 
        query_req: ResourcePackageQueryRequest
    ) -> Dict[str, Any]:
        """基于ES模板执行查询
        
        Args:
            package: 资源包
            template: ES查询模板
            query_req: 查询请求
            
        Returns:
            Dict[str, Any]: 查询结果
        """
        # 获取模板的查询配置
        base_query = template.query
        indices = template.indices
        
        # 合并动态参数
        effective_params = {}
        if package.dynamic_params:
            effective_params.update(package.dynamic_params)
        if query_req.dynamic_params:
            effective_params.update(query_req.dynamic_params)
        
        # 处理ES查询中的参数
        processed_query = self._process_es_parameters(base_query, effective_params)
        
        # 添加分页
        if query_req.limit or query_req.offset:
            if "size" not in processed_query:
                processed_query["size"] = query_req.limit or 100
            if "from" not in processed_query:
                processed_query["from"] = query_req.offset or 0
        
        try:
            # 执行ES查询
            query_result = await self.elasticsearch_service.search(
                package.datasource_id, indices, processed_query
            )
            
            return {
                "data": query_result.get("hits", []),
                "total": query_result.get("total", 0),
                "columns": [],  # ES查询的列信息需要从结果中推断
                "query": json.dumps(processed_query, ensure_ascii=False)
            }
        except Exception as e:
            logger.error(f"ES查询执行失败: {e}")
            raise HTTPException(status_code=500, detail=f"查询执行失败: {str(e)}")

    def _process_sql_parameters(self, query: str, params: Dict[str, Any]) -> str:
        """处理SQL查询中的参数占位符
        
        Args:
            query: SQL查询语句
            params: 参数字典
            
        Returns:
            str: 处理后的查询语句
        """
        # 简单的参数替换实现
        # 在实际项目中，应该使用更安全的参数绑定方式
        processed_query = query
        for param_name, param_value in params.items():
            placeholder = f":{param_name}"
            if isinstance(param_value, str):
                processed_query = processed_query.replace(placeholder, f"'{param_value}'")
            else:
                processed_query = processed_query.replace(placeholder, str(param_value))
        
        return processed_query

    def _process_es_parameters(self, query: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        """处理ES查询中的参数
        
        Args:
            query: ES查询配置
            params: 参数字典
            
        Returns:
            Dict[str, Any]: 处理后的查询配置
        """
        # 深拷贝查询配置
        processed_query = json.loads(json.dumps(query))
        
        # 递归替换参数占位符
        def replace_params(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    obj[key] = replace_params(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    obj[i] = replace_params(item)
            elif isinstance(obj, str) and obj.startswith("{{") and obj.endswith("}}"):
                param_name = obj[2:-2].strip()
                if param_name in params:
                    return params[param_name]
            return obj
        
        return replace_params(processed_query)

    async def _check_permission(self, package_id: int, user_id: int, required_permission: PermissionType) -> bool:
        """检查用户权限
        
        Args:
            package_id: 资源包ID
            user_id: 用户ID
            required_permission: 所需权限
            
        Returns:
            bool: 是否有权限
        """
        query = select(ResourcePackagePermission).where(
            and_(
                ResourcePackagePermission.package_id == package_id,
                ResourcePackagePermission.user_id == user_id,
                ResourcePackagePermission.is_active == True
            )
        )
        
        result = await self.db.execute(query)
        permission = result.scalar_one_or_none()
        
        if not permission:
            return False
        
        # 检查权限等级
        permission_levels = {
            PermissionType.READ: 1,
            PermissionType.WRITE: 2,
            PermissionType.ADMIN: 3
        }
        
        user_level = permission_levels.get(permission.permission_type, 0)
        required_level = permission_levels.get(required_permission, 0)
        
        return user_level >= required_level

    async def _record_query_history(
        self, 
        package_id: int, 
        user_id: int, 
        dynamic_params: Dict[str, Any],
        generated_query: Optional[str], 
        result_count: int, 
        execution_time: int,
        status: QueryStatus, 
        error_message: Optional[str]
    ):
        """记录查询历史
        
        Args:
            package_id: 资源包ID
            user_id: 用户ID
            dynamic_params: 动态参数
            generated_query: 生成的查询语句
            result_count: 结果行数
            execution_time: 执行时间
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
            error_message=error_message
        )
        
        self.db.add(history)
        await self.db.commit()