#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：将customers表中的link_read_id字段迁移至custom_apis表

此脚本执行以下操作：
1. 在custom_apis表中添加link_read_id字段
2. 将customers表中的link_read_id值迁移到对应客户的所有custom_apis记录中
3. 为新字段添加索引以提高查询性能
"""

import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine

def migrate_link_read_id():
    """
    执行link_read_id字段从customers表迁移到custom_apis表的操作
    
    Returns:
        bool: 迁移是否成功
    """
    try:
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                print("开始迁移link_read_id字段...")
                
                # 1. 检查custom_apis表中是否已存在link_read_id字段
                check_column_sql = """
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'custom_apis'
                    AND COLUMN_NAME = 'link_read_id'
                """
                
                result = connection.execute(text(check_column_sql))
                if result.fetchone():
                    print("字段link_read_id已存在于custom_apis表中，跳过字段创建")
                else:
                    # 2. 在custom_apis表中添加link_read_id字段
                    print("在custom_apis表中添加link_read_id字段")
                    add_column_sql = """
                    ALTER TABLE `custom_apis` 
                    ADD COLUMN `link_read_id` varchar(50) DEFAULT NULL COMMENT '链接其他系统的ID'
                    """
                    connection.execute(text(add_column_sql))
                    
                    # 3. 添加索引
                    print("为link_read_id字段添加索引")
                    add_index_sql = """
                    ALTER TABLE `custom_apis` 
                    ADD INDEX `idx_link_read_id` (`link_read_id`)
                    """
                    connection.execute(text(add_index_sql))
                
                # 4. 获取所有客户的ID和link_read_id
                print("获取customers表中的link_read_id数据")
                get_customers_sql = """
                SELECT id, link_read_id 
                FROM customers 
                WHERE link_read_id IS NOT NULL AND link_read_id != ''
                """
                
                customers = connection.execute(text(get_customers_sql)).fetchall()
                print(f"找到{len(customers)}个客户有link_read_id值")
                
                # 5. 将link_read_id值迁移到custom_apis表
                for customer in customers:
                    customer_id = customer[0]
                    link_read_id = customer[1]
                    
                    print(f"迁移客户ID {customer_id} 的link_read_id值: {link_read_id}")
                    update_apis_sql = """
                    UPDATE custom_apis 
                    SET link_read_id = :link_read_id 
                    WHERE customer_id = :customer_id
                    """
                    
                    connection.execute(
                        text(update_apis_sql),
                        {"link_read_id": link_read_id, "customer_id": customer_id}
                    )
                
                # 6. 验证迁移结果
                print("\n验证迁移结果...")
                verify_sql = """
                SELECT c.id as customer_id, c.name as customer_name, c.link_read_id as customer_link_id,
                       ca.id as api_id, ca.api_name, ca.link_read_id as api_link_id
                FROM customers c
                JOIN custom_apis ca ON c.id = ca.customer_id
                WHERE c.link_read_id IS NOT NULL AND c.link_read_id != ''
                LIMIT 10
                """
                
                verification = connection.execute(text(verify_sql)).fetchall()
                
                if verification:
                    print("\n迁移验证示例:")
                    print("-" * 80)
                    print(f"{'客户ID':<10} {'客户名称':<20} {'客户link_read_id':<20} {'API ID':<10} {'API名称':<20} {'API link_read_id':<20}")
                    print("-" * 80)
                    
                    for row in verification:
                        print(f"{row[0]:<10} {row[1][:18]:<20} {row[2][:18]:<20} {row[3]:<10} {row[4][:18]:<20} {row[5][:18]:<20}")
                
                # 提交事务
                trans.commit()
                print("\nlink_read_id字段迁移完成！")
                return True
                
            except Exception as e:
                # 回滚事务
                trans.rollback()
                print(f"迁移失败，已回滚: {e}")
                return False
                
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    print("开始执行link_read_id字段迁移...")
    success = migrate_link_read_id()
    
    if success:
        print("迁移成功完成！")
        sys.exit(0)
    else:
        print("迁移失败！")
        sys.exit(1)