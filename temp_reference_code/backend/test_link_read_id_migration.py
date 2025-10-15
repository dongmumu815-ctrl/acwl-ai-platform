#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证link_read_id字段迁移结果

此脚本用于验证customers表中的link_read_id字段是否成功迁移到custom_apis表中
"""

import sys
import os
from sqlalchemy import text
from tabulate import tabulate

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine

def verify_migration():
    """
    验证link_read_id字段迁移结果
    
    Returns:
        bool: 验证是否通过
    """
    try:
        with engine.connect() as connection:
            # 1. 检查custom_apis表中是否存在link_read_id字段
            check_column_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'custom_apis'
                AND COLUMN_NAME = 'link_read_id'
            """
            
            column_info = connection.execute(text(check_column_sql)).fetchone()
            if not column_info:
                print("❌ 验证失败: custom_apis表中不存在link_read_id字段")
                return False
            
            print("✅ 验证通过: custom_apis表中存在link_read_id字段")
            print(f"   字段类型: {column_info[1]}")
            print(f"   字段注释: {column_info[2]}")
            
            # 2. 检查索引是否存在
            check_index_sql = """
            SELECT INDEX_NAME 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'custom_apis'
                AND COLUMN_NAME = 'link_read_id'
            """
            
            index_info = connection.execute(text(check_index_sql)).fetchone()
            if not index_info:
                print("❌ 验证失败: custom_apis表中link_read_id字段没有索引")
            else:
                print(f"✅ 验证通过: custom_apis表中link_read_id字段有索引 ({index_info[0]})")
            
            # 3. 验证数据迁移结果
            verify_data_sql = """
            SELECT 
                c.id as customer_id, 
                c.name as customer_name, 
                c.link_read_id as customer_link_id,
                COUNT(ca.id) as api_count, 
                COUNT(CASE WHEN ca.link_read_id = c.link_read_id THEN 1 END) as matched_count
            FROM customers c
            JOIN custom_apis ca ON c.id = ca.customer_id
            WHERE c.link_read_id IS NOT NULL AND c.link_read_id != ''
            GROUP BY c.id, c.name, c.link_read_id
            """
            
            migration_results = connection.execute(text(verify_data_sql)).fetchall()
            
            if not migration_results:
                print("⚠️ 注意: 没有找到需要迁移的数据 (没有客户有link_read_id值)")
                return True
            
            # 准备表格数据
            table_data = []
            all_matched = True
            
            for row in migration_results:
                customer_id, customer_name, customer_link_id, api_count, matched_count = row
                status = "✅" if api_count == matched_count else "❌"
                
                if api_count != matched_count:
                    all_matched = False
                
                table_data.append([
                    customer_id, 
                    customer_name, 
                    customer_link_id, 
                    api_count, 
                    matched_count, 
                    status
                ])
            
            # 打印表格
            print("\n迁移数据验证结果:")
            headers = ["客户ID", "客户名称", "link_read_id", "API总数", "匹配数", "状态"]
            print(tabulate(table_data, headers=headers, tablefmt="grid"))
            
            # 4. 统计总体结果
            stats_sql = """
            SELECT 
                COUNT(*) as total_apis,
                COUNT(CASE WHEN link_read_id IS NOT NULL AND link_read_id != '' THEN 1 END) as apis_with_link_id,
                COUNT(DISTINCT customer_id) as total_customers,
                COUNT(DISTINCT CASE WHEN link_read_id IS NOT NULL AND link_read_id != '' THEN customer_id END) as customers_with_link_id
            FROM custom_apis
            """
            
            stats = connection.execute(text(stats_sql)).fetchone()
            
            print("\n总体统计:")
            print(f"总API数: {stats[0]}")
            print(f"有link_read_id的API数: {stats[1]}")
            print(f"总客户数: {stats[2]}")
            print(f"有link_read_id的客户数: {stats[3]}")
            
            if all_matched:
                print("\n✅ 验证通过: 所有客户的link_read_id已成功迁移到对应的API记录中")
                return True
            else:
                print("\n❌ 验证失败: 部分客户的link_read_id未成功迁移到所有API记录中")
                return False
                
    except Exception as e:
        print(f"验证过程出错: {e}")
        return False

if __name__ == "__main__":
    print("开始验证link_read_id字段迁移结果...\n")
    success = verify_migration()
    
    if success:
        print("\n总体验证结果: 成功 ✅")
        sys.exit(0)
    else:
        print("\n总体验证结果: 失败 ❌")
        sys.exit(1)