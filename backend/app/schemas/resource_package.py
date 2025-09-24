"""资源包相关的Pydantic模式定义"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class PackageType(str, Enum):
    """资源包类型枚举"""
    SQL = "sql"
    ELASTICSEARCH = "elasticsearch"


class PermissionType(str, Enum):
    """权限类型枚举"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class QueryStatus(str, Enum):
    """查询状态枚举"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class ConditionOperator(str, Enum):
    """条件操作符枚举"""
    EQ = "="
    NE = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    LIKE = "LIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"
    NOT_BETWEEN = "NOT BETWEEN"


class LogicOperator(str, Enum):
    """逻辑操作符枚举"""
    AND = "AND"
    OR = "OR"


class SortDirection(str, Enum):
    """排序方向枚举"""
    ASC = "ASC"
    DESC = "DESC"


# 基础配置模式
class BaseConfig(BaseModel):
    """基础配置模式"""
    schema: Optional[str] = Field(None, description="数据库/索引名称")
    table: Optional[str] = Field(None, description="表名/索引名")
    fields: List[str] = Field(default_factory=list, description="字段列表")
    
    class Config:
        extra = "allow"


# 条件配置模式
class ConditionConfig(BaseModel):
    """条件配置模式"""
    field: str = Field(..., description="字段名")
    operator: ConditionOperator = Field(..., description="操作符")
    value: Optional[Union[str, int, float, List[Any]]] = Field(None, description="值")
    logic: LogicOperator = Field(LogicOperator.AND, description="逻辑操作符")
    description: Optional[str] = Field(None, description="条件描述")


# 动态条件配置模式
class DynamicConditionConfig(ConditionConfig):
    """动态条件配置模式"""
    default_value: Optional[Union[str, int, float, List[Any]]] = Field(None, description="默认值")
    required: bool = Field(False, description="是否必填")
    param_name: Optional[str] = Field(None, description="参数名称")
    param_type: Optional[str] = Field("string", description="参数类型")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")


# 排序配置模式
class OrderConfig(BaseModel):
    """排序配置模式"""
    field: str = Field(..., description="排序字段")
    direction: SortDirection = Field(SortDirection.ASC, description="排序方向")


# 标签模式
class ResourcePackageTagBase(BaseModel):
    """资源包标签基础模式"""
    tag_name: str = Field(..., max_length=100, description="标签名称")
    tag_color: str = Field("#409EFF", max_length=20, description="标签颜色")


class ResourcePackageTagCreate(ResourcePackageTagBase):
    """创建资源包标签模式"""
    pass


class ResourcePackageTag(ResourcePackageTagBase):
    """资源包标签模式"""
    id: int
    package_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 权限模式
class ResourcePackagePermissionBase(BaseModel):
    """资源包权限基础模式"""
    user_id: int = Field(..., description="用户ID")
    permission_type: PermissionType = Field(..., description="权限类型")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ResourcePackagePermissionCreate(ResourcePackagePermissionBase):
    """创建资源包权限模式"""
    pass


class ResourcePackagePermission(ResourcePackagePermissionBase):
    """资源包权限模式"""
    id: int
    package_id: int
    granted_by: int
    granted_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# 查询历史模式
class ResourcePackageQueryHistoryBase(BaseModel):
    """资源包查询历史基础模式"""
    dynamic_params: Optional[Dict[str, Any]] = Field(None, description="动态参数值")
    generated_query: Optional[str] = Field(None, description="生成的查询语句")
    result_count: int = Field(0, description="结果行数")
    execution_time: int = Field(0, description="执行时间(毫秒)")
    status: QueryStatus = Field(QueryStatus.SUCCESS, description="执行状态")
    error_message: Optional[str] = Field(None, description="错误信息")


class ResourcePackageQueryHistory(ResourcePackageQueryHistoryBase):
    """资源包查询历史模式"""
    id: int
    package_id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# 资源包模式
class ResourcePackageBase(BaseModel):
    """资源包基础模式"""
    name: str = Field(..., max_length=255, description="资源包名称")
    description: Optional[str] = Field(None, description="资源包描述")
    type: PackageType = Field(..., description="资源包类型")
    datasource_id: int = Field(..., description="数据源ID")
    resource_id: Optional[int] = Field(None, description="数据资源ID")
    template_id: Optional[int] = Field(None, description="查询模板ID")
    template_type: str = Field(..., description="模板类型(sql/elasticsearch)")
    dynamic_params: Optional[Dict[str, Any]] = Field(None, description="动态参数")
    is_active: bool = Field(True, description="是否启用")


class ResourcePackageCreate(ResourcePackageBase):
    """创建资源包模式"""
    tags: Optional[List[str]] = Field(default_factory=list, description="标签列表")
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('资源包名称不能为空')
        return v.strip()
    
    @validator('template_type')
    def validate_template_type(cls, v):
        if v not in ['sql', 'elasticsearch']:
            raise ValueError('模板类型必须是sql或elasticsearch')
        return v


class ResourcePackageUpdate(BaseModel):
    """更新资源包模式"""
    name: Optional[str] = Field(None, max_length=255, description="资源包名称")
    description: Optional[str] = Field(None, description="资源包描述")
    template_id: Optional[int] = Field(None, description="查询模板ID")
    template_type: Optional[str] = Field(None, description="模板类型(sql/elasticsearch)")
    dynamic_params: Optional[Dict[str, Any]] = Field(None, description="动态参数")
    is_active: Optional[bool] = Field(None, description="是否启用")
    tags: Optional[List[str]] = Field(None, description="标签列表")


class ResourcePackage(ResourcePackageBase):
    """资源包模式"""
    id: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    tags: List[ResourcePackageTag] = Field(default_factory=list, description="标签列表")
    permissions: List[ResourcePackagePermission] = Field(default_factory=list, description="权限列表")
    
    class Config:
        from_attributes = True


class ResourcePackageResponse(BaseModel):
    """资源包响应模式（不包含dynamic_params）"""
    id: int
    name: str = Field(..., max_length=255, description="资源包名称")
    description: Optional[str] = Field(None, description="资源包描述")
    type: PackageType = Field(..., description="资源包类型")
    datasource_id: int = Field(..., description="数据源ID")
    resource_id: Optional[int] = Field(None, description="数据资源ID")
    template_id: Optional[int] = Field(None, description="查询模板ID")
    template_type: str = Field(..., description="模板类型(sql/elasticsearch)")
    is_active: bool = Field(True, description="是否启用")
    created_by: int
    created_at: datetime
    updated_at: datetime
    tags: List[ResourcePackageTag] = Field(default_factory=list, description="标签列表")
    permissions: List[ResourcePackagePermission] = Field(default_factory=list, description="权限列表")
    
    class Config:
        from_attributes = True


# 查询请求模式
class ResourcePackageQueryRequest(BaseModel):
    """资源包查询请求模式"""
    dynamic_params: Dict[str, Any] = Field(default_factory=dict, description="动态参数值")
    limit: Optional[int] = Field(None, ge=1, le=10000, description="限制条数")
    offset: int = Field(0, ge=0, description="偏移量")
    format: Optional[str] = Field("json", description="返回格式")


# 查询响应模式
class ResourcePackageQueryResponse(BaseModel):
    """资源包查询响应模式"""
    success: bool = Field(..., description="是否成功")
    columns: List[str] = Field(default_factory=list, description="列名列表")
    data: List[List[Any]] = Field(default_factory=list, description="数据行")
    total_count: int = Field(0, description="总行数")
    execution_time: int = Field(0, description="执行时间(毫秒)")
    query_id: Optional[str] = Field(None, description="查询ID")
    generated_query: Optional[str] = Field(None, description="生成的查询语句")
    error_message: Optional[str] = Field(None, description="错误信息")


# 搜索请求模式
class ResourcePackageSearchRequest(BaseModel):
    """资源包搜索请求模式"""
    keyword: Optional[str] = Field(None, description="关键词")
    type: Optional[PackageType] = Field(None, description="资源包类型")
    datasource_id: Optional[int] = Field(None, description="数据源ID")
    created_by: Optional[int] = Field(None, description="创建者ID")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_active: Optional[bool] = Field(None, description="是否启用")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页大小")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")


# 列表响应模式
class ResourcePackageListResponse(BaseModel):
    """资源包列表响应模式"""
    items: List[ResourcePackage] = Field(default_factory=list, description="资源包列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    size: int = Field(20, description="每页大小")
    pages: int = Field(0, description="总页数")


# 参数信息模式
class ResourcePackageParamInfo(BaseModel):
    """资源包参数信息模式"""
    param_name: str = Field(..., description="参数名称")
    field: str = Field(..., description="字段名")
    operator: ConditionOperator = Field(..., description="操作符")
    param_type: str = Field("string", description="参数类型")
    default_value: Optional[Any] = Field(None, description="默认值")
    required: bool = Field(False, description="是否必填")
    description: Optional[str] = Field(None, description="参数描述")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")