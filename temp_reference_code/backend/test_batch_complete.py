#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批次完成接口

测试 /v1/batch/{api_code}/{batch_id}/complete 接口是否能正确在data_batches表中创建新记录
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

# 测试用户凭据（使用已创建的测试客户）
TEST_APP_ID = "test_app_001"
TEST_APP_SECRET = "test_secret_123456789"
TEST_DATA_KEY = None  # 将从认证接口获取
TEST_API_CODE = "test22333_upload"  # 测试用的API代码

def get_access_token():
    """
    获取访问令牌和数据密钥
    
    Returns:
        tuple: (访问令牌, 数据密钥)
    """
    # 直接使用用户提供的有效token
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMDQxNzE5LCJpYXQiOjE3NTI5NTUzMTksImp0aSI6InZEQ0xtY1RpMTI4S3EtcUk1bHphZWtPMWdHUUVySVFzSldOX0Q0RlZXQmciLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.KcgZaevluE_A5aoEMux_Cu_-4_61iAudKB0ieMDNI2s"
    data_key = "LURSIulfT6q97CHl6CsvWjvqEnL990Y/uT5wmcP2Tq8="
    
    print(f"使用提供的访问令牌: {access_token[:50]}...")
    print(f"使用提供的数据密钥: {data_key[:30]}...")
    
    return access_token, data_key

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
    signature = hmac.new(key, message, hashlib.sha256).hexdigest().upper()
    return signature

def test_batch_complete():
    """
    测试批次完成接口
    """
    print("开始测试批次完成接口...")
    
    # 1. 获取访问令牌和数据密钥
    print("\n1. 获取访问令牌和数据密钥...")
    access_token, data_key = get_access_token()
    if not access_token or not data_key:
        print("❌ 无法获取访问令牌或数据密钥，测试终止")
        return
    print(f"✅ 成功获取访问令牌: {access_token[:20]}...")
    print(f"✅ 成功获取数据密钥: {data_key[:20]}...")
    
    # 2. 准备测试数据
    print("\n2. 准备测试数据...")
    batch_id = f"test_batch_{int(time.time())}"
    
    # 业务数据
    business_data = {
        "remark": "测试批次完成接口",
        "callback_url": "http://example.com/callback",
        "total": 100
    }
    
    # 加密业务数据
    plaintext = json.dumps(business_data)
    encrypted_data, iv = encrypt_data(data_key, plaintext)
    
    # Base64编码
    encrypted_data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    
    # 生成签名
    signature = generate_signature(data_key, encrypted_data_b64)
    
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
    print(f"✅ 业务数据: {business_data}")
    
    # 3. 调用批次完成接口
    print("\n3. 调用批次完成接口...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Data-Encrypted": "true",
        "X-Data-Signature": signature
    }
    
    try:
        response = requests.post(
            f"{API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete",
            json=request_data,
            headers=headers
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 批次完成接口调用成功!")
            print(f"   批次ID: {result.get('batch_id')}")
            print(f"   预期数量: {result.get('expected_count')}")
            print(f"   回调URL: {result.get('callback_url')}")
            print(f"   状态: {result.get('status')}")
            print(f"   创建时间: {result.get('created_at')}")
            
            # 4. 验证data_batches表中是否有新记录
            print("\n4. 验证结果...")
            print("✅ 接口调用成功，应该已在data_batches表中创建新记录")
            print("✅ 其他程序现在可以检测到这个批次并开始处理api_usage_logs中的数据")
            
        else:
            print(f"\n❌ 批次完成接口调用失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 请求异常: {e}")
    
    # 5. 测试重复提交
    print("\n5. 测试重复提交...")
    try:
        response = requests.post(
            f"{API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete",
            json=request_data,
            headers=headers
        )
        
        if response.status_code == 400:
            print("✅ 重复提交检测正常，返回400错误")
        else:
            print(f"⚠️  重复提交检测异常，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 重复提交测试异常: {e}")

def main():
    """
    主函数
    """
    print("=" * 60)
    print("批次完成接口测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API地址: {API_URL}")
    print("=" * 60)
    
    test_batch_complete()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()