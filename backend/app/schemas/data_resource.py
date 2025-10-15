#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据资源中心相关模式
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

from app.models.data_resource import (
    ResourceType,
    ResourceStatus,
    PermissionType,
    AccessType,
    AccessStatus,
    TagStatus
)
from app.schemas.datasource import DatasourceResponse


class DataResourceCategoryBase(BaseModel):
    """数据资源分类基础模式"""
    name: str = Field(..., description="分类名称", max_length=50)
    display_name: str = Field(..., description="显示名称", max_length=50)
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")


class DataResourceCategoryCreate(DataResourceCategoryBase):
    """创建数据资源分类模式"""
    pass


class DataResourceCategoryUpdate(BaseModel):
    """更新数据资源分类模式"""
    name: Optional[str] = Field(None, description="分类名称", max_length=50)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=50)
    description: Optional[str] = Field(None, description="分类描述")
    parent_id: Optional[int] = Field(None, description="父分类ID")
    sort_order: Optional[int] = Field(None, description="排序")
    is_active: Optional[bool] = Field(None, description="是否启用")


class DataResourceCategoryResponse(DataResourceCategoryBase):
    """数据资源分类响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="分类ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    children: Optional[List["DataResourceCategoryResponse"]] = Field(None, description="子分类")
    resource_count: Optional[int] = Field(None, description="资源数量")


class DataResourceBase(BaseModel):
    """数据资源基础模式"""
    name: str = Field(..., description="资源名称", max_length=100)
    display_name: str = Field(..., description="显示名称", max_length=100)
    description: Optional[str] = Field(None, description="资源描述")
    resource_type: ResourceType = Field(..., description="资源类型")
    datasource_id: int = Field(..., description="数据源ID")
    database_name: Optional[str] = Field(None, description="数据库名称(Doris)", max_length=100)
    table_name: Optional[str] = Field(None, description="表名称(Doris)", max_length=100)
    index_name: Optional[str] = Field(None, description="索引名称(ES)", max_length=100)
    schema_info: Optional[Dict[str, Any]] = Field(None, description="表结构信息")
    tags: Optional[Dict[str, Any]] = Field(None, description="标签信息")
    category_id: Optional[int] = Field(None, description="分类ID")
    is_public: bool = Field(False, description="是否公开")
    status: ResourceStatus = Field(ResourceStatus.ACTIVE, description="状态")


class DataResourceCreate(DataResourceBase):
    """创建数据资源模式"""
    pass


class DataResourceUpdate(BaseModel):
    """更新数据资源模式"""
    name: Optional[str] = Field(None, description="资源名称", max_length=100)
    display_name: Optional[str] = Field(None, description="显示名称", max_length=100)
    description: Optional[str] = Field(None, description="资源描述")
    database_name: Optional[str] = Field(None, description="数据库名称(Doris)", max_length=100)
    table_name: Optional[str] = Field(None, description="表名称(Doris)", max_length=100)
    index_name: Optional[str] = Field(None, description="索引名称(ES)", max_length=100)
    schema_info: Optional[Dict[str, Any]] = Field(None, description="表结构信息")
    tags: Optional[Dict[str, Any]] = Field(None, description="标签信息")
    category_id: Optional[int] = Field(None, description="分类ID")
    is_public: Optional[bool] = Field(None, description="是否公开")
    status: Optional[ResourceStatus] = Field(None, description="状态")


class DataResourceResponse(DataResourceBase):
    """数据资源响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="资源ID")
    view_count: int = Field(..., description="查看次数")
    query_count: int = Field(..., description="查询次数")
    last_accessed_at: Optional[datetime] = Field(None, description="最后访问时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: int = Field(..., description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")
    
    # 关联数据
    category: Optional[DataResourceCategoryResponse] = Field(None, description="分类信息")
    datasource: Optional[DatasourceResponse] = Field(None, description="数据源信息")
    tag_list: Optional[List["DataResourceTagResponse"]] = Field(None, description="标签列表")
    user_permission: Optional[PermissionType] = Field(None, description="用户权限")
    is_favorited: Optional[bool] = Field(None, description="是否已收藏")
    
    @classmethod
    def from_orm_with_tags(cls, obj):
        """从ORM对象创建响应对象，包含标签信息
        
        Args:
            obj: DataResource ORM对象
            
        Returns:
            DataResourceResponse对象
        """
        # 基础数据
        data = {
            'id': obj.id,
            'name': obj.name,
            'display_name': obj.display_name,
            'description': obj.description,
            'resource_type': obj.resource_type,
            'datasource_id': obj.datasource_id,
            'database_name': obj.database_name,
            'table_name': obj.table_name,
            'index_name': obj.index_name,
            'schema_info': obj.schema_info,
            # 返回数据库中的原始 tags 字段（JSON），以满足前端读取需求
            'tags': obj.tags if hasattr(obj, 'tags') else None,
            'category_id': obj.category_id,
            'is_public': obj.is_public,
            'status': obj.status,
            'view_count': obj.view_count,
            'query_count': obj.query_count,
            'last_accessed_at': obj.last_accessed_at,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'created_by': obj.created_by,
            'updated_by': obj.updated_by,
            'category': obj.category,
            'datasource': obj.datasource,
        }
        
        # 处理标签列表
        if hasattr(obj, 'tag_relations') and obj.tag_relations:
            data['tag_list'] = [
                DataResourceTagResponse.model_validate(relation.tag)
                for relation in obj.tag_relations
                if relation.tag  # 确保tag存在
            ]
        else:
            data['tag_list'] = []
            
        return cls.model_validate(data)


class DataResourceListResponse(BaseModel):
    """数据资源列表响应模式"""
    items: List[DataResourceResponse] = Field(..., description="资源列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")


class DataResourcePermissionBase(BaseModel):
    """数据资源权限基础模式"""
    resource_id: int = Field(..., description="资源ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    role_id: Optional[int] = Field(None, description="角色ID")
    permission_type: PermissionType = Field(..., description="权限类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    notes: Optional[str] = Field(None, description="备注")


class DataResourcePermissionCreate(DataResourcePermissionBase):
    """创建数据资源权限模式"""
    pass


class DataResourcePermissionUpdate(BaseModel):
    """更新数据资源权限模式"""
    permission_type: Optional[PermissionType] = Field(None, description="权限类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    is_active: Optional[bool] = Field(None, description="是否有效")
    notes: Optional[str] = Field(None, description="备注")


class DataResourcePermissionResponse(DataResourcePermissionBase):
    """数据资源权限响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="权限ID")
    granted_by: int = Field(..., description="授权者ID")
    granted_at: datetime = Field(..., description="授权时间")
    is_active: bool = Field(..., description="是否有效")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # 关联数据
    user: Optional[Dict[str, Any]] = Field(None, description="用户信息")
    granter: Optional[Dict[str, Any]] = Field(None, description="授权者信息")


class DataResourceQueryRequest(BaseModel):
    """数据资源查询请求模式"""
    sql: str = Field(..., description="查询SQL")
    params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    limit: Optional[int] = Field(100, description="限制条数", ge=1, le=10000)
    offset: Optional[int] = Field(0, description="偏移量", ge=0)
    save_query: bool = Field(False, description="是否保存查询")
    query_name: Optional[str] = Field(None, description="查询名称", max_length=100)


class DataResourceQueryResponse(BaseModel):
    """数据资源查询响应模式"""
    columns: List[Dict[str, Any]] = Field(..., description="列信息")
    data: List[Dict[str, Any]] = Field(..., description="数据")
    total: int = Field(..., description="总数")
    execution_time: int = Field(..., description="执行时间(毫秒)")
    query_id: Optional[int] = Field(None, description="查询ID")


class DataResourceSchemaResponse(BaseModel):
    """数据资源结构响应模式"""
    table_name: str = Field(..., description="表名")
    columns: List[Dict[str, Any]] = Field(..., description="列信息")
    indexes: Optional[List[Dict[str, Any]]] = Field(None, description="索引信息")
    row_count: Optional[int] = Field(None, description="行数")
    size: Optional[str] = Field(None, description="大小")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")


class DataResourcePreviewResponse(BaseModel):
    """数据资源预览响应模式"""
    columns: List[Dict[str, Any]] = Field(..., description="列信息")
    data: List[Dict[str, Any]] = Field(..., description="预览数据")
    total_rows: Optional[int] = Field(None, description="总行数")


class DataResourceTagBase(BaseModel):
    """数据资源标签基础模式"""
    name: str = Field(..., description="标签名称", max_length=50)
    color: str = Field("#409EFF", description="标签颜色", max_length=30)
    description: Optional[str] = Field(None, description="标签描述")
    status: TagStatus = Field(TagStatus.ACTIVE, description="标签状态")


class DataResourceTagCreate(DataResourceTagBase):
    """创建数据资源标签模式"""
    pass


class DataResourceTagUpdate(BaseModel):
    """更新数据资源标签模式"""
    name: Optional[str] = Field(None, description="标签名称", max_length=50)
    color: Optional[str] = Field(None, description="标签颜色", max_length=30)
    description: Optional[str] = Field(None, description="标签描述")
    status: Optional[TagStatus] = Field(None, description="标签状态")


class DataResourceTagResponse(DataResourceTagBase):
    """数据资源标签响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="标签ID")
    usage_count: int = Field(..., description="使用次数")
    status: TagStatus = Field(..., description="标签状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: int = Field(..., description="创建者ID")
    updated_by: Optional[int] = Field(None, description="更新者ID")


class DataResourceAccessLogResponse(BaseModel):
    """数据资源访问日志响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="日志ID")
    resource_id: int = Field(..., description="资源ID")
    user_id: int = Field(..., description="用户ID")
    access_type: AccessType = Field(..., description="访问类型")
    query_sql: Optional[str] = Field(None, description="查询SQL")
    result_count: Optional[int] = Field(None, description="结果数量")
    execution_time: Optional[int] = Field(None, description="执行时间(毫秒)")
    ip_address: Optional[str] = Field(None, description="IP地址")
    status: AccessStatus = Field(..., description="状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    accessed_at: datetime = Field(..., description="访问时间")
    
    # 关联数据
    user: Optional[Dict[str, Any]] = Field(None, description="用户信息")
    resource: Optional[Dict[str, Any]] = Field(None, description="资源信息")


class DataResourceQueryHistoryResponse(BaseModel):
    """数据资源查询历史响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(..., description="历史ID")
    resource_id: int = Field(..., description="资源ID")
    user_id: int = Field(..., description="用户ID")
    query_name: Optional[str] = Field(None, description="查询名称")
    query_sql: str = Field(..., description="查询SQL")
    query_params: Optional[Dict[str, Any]] = Field(None, description="查询参数")
    result_count: Optional[int] = Field(None, description="结果数量")
    execution_time: Optional[int] = Field(None, description="执行时间(毫秒)")
    is_saved: bool = Field(..., description="是否保存")
    created_at: datetime = Field(..., description="创建时间")
    
    # 关联数据
    user: Optional[Dict[str, Any]] = Field(None, description="用户信息")
    resource: Optional[Dict[str, Any]] = Field(None, description="资源信息")


class DataResourceSearchRequest(BaseModel):
    """数据资源搜索请求模式"""
    keyword: Optional[str] = Field(None, description="关键词")
    category_id: Optional[int] = Field(None, description="分类ID")
    resource_type: Optional[ResourceType] = Field(None, description="资源类型")
    datasource_id: Optional[int] = Field(None, description="数据源ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_public: Optional[bool] = Field(None, description="是否公开")
    status: Optional[ResourceStatus] = Field(None, description="状态")
    created_by: Optional[int] = Field(None, description="创建者ID")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")
    page: int = Field(1, description="页码", ge=1)
    size: int = Field(20, description="每页大小", ge=1, le=100)


class DataResourceStatisticsResponse(BaseModel):
    """数据资源统计响应模式"""
    total_resources: int = Field(..., description="总资源数")
    doris_resources: int = Field(..., description="Doris资源数")
    es_resources: int = Field(..., description="ES资源数")
    public_resources: int = Field(..., description="公开资源数")
    private_resources: int = Field(..., description="私有资源数")
    total_views: int = Field(..., description="总查看次数")
    total_queries: int = Field(..., description="总查询次数")
    active_users: int = Field(..., description="活跃用户数")
    category_stats: List[Dict[str, Any]] = Field(..., description="分类统计")
    tag_stats: List[Dict[str, Any]] = Field(..., description="标签统计")
    recent_activities: List[Dict[str, Any]] = Field(..., description="最近活动")


class BatchOperationRequest(BaseModel):
    """批量操作请求模式"""
    resource_ids: List[int] = Field(..., description="资源ID列表")
    operation: str = Field(..., description="操作类型")
    params: Optional[Dict[str, Any]] = Field(None, description="操作参数")


class BatchOperationResponse(BaseModel):
    """批量操作响应模式"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    success_ids: List[int] = Field(..., description="成功的资源ID")
    failed_items: List[Dict[str, Any]] = Field(..., description="失败的项目")
    message: str = Field(..., description="操作结果消息")


# 更新前向引用
DataResourceCategoryResponse.model_rebuild()
DataResourceResponse.model_rebuild()