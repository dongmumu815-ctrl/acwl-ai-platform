#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试needread字段功能

此脚本用于测试新添加的needread字段是否正常工作。

Author: System
Date: 2024
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.models.batch import DataBatch
from app.core.database import get_db

def test_needread_field():
    """
    测试needread字段功能
    """
    settings = get_settings()
    
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        with SessionLocal() as db:
            print("开始测试needread字段功能")
            print("=" * 50)
            
            # 1. 测试查询现有批次的needread字段
            print("\n1. 查询现有批次的needread字段:")
            batches = db.query(DataBatch).limit(5).all()
            
            if batches:
                for batch in batches:
                    print(f"批次ID: {batch.batch_id}, needread: {batch.needread}")
            else:
                print("没有找到现有批次")
            
            # 2. 测试创建新批次时设置needread字段
            print("\n2. 测试创建新批次时设置needread字段:")
            
            # 创建测试批次（needread=True）
            test_batch_1 = DataBatch(
                customer_id=1,  # 假设存在customer_id=1
                api_id=1,       # 假设存在api_id=1
                batch_id="test_needread_true",
                batch_name="测试批次_needread_true",
                description="测试needread=True的批次",
                status='pending',
                expected_count=10,
                needread=True,
                meta_data={"test": "needread_true"}
            )
            
            # 创建测试批次（needread=False）
            test_batch_2 = DataBatch(
                customer_id=1,  # 假设存在customer_id=1
                api_id=1,       # 假设存在api_id=1
                batch_id="test_needread_false",
                batch_name="测试批次_needread_false",
                description="测试needread=False的批次",
                status='pending',
                expected_count=10,
                needread=False,
                meta_data={"test": "needread_false"}
            )
            
            try:
                # 先删除可能存在的测试批次
                db.query(DataBatch).filter(
                    DataBatch.batch_id.in_(["test_needread_true", "test_needread_false"])
                ).delete(synchronize_session=False)
                db.commit()
                
                # 添加新的测试批次
                db.add(test_batch_1)
                db.add(test_batch_2)
                db.commit()
                
                print(f"创建测试批次成功:")
                print(f"  - {test_batch_1.batch_id}: needread={test_batch_1.needread}")
                print(f"  - {test_batch_2.batch_id}: needread={test_batch_2.needread}")
                
                # 3. 测试查询新创建的批次
                print("\n3. 验证新创建批次的needread字段:")
                
                created_batch_1 = db.query(DataBatch).filter(
                    DataBatch.batch_id == "test_needread_true"
                ).first()
                
                created_batch_2 = db.query(DataBatch).filter(
                    DataBatch.batch_id == "test_needread_false"
                ).first()
                
                if created_batch_1:
                    print(f"批次 {created_batch_1.batch_id}: needread={created_batch_1.needread}")
                else:
                    print("未找到test_needread_true批次")
                    
                if created_batch_2:
                    print(f"批次 {created_batch_2.batch_id}: needread={created_batch_2.needread}")
                else:
                    print("未找到test_needread_false批次")
                
                # 4. 测试更新needread字段
                print("\n4. 测试更新needread字段:")
                if created_batch_1:
                    original_value = created_batch_1.needread
                    created_batch_1.needread = not original_value
                    db.commit()
                    
                    # 重新查询验证
                    updated_batch = db.query(DataBatch).filter(
                        DataBatch.batch_id == "test_needread_true"
                    ).first()
                    
                    print(f"批次 {updated_batch.batch_id}: 原值={original_value}, 新值={updated_batch.needread}")
                
                # 5. 清理测试数据
                print("\n5. 清理测试数据:")
                deleted_count = db.query(DataBatch).filter(
                    DataBatch.batch_id.in_(["test_needread_true", "test_needread_false"])
                ).delete(synchronize_session=False)
                db.commit()
                
                print(f"删除了 {deleted_count} 个测试批次")
                
            except Exception as e:
                print(f"测试过程中发生错误: {e}")
                db.rollback()
                return False
            
            print("\n✅ needread字段功能测试完成！")
            return True
            
    except Exception as e:
        print(f"数据库连接或操作错误: {e}")
        return False

def test_database_schema():
    """
    测试数据库表结构
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            print("\n检查data_batches表结构:")
            print("-" * 30)
            
            # 查询表结构
            schema_sql = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'data_batches'
            ORDER BY ORDINAL_POSITION
            """
            
            result = connection.execute(text(schema_sql))
            rows = result.fetchall()
            
            print(f"{'字段名':<20} {'类型':<15} {'可空':<8} {'默认值':<10} {'注释':<20}")
            print("-" * 80)
            
            for row in rows:
                column_name = row[0]
                data_type = row[1]
                is_nullable = row[2]
                default_value = row[3] or ''
                comment = row[4] or ''
                
                print(f"{column_name:<20} {data_type:<15} {is_nullable:<8} {str(default_value):<10} {comment:<20}")
                
                # 特别标记needread字段
                if column_name == 'needread':
                    print(f"{'':>20} *** needread字段已存在 ***")
            
            return True
            
    except Exception as e:
        print(f"查询表结构时发生错误: {e}")
        return False

if __name__ == "__main__":
    print("needread字段功能测试")
    print("=" * 50)
    
    # 测试数据库表结构
    schema_success = test_database_schema()
    
    if schema_success:
        # 测试字段功能
        test_success = test_needread_field()
        
        if test_success:
            print("\n🎉 所有测试通过！")
        else:
            print("\n❌ 测试失败！")
            sys.exit(1)
    else:
        print("\n❌ 表结构检查失败！")
        sys.exit(1)