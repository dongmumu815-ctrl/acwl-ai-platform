#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API复制功能测试脚本

测试API复制功能的基本流程：
1. 创建测试客户
2. 创建源API
3. 复制API到另一个客户
4. 验证复制结果
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.api import custom_api_service
from app.services.customer import CustomerService
from app.models.customer import Customer
from app.models.api import CustomApi, ApiField
from app.schemas.customer import CustomerCreate
from app.schemas.api import CustomApiCreate, ApiFieldCreate


def test_api_copy():
    """
    测试API复制功能
    """
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        customer_service = CustomerService()
        
        print("=== API复制功能测试 ===")
        
        # 1. 创建测试客户
        print("\n1. 创建测试客户...")
        
        # 检查是否已存在测试客户
        source_customer = db.query(Customer).filter(Customer.name == "测试客户A").first()
        if not source_customer:
            source_customer_data = CustomerCreate(
                name="测试客户A",
                email="test_a@example.com",
                phone="13800000001",
                company="测试公司A",
                contact_person="张三"
            )
            source_customer = customer_service.create_customer(db, source_customer_data)
            print(f"   创建源客户: {source_customer.name} (ID: {source_customer.id})")
        else:
            print(f"   使用现有源客户: {source_customer.name} (ID: {source_customer.id})")
        
        target_customer = db.query(Customer).filter(Customer.name == "测试客户B").first()
        if not target_customer:
            target_customer_data = CustomerCreate(
                name="测试客户B",
                email="test_b@example.com",
                phone="13800000002",
                company="测试公司B",
                contact_person="李四"
            )
            target_customer = customer_service.create_customer(db, target_customer_data)
            print(f"   创建目标客户: {target_customer.name} (ID: {target_customer.id})")
        else:
            print(f"   使用现有目标客户: {target_customer.name} (ID: {target_customer.id})")
        
        # 2. 创建源API
        print("\n2. 创建源API...")
        
        # 检查是否已存在源API
        source_api = db.query(CustomApi).filter(
            CustomApi.customer_id == source_customer.id,
            CustomApi.api_code == "test_source_api"
        ).first()
        
        if not source_api:
            source_api_data = CustomApiCreate(
                customer_id=source_customer.id,
                api_name="测试源API",
                api_code="test_source_api",
                api_description="这是一个用于测试复制功能的源API",
                http_method="POST",
                status=True,
                rate_limit=100,
                require_authentication=True
            )
            source_api = custom_api_service.create_api(
                db, source_api_data, source_customer.id
            )
            print(f"   创建源API: {source_api.api_name} (ID: {source_api.id})")
            
            # 为源API添加一些字段
            field1 = ApiField(
                api_id=source_api.id,
                field_name="username",
                field_label="用户名",
                field_type="string",
                is_required=True,
                max_length=50,
                sort_order=1
            )
            field2 = ApiField(
                api_id=source_api.id,
                field_name="age",
                field_label="年龄",
                field_type="int",
                is_required=False,
                min_value=0,
                max_value=150,
                sort_order=2
            )
            db.add(field1)
            db.add(field2)
            db.commit()
            print(f"   为源API添加了2个字段")
        else:
            print(f"   使用现有源API: {source_api.api_name} (ID: {source_api.id})")
        
        # 3. 复制API
        print("\n3. 复制API到目标客户...")
        
        try:
            copied_api = custom_api_service.copy_api(
                db,
                source_api_id=source_api.id,
                target_customer_id=target_customer.id,
                new_api_code="test_copied_api",
                new_api_name="复制的测试API"
            )
            print(f"   ✅ API复制成功!")
            print(f"   复制的API: {copied_api.api_name} (ID: {copied_api.id})")
            print(f"   API代码: {copied_api.api_code}")
            print(f"   API URL: {copied_api.api_url}")
            
            # 4. 验证复制结果
            print("\n4. 验证复制结果...")
            
            # 检查API基本信息
            assert copied_api.customer_id == target_customer.id, "客户ID不匹配"
            assert copied_api.api_code == "test_copied_api", "API代码不匹配"
            assert copied_api.api_name == "复制的测试API", "API名称不匹配"
            assert copied_api.http_method == source_api.http_method, "HTTP方法不匹配"
            assert copied_api.status == source_api.status, "状态不匹配"
            assert copied_api.rate_limit == source_api.rate_limit, "频率限制不匹配"
            print(f"   ✅ API基本信息验证通过")
            
            # 检查字段复制
            source_fields = db.query(ApiField).filter(ApiField.api_id == source_api.id).count()
            copied_fields = db.query(ApiField).filter(ApiField.api_id == copied_api.id).count()
            assert source_fields == copied_fields, f"字段数量不匹配: 源{source_fields} vs 复制{copied_fields}"
            print(f"   ✅ 字段复制验证通过 (共{copied_fields}个字段)")
            
            # 检查字段详细信息
            source_field_list = db.query(ApiField).filter(ApiField.api_id == source_api.id).order_by(ApiField.sort_order).all()
            copied_field_list = db.query(ApiField).filter(ApiField.api_id == copied_api.id).order_by(ApiField.sort_order).all()
            
            for i, (src_field, copy_field) in enumerate(zip(source_field_list, copied_field_list)):
                assert src_field.field_name == copy_field.field_name, f"字段{i+1}名称不匹配"
                assert src_field.field_type == copy_field.field_type, f"字段{i+1}类型不匹配"
                assert src_field.is_required == copy_field.is_required, f"字段{i+1}必填属性不匹配"
                print(f"   ✅ 字段 '{copy_field.field_name}' 验证通过")
            
            print("\n🎉 API复制功能测试全部通过!")
            
        except Exception as e:
            print(f"   ❌ API复制失败: {e}")
            return False
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    print("开始测试API复制功能...")
    print("=" * 50)
    
    success = test_api_copy()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ 测试完成，所有功能正常!")
    else:
        print("❌ 测试失败，请检查错误信息")
        sys.exit(1)