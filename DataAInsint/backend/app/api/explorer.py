from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import io
import csv
from app.models.schemas import (
    TableInfo, TableDetailResponse, SQLExecuteRequest, SQLExecuteResponse,
    SQLHistoryCreate, SQLHistoryResponse, TableDataRequest,
    TableStructureRequest, CreateTableRequest, CreateTableByDDLRequest,
    TableOperationResponse, TableChangeLogEntry, TableChangeLogResponse
)
from app.database.sqlite_db import execute_query, execute_insert
from app.services.database_service import DatabaseService
from datetime import datetime

router = APIRouter()

async def get_datasource_info(datasource_id: int):
    """获取数据源信息"""
    results = execute_query(
        "SELECT * FROM datasources WHERE id = ?", (datasource_id,)
    )
    
    if not results:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    return results[0]

@router.get("/schemas/{datasource_id}")
async def get_schemas(datasource_id: int):
    """获取数据源的模式列表"""
    try:
        datasource = await get_datasource_info(datasource_id)
        
        # 检查是否为支持Schema的数据库
        if datasource['db_type'] not in ['oracle', 'mysql', 'doris']:
            raise HTTPException(status_code=400, detail="该数据库类型不支持模式查询")
        
        # 获取模式列表
        schemas = DatabaseService.get_schemas(
            datasource['db_type'], datasource['host'], datasource['port'],
            datasource['database_name'], datasource['username'], datasource['password'],
            datasource.get('oracle_connection_type', 'service_name')
        )
        
        return schemas
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模式列表失败: {str(e)}")

@router.get("/tables/{datasource_id}", response_model=List[TableInfo])
async def get_tables(datasource_id: int):
    """获取指定数据源的表列表"""
    try:
        datasource = await get_datasource_info(datasource_id)
        
        tables = DatabaseService.get_tables(
            datasource['db_type'], datasource['host'], datasource['port'],
            datasource['database_name'], datasource['username'], datasource['password'],
            datasource.get('oracle_connection_type', 'service_name')
        )
        
        return tables
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")

@router.get("/tables/{datasource_id}/{schema}")
async def get_tables_by_schema(datasource_id: int, schema: str):
    """根据模式获取数据源的表列表"""
    try:
        datasource = await get_datasource_info(datasource_id)
        
        # 检查是否为支持Schema的数据库
        if datasource['db_type'] not in ['oracle', 'mysql', 'doris']:
            raise HTTPException(status_code=400, detail="该数据库类型不支持按模式查询表")
        
        # 根据模式获取表列表
        tables = DatabaseService.get_tables_by_schema(
            datasource['db_type'], datasource['host'], datasource['port'],
            datasource['database_name'], datasource['username'], datasource['password'],
            schema, datasource.get('oracle_connection_type', 'service_name')
        )
        
        return tables
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")

@router.get("/table-detail/{datasource_id}/{table_name}", response_model=TableDetailResponse)
async def get_table_detail(datasource_id: int, table_name: str, schema: str = None):
    """获取表的详细信息"""
    try:
        datasource = await get_datasource_info(datasource_id)
        
        # 对于Oracle，始终使用配置表中的database_name（SID或服务名）进行连接
        # schema参数用于指定查询的用户模式，不影响连接参数
        if datasource['db_type'].lower() == 'oracle':
            # Oracle: 连接使用配置的database_name，schema作为查询参数
            table_detail = DatabaseService.get_table_detail(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                table_name, datasource.get('oracle_connection_type', 'service_name'), schema
            )
        else:
            # MySQL等：schema可以作为数据库名使用
            target_database = schema if schema else datasource['database_name']
            table_detail = DatabaseService.get_table_detail(
                 datasource['db_type'], datasource['host'], datasource['port'],
                 target_database, datasource['username'], datasource['password'],
                 table_name, datasource.get('oracle_connection_type', 'service_name'), None
             )
        
        return table_detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表详情失败: {str(e)}")

@router.post("/table-data", response_model=SQLExecuteResponse)
async def get_table_data(request: TableDataRequest):
    """获取表数据"""
    try:
        datasource = await get_datasource_info(request.datasource_id)
        
        # 对于Oracle，始终使用配置表中的database_name（SID或服务名）进行连接
        # schema参数用于指定查询的用户模式，不影响连接参数
        if datasource['db_type'].lower() == 'oracle':
            # Oracle: 连接使用配置的database_name，schema作为查询参数
            result = DatabaseService.get_table_data(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                request.table_name, request.limit or 100, request.offset or 0,
                datasource.get('oracle_connection_type', 'service_name'), request.schema
            )
        else:
            # MySQL等：schema可以作为数据库名使用
            target_database = request.schema if request.schema else datasource['database_name']
            result = DatabaseService.get_table_data(
                datasource['db_type'], datasource['host'], datasource['port'],
                target_database, datasource['username'], datasource['password'],
                request.table_name, request.limit or 100, request.offset or 0,
                datasource.get('oracle_connection_type', 'service_name'), None
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表数据失败: {str(e)}")

@router.post("/execute-sql", response_model=SQLExecuteResponse)
async def execute_sql(request: SQLExecuteRequest):
    """执行SQL查询"""
    try:
        datasource = await get_datasource_info(request.datasource_id)
        
        # 对于Oracle，始终使用配置表中的database_name（SID或服务名）进行连接
        # schema参数用于指定查询的用户模式，不影响连接参数
        if datasource['db_type'].lower() == 'oracle':
            # Oracle: 连接使用配置的database_name，schema作为查询参数
            result = DatabaseService.execute_sql(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                request.sql, request.limit or 1000,
                datasource.get('oracle_connection_type', 'service_name'), request.schema
            )
        else:
            # MySQL等：schema可以作为数据库名使用
            target_database = request.schema if request.schema else datasource['database_name']
            result = DatabaseService.execute_sql(
                datasource['db_type'], datasource['host'], datasource['port'],
                target_database, datasource['username'], datasource['password'],
                request.sql, request.limit or 1000,
                datasource.get('oracle_connection_type', 'service_name'), None
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行SQL失败: {str(e)}")

@router.post("/sql-history", response_model=SQLHistoryResponse)
async def save_sql_history(request: SQLHistoryCreate):
    """保存SQL历史"""
    try:
        # 验证数据源存在
        await get_datasource_info(request.datasource_id)
        
        query = """
            INSERT INTO sql_history (datasource_id, sql_content, name, description)
            VALUES (?, ?, ?, ?)
        """
        
        history_id = execute_insert(query, (
            request.datasource_id, request.sql_content, 
            request.name, request.description
        ))
        
        # 查询创建的历史记录
        result = execute_query(
            "SELECT * FROM sql_history WHERE id = ?", (history_id,)
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="保存SQL历史失败")
        
        row = result[0]
        return SQLHistoryResponse(
            id=row['id'],
            datasource_id=row['datasource_id'],
            sql_content=row['sql_content'],
            name=row['name'],
            description=row['description'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sql-history/{datasource_id}", response_model=List[SQLHistoryResponse])
async def get_sql_history(datasource_id: int):
    """获取指定数据源的SQL历史"""
    try:
        # 验证数据源存在
        await get_datasource_info(datasource_id)
        
        results = execute_query(
            "SELECT * FROM sql_history WHERE datasource_id = ? ORDER BY created_at DESC",
            (datasource_id,)
        )
        
        history_list = []
        for row in results:
            history_list.append(SQLHistoryResponse(
                id=row['id'],
                datasource_id=row['datasource_id'],
                sql_content=row['sql_content'],
                name=row['name'],
                description=row['description'],
                created_at=datetime.fromisoformat(row['created_at'])
            ))
        
        return history_list
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sql-history-detail/{history_id}", response_model=SQLHistoryResponse)
async def get_sql_history_detail(history_id: int):
    """获取SQL历史详情"""
    try:
        results = execute_query(
            "SELECT * FROM sql_history WHERE id = ?", (history_id,)
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="SQL历史不存在")
        
        row = results[0]
        return SQLHistoryResponse(
            id=row['id'],
            datasource_id=row['datasource_id'],
            sql_content=row['sql_content'],
            name=row['name'],
            description=row['description'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sql-history/{history_id}")
async def delete_sql_history(history_id: int):
    """删除SQL历史"""
    try:
        # 检查历史记录是否存在
        existing = execute_query(
            "SELECT * FROM sql_history WHERE id = ?", (history_id,)
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="SQL历史不存在")
        
        # 删除历史记录
        from app.database.sqlite_db import execute_update
        execute_update(
            "DELETE FROM sql_history WHERE id = ?", (history_id,)
        )
        
        return {"message": "SQL历史删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export-sql-result")
async def export_sql_result(request: SQLExecuteRequest):
    """导出SQL查询结果为CSV文件"""
    try:
        datasource = await get_datasource_info(request.datasource_id)
        
        # 对于Oracle，始终使用配置表中的database_name（SID或服务名）进行连接
        # schema参数用于指定查询的用户模式，不影响连接参数
        if datasource['db_type'].lower() == 'oracle':
            # Oracle: 连接使用配置的database_name，schema作为查询参数
            result = DatabaseService.execute_sql(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                request.sql, request.limit or 10000,  # 导出时默认限制10000行
                datasource.get('oracle_connection_type', 'service_name'), request.schema
            )
        else:
            # MySQL等：schema可以作为数据库名使用
            target_database = request.schema if request.schema else datasource['database_name']
            result = DatabaseService.execute_sql(
                datasource['db_type'], datasource['host'], datasource['port'],
                target_database, datasource['username'], datasource['password'],
                request.sql, request.limit or 10000,  # 导出时默认限制10000行
                datasource.get('oracle_connection_type', 'service_name'), None
            )
        
        if not result.success:
            raise HTTPException(status_code=400, detail=f"SQL执行失败: {result.error_message}")
        
        # 创建CSV内容
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        if result.columns:
            writer.writerow(result.columns)
        
        # 写入数据
        if result.data:
            for row in result.data:
                # 确保所有值都转换为字符串，处理None值
                csv_row = [str(row.get(col, '')) if row.get(col) is not None else '' for col in result.columns]
                writer.writerow(csv_row)
        
        # 准备响应
        output.seek(0)
        csv_content = output.getvalue()
        output.close()
        
        # 生成文件名
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sql_result_{timestamp}.csv"
        
        # 返回CSV文件
        return StreamingResponse(
            io.BytesIO(csv_content.encode('utf-8-sig')),  # 使用utf-8-sig支持中文
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

# 表结构编辑相关接口
def translate_database_error(error_message: str) -> str:
    """将数据库错误信息翻译为用户友好的中文提示"""
    error_str = str(error_message).lower()
    
    # 列已存在错误
    if 'already exists' in error_str or 'duplicate column' in error_str:
        return "列名已存在，请使用不同的列名"
    
    # 字段名重复错误（Doris/StarRocks特有）
    if 'duplicate column name' in error_str or 'column already exists' in error_str:
        return "列名已存在，请使用不同的列名"
    
    # 数字格式错误（通常是默认值类型不匹配）
    if 'invalid number format' in error_str:
        # 提取字段名
        import re
        match = re.search(r'invalid number format:\s*(\w+)', error_str)
        if match:
            field_value = match.group(1)
            return f"数字类型字段的默认值格式错误：'{field_value}' 不是有效的数字，请检查默认值设置"
        return "数字类型字段的默认值格式错误，请检查默认值设置"
    
    # 数据类型不匹配错误
    if 'data type mismatch' in error_str or 'type mismatch' in error_str:
        return "数据类型不匹配，请检查字段类型和默认值是否匹配"
    
    # 列不存在错误
    if 'column' in error_str and ('not found' in error_str or 'does not exist' in error_str):
        return "指定的列不存在"
    
    # 表不存在错误
    if 'table' in error_str and ('not found' in error_str or 'does not exist' in error_str):
        return "指定的表不存在"
    
    # 数据类型错误
    if 'data type' in error_str or 'invalid type' in error_str:
        return "数据类型不正确"
    
    # 默认值错误
    if 'default value' in error_str or 'invalid default' in error_str:
        return "默认值设置错误，请检查默认值是否与字段类型匹配"
    
    # 权限错误
    if 'permission' in error_str or 'access denied' in error_str or 'privilege' in error_str:
        return "权限不足，无法执行此操作"
    
    # 语法错误
    if 'syntax error' in error_str or 'sql syntax' in error_str:
        return "SQL语法错误"
    
    # 连接错误
    if 'connection' in error_str and ('refused' in error_str or 'timeout' in error_str):
        return "数据库连接失败"
    
    # 约束违反错误
    if 'constraint' in error_str and 'violation' in error_str:
        return "违反数据库约束条件"
    
    # 默认返回原始错误信息
    return error_message

@router.post("/table-structure/modify", response_model=TableOperationResponse)
async def modify_table_structure(request: TableStructureRequest):
    """修改表结构（添加列、修改列、删除列）"""
    try:
        datasource = await get_datasource_info(request.datasource_id)
        
        # 调用数据库服务执行表结构修改
        if datasource['db_type'].lower() == 'oracle':
            result = DatabaseService.modify_table_structure(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                request.table_name, request.operation_type, request.column_data,
                datasource.get('oracle_connection_type', 'service_name'), request.schema
            )
        else:
            target_database = request.schema if request.schema else datasource['database_name']
            result = DatabaseService.modify_table_structure(
                datasource['db_type'], datasource['host'], datasource['port'],
                target_database, datasource['username'], datasource['password'],
                request.table_name, request.operation_type, request.column_data,
                datasource.get('oracle_connection_type', 'service_name'), None
            )
        
        # 记录变更日志
        await log_table_change(
            request.datasource_id, request.table_name, request.schema,
            request.operation_type, request.column_data, getattr(result, 'generated_sql', ''),
            getattr(result, 'execution_time', 0)
        )
        
        # 处理错误信息翻译
        if not result.success:
            error_message = getattr(result, 'error_message', '操作失败')
            translated_message = translate_database_error(error_message)
            message = translated_message
        else:
            message = '表结构修改成功'
        
        return TableOperationResponse(
            success=result.success,
            message=message,
            affected_rows=getattr(result, 'affected_rows', None),
            execution_time=getattr(result, 'execution_time', None),
            generated_sql=getattr(result, 'generated_sql', None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # 翻译异常错误信息
        translated_error = translate_database_error(str(e))
        raise HTTPException(status_code=500, detail=f"修改表结构失败: {translated_error}")

@router.post("/table/create", response_model=TableOperationResponse)
async def create_table(request: CreateTableRequest):
    """创建新表（向导模式）"""
    try:
        datasource = await get_datasource_info(request.datasource_id)
        
        # 将Pydantic模型转换为字典格式
        columns_dict = [col.dict() for col in request.columns]
        
        # 调用数据库服务创建表
        if datasource['db_type'].lower() == 'oracle':
            result = DatabaseService.create_table(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                request.table_name, columns_dict,
                datasource.get('oracle_connection_type', 'service_name'), request.schema
            )
        else:
            target_database = request.schema if request.schema else datasource['database_name']
            result = DatabaseService.create_table(
                datasource['db_type'], datasource['host'], datasource['port'],
                target_database, datasource['username'], datasource['password'],
                request.table_name, columns_dict,
                datasource.get('oracle_connection_type', 'service_name'), None
            )
        
        # 记录变更日志
        await log_table_change(
            request.datasource_id, request.table_name, request.schema,
            'create_table', {
                'columns': [col.dict() for col in request.columns],
                'table_comment': request.table_comment,
                'primary_keys': request.primary_keys,
                'indexes': request.indexes
            }, getattr(result, 'generated_sql', ''), getattr(result, 'execution_time', 0)
        )
        
        return TableOperationResponse(
            success=result.success,
            message=getattr(result, 'error_message', '操作成功') if not result.success else '表创建成功',
            affected_rows=getattr(result, 'affected_rows', None),
            execution_time=getattr(result, 'execution_time', None),
            generated_sql=getattr(result, 'generated_sql', None)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建表失败: {str(e)}")

@router.post("/table/create-by-ddl", response_model=TableOperationResponse)
async def create_table_by_ddl(request: CreateTableByDDLRequest):
    """通过DDL语句创建表（SQL命令行模式）"""
    try:
        datasource = await get_datasource_info(request.datasource_id)
        
        # 调用数据库服务执行DDL
        if datasource['db_type'].lower() == 'oracle':
            result = DatabaseService.execute_ddl(
                datasource['db_type'], datasource['host'], datasource['port'],
                datasource['database_name'], datasource['username'], datasource['password'],
                request.ddl_sql,
                datasource.get('oracle_connection_type', 'service_name'), request.schema
            )
        else:
            target_database = request.schema if request.schema else datasource['database_name']
            result = DatabaseService.execute_ddl(
                datasource['db_type'], datasource['host'], datasource['port'],
                target_database, datasource['username'], datasource['password'],
                request.ddl_sql,
                datasource.get('oracle_connection_type', 'service_name'), None
            )
        
        # 从DDL中提取表名（简单解析）
        table_name = extract_table_name_from_ddl(request.ddl_sql)
        
        # 记录变更日志
        await log_table_change(
            request.datasource_id, table_name, request.schema,
            'create_table_ddl', {'ddl_sql': request.ddl_sql},
            request.ddl_sql, getattr(result, 'execution_time', 0)
        )
        
        return TableOperationResponse(
            success=result.success,
            message=getattr(result, 'error_message', '操作成功') if not result.success else 'DDL执行成功',
            affected_rows=getattr(result, 'affected_rows', None),
            execution_time=getattr(result, 'execution_time', None),
            generated_sql=request.ddl_sql
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行DDL失败: {str(e)}")

@router.get("/table-change-log/{datasource_id}", response_model=TableChangeLogResponse)
async def get_table_change_log(datasource_id: int, table_name: str = None, page: int = 1, page_size: int = 20):
    """获取表结构变更日志"""
    try:
        # 验证数据源存在
        await get_datasource_info(datasource_id)
        
        # 构建查询条件
        where_clause = "WHERE datasource_id = ?"
        params = [datasource_id]
        
        if table_name:
            where_clause += " AND table_name = ?"
            params.append(table_name)
        
        # 获取总数
        count_query = f"SELECT COUNT(*) FROM table_change_log {where_clause}"
        count_result = execute_query(count_query, params)
        total_count = count_result[0][0] if count_result else 0
        
        # 获取分页数据
        offset = (page - 1) * page_size
        query = f"""
            SELECT id, datasource_id, table_name, schema_name, operation_type, 
                   operation_details, generated_sql, executed_by, execution_time, created_at
            FROM table_change_log {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        
        results = execute_query(query, params)
        
        logs = []
        for row in results:
            import json
            logs.append(TableChangeLogEntry(
                id=row[0],
                datasource_id=row[1],
                table_name=row[2],
                schema=row[3],
                operation_type=row[4],
                operation_details=json.loads(row[5]) if row[5] else {},
                generated_sql=row[6],
                executed_by=row[7],
                execution_time=row[8],
                created_at=row[9]
            ))
        
        return TableChangeLogResponse(
            logs=logs,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取变更日志失败: {str(e)}")

# 辅助函数
async def log_table_change(datasource_id: int, table_name: str, schema: str, 
                          operation_type: str, operation_details: dict, 
                          generated_sql: str, execution_time: float):
    """记录表结构变更日志"""
    try:
        import json
        query = """
            INSERT INTO table_change_log 
            (datasource_id, table_name, schema_name, operation_type, operation_details, 
             generated_sql, executed_by, execution_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        execute_insert(query, (
            datasource_id, table_name, schema, operation_type,
            json.dumps(operation_details, ensure_ascii=False),
            generated_sql, 'system', execution_time, datetime.now()
        ))
    except Exception as e:
        # 日志记录失败不应影响主要操作
        print(f"记录变更日志失败: {str(e)}")

def extract_table_name_from_ddl(ddl_sql: str) -> str:
    """从DDL语句中提取表名"""
    import re
    # 简单的正则表达式匹配CREATE TABLE语句中的表名
    match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`?([^\s`]+)`?\.)?`?([^\s`(]+)`?', ddl_sql, re.IGNORECASE)
    if match:
        return match.group(2) if match.group(2) else match.group(1)
    return 'unknown_table'