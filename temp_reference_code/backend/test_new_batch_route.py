#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新的批次完成路由

测试 /v1/batch/{api_code}/{batch_id}/complete 接口是否正常工作
"""

import requests
import json
import base64
import time
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import hashlib
import hmac

# 测试配置
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# 测试用户凭据
TEST_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMDQxNzE5LCJpYXQiOjE3NTI5NTUzMTksImp0aSI6InZEQ0xtY1RpMTI4S3EtcUk1bHphZWtPMWdHUUVySVFzSldOX0Q0RlZXQmciLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.KcgZaevluE_A5aoEMux_Cu_-4_61iAudKB0ieMDNI2s"
TEST_DATA_KEY = "LURSIulfT6q97CHl6CsvWjvqEnL990Y/uT5wmcP2Tq8="
TEST_API_CODE = "test22333_upload"  # 测试用的API代码

def encrypt_data(data_key: str, plaintext: str):
    """
    使用AES-256-GCM加密数据
    
    Args:
        data_key: 数据密钥（Base64编码）
        plaintext: 明文数据
        
    Returns:
        tuple: (加密数据, IV)
    """
    try:
        # 解码data_key（假设是Base64编码）
        key = base64.b64decode(data_key)
        
        # 生成随机IV
        iv = get_random_bytes(12)  # GCM模式推荐12字节IV
        
        # 创建加密器
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        
        # 加密数据
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
        
        # 返回加密数据（包含tag）和IV
        return ciphertext + tag, iv
    except Exception as e:
        raise Exception(f"数据加密失败: {str(e)}")

def generate_signature(data_key: str, encrypted_data: str):
    """
    生成HMAC-SHA256签名
    
    Args:
        data_key: 数据密钥
        encrypted_data: 加密后的数据（Base64编码）
        
    Returns:
        str: 签名值
    """
    key = data_key.encode('utf-8')
    message = encrypted_data.encode('utf-8')
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return signature

def test_new_batch_route():
    """
    测试新的批次完成路由
    """
    print("开始测试新的批次完成路由...")
    print(f"新路由格式: /v1/batch/{TEST_API_CODE}/{{batch_id}}/complete")
    
    # 1. 准备测试数据
    print("\n1. 准备测试数据...")
    batch_id = f"test_batch_{int(time.time())}"
    
    # 业务数据
    business_data = {
        "remark": "测试新路由格式",
        "callback_url": "http://example.com/callback",
        "total": 100
    }
    
    # 加密业务数据
    plaintext = json.dumps(business_data)
    encrypted_data, iv = encrypt_data(TEST_DATA_KEY, plaintext)
    
    # Base64编码
    encrypted_data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    
    # 生成签名
    signature = generate_signature(TEST_DATA_KEY, encrypted_data_b64)
    
    # 构建请求数据
    request_data = {
        "timestamp": int(time.time()),
        "nonce": f"test_nonce_{int(time.time())}",
        "data": encrypted_data_b64,
        "iv": iv_b64,
        "signature": signature,
        "needread": True
    }
    
    print(f"✅ 测试批次ID: {batch_id}")
    print(f"✅ API代码: {TEST_API_CODE}")
    print(f"✅ 业务数据: {business_data}")
    
    # 2. 调用新的批次完成接口
    print("\n2. 调用新的批次完成接口...")
    new_url = f"{API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete"
    print(f"请求URL: {new_url}")
    
    headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Data-Encrypted": "true",
        "X-Data-Signature": signature
    }
    
    try:
        response = requests.post(
            new_url,
            json=request_data,
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 新路由测试成功!")
            print(f"   批次ID: {result.get('batch_id')}")
            print(f"   预期数量: {result.get('expected_count')}")
            print(f"   回调URL: {result.get('callback_url')}")
            print(f"   状态: {result.get('status')}")
            print(f"   创建时间: {result.get('created_at')}")
            return True
        else:
            print(f"\n❌ 新路由测试失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
        return False

def test_old_route_should_fail():
    """
    测试旧路由应该失败（404）
    """
    print("\n3. 测试旧路由是否已失效...")
    batch_id = f"test_batch_{int(time.time())}"
    old_url = f"{API_URL}/batch/{batch_id}/complete"
    print(f"旧路由URL: {old_url}")
    
    headers = {
        "Authorization": f"Bearer {TEST_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            old_url,
            json={"test": "data"},
            headers=headers
        )
        
        print(f"旧路由响应状态码: {response.status_code}")
        
        if response.status_code == 404:
            print("✅ 旧路由已正确失效（404）")
            return True
        else:
            print(f"⚠️  旧路由仍然可用，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 旧路由测试异常: {e}")
        return False

def main():
    """
    主函数
    """
    print("=" * 60)
    print("新批次完成路由测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {API_URL}")
    print("=" * 60)
    
    # 测试新路由
    new_route_success = test_new_batch_route()
    
    # 测试旧路由失效
    old_route_failed = test_old_route_should_fail()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"新路由测试: {'✅ 成功' if new_route_success else '❌ 失败'}")
    print(f"旧路由失效: {'✅ 已失效' if old_route_failed else '⚠️  仍可用'}")
    
    if new_route_success and old_route_failed:
        print("\n🎉 路由迁移完全成功！")
        print("   - 新路由格式正常工作")
        print("   - 旧路由已正确失效")
        print("   - API代码验证正常")
    else:
        print("\n⚠️  路由迁移需要进一步检查")
    
    print("=" * 60)

if __name__ == "__main__":
    main()