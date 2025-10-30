from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import (
    DataSourceCreate, DataSourceUpdate, DataSourceResponse, 
    ConnectionTestRequest, ConnectionTestResponse
)
from app.database.sqlite_db import execute_query, execute_insert, execute_update
from app.services.database_service import DatabaseService
from datetime import datetime

router = APIRouter()

@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(request: ConnectionTestRequest):
    """测试数据库连接"""
    return DatabaseService.test_connection(
        request.db_type, request.host, request.port,
        request.database_name, request.username, request.password,
        request.oracle_connection_type or "service_name"
    )

@router.post("/", response_model=DataSourceResponse)
async def create_datasource(datasource: DataSourceCreate):
    """创建数据源"""
    try:
        # 先测试连接
        test_result = DatabaseService.test_connection(
            datasource.db_type, datasource.host, datasource.port,
            datasource.database_name, datasource.username, datasource.password,
            datasource.oracle_connection_type or "service_name"
        )
        
        if not test_result.success:
            raise HTTPException(status_code=400, detail=f"数据库连接失败: {test_result.message}")
        
        # 插入数据源
        query = """
            INSERT INTO datasources (name, db_type, host, port, database_name, username, password, oracle_connection_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        datasource_id = execute_insert(query, (
            datasource.name, datasource.db_type, datasource.host, datasource.port,
            datasource.database_name, datasource.username, datasource.password,
            datasource.oracle_connection_type or "service_name"
        ))
        
        # 查询创建的数据源
        result = execute_query(
            "SELECT * FROM datasources WHERE id = ?", (datasource_id,)
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="创建数据源失败")
        
        row = result[0]
        return DataSourceResponse(
            id=row['id'],
            name=row['name'],
            db_type=row['db_type'],
            host=row['host'],
            port=row['port'],
            database_name=row['database_name'],
            username=row['username'],
            oracle_connection_type=row.get('oracle_connection_type', 'service_name'),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="数据源名称已存在")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DataSourceResponse])
async def get_datasources():
    """获取所有数据源"""
    try:
        results = execute_query("SELECT * FROM datasources ORDER BY created_at DESC")
        
        datasources = []
        for row in results:
            datasources.append(DataSourceResponse(
                id=row['id'],
                name=row['name'],
                db_type=row['db_type'],
                host=row['host'],
                port=row['port'],
                database_name=row['database_name'],
                username=row['username'],
                oracle_connection_type=row.get('oracle_connection_type', 'service_name'),
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at'])
            ))
        
        return datasources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{datasource_id}", response_model=DataSourceResponse)
async def get_datasource(datasource_id: int):
    """获取指定数据源"""
    try:
        results = execute_query(
            "SELECT * FROM datasources WHERE id = ?", (datasource_id,)
        )
        
        if not results:
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        row = results[0]
        return DataSourceResponse(
            id=row['id'],
            name=row['name'],
            db_type=row['db_type'],
            host=row['host'],
            port=row['port'],
            database_name=row['database_name'],
            username=row['username'],
            oracle_connection_type=row.get('oracle_connection_type', 'service_name'),
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{datasource_id}", response_model=DataSourceResponse)
async def update_datasource(datasource_id: int, datasource: DataSourceUpdate):
    """更新数据源"""
    try:
        # 检查数据源是否存在
        existing = execute_query(
            "SELECT * FROM datasources WHERE id = ?", (datasource_id,)
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        # 构建更新字段
        update_fields = []
        update_values = []
        
        if datasource.name is not None:
            update_fields.append("name = ?")
            update_values.append(datasource.name)
        if datasource.db_type is not None:
            update_fields.append("db_type = ?")
            update_values.append(datasource.db_type)
        if datasource.host is not None:
            update_fields.append("host = ?")
            update_values.append(datasource.host)
        if datasource.port is not None:
            update_fields.append("port = ?")
            update_values.append(datasource.port)
        if datasource.database_name is not None:
            update_fields.append("database_name = ?")
            update_values.append(datasource.database_name)
        if datasource.username is not None:
            update_fields.append("username = ?")
            update_values.append(datasource.username)
        if datasource.password is not None:
            update_fields.append("password = ?")
            update_values.append(datasource.password)
        if datasource.oracle_connection_type is not None:
            update_fields.append("oracle_connection_type = ?")
            update_values.append(datasource.oracle_connection_type)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="没有提供更新字段")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(datasource_id)
        
        query = f"UPDATE datasources SET {', '.join(update_fields)} WHERE id = ?"
        execute_update(query, tuple(update_values))
        
        # 返回更新后的数据源
        return await get_datasource(datasource_id)
    except HTTPException:
        raise
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="数据源名称已存在")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{datasource_id}")
async def delete_datasource(datasource_id: int):
    """删除数据源"""
    try:
        # 检查数据源是否存在
        existing = execute_query(
            "SELECT * FROM datasources WHERE id = ?", (datasource_id,)
        )
        
        if not existing:
            raise HTTPException(status_code=404, detail="数据源不存在")
        
        # 删除相关的SQL历史
        execute_update(
            "DELETE FROM sql_history WHERE datasource_id = ?", (datasource_id,)
        )
        
        # 删除数据源
        execute_update(
            "DELETE FROM datasources WHERE id = ?", (datasource_id,)
        )
        
        return {"message": "数据源删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))