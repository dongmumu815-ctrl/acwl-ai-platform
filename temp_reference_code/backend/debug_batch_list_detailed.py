#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次列表接口详细调试脚本
"""

import requests
import json
from app.core.database import get_db
from app.models.batch import DataBatch
from app.api.v1.endpoints.data import get_current_customer
from app.services.auth import JWTService

def test_token_decode():
    """测试Token解码"""
    print("=== 测试Token解码 ===")
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMTY0MDc1LCJpYXQiOjE3NTMwNzc2NzUsImp0aSI6InlOUm9GZWpobkZJR3p6YlB4QkF4ejVfTkRrdWl2Um5pSXhhOGxUQXBJWUUiLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.r1if0CDb9ANFCd2_VVA1Q_k59YmTLrKOSqPu1oM8QoQ"
    
    try:
        jwt_service = JWTService()
        decoded = jwt_service.decode_token(token)
        print(f"Token解码成功: {decoded}")
        
        # 测试get_current_customer函数
        authorization = f"Bearer {token}"
        customer_info = get_current_customer(authorization)
        print(f"客户信息: {customer_info}")
        
    except Exception as e:
        print(f"Token解码失败: {e}")
        import traceback
        traceback.print_exc()

def test_database_query():
    """测试数据库查询"""
    print("\n=== 测试数据库查询 ===")
    try:
        db = next(get_db())
        
        # 查询所有批次
        all_batches = db.query(DataBatch).all()
        print(f"数据库中总批次数: {len(all_batches)}")
        
        # 分页查询
        page = 1
        size = 20
        offset = (page - 1) * size
        batches = db.query(DataBatch).order_by(DataBatch.created_at.desc()).offset(offset).limit(size).all()
        print(f"分页查询结果: {len(batches)} 个批次")
        
        for batch in batches:
            print(f"  - 批次ID: {batch.batch_id}, 状态: {batch.status}, 创建时间: {batch.created_at}")
            
    except Exception as e:
        print(f"数据库查询失败: {e}")
        import traceback
        traceback.print_exc()

def test_batch_list_api():
    """测试批次列表API"""
    print("\n=== 测试批次列表API ===")
    
    url = "http://localhost:8000/api/v1/batch/"
    headers = {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMTY0MDc1LCJpYXQiOjE3NTMwNzc2NzUsImp0aSI6InlOUm9GZWpobkZJR3p6YlB4QkF4ejVfTkRrdWl2Um5pSXhhOGxUQXBJWUUiLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.r1if0CDb9ANFCd2_VVA1Q_k59YmTLrKOSqPu1oM8QoQ",
        "Content-Type": "application/json"
    }
    
    params = {
        "page": 1,
        "size": 20
    }
    
    try:
        print(f"请求URL: {url}")
        print(f"请求参数: {params}")
        print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 请求成功")
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
                
    except Exception as e:
        print(f"请求异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("批次列表接口详细调试")
    
    test_token_decode()
    test_database_query()
    test_batch_list_api()
    
    print("\n调试完成！")