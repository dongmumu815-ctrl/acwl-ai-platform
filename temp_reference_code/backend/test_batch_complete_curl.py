#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用curl命令测试批次完成接口

生成curl命令来测试批次完成接口
"""

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

# 测试用的访问令牌（需要先通过其他方式获取）
# 这里使用一个示例令牌，实际使用时需要替换
TEST_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example_token"
TEST_DATA_KEY = "your_32_byte_data_key_here_123456"  # 32字节的data_key
TEST_API_CODE = "test_api_001"  # 测试用的API代码

def encrypt_data(data_key: str, plaintext: str):
    """
    使用AES-256-GCM加密数据
    
    Args:
        data_key: 数据密钥
        plaintext: 明文数据
        
    Returns:
        tuple: (加密数据, IV)
    """
    # 确保data_key是32字节
    key = data_key.encode('utf-8')[:32].ljust(32, b'\0')
    
    # 生成随机IV
    iv = get_random_bytes(12)  # GCM模式推荐12字节IV
    
    # 创建加密器
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    
    # 加密数据
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
    
    # 返回加密数据（包含tag）和IV
    return ciphertext + tag, iv

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

def generate_test_data():
    """
    生成测试数据
    
    Returns:
        dict: 测试数据
    """
    # 生成批次ID
    batch_id = f"test_batch_{int(time.time())}"
    
    # 业务数据
    business_data = {
        "remark": "测试批次完成接口 - curl测试",
        "callback_url": "http://example.com/callback",
        "total": 150
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
    
    return batch_id, request_data, business_data

def generate_curl_command():
    """
    生成curl测试命令
    """
    print("=" * 60)
    print("批次完成接口 curl 测试命令生成器")
    print("=" * 60)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 生成测试数据
    batch_id, request_data, business_data = generate_test_data()
    
    print(f"\n📋 测试信息:")
    print(f"   批次ID: {batch_id}")
    print(f"   业务数据: {json.dumps(business_data, ensure_ascii=False)}")
    print(f"   API地址: {API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete")
    
    # 生成curl命令
    request_json = json.dumps(request_data, ensure_ascii=False)
    
    curl_command = f'''curl -X POST "{API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete" \\
  -H "Authorization: Bearer {TEST_ACCESS_TOKEN}" \\
  -H "Content-Type: application/json" \\
  -H "X-Data-Encrypted: true" \\
  -H "X-Data-Signature: {request_data['signature']}" \\
  -d '{request_json}' \\
  -v'''
    
    print(f"\n🚀 curl 测试命令:")
    print("-" * 40)
    print(curl_command)
    print("-" * 40)
    
    # 生成PowerShell版本的命令
    powershell_command = f'''Invoke-RestMethod -Uri "{API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete" `
  -Method POST `
  -Headers @{{
    "Authorization" = "Bearer {TEST_ACCESS_TOKEN}"
    "Content-Type" = "application/json"
    "X-Data-Encrypted" = "true"
    "X-Data-Signature" = "{request_data['signature']}"
  }} `
  -Body '{request_json}' `
  -Verbose'''
    
    print(f"\n🔷 PowerShell 测试命令:")
    print("-" * 40)
    print(powershell_command)
    print("-" * 40)
    
    # 预期响应
    expected_response = {
        "code": 200,
        "message": "批次完成标记成功，已在data_batches表中创建记录",
        "batch_id": batch_id,
        "expected_count": business_data["total"],
        "callback_url": business_data["callback_url"],
        "status": "待处理",
        "created_at": "2025-07-20T03:45:00.000000"
    }
    
    print(f"\n✅ 预期响应:")
    print(json.dumps(expected_response, indent=2, ensure_ascii=False))
    
    # 测试重复提交的curl命令
    print(f"\n🔄 重复提交测试命令 (应该返回400错误):")
    print("-" * 40)
    duplicate_curl = curl_command.replace('-v', '-v --fail-with-body')
    print(duplicate_curl)
    print("-" * 40)
    
    print(f"\n📝 使用说明:")
    print("1. 首先确保后端服务器正在运行 (http://localhost:8000)")
    print("2. 替换 TEST_ACCESS_TOKEN 为有效的访问令牌")
    print("3. 替换 TEST_DATA_KEY 为正确的32字节数据密钥")
    print("4. 运行第一个curl命令，应该返回200成功响应")
    print("5. 再次运行相同命令，应该返回400错误（重复提交）")
    print("6. 检查data_batches表，应该有新的记录被创建")
    
    print(f"\n🔍 验证步骤:")
    print("1. 检查响应状态码是否为200")
    print("2. 检查响应消息是否包含'已在data_batches表中创建记录'")
    print("3. 检查返回的batch_id是否正确")
    print("4. 检查data_batches表中是否有对应记录")
    print("5. 验证其他程序是否能检测到新记录")

def generate_simple_test():
    """
    生成简化的测试数据（不加密）
    """
    print("\n" + "=" * 60)
    print("简化测试（仅用于开发调试）")
    print("=" * 60)
    
    batch_id = f"simple_test_{int(time.time())}"
    
    # 简化的请求数据（不加密）
    simple_data = {
        "timestamp": int(time.time()),
        "nonce": f"simple_nonce_{int(time.time())}",
        "data": base64.b64encode(json.dumps({
            "remark": "简化测试",
            "callback_url": "http://example.com/simple",
            "total": 50
        }).encode()).decode(),
        "iv": base64.b64encode(b"simple_iv_12345").decode(),
        "signature": "simple_signature",
        "needread": False
    }
    
    simple_curl = f'''curl -X POST "{API_URL}/batch/{TEST_API_CODE}/{batch_id}/complete" \\
  -H "Authorization: Bearer {TEST_ACCESS_TOKEN}" \\
  -H "Content-Type: application/json" \\
  -H "X-Data-Encrypted: false" \\
  -d '{json.dumps(simple_data)}' \\
  -v'''
    
    print(f"简化测试命令:")
    print("-" * 40)
    print(simple_curl)
    print("-" * 40)
    print("注意: 此命令仅用于开发调试，生产环境必须使用加密")

def main():
    """
    主函数
    """
    try:
        generate_curl_command()
        generate_simple_test()
        
        print("\n" + "=" * 60)
        print("命令生成完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 生成命令时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()