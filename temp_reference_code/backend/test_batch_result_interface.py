#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批次结果查询接口

完整测试 /api/v1/results/{batch_id} 接口功能，包括：
1. 客户认证获取token
2. 创建测试批次
3. 查询批次结果
4. 验证加密数据
5. 错误场景测试

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
from typing import Dict, Any, Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入项目模块
from app.core.database import get_db
from app.models.batch import DataBatch
from app.models.customer import Customer
from sqlalchemy import desc

# 测试配置
BASE_URL = "http://localhost:8081"
TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"
RESULTS_ENDPOINT = f"{BASE_URL}/api/v1/results"

# 测试客户凭据（需要在数据库中存在）
TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

class BatchResultTester:
    """
    批次结果查询接口测试类
    
    提供完整的批次结果查询接口测试功能
    """
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token_endpoint = TOKEN_ENDPOINT
        self.results_endpoint = RESULTS_ENDPOINT
        self.test_customer = TEST_CUSTOMER
        self.access_token = None
        self.data_key = None
        self.customer_id = None
    
    def generate_nonce(self, length: int = 12) -> str:
        """
        生成随机nonce字符串
        
        Args:
            length: nonce长度
            
        Returns:
            str: 随机nonce字符串
        """
        import random
        import string
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_signature(self, appid: str, timestamp: int, nonce: str, secret: str) -> str:
        """
        生成HMAC-SHA256签名
        
        Args:
            appid: 应用ID
            timestamp: 时间戳
            nonce: 随机字符串
            secret: 预共享密钥
            
        Returns:
            str: 签名值（大写十六进制）
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
        客户认证获取访问令牌
        
        Returns:
            bool: 认证是否成功
        """
        print("\n=== 客户认证 ===")
        
        try:
            # 准备认证数据
            timestamp = int(time.time())
            nonce = self.generate_nonce()
            signature = self.generate_signature(
                self.test_customer["app_id"],
                timestamp,
                nonce,
                self.test_customer["app_secret"]
            )
            
            auth_data = {
                "appid": self.test_customer["app_id"],
                "timestamp": timestamp,
                "nonce": nonce,
                "signature": signature
            }
            
            print(f"📝 认证请求数据: {json.dumps(auth_data, indent=2)}")
            
            # 发送认证请求
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                self.token_endpoint,
                json=auth_data,
                headers=headers,
                timeout=10
            )
            
            print(f"📝 响应状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.data_key = data.get("data_key")
                
                # 从数据库获取客户ID
                db = next(get_db())
                try:
                    customer = db.query(Customer).filter(
                        Customer.app_id == self.test_customer["app_id"]
                    ).first()
                    if customer:
                        self.customer_id = customer.id
                        print(f"✅ 认证成功!")
                        print(f"   客户ID: {self.customer_id}")
                        print(f"   访问令牌: {self.access_token[:50]}...")
                        print(f"   数据密钥: {self.data_key[:30]}...")
                        return True
                    else:
                        print(f"❌ 找不到客户记录")
                        return False
                finally:
                    db.close()
            else:
                print(f"❌ 认证失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 认证异常: {e}")
            return False
    
    def create_test_batch(self) -> Optional[str]:
        """
        创建测试批次
        
        Returns:
            Optional[str]: 批次ID，失败时返回None
        """
        print("\n=== 创建测试批次 ===")
        
        if not self.customer_id:
            print("❌ 客户ID未设置，请先认证")
            return None
        
        try:
            db = next(get_db())
            try:
                # 生成测试批次ID
                test_batch_id = f"test_batch_{int(time.time())}"
                
                # 创建测试批次
                batch = DataBatch(
                    customer_id=self.customer_id,
                    api_id=None,  # 可以为空
                    batch_id=test_batch_id,
                    batch_name=f"测试批次 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    description="批次结果查询接口测试",
                    status="completed",  # 已完成状态
                    expected_count=10,
                    total_count=10,
                    pending_count=0,
                    processing_count=0,
                    completed_count=8,
                    failed_count=2,
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    processing_time=5.5,  # 5.5秒处理时间
                    error_message=None
                )
                
                db.add(batch)
                db.commit()
                db.refresh(batch)
                
                print(f"✅ 测试批次创建成功!")
                print(f"   批次ID: {test_batch_id}")
                print(f"   批次名称: {batch.batch_name}")
                print(f"   状态: {batch.status}")
                print(f"   总数: {batch.total_count}")
                print(f"   完成数: {batch.completed_count}")
                print(f"   失败数: {batch.failed_count}")
                
                return test_batch_id
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ 创建测试批次失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def decrypt_result_data(self, encrypted_data: str, iv: str) -> Optional[Dict[str, Any]]:
        """
        解密结果数据
        
        Args:
            encrypted_data: 加密的数据
            iv: 初始化向量
            
        Returns:
            Optional[Dict[str, Any]]: 解密后的数据，失败时返回None
        """
        try:
            if not self.data_key:
                print("❌ 数据密钥未设置")
                return None
            
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            iv_bytes = base64.b64decode(iv)
            
            # AES解密
            cipher = AES.new(self.data_key.encode('utf-8')[:32].ljust(32, b'\0'), AES.MODE_CBC, iv_bytes)
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            
            # 去除填充
            decrypted_data = unpad(decrypted_bytes, AES.block_size)
            
            # 解析JSON
            result_data = json.loads(decrypted_data.decode('utf-8'))
            return result_data
            
        except Exception as e:
            print(f"❌ 解密失败: {e}")
            return None
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """
        验证数据签名
        
        Args:
            data: 数据
            signature: 签名
            
        Returns:
            bool: 签名是否有效
        """
        try:
            if not self.data_key:
                return False
            
            expected_signature = hmac.new(
                self.data_key.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            print(f"❌ 签名验证失败: {e}")
            return False
    
    def test_get_batch_result(self, batch_id: str) -> bool:
        """
        测试查询批次结果
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 测试是否成功
        """
        print(f"\n=== 查询批次结果: {batch_id} ===")
        
        if not self.access_token:
            print("❌ 访问令牌未设置，请先认证")
            return False
        
        try:
            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            url = f"{self.results_endpoint}/{batch_id}"
            print(f"🚀 发送请求: GET {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"📝 响应状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ 查询成功!")
                print(f"   状态: {result.get('status')}")
                
                # 如果有加密数据，尝试解密和验证
                if result.get('data') and result.get('iv') and result.get('result_sign'):
                    print(f"   加密数据长度: {len(result['data'])}")
                    print(f"   IV: {result['iv']}")
                    print(f"   签名: {result['result_sign']}")
                    
                    # 验证签名
                    if self.verify_signature(result['data'], result['result_sign']):
                        print("   ✅ 签名验证通过")
                    else:
                        print("   ❌ 签名验证失败")
                    
                    # 解密数据
                    decrypted_data = self.decrypt_result_data(result['data'], result['iv'])
                    if decrypted_data:
                        print("   ✅ 数据解密成功")
                        print(f"   解密后数据: {json.dumps(decrypted_data, indent=4, ensure_ascii=False)}")
                    else:
                        print("   ❌ 数据解密失败")
                else:
                    print("   数据: [无加密数据]")
                
                return True
            else:
                print(f"❌ 查询失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 查询异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_get_nonexistent_batch(self) -> bool:
        """
        测试查询不存在的批次
        
        Returns:
            bool: 测试是否成功
        """
        print("\n=== 测试查询不存在的批次 ===")
        
        if not self.access_token:
            print("❌ 访问令牌未设置，请先认证")
            return False
        
        try:
            # 使用不存在的批次ID
            nonexistent_batch_id = f"nonexistent_{uuid.uuid4().hex}"
            print(f"📝 不存在的批次ID: {nonexistent_batch_id}")
            
            # 准备请求头
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            url = f"{self.results_endpoint}/{nonexistent_batch_id}"
            print(f"🚀 发送请求: GET {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"📝 响应状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text}")
            
            if response.status_code == 404:
                print("✅ 测试成功! 正确返回404状态码")
                return True
            else:
                print(f"❌ 测试失败，期望404，实际{response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_unauthorized_access(self) -> bool:
        """
        测试未授权访问
        
        Returns:
            bool: 测试是否成功
        """
        print("\n=== 测试未授权访问 ===")
        
        try:
            # 使用无效的访问令牌
            invalid_token = "invalid_token_12345"
            print(f"📝 无效访问令牌: {invalid_token}")
            
            # 准备请求头
            headers = {
                "Authorization": f"Bearer {invalid_token}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            test_batch_id = "test_batch_123"
            url = f"{self.results_endpoint}/{test_batch_id}"
            print(f"🚀 发送请求: GET {url}")
            
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"📝 响应状态码: {response.status_code}")
            print(f"📝 响应内容: {response.text}")
            
            if response.status_code == 401:
                print("✅ 测试成功! 正确返回401状态码")
                return True
            else:
                print(f"❌ 测试失败，期望401，实际{response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """
        运行所有测试
        
        Returns:
            bool: 所有测试是否通过
        """
        print("🧪 批次结果查询接口完整测试")
        print("=" * 80)
        
        test_results = []
        
        # 1. 客户认证
        test_results.append(self.authenticate())
        
        if test_results[-1]:  # 认证成功才继续
            # 2. 创建测试批次
            test_batch_id = self.create_test_batch()
            
            if test_batch_id:
                # 3. 查询批次结果
                test_results.append(self.test_get_batch_result(test_batch_id))
            else:
                test_results.append(False)
            
            # 4. 测试查询不存在的批次
            test_results.append(self.test_get_nonexistent_batch())
        else:
            test_results.extend([False, False])
        
        # 5. 测试未授权访问
        test_results.append(self.test_unauthorized_access())
        
        # 输出测试结果
        print("\n" + "=" * 80)
        print("📊 测试结果汇总:")
        test_names = [
            "客户认证",
            "查询批次结果",
            "查询不存在批次",
            "未授权访问测试"
        ]
        
        for i, (name, result) in enumerate(zip(test_names, test_results)):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"   {i+1}. {name}: {status}")
        
        all_passed = all(test_results)
        print(f"\n🎯 总体结果: {'✅ 全部通过' if all_passed else '❌ 部分失败'}")
        
        return all_passed

def main():
    """
    主函数
    """
    try:
        # 检查服务器是否运行
        print("🔍 检查服务器状态...")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ 服务器未正常运行，状态码: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        print(f"请确保服务器在 {BASE_URL} 上运行")
        return
    
    # 运行测试
    tester = BatchResultTester()
    success = tester.run_all_tests()
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()