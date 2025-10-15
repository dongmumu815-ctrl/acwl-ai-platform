#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批次结果查询接口

测试 /v1/results/{batch_id} 接口功能

Author: System
Date: 2024
"""

import requests
import json
import uuid
import time
import base64
import hmac
import hashlib
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
from app.core.database import get_db
from app.models.batch import DataBatch
from app.services.auth import JWTService
from sqlalchemy import desc

# 测试配置
BASE_URL = "http://localhost:8000"
API_ENDPOINT = "/api/v1/results"

# 测试凭据
TEST_CUSTOMER_ID = 6  # 测试客户ID
TEST_APP_ID = "test_app"  # 测试应用ID
TEST_APP_SECRET = "test_secret"  # 测试应用密钥

# 获取测试访问令牌
def get_test_token():
    """
    获取测试访问令牌
    
    Returns:
        str: 访问令牌
    """
    jwt_service = JWTService()
    payload = {
        "customer_id": TEST_CUSTOMER_ID,
        "app_id": TEST_APP_ID,
        "exp": int(time.time()) + 3600  # 1小时有效期
    }
    return jwt_service.create_token(payload)

# 测试批次结果查询接口
def test_batch_results_api():
    """
    测试批次结果查询接口
    
    Returns:
        bool: 测试是否成功
    """
    print("🧪 测试批次结果查询接口...")
    print("=" * 60)
    
    # 获取测试访问令牌
    access_token = get_test_token()
    print(f"📝 测试访问令牌: {access_token}")
    
    # 获取测试批次ID
    db = next(get_db())
    try:
        # 查询最新的批次
        latest_batch = db.query(DataBatch).filter(
            DataBatch.customer_id == TEST_CUSTOMER_ID
        ).order_by(desc(DataBatch.created_at)).first()
        
        if not latest_batch:
            # 如果没有批次，创建一个测试批次
            test_batch_id = f"test_batch_{uuid.uuid4().hex[:8]}"
            print(f"📝 创建测试批次: {test_batch_id}")
            
            batch = DataBatch(
                customer_id=TEST_CUSTOMER_ID,
                api_id=3,  # 测试API ID
                batch_id=test_batch_id,
                batch_name=f"测试批次 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                description="测试批次结果查询接口",
                status="completed",  # 已完成状态
                total_count=10,
                pending_count=0,
                processing_count=0,
                completed_count=8,
                failed_count=2,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                processing_time=5.0,  # 5秒处理时间
                error_message=None
            )
            
            db.add(batch)
            db.commit()
            db.refresh(batch)
            
            test_batch_id = batch.batch_id
        else:
            test_batch_id = latest_batch.batch_id
            print(f"📝 使用现有批次: {test_batch_id}")
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        print(f"\n🚀 发送请求: GET {BASE_URL}{API_ENDPOINT}/{test_batch_id}")
        try:
            response = requests.get(
                f"{BASE_URL}{API_ENDPOINT}/{test_batch_id}",
                headers=headers
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ 请求成功!")
                print(f"   状态: {result.get('status')}")
                
                # 如果有加密数据，尝试解密
                if result.get('data') and result.get('result_sign'):
                    print("   数据: [加密数据]")
                    print(f"   签名: {result.get('result_sign')}")
                    
                    # 这里可以添加解密逻辑，但需要data_key
                    # 实际应用中，客户端会使用自己的data_key解密
                else:
                    print("   数据: [无数据]")
                
                return True
            else:
                print(f"\n❌ 请求失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
                
        except Exception as e:
            print(f"\n❌ 请求异常: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

# 测试失败情况
def test_batch_results_api_failure():
    """
    测试批次结果查询接口失败情况
    
    Returns:
        bool: 测试是否成功
    """
    print("\n🧪 测试批次结果查询接口失败情况...")
    print("=" * 60)
    
    # 获取测试访问令牌
    access_token = get_test_token()
    
    # 使用不存在的批次ID
    non_existent_batch_id = f"non_existent_{uuid.uuid4().hex}"
    print(f"📝 不存在的批次ID: {non_existent_batch_id}")
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 发送请求
    print(f"\n🚀 发送请求: GET {BASE_URL}{API_ENDPOINT}/{non_existent_batch_id}")
    try:
        response = requests.get(
            f"{BASE_URL}{API_ENDPOINT}/{non_existent_batch_id}",
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 404:
            print("\n✅ 测试成功! 正确返回404状态码")
            return True
        else:
            print(f"\n❌ 测试失败: 预期404状态码，实际为{response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

# 主函数
def main():
    """
    主函数
    """
    print("🚀 开始测试批次结果查询接口...")
    print("=" * 60)
    
    success1 = test_batch_results_api()
    success2 = test_batch_results_api_failure()
    
    print(f"\n📊 测试结果: {'✅ 成功' if success1 and success2 else '❌ 失败'}")
    
    print(f"\n💡 接口说明:")
    print(f"   - ✅ GET /v1/results/{'{batch_id}'}")
    print(f"   - ✅ 支持查询批次处理结果")
    print(f"   - ✅ 返回批次状态和加密数据")
    print(f"   - ✅ 支持数据签名验证")

if __name__ == '__main__':
    main()