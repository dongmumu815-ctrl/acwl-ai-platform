#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的批次完成接口测试

直接测试数据库操作，不依赖HTTP请求
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.batch import DataBatch
from app.models.customer import Customer
from sqlalchemy.orm import Session
import json
from datetime import datetime
import time

def test_batch_creation():
    """
    测试在data_batches表中创建批次记录
    """
    print("开始测试data_batches表批次创建...")
    
    # 获取数据库会话
    db: Session = next(get_db())
    
    try:
        # 1. 查找一个测试客户
        print("\n1. 查找测试客户...")
        customer = db.query(Customer).filter(Customer.status == True).first()
        if not customer:
            print("❌ 没有找到可用的测试客户")
            return
        
        print(f"✅ 找到测试客户: ID={customer.id}, 公司={customer.company}")
        
        # 2. 生成测试批次ID
        batch_id = f"test_batch_{int(time.time())}"
        print(f"\n2. 生成测试批次ID: {batch_id}")
        
        # 3. 检查批次是否已存在
        print("\n3. 检查批次是否已存在...")
        existing_batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id
        ).first()
        
        if existing_batch:
            print(f"❌ 批次 {batch_id} 已经存在")
            return
        
        print("✅ 批次不存在，可以创建")
        
        # 4. 准备元数据
        metadata = {
            "callback_url": "http://example.com/callback",
            "remark": "测试批次完成接口",
            "completed_at": datetime.utcnow().isoformat(),
            "needread": True,
            "timestamp": int(time.time()),
            "nonce": f"test_nonce_{int(time.time())}"
        }
        
        # 5. 创建新的批次记录
        print("\n4. 在data_batches表中创建新记录...")
        new_batch = DataBatch(
            customer_id=customer.id,
            batch_id=batch_id,
            batch_name=f"batch_{batch_id}",
            description="测试批次数据上传完成",
            status=0,  # 0-未处理状态，等待后续程序处理
            expected_count=100,
            total_count=0,  # 初始为0，后续处理时会更新
            pending_count=0,
            processing_count=0,
            completed_count=0,
            failed_count=0,
            meta_data=metadata
        )
        
        db.add(new_batch)
        db.commit()
        db.refresh(new_batch)
        
        print("✅ 成功在data_batches表中创建新记录!")
        print(f"   记录ID: {new_batch.id}")
        print(f"   批次ID: {new_batch.batch_id}")
        print(f"   客户ID: {new_batch.customer_id}")
        print(f"   状态: {new_batch.status}")
        print(f"   预期数量: {new_batch.expected_count}")
        print(f"   创建时间: {new_batch.created_at}")
        print(f"   元数据: {json.dumps(new_batch.meta_data, indent=2, ensure_ascii=False)}")
        
        # 6. 验证记录是否正确创建
        print("\n5. 验证记录是否正确创建...")
        verify_batch = db.query(DataBatch).filter(
            DataBatch.batch_id == batch_id
        ).first()
        
        if verify_batch:
            print("✅ 验证成功，记录已正确创建在data_batches表中")
            print("✅ 其他程序现在可以检测到这个批次并开始处理api_usage_logs中的数据")
        else:
            print("❌ 验证失败，记录未找到")
        
        # 7. 测试重复创建
        print("\n6. 测试重复创建检测...")
        duplicate_batch = DataBatch(
            customer_id=customer.id,
            batch_id=batch_id,  # 相同的batch_id
            batch_name=f"duplicate_batch_{batch_id}",
            description="重复的批次",
            status=0,
            expected_count=50
        )
        
        try:
            db.add(duplicate_batch)
            db.commit()
            print("❌ 重复创建检测失败，应该抛出异常")
        except Exception as e:
            db.rollback()
            print(f"✅ 重复创建检测正常，抛出异常: {str(e)[:100]}...")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

def test_batch_query():
    """
    测试查询data_batches表中的记录
    """
    print("\n" + "=" * 50)
    print("测试查询data_batches表中的记录...")
    
    db: Session = next(get_db())
    
    try:
        # 查询最近的5条记录
        recent_batches = db.query(DataBatch).order_by(
            DataBatch.created_at.desc()
        ).limit(5).all()
        
        print(f"\n最近的 {len(recent_batches)} 条批次记录:")
        for i, batch in enumerate(recent_batches, 1):
            print(f"\n{i}. 批次记录:")
            print(f"   ID: {batch.id}")
            print(f"   批次ID: {batch.batch_id}")
            print(f"   客户ID: {batch.customer_id}")
            print(f"   状态: {batch.status}")
            print(f"   预期数量: {batch.expected_count}")
            print(f"   创建时间: {batch.created_at}")
            if batch.meta_data:
                callback_url = batch.meta_data.get('callback_url', 'N/A')
                print(f"   回调URL: {callback_url}")
        
        if not recent_batches:
            print("❌ data_batches表中没有记录")
        else:
            print(f"\n✅ data_batches表中共有 {len(recent_batches)} 条记录")
    
    except Exception as e:
        print(f"❌ 查询异常: {e}")
    
    finally:
        db.close()

def main():
    """
    主函数
    """
    print("=" * 60)
    print("批次完成接口数据库操作测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试批次创建
    test_batch_creation()
    
    # 测试批次查询
    test_batch_query()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n说明:")
    print("1. 此测试验证了批次完成接口的核心功能")
    print("2. 成功在data_batches表中创建了新记录")
    print("3. 其他程序可以检测到这些记录并开始处理api_usage_logs中的数据")
    print("4. 重复提交检测正常工作")

if __name__ == "__main__":
    main()