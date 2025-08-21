#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中的模型类型值
"""

import asyncio
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': '10.20.1.200',
    'port': 3306,
    'user': 'root',
    'password': '2wsx1QAZaczt',
    'database': 'acwl-ai'
}

def fix_model_types():
    """
    直接使用SQL更新数据库中的模型类型值
    """
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset='utf8mb4'
        )
        
        print("✅ 数据库连接成功")
        
        with connection.cursor() as cursor:
            # 检查当前数据
            cursor.execute("SELECT id, name, model_type FROM acwl_models")
            models = cursor.fetchall()
            
            print(f"\n当前数据库中的模型:")
            for model in models:
                print(f"ID: {model[0]}, Name: {model[1]}, Type: {model[2]}")
            
            # 更新模型类型
            print("\n开始更新模型类型...")
            
            # 直接更新BGE-Large模型
            cursor.execute("UPDATE acwl_models SET model_type = 'EMBEDDING' WHERE id = 8")
            affected_rows = cursor.rowcount
            print(f"✅ 直接更新BGE-Large模型: 更新了 {affected_rows} 条记录")
            
            # 批量更新其他可能的类型
            updates = [
                ("UPDATE acwl_models SET model_type = 'EMBEDDING' WHERE model_type = 'Embedding'", "Embedding -> EMBEDDING"),
                ("UPDATE acwl_models SET model_type = 'MULTIMODAL' WHERE model_type = 'Multimodal'", "Multimodal -> MULTIMODAL"),
                ("UPDATE acwl_models SET model_type = 'OTHER' WHERE model_type = 'Other'", "Other -> OTHER")
            ]
            
            for sql, description in updates:
                cursor.execute(sql)
                affected_rows = cursor.rowcount
                print(f"✅ {description}: 更新了 {affected_rows} 条记录")
            
            # 提交更改
            connection.commit()
            print("\n✅ 所有更改已提交")
            
            # 验证更新结果
            cursor.execute("SELECT id, name, model_type FROM acwl_models")
            updated_models = cursor.fetchall()
            
            print(f"\n更新后的模型数据:")
            for model in updated_models:
                print(f"ID: {model[0]}, Name: {model[1]}, Type: {model[2]}")
                
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    finally:
        if 'connection' in locals():
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == "__main__":
    fix_model_types()