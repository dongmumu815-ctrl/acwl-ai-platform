#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接和模型数据查询
"""

import asyncio
import pymysql
from backend.app.core.config import settings


def test_database_sync():
    """使用同步方式测试数据库连接和查询"""
    
    try:
        # 创建数据库连接
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset=settings.DB_CHARSET
        )
        
        print(f"数据库连接成功！")
        print(f"连接信息: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
        
        with connection.cursor() as cursor:
            # 测试基本连接
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            print(f"数据库连接测试: {result}")
            
            # 检查表是否存在
            cursor.execute(
                "SELECT COUNT(*) as table_exists FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = 'acwl_models'",
                (settings.DB_NAME,)
            )
            table_exists = cursor.fetchone()[0]
            print(f"acwl_models表是否存在: {table_exists > 0}")
            
            if table_exists > 0:
                # 查询表结构
                cursor.execute("DESCRIBE acwl_models")
                columns = cursor.fetchall()
                print("\nacwl_models表结构:")
                for col in columns:
                    print(f"  {col[0]} - {col[1]} - {col[2]}")
                
                # 查询表中的数据数量
                cursor.execute("SELECT COUNT(*) FROM acwl_models")
                count = cursor.fetchone()[0]
                print(f"\nacwl_models表中的数据数量: {count}")
                
                if count > 0:
                    # 查询前5条数据
                    cursor.execute(
                        "SELECT id, name, version, model_type, is_active, created_at "
                        "FROM acwl_models LIMIT 5"
                    )
                    rows = cursor.fetchall()
                    print("\n前5条模型数据:")
                    for row in rows:
                        print(f"  ID: {row[0]}, Name: {row[1]}, Version: {row[2]}, Type: {row[3]}, Active: {row[4]}, Created: {row[5]}")
                else:
                    print("\nacwl_models表中没有数据！")
            else:
                print("acwl_models表不存在！")
                
                # 列出所有表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print("\n数据库中的所有表:")
                for table in tables:
                    print(f"  {table[0]}")
                
    except Exception as e:
        print(f"数据库连接或查询错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if 'connection' in locals():
            connection.close()


if __name__ == "__main__":
    print("开始测试数据库连接...")
    test_database_sync()