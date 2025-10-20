from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime

class DataSourceCreate(BaseModel):
    """创建数据源的请求模型"""
    name: str
    db_type: str  # oracle, mysql, doris
    host: str
    port: int
    database_name: str
    username: str
    password: str
    oracle_connection_type: Optional[str] = "service_name"  # service_name 或 sid，仅Oracle使用

class DataSourceUpdate(BaseModel):
    """更新数据源的请求模型"""
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    oracle_connection_type: Optional[str] = None  # service_name 或 sid，仅Oracle使用

class DataSourceResponse(BaseModel):
    """数据源响应模型"""
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    oracle_connection_type: Optional[str] = None  # service_name 或 sid，仅Oracle使用
    created_at: datetime
    updated_at: datetime

class ConnectionTestRequest(BaseModel):
    """连接测试请求模型"""
    db_type: str
    host: str
    port: int
    database_name: str
    username: str
    password: str
    oracle_connection_type: Optional[str] = "service_name"  # service_name 或 sid，仅Oracle使用

class ConnectionTestResponse(BaseModel):
    """连接测试响应模型"""
    success: bool
    message: str

class TableInfo(BaseModel):
    """表信息模型"""
    table_name: str
    table_type: str  # TABLE, VIEW
    table_comment: Optional[str] = None

class ColumnInfo(BaseModel):
    """列信息模型"""
    column_name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None
    column_comment: Optional[str] = None
    is_primary_key: bool = False

class TableDetailResponse(BaseModel):
    """表详情响应模型"""
    table_name: str
    table_type: str
    table_comment: Optional[str] = None
    columns: List[ColumnInfo]
    row_count: Optional[int] = None

class SQLExecuteRequest(BaseModel):
    """SQL执行请求模型"""
    datasource_id: int
    sql: str
    limit: Optional[int] = 1000
    schema: Optional[str] = None  # 可选的schema参数，用于多schema环境

class SQLExecuteResponse(BaseModel):
    """SQL执行响应模型"""
    success: bool
    columns: Optional[List[str]] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    total_count: Optional[int] = None  # 表的总行数，用于虚拟滚动
    execution_time: Optional[float] = None
    error_message: Optional[str] = None

class SQLHistoryCreate(BaseModel):
    """SQL历史创建请求模型"""
    datasource_id: int
    sql_content: str
    name: Optional[str] = None
    description: Optional[str] = None

class SQLHistoryResponse(BaseModel):
    """SQL历史响应模型"""
    id: int
    datasource_id: int
    sql_content: str
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

class TableDataRequest(BaseModel):
    """表数据请求模型"""
    datasource_id: int
    table_name: str
    limit: Optional[int] = 100
    offset: Optional[int] = 0
    schema: Optional[str] = None

# 表结构编辑相关模型
class ColumnCreateRequest(BaseModel):
    """添加列请求模型"""
    column_name: str
    data_type: str
    is_nullable: bool = True
    column_default: Optional[str] = None
    column_comment: Optional[str] = None
    after_column: Optional[str] = None  # 在指定列之后添加（MySQL支持）

class ColumnUpdateRequest(BaseModel):
    """修改列请求模型"""
    old_column_name: str
    new_column_name: Optional[str] = None
    data_type: Optional[str] = None
    is_nullable: Optional[bool] = None
    column_default: Optional[str] = None
    column_comment: Optional[str] = None

class ColumnDropRequest(BaseModel):
    """删除列请求模型"""
    column_name: str

class TableStructureRequest(BaseModel):
    """表结构操作请求模型"""
    datasource_id: int
    table_name: str
    schema: Optional[str] = None
    operation_type: str  # 'add_column', 'modify_column', 'drop_column'
    column_data: Optional[Dict[str, Any]] = None  # 列操作的具体数据

class CreateTableRequest(BaseModel):
    """创建表请求模型"""
    datasource_id: int
    table_name: str
    schema: Optional[str] = None
    columns: List[ColumnCreateRequest]
    table_comment: Optional[str] = None
    primary_keys: Optional[List[str]] = None  # 主键列名列表
    indexes: Optional[List[Dict[str, Any]]] = None  # 索引定义

class CreateTableByDDLRequest(BaseModel):
    """通过DDL创建表请求模型"""
    datasource_id: int
    ddl_sql: str
    schema: Optional[str] = None

class TableOperationResponse(BaseModel):
    """表操作响应模型"""
    success: bool
    message: str
    affected_rows: Optional[int] = None
    execution_time: Optional[float] = None
    generated_sql: Optional[str] = None  # 生成的SQL语句

class TableChangeLogEntry(BaseModel):
    """表结构变更日志条目模型"""
    id: int
    datasource_id: int
    table_name: str
    schema: Optional[str] = None
    operation_type: str  # 'create_table', 'add_column', 'modify_column', 'drop_column', 'drop_table'
    operation_details: Dict[str, Any]  # 操作详情（JSON格式）
    generated_sql: str  # 生成的SQL语句
    executed_by: Optional[str] = None  # 执行用户
    execution_time: float  # 执行耗时（秒）
    created_at: datetime

class TableChangeLogResponse(BaseModel):
    """表结构变更日志响应模型"""
    logs: List[TableChangeLogEntry]
    total_count: int
    page: int
    page_size: int