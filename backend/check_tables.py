#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_tables():
    """检查数据库中的表"""
    try:
        # 创建同步数据库连接
        sync_url = settings.database_url  # 使用pymysql
        engine = create_engine(sync_url, echo=False)
        
        with engine.connect() as conn:
            # 检查所有表
            result = conn.execute(text('SHOW TABLES'))
            tables = [row[0] for row in result]
            print("数据库中的表:")
            for table in tables:
                print(f"  - {table}")
            
            # 检查数据资源相关表是否存在
            data_resource_tables = [
                'acwl_data_resources',
                'acwl_data_resource_categories', 
                'acwl_data_resource_permissions',
                'acwl_data_resource_tags',
                'acwl_data_resource_tag_relations'
            ]
            
            print("\n数据资源相关表检查:")
            for table in data_resource_tables:
                if table in tables:
                    print(f"  ✓ {table} - 存在")
                    # 检查表中的记录数
                    count_result = conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                    count = count_result.scalar()
                    print(f"    记录数: {count}")
                else:
                    print(f"  ✗ {table} - 不存在")
                    
    except Exception as e:
        print(f"检查数据库表时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_tables()