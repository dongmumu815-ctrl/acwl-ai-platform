#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次完成接口测试脚本
测试 /api/v1/batch/{api_code}/{batch_id}/complete 接口
"""

import requests
import json
import base64
import hashlib
import hmac
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import uuid

# 测试配置
API_BASE_URL = "http://localhost:8000"
API_CODE = "test22333_upload"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2IiwidHlwZSI6ImN1c3RvbWVyIiwiZXhwIjoxNzUzMTY0MDc1LCJpYXQiOjE3NTMwNzc2NzUsImp0aSI6InlOUm9GZWpobkZJR3p6YlB4QkF4ejVfTkRrdWl2Um5pSXhhOGxUQXBJWUUiLCJjdXN0b21lcl9pZCI6NiwiYXBwX2lkIjoidGVzdF9hcHBfMDAxIn0.r1if0CDb9ANFCd2_VVA1Q_k59YmTLrKOSqPu1oM8QoQ"
DATA_KEY = "zxhAY7pSTriPqqnQkXjNWfbO4Pzh20Olj7TblteYBO8="

def encrypt_data_aes_gcm(data_key: str, data: dict) -> tuple:
    """
    使用AES-GCM模式加密数据
    
    Args:
        data_key: Base64编码的密钥
        data: 要加密的数据字典
        
    Returns:
        tuple: (加密后的数据, IV)
    """
    # 解码密钥
    key = base64.b64decode(data_key)
    
    # 生成随机IV (12字节用于GCM)
    iv = os.urandom(12)
    
    # 将数据转换为JSON字符串
    data_json = json.dumps(data, ensure_ascii=False)
    data_bytes = data_json.encode('utf-8')
    
    # 创建AES-GCM加密器
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    
    # 加密数据
    ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
    
    # 获取认证标签
    tag = encryptor.tag
    
    # 组合密文和标签
    encrypted_data = ciphertext + tag
    
    # Base64编码
    encrypted_b64 = base64.b64encode(encrypted_data).decode('utf-8')
    iv_b64 = base64.b64encode(iv).decode('utf-8')
    
    return encrypted_b64, iv_b64

def create_signature(data_key: str, data: str) -> str:
    """
    创建数据签名（与服务端verify_signature函数保持一致）
    
    Args:
        data_key: Base64编码的密钥
        data: 要签名的数据
        
    Returns:
        str: 十六进制编码的签名（大写）
    """
    # 注意：这里直接使用data_key字符串，不进行base64解码
    # 与服务端data.py中的verify_signature函数保持一致
    signature = hmac.new(
        data_key.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def test_batch_complete():
    """
    测试批次完成接口
    """
    print("=== 批次完成接口测试 ===")
    
    # 生成测试批次ID
    batch_id = f"test_batch_{int(datetime.now().timestamp())}"
    print(f"测试批次ID: {batch_id}")
    
    # 准备业务数据
    business_data = {
        "total": 100,
        "callback_url": "https://example.com/callback",
        "remark": "测试批次完成接口"
    }
    
    # 加密业务数据
    encrypted_data, iv = encrypt_data_aes_gcm(DATA_KEY, business_data)
    
    # 创建签名
    signature = create_signature(DATA_KEY, encrypted_data)
    
    # 准备请求数据
    request_data = {
        "data": encrypted_data,
        "iv": iv,
        "signature": signature,
        "needread": True,
        "timestamp": int(datetime.now().timestamp()),
        "nonce": str(uuid.uuid4())
    }
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Data-Encrypted": "true",
        "X-Data-Signature": signature,
        "Content-Type": "application/json"
    }
    
    # 构建请求URL
    url = f"{API_BASE_URL}/api/v1/batch/{API_CODE}/{batch_id}/complete"
    
    print(f"请求URL: {url}")
    print(f"请求头: {json.dumps(headers, indent=2, ensure_ascii=False)}")
    print(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    print(f"业务数据: {json.dumps(business_data, indent=2, ensure_ascii=False)}")
    
    try:
        # 发送请求
        response = requests.post(url, json=request_data, headers=headers)
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"响应数据: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError:
            print(f"响应文本: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ 测试成功！")
        else:
            print("\n❌ 测试失败！")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求异常: {e}")
    except Exception as e:
        print(f"\n❌ 其他异常: {e}")

def test_duplicate_batch():
    """
    测试重复提交同一个批次ID的情况
    """
    print("\n=== 测试重复批次提交 ===")
    
    # 使用固定的批次ID
    batch_id = "test_duplicate_batch_123"
    print(f"测试批次ID: {batch_id}")
    
    # 准备业务数据
    business_data = {
        "total": 50,
        "callback_url": "https://example.com/callback",
        "remark": "测试重复批次提交"
    }
    
    # 加密业务数据
    encrypted_data, iv = encrypt_data_aes_gcm(DATA_KEY, business_data)
    
    # 创建签名
    signature = create_signature(DATA_KEY, encrypted_data)
    
    # 准备请求数据
    request_data = {
        "data": encrypted_data,
        "iv": iv,
        "signature": signature,
        "needread": True,
        "timestamp": int(datetime.now().timestamp()),
        "nonce": str(uuid.uuid4())
    }
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "X-Data-Encrypted": "true",
        "X-Data-Signature": signature,
        "Content-Type": "application/json"
    }
    
    # 构建请求URL
    url = f"{API_BASE_URL}/api/v1/batch/{API_CODE}/{batch_id}/complete"
    
    # 第一次提交
    print("\n第一次提交:")
    try:
        response = requests.post(url, json=request_data, headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print("✅ 第一次提交成功")
        else:
            print(f"❌ 第一次提交失败: {response.text}")
    except Exception as e:
        print(f"❌ 第一次提交异常: {e}")
    
    # 第二次提交（应该失败）
    print("\n第二次提交（应该返回400错误）:")
    try:
        response = requests.post(url, json=request_data, headers=headers)
        print(f"状态码: {response.status_code}")
        if response.status_code == 400:
            response_data = response.json()
            print(f"✅ 正确返回400错误: {response_data.get('detail', '')}")
        else:
            print(f"❌ 未返回预期的400错误: {response.text}")
    except Exception as e:
        print(f"❌ 第二次提交异常: {e}")

if __name__ == "__main__":
    print("批次完成接口测试脚本")
    print(f"API代码: {API_CODE}")
    print(f"Token: {TOKEN[:50]}...")
    print(f"Data Key: {DATA_KEY[:20]}...")
    
    # 测试正常情况
    test_batch_complete()
    
    # 测试重复提交
    test_duplicate_batch()
    
    print("\n测试完成！")