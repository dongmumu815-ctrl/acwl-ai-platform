#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试客户数据

为Token接口测试创建必要的测试客户数据

Author: System
Date: 2024
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate
from app.services.customer import CustomerService

def create_test_customer():
    """
    创建测试客户数据
    """
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            customer_service = CustomerService()
            
            # 测试客户配置
            test_customers = [
                {
                    "name": "测试客户001",
                    "email": "test001@example.com",
                    "phone": "13800138001",
                    "company": "测试公司001",
                    "contact_person": "张三",
                    "description": "Token接口测试客户",
                    "app_id": "test_app_001",
                    "app_secret": "test_secret_123456789"
                },
                {
                    "name": "测试客户002",
                    "email": "test002@example.com",
                    "phone": "13800138002",
                    "company": "测试公司002",
                    "contact_person": "李四",
                    "description": "Token接口测试客户2",
                    "app_id": "test_app_002",
                    "app_secret": "test_secret_987654321"
                }
            ]
            
            print("=== 创建测试客户数据 ===")
            
            for customer_data in test_customers:
                app_id = customer_data.pop("app_id")
                app_secret = customer_data.pop("app_secret")
                
                # 检查客户是否已存在
                existing_customer = db.query(Customer).filter(
                    Customer.app_id == app_id
                ).first()
                
                if existing_customer:
                    print(f"✅ 测试客户已存在: {existing_customer.name} (app_id: {existing_customer.app_id})")
                    continue
                
                # 创建客户
                customer_create = CustomerCreate(**customer_data)
                customer = customer_service.create_customer(db, customer_create)
                
                # 更新app_id和app_secret
                customer.app_id = app_id
                customer.app_secret = app_secret
                customer.status = True  # 确保客户状态为启用
                
                db.commit()
                db.refresh(customer)
                
                print(f"✅ 创建测试客户: {customer.name}")
                print(f"   app_id: {customer.app_id}")
                print(f"   app_secret: {customer.app_secret}")
                print(f"   状态: {'启用' if customer.status else '禁用'}")
                print()
            
            print("🎉 测试客户数据创建完成！")
            print()
            print("现在可以运行Token接口测试:")
            print("  python test_token_endpoint.py")
            print("  或")
            print("  python run_token_tests.py --quick")
            
            return True
            
        finally:
            db.close()
            engine.dispose()
            
    except Exception as e:
        print(f"❌ 创建测试客户失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_test_customer():
    """
    验证测试客户数据
    """
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            print("=== 验证测试客户数据 ===")
            
            # 查询测试客户
            test_customers = db.query(Customer).filter(
                Customer.app_id.like("test_app_%")
            ).all()
            
            if not test_customers:
                print("❌ 未找到测试客户数据")
                return False
            
            for customer in test_customers:
                print(f"✅ 客户: {customer.name}")
                print(f"   ID: {customer.id}")
                print(f"   app_id: {customer.app_id}")
                print(f"   app_secret: {customer.app_secret}")
                print(f"   状态: {'启用' if customer.status else '禁用'}")
                print(f"   创建时间: {customer.created_at}")
                print()
            
            print(f"总计找到 {len(test_customers)} 个测试客户")
            return True
            
        finally:
            db.close()
            engine.dispose()
            
    except Exception as e:
        print(f"❌ 验证测试客户失败: {str(e)}")
        return False

def delete_test_customer():
    """
    删除测试客户数据
    """
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            print("=== 删除测试客户数据 ===")
            
            # 查询测试客户
            test_customers = db.query(Customer).filter(
                Customer.app_id.like("test_app_%")
            ).all()
            
            if not test_customers:
                print("ℹ️  未找到测试客户数据")
                return True
            
            # 确认删除
            print(f"找到 {len(test_customers)} 个测试客户:")
            for customer in test_customers:
                print(f"  - {customer.name} (app_id: {customer.app_id})")
            
            confirm = input("\n确认删除这些测试客户吗？(y/N): ")
            if confirm.lower() != 'y':
                print("取消删除操作")
                return False
            
            # 删除客户
            for customer in test_customers:
                db.delete(customer)
                print(f"✅ 删除客户: {customer.name}")
            
            db.commit()
            print("\n🎉 测试客户数据删除完成！")
            return True
            
        finally:
            db.close()
            engine.dispose()
            
    except Exception as e:
        print(f"❌ 删除测试客户失败: {str(e)}")
        return False

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="测试客户数据管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python create_test_customer.py --create     # 创建测试客户
  python create_test_customer.py --verify     # 验证测试客户
  python create_test_customer.py --delete     # 删除测试客户
        """
    )
    
    parser.add_argument(
        "--create", 
        action="store_true", 
        help="创建测试客户数据"
    )
    parser.add_argument(
        "--verify", 
        action="store_true", 
        help="验证测试客户数据"
    )
    parser.add_argument(
        "--delete", 
        action="store_true", 
        help="删除测试客户数据"
    )
    
    args = parser.parse_args()
    
    # 如果没有指定参数，默认创建
    if not any(vars(args).values()):
        args.create = True
    
    success = True
    
    if args.create:
        success = create_test_customer() and success
    
    if args.verify:
        success = verify_test_customer() and success
    
    if args.delete:
        success = delete_test_customer() and success
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 未预期的错误: {str(e)}")
        sys.exit(1)