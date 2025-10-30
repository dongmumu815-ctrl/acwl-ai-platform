import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = "data_insight.db"

def get_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """初始化数据库表"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 创建数据源配置表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            db_type TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            database_name TEXT NOT NULL,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            oracle_connection_type TEXT DEFAULT 'service_name',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建SQL历史表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sql_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datasource_id INTEGER,
            sql_content TEXT NOT NULL,
            name TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (datasource_id) REFERENCES datasources (id)
        )
    """)
    
    # 创建表结构变更日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS table_change_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datasource_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            schema_name TEXT,
            operation_type TEXT NOT NULL,
            operation_details TEXT,
            generated_sql TEXT NOT NULL,
            executed_by TEXT,
            execution_time REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (datasource_id) REFERENCES datasources (id)
        )
    """)
    
    # 检查并添加oracle_connection_type字段（用于数据库升级）
    try:
        cursor.execute("ALTER TABLE datasources ADD COLUMN oracle_connection_type TEXT DEFAULT 'service_name'")
        conn.commit()
    except Exception:
        # 字段已存在，忽略错误
        pass
    
    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """执行查询并返回结果"""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()

def execute_update(query: str, params: tuple = ()) -> int:
    """执行更新操作并返回影响的行数"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

def execute_insert(query: str, params: tuple = ()) -> int:
    """执行插入操作并返回新记录的ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()