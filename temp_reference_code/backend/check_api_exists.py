#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查自定义API是否存在

用于调试API 404错误的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def check_api_exists(api_code: str):
    """
    检查指定API代码的自定义API是否存在
    
    Args:
        api_code: API代码
    """
    # 创建数据库连接
    engine = create_engine(settings.DATABASE_URL, echo=False)
    
    try:
        with engine.connect() as conn:
            # 查找API
            result = conn.execute(
                text("SELECT * FROM custom_apis WHERE api_code = :api_code"),
                {"api_code": api_code}
            )
            
            api_row = result.fetchone()
            
            if api_row:
                print(f"✅ 找到API: {api_code}")
                print(f"   - API ID: {api_row.id}")
                print(f"   - API名称: {api_row.api_name}")
                print(f"   - 客户ID: {api_row.customer_id}")
                print(f"   - HTTP方法: {api_row.http_method}")
                print(f"   - 状态: {'激活' if api_row.status else '停用'}")
                print(f"   - 创建时间: {api_row.created_at}")
                
                # 获取平台信息
                customer_result = conn.execute(
                    text("SELECT * FROM customers WHERE id = :customer_id"),
                    {"customer_id": api_row.customer_id}
                )
                
                customer_row = customer_result.fetchone()
                if customer_row:
                    print(f"   - 客户名称: {customer_row.name}")
                    print(f"   - 应用ID: {customer_row.app_id}")
                
                return True
            else:
                print(f"❌ 未找到API: {api_code}")
                
                # 列出所有现有的API代码
                all_apis_result = conn.execute(
                    text("SELECT api_code, status FROM custom_apis")
                )
                
                all_apis = all_apis_result.fetchall()
                if all_apis:
                    print("\n现有的API代码:")
                    for existing_api in all_apis:
                        status = '激活' if existing_api.status else '停用'
                        print(f"   - {existing_api.api_code} ({status})")
                        
                        # 获取每个API的平台信息
                        customer_result = conn.execute(
                            text("SELECT id, name FROM customers WHERE id = (SELECT customer_id FROM custom_apis WHERE api_code = :api_code)"),
                            {"api_code": existing_api.api_code}
                        )
                        customer_row = customer_result.fetchone()
                        if customer_row:
                            print(f"     所有者ID: {customer_row.id}, 所有者名称: {customer_row.name}")
                else:
                    print("\n数据库中没有任何自定义API")
                
                return False
                
    except Exception as e:
        print(f"❌ 检查API时发生错误: {e}")
        return False

if __name__ == "__main__":
    # 检查test22333 API
    api_code = "test22333"
    print(f"检查API代码: {api_code}")
    print("=" * 50)
    
    check_api_exists(api_code)