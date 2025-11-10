#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试带batch_id的动态自定义API接口（加密版本）

测试按照API文档要求的带batch_id的自定义API功能：
1. 获取access_token和data_key
2. 使用AES-256-GCM加密数据
3. 调用带batch_id的自定义API接口
4. 验证数据正确解密和处理

使用方法：
- 基本用法: python test_data_upload_encrypted.py
- 指定API代码: python test_data_upload_encrypted.py my_api
- 指定API代码和HTTP方法: python test_data_upload_encrypted.py my_api POST

测试的API路径格式: /api/v1/{batch_id}/{api_code}

Author: System
Date: 2024
"""

import json
import time
import hmac
import hashlib
import random
import string
import base64
import requests
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from typing import Dict, Any, Optional

# 测试配置
BASE_URL = "http://10.20.1.201:8081"
BASE_URL = "http://127.0.0.1:8081"
AUTH_ENDPOINT = "/api/v1/auth/token"
CUSTOM_API_ENDPOINT = "/api/v1"  # 带batch_id的自定义API基础路径

# 测试平台信息
TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

# 测试数据（原始明文数据）
TEST_DATA = [
    {"test": "test_value_1"},
    {"test": "test_value_2"}
]

class CustomApiWithBatchTester:
    """
    带batch_id的自定义API测试类
    
    提供完整的带batch_id的自定义API加密测试功能
    """
    
    def __init__(self):
        self.base_url = BASE_URL
        self.auth_endpoint = AUTH_ENDPOINT
        self.custom_api_endpoint = CUSTOM_API_ENDPOINT
        self.test_customer = TEST_CUSTOMER
        self.access_token: Optional[str] = None
        self.data_key: Optional[str] = None
        self.used_nonces = set()
    
    def generate_nonce(self, length: int = 12) -> str:
        """
        生成随机nonce字符串
        
        Args:
            length: nonce长度
            
        Returns:
            str: 随机nonce字符串
        """
        chars = string.ascii_letters + string.digits
        nonce = ''.join(random.choice(chars) for _ in range(length))
        
        # 确保nonce唯一
        while nonce in self.used_nonces:
            nonce = ''.join(random.choice(chars) for _ in range(length))
        
        self.used_nonces.add(nonce)
        return nonce
    
    def generate_signature(self, appid: str, timestamp: int, nonce: str, secret: str) -> str:
        """
        生成HMAC-SHA256签名
        
        Args:
            appid: 应用ID
            timestamp: 时间戳
            nonce: 随机字符串
            secret: 预共享密钥
            
        Returns:
            str: 签名值
        """
        signature_data = f"{appid}{timestamp}{nonce}"
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    def authenticate(self) -> bool:
        """
        获取访问令牌和数据密钥
        
        Returns:
            bool: 认证是否成功
        """
        try:
            # 创建认证请求
            appid = self.test_customer["app_id"]
            timestamp = int(time.time())
            nonce = self.generate_nonce()
            secret = self.test_customer["app_secret"]
            
            signature = self.generate_signature(appid, timestamp, nonce, secret)
            
            auth_data = {
                "appid": appid,
                "timestamp": timestamp,
                "nonce": nonce,
                "signature": signature
            }
            
            print(f"发送认证请求: {json.dumps(auth_data, indent=2)}")
            
            # 发送认证请求
            response = requests.post(
                f"{self.base_url}{self.auth_endpoint}",
                json=auth_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"认证响应状态码: {response.status_code}")
            print(f"认证响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                # 检查响应格式，可能有嵌套的data字段
                if "data" in result:
                    data = result["data"]
                    self.access_token = data.get("access_token")
                    self.data_key = data.get("data_key")
                else:
                    self.access_token = result.get("access_token")
                    self.data_key = result.get("data_key")
                
                if self.access_token and self.data_key:
                    print(f"✅ 认证成功")
                    print(f"Access Token: {self.access_token[:20]}...")
                    print(f"Data Key: {self.data_key[:20]}...")
                    return True
                else:
                    print(f"❌ 认证响应中缺少必要字段")
                    print(f"响应内容: {json.dumps(result, indent=2)}")
                    return False
            else:
                print(f"❌ 认证失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 认证异常: {e}")
            return False
    
    def encrypt_data(self, data: Any) -> Dict[str, str]:
        """
        使用AES-256-GCM加密数据
        
        Args:
            data: 要加密的数据
            
        Returns:
            Dict[str, str]: 包含加密数据和IV的字典
        """
        try:
            # 将数据转换为JSON字符串
            json_data = json.dumps(data, ensure_ascii=False)
            plaintext = json_data.encode('utf-8')
            
            # 解码data_key（假设是Base64编码）
            key = base64.b64decode(self.data_key)
            
            # 生成随机IV
            iv = get_random_bytes(12)  # GCM模式推荐12字节IV
            
            # 创建AES-GCM加密器
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            
            # 加密数据
            ciphertext, tag = cipher.encrypt_and_digest(plaintext)
            
            # 将密文和认证标签合并
            encrypted_data = ciphertext + tag
            
            return {
                "data": base64.b64encode(encrypted_data).decode('utf-8'),
                "iv": base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            raise Exception(f"数据加密失败: {str(e)}")
    
    def generate_data_signature(self, encrypted_data: str) -> str:
        """
        生成数据签名
        
        Args:
            encrypted_data: 加密后的数据
            
        Returns:
            str: HMAC-SHA256签名
        """
        signature = hmac.new(
            self.data_key.encode('utf-8'),
            encrypted_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    def call_custom_api_with_batch(self, batch_id: str, api_code: str, data: Any, method: str = "POST") -> bool:
        """
        调用带batch_id的自定义API接口
        
        Args:
            batch_id: 批次ID
            api_code: API代码
            data: 要发送的数据
            method: HTTP方法（默认POST）
            
        Returns:
            bool: 调用是否成功
        """
        try:
            if not self.access_token or not self.data_key:
                print("❌ 请先进行认证")
                return False
            
            # 加密数据
            encrypted_result = self.encrypt_data(data)
            encrypted_data = encrypted_result["data"]
            iv = encrypted_result["iv"]
            print("encrypted_data",encrypted_data)
            # 生成签名
            signature = self.generate_data_signature(encrypted_data)
            
            # 构造上传请求
            upload_data = {
                "timestamp": int(time.time()),
                "nonce": self.generate_nonce(),
                "data": encrypted_data,
                "iv": iv,
                "signature": signature,
                "needread": True
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "X-Data-Encrypted": "true",
                "X-Data-Signature": signature
            }
            
            # 构建请求URL
            url = f"{self.base_url}{self.custom_api_endpoint}/{batch_id}/{api_code}"
            
            print(f"\n调用自定义API: {api_code}")
            print(f"批次ID: {batch_id}")
            print(f"HTTP方法: {method}")
            print(f"请求URL: {url}")
            print(f"原始数据: {json.dumps(data, ensure_ascii=False)}")
            print(f"加密数据长度: {len(encrypted_data)} 字符")
            print(f"IV: {iv}")
            print(f"签名: {signature[:20]}...")
            
            # 发送自定义API请求
            
            if method.upper() == "GET":
                response = requests.get(url, params=upload_data, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=upload_data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=upload_data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=upload_data, headers=headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=upload_data, headers=headers)
            else:
                print(f"❌ 不支持的HTTP方法: {method}")
                return False
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"✅ 自定义API调用成功")
                    print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
                except:
                    print(f"✅ 自定义API调用成功（非JSON响应）")
                    print(f"响应内容: {response.text}")
                return True
            else:
                print(f"❌ 自定义API调用失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API调用异常: {e}")
            return False
    
    def call_custom_api_without_encryption(self, batch_id: str, api_code: str, data: Any, method: str = "POST") -> bool:
        """
        调用带batch_id的自定义API接口（不加密）
        
        Args:
            batch_id: 批次ID
            api_code: API代码
            data: 要发送的数据
            method: HTTP方法（默认POST）
            
        Returns:
            bool: 调用是否成功
        """
        try:
            if not self.access_token:
                print("❌ 请先进行认证")
                return False
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.base_url}{self.custom_api_endpoint}/{batch_id}/{api_code}"
            
            print(f"\n调用自定义API（非加密）: {api_code}")
            print(f"批次ID: {batch_id}")
            print(f"HTTP方法: {method}")
            print(f"请求URL: {url}")
            print(f"原始数据: {json.dumps(data, ensure_ascii=False)}")
            
            # 发送自定义API请求
            if method.upper() == "GET":
                response = requests.get(url, params=data, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=data, headers=headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=data, headers=headers)
            else:
                print(f"❌ 不支持的HTTP方法: {method}")
                return False
            
            print(f"API响应状态码: {response.status_code}")
            print(f"API响应内容: {response.text}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"✅ 自定义API调用成功（非加密）")
                    print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
                except:
                    print(f"✅ 自定义API调用成功（非加密，非JSON响应）")
                    print(f"响应内容: {response.text}")
                return True
            else:
                print(f"❌ 自定义API调用失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API调用异常: {e}")
            return False
    
    def run_test(self, api_code: str = "test_api", method: str = "POST"):
        """
        运行完整的测试流程
        
        Args:
            api_code: 要测试的API代码（默认为test_api）
            method: HTTP方法（默认为POST）
        """
        print("=== 开始带batch_id的自定义API加密测试 ===")
        print(f"测试API代码: {api_code}")
        print(f"HTTP方法: {method}")
        
        # 1. 认证获取token
        print("\n步骤1: 获取访问令牌和数据密钥")
        if not self.authenticate():
            print("❌ 认证失败，测试终止")
            return
        
        # 2. 调用自定义API（加密版本）
        print("\n步骤2: 调用带batch_id的自定义API（加密版本）")
        batch_id = f"test_batch_{int(time.time())}"
        
        # 测试数据 - 根据API字段要求调整
        test_data = [
            {"test": "test_value_1"},
            {"test": "test_value_2"}
        ]
        
        success_encrypted = self.call_custom_api_with_batch(batch_id, api_code, test_data, method)
        
        # 3. 调用自定义API（非加密版本）
        print("\n步骤3: 调用带batch_id的自定义API（非加密版本）")
        batch_id_plain = f"test_batch_plain_{int(time.time())}"
        
        success_plain = self.call_custom_api_without_encryption(batch_id_plain, api_code, test_data, method)
        
        if success_encrypted and success_plain:
            print("\n✅ 所有测试通过")
            print("\n💡 提示:")
            print("- 检查数据库中的api_usage_logs表，确认API调用是否正确记录")
            print("- 检查自定义API的处理逻辑，确认加密数据是否正确解密")
            print("- 观察服务器日志，查看详细的处理过程")
            print(f"- 测试的API路径: /api/v1/{{batch_id}}/{api_code}")
            print(f"- 加密测试批次ID: {batch_id}")
            print(f"- 非加密测试批次ID: {batch_id_plain}")
        elif success_encrypted:
            print("\n⚠️ 加密测试通过，非加密测试失败")
        elif success_plain:
            print("\n⚠️ 非加密测试通过，加密测试失败")
        else:
            print("\n❌ 所有测试失败")

def main():
    """
    主函数
    """
    import sys
    
    # 从命令行参数获取API代码和HTTP方法
    api_code = sys.argv[1] if len(sys.argv) > 1 else "test_api"
    method = sys.argv[2] if len(sys.argv) > 2 else "POST"
    
    print(f"使用参数: API代码={api_code}, HTTP方法={method}")
    print("用法: python test_data_upload_encrypted.py [api_code] [method]")
    print("示例: python test_data_upload_encrypted.py my_api POST")
    print()
    
    tester = CustomApiWithBatchTester()
    tester.run_test(api_code, method)

if __name__ == "__main__":
    main()