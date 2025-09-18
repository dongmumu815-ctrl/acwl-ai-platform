#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据资源表中数据源8相关的记录
"""

import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_data_resources():
    """检查数据资源表中的记录"""
    try:
        # 使用同步的pymysql连接
        engine = create_engine('mysql+pymysql://root:2wsx1QAZaczt@localhost:3306/acwl-ai-data')
        SessionLocal = sessionmaker(bind=engine)
        
        with SessionLocal() as db:
            # 查询数据源8相关的数据资源
            result = db.execute(text("""
                SELECT id, name, display_name, database_name, table_name, resource_type, datasource_id
                FROM acwl_data_resources 
                WHERE datasource_id = 8
            """))
            
            resources = result.fetchall()
            
            print("数据源8相关的数据资源:")
            if resources:
                for resource in resources:
                    print(f"ID: {resource.id}, 名称: {resource.name}, 显示名称: {resource.display_name}")
                    print(f"  数据库: {resource.database_name}, 表名: {resource.table_name}")
                    print(f"  资源类型: {resource.resource_type}, 数据源ID: {resource.datasource_id}")
                    print("-" * 50)
            else:
                print("没有找到数据源8相关的数据资源")
                
            # 同时检查数据源8的配置
            datasource_result = db.execute(text("""
                SELECT id, name, database_name, connection_params
                FROM acwl_datasources 
                WHERE id = 8
            """))
            
            datasource = datasource_result.fetchone()
            if datasource:
                print("\n数据源8的配置:")
                print(f"ID: {datasource.id}, 名称: {datasource.name}")
                print(f"数据库名称: {datasource.database_name}")
                print(f"连接参数: {datasource.connection_params}")
            else:
                print("\n未找到数据源8")
                
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    check_data_resources()