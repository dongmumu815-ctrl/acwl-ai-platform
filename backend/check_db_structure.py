#!/usr/bin/env python3
"""
检查数据库表结构
"""
import sys
import os
import asyncio
sys.path.append('.')

from app.core.database import sync_engine, SessionLocal
from sqlalchemy import inspect, text, create_engine

def check_custom_apis_table():
    """检查custom_apis表结构"""
    try:
        # 使用同步引擎进行检查
        inspector = inspect(sync_engine)
        
        # 检查表是否存在
        tables = inspector.get_table_names()
        print("当前数据库中的表:")
        for table in tables:
            print(f"  - {table}")
        
        if 'custom_apis' in tables:
            print("\ncustom_apis表的列:")
            columns = inspector.get_columns('custom_apis')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable: {col.get('nullable', True)})")
        else:
            print("\n❌ custom_apis表不存在!")
            
        # 测试简单查询
        print("\n测试数据库连接...")
        with SessionLocal() as db:
            result = db.execute(text("SELECT DATABASE()")).fetchone()
            print(f"✅ 当前连接的数据库: {result[0]}")
            
        # 检查acwl_api_system数据库
        print("\n检查acwl_api_system数据库...")
        api_system_url = "mysql+pymysql://root:2wsx1QAZaczt@10.20.1.200:3306/acwl_api_system?charset=utf8mb4"
        api_system_engine = create_engine(api_system_url)
        api_inspector = inspect(api_system_engine)
        
        api_tables = api_inspector.get_table_names()
        print("acwl_api_system数据库中的表:")
        for table in api_tables:
            print(f"  - {table}")
            
        if 'custom_apis' in api_tables:
            print("\n✅ custom_apis表在acwl_api_system数据库中存在!")
            columns = api_inspector.get_columns('custom_apis')
            for col in columns:
                print(f"  - {col['name']}: {col['type']} (nullable: {col.get('nullable', True)})")
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_custom_apis_table()