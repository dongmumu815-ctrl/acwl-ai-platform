#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次结果加密查询测试脚本

测试通过API接口查询加密的批次处理结果，并验证返回的加密数据和IV是否正确。
"""

import json
import time
import hmac
import hashlib
import secrets
import requests
from typing import Dict, Any, Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64


class BatchResultEncryptionTester:
    """批次结果加密查询测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.data_key = None
        self.session = requests.Session()
        
    def authenticate(self, app_id: str, app_secret: str) -> bool:
        """
        客户认证，获取访问令牌和数据密钥
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            
        Returns:
            认证是否成功
        """
        try:
            # 生成认证参数
            timestamp = int(time.time())
            nonce = secrets.token_hex(8)
            
            # 生成签名
            signature_data = f"{app_id}{timestamp}{nonce}"
            signature = hmac.new(
                app_secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().upper()
            
            auth_url = f"{self.base_url}/api/v1/auth/token"
            auth_data = {
                "appid": app_id,
                "timestamp": timestamp,
                "nonce": nonce,
                "signature": signature
            }
            
            print(f"正在认证客户: {app_id}")
            response = self.session.post(auth_url, json=auth_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"认证响应: {result}")
                data = result.get("data", {})
                self.access_token = data.get("access_token")
                self.data_key = data.get("data_key", "default_encryption_key_32_bytes!")
                print(f"认证成功，获取到token: {self.access_token[:20] if self.access_token else 'None'}...")
                return True
            else:
                print(f"认证失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"认证过程中发生错误: {e}")
            return False
    
    def decrypt_data(self, encrypted_data: str, iv: str) -> Dict[str, Any]:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的数据（Base64编码）
            iv: 初始化向量（Base64编码）
            
        Returns:
            解密后的数据
        """
        try:
            # 解码数据
            ciphertext = base64.b64decode(encrypted_data)
            iv_bytes = base64.b64decode(iv)
            key = base64.b64decode(self.data_key)
            
            # 分离密文和认证标签
            tag_length = 16  # GCM模式的认证标签长度为16字节
            actual_ciphertext = ciphertext[:-tag_length]
            tag = ciphertext[-tag_length:]
            
            # 创建AES-GCM解密器
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv_bytes)
            
            # 解密数据
            plaintext = cipher.decrypt_and_verify(actual_ciphertext, tag)
            
            # 解析JSON数据
            return json.loads(plaintext.decode('utf-8'))
            
        except Exception as e:
            raise Exception(f"数据解密失败: {str(e)}")
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """
        验证数据签名
        
        Args:
            data: 加密的数据
            signature: 数据签名
            
        Returns:
            签名是否有效
        """
        try:
            # 使用数据密钥作为HMAC密钥
            key = self.data_key.encode('utf-8')
            
            # 计算HMAC-SHA256签名
            calculated_signature = hmac.new(
                key,
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # 比较签名
            return calculated_signature == signature
            
        except Exception as e:
            print(f"签名验证失败: {e}")
            return False
    
    def query_batch_result(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        查询批次处理结果
        
        Args:
            batch_id: 批次ID
            
        Returns:
            批次处理结果
        """
        try:
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/result/batch/{batch_id}/encrypted"
            print(f"正在查询批次结果: {url}")
            print(f"使用token: {self.access_token[:20] if self.access_token else 'None'}...")
            
            response = self.session.get(url, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"查询响应: {result}")
                return result
            else:
                print(f"查询失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"查询过程中发生错误: {e}")
            return None
    
    def create_test_batch(self) -> str:
        """
        创建测试批次
        
        Returns:
            str: 批次ID
        """
        try:
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 构造请求体
            batch_data = {
                "batch_name": f"test_batch_{int(time.time())}",
                "description": "测试批次",
                "expected_count": 10
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/batch"
            print(f"正在创建测试批次: {url}")
            print(f"使用token: {self.access_token[:20] if self.access_token else 'None'}...")
            
            response = self.session.post(url, json=batch_data, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"创建批次响应: {result}")
                batch_id = result.get("batch_id")
                print(f"创建的批次ID: {batch_id}")
                return batch_id
            else:
                print(f"创建批次失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"创建批次过程中发生错误: {e}")
            return None
    
    def upload_test_data(self, batch_id: str) -> bool:
        """
        上传测试数据
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 上传是否成功
        """
        try:
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 生成时间戳和随机数
            timestamp = str(int(time.time() * 1000))
            nonce = secrets.token_hex(16)
            
            # 准备测试数据
            test_data = {"test": "test", "test2": "test2"}
            
            # 加密数据
            encrypted_result = self.encrypt_data(self.data_key, json.dumps(test_data))
            encrypted_data = encrypted_result["data"]
            iv = encrypted_result["iv"]
            
            # 生成签名
            signature = hmac.new(
                self.data_key.encode('utf-8'),
                encrypted_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # 构造请求体
            request_body = {
                "timestamp": timestamp,
                "nonce": nonce,
                "data": encrypted_data,
                "iv": iv,
                "signature": signature,
                "needread": True,
                "batch_id": batch_id
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/data/upload"
            print(f"正在上传测试数据: {url}")
            print(f"使用token: {self.access_token[:20] if self.access_token else 'None'}...")
            
            response = self.session.post(url, json=request_body, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"上传数据响应: {result}")
                return True
            else:
                print(f"上传数据失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"上传数据过程中发生错误: {e}")
            return False
    
    def complete_batch(self, batch_id: str) -> bool:
        """
        完成批次
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 完成是否成功
        """
        try:
            # 构造请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 构造请求体
            request_body = {
                "status": "completed",
                "total_count": 1,
                "completed_count": 1,
                "failed_count": 0
            }
            
            # 发送请求
            url = f"{self.base_url}/api/v1/batch/{batch_id}/complete"
            print(f"正在完成批次: {url}")
            print(f"使用token: {self.access_token[:20] if self.access_token else 'None'}...")
            
            response = self.session.post(url, json=request_body, headers=headers)
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"完成批次响应: {result}")
                return True
            else:
                print(f"完成批次失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"完成批次过程中发生错误: {e}")
            return False
    
    def encrypt_data(self, data_key: str, plaintext: str) -> Dict[str, str]:
        """
        使用AES-256-GCM加密数据
        
        Args:
            data_key: 数据密钥（Base64编码）
            plaintext: 明文数据
            
        Returns:
            Dict[str, str]: 包含加密数据和IV的字典
        """
        try:
            # 解码data_key（假设是Base64编码）
            key = base64.b64decode(data_key)
            
            # 生成随机IV
            iv = get_random_bytes(12)  # GCM模式推荐12字节IV
            
            # 创建AES-GCM加密器
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            
            # 加密数据
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            
            # 将密文和认证标签合并
            encrypted_data = ciphertext + tag
            
            return {
                "data": base64.b64encode(encrypted_data).decode('utf-8'),
                "iv": base64.b64encode(iv).decode('utf-8')
            }
            
        except Exception as e:
            raise Exception(f"数据加密失败: {str(e)}")
    
    def run_test(self, app_id: str, app_secret: str, batch_id: str = None):
        """
        运行完整的批次结果加密查询测试
        
        Args:
            app_id: 应用ID
            app_secret: 应用密钥
            batch_id: 批次ID（可选，如果不提供则创建新批次）
        """
        print("=== 批次结果加密查询测试 ===\n")
        
        # 步骤1: 认证
        if not self.authenticate(app_id, app_secret):
            print("认证失败，测试终止")
            return
        
        # 如果没有提供批次ID，则创建新批次
        if not batch_id:
            print("\n创建测试批次...")
            batch_id = self.create_test_batch()
            if not batch_id:
                print("创建测试批次失败，测试终止")
                return
            
            print("\n上传测试数据...")
            if not self.upload_test_data(batch_id):
                print("上传测试数据失败，测试终止")
                return
            
            print("\n完成批次...")
            if not self.complete_batch(batch_id):
                print("完成批次失败，测试终止")
                return
        
        # 步骤2: 查询批次结果
        print("\n查询批次结果...")
        result = self.query_batch_result(batch_id)
        
        if not result:
            print("查询批次结果失败，测试终止")
            return
        
        # 步骤3: 验证结果
        status = result.get("status")
        print(f"\n批次状态: {status}")
        
        if status in ["completed", "failed"]:
            encrypted_data = result.get("data")
            iv = result.get("iv")
            signature = result.get("result_sign")
            
            if not all([encrypted_data, iv, signature]):
                print("返回的加密数据不完整，测试失败")
                return
            
            print("\n验证数据签名...")
            if self.verify_signature(encrypted_data, signature):
                print("签名验证成功!")
            else:
                print("签名验证失败!")
                return
            
            print("\n解密数据...")
            try:
                decrypted_data = self.decrypt_data(encrypted_data, iv)
                print(f"解密成功! 解密后的数据:\n{json.dumps(decrypted_data, indent=2, ensure_ascii=False)}")
                print("\n测试成功完成!")
            except Exception as e:
                print(f"解密失败: {e}")
        else:
            print(f"批次尚未完成，当前状态: {status}")


if __name__ == "__main__":
    # 测试配置
    BASE_URL = "http://localhost:8000"
    APP_ID = "test_app_001"  # 使用已创建的测试客户
    APP_SECRET = "test_secret_123456789"  # 对应的密钥
    BATCH_ID = None  # 设置为None，让脚本自动创建新批次
    
    # 创建测试器并运行测试
    tester = BatchResultEncryptionTester(BASE_URL)
    tester.run_test(APP_ID, APP_SECRET, BATCH_ID)