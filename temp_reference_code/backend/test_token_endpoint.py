#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 /token 接口的完整功能

测试场景包括：
1. 正常认证流程
2. 时间窗口校验
3. 防重放攻击（nonce校验）
4. 签名验证
5. 无效appid处理
6. 各种错误场景

Author: System
Date: 2024
"""

import pytest
import requests
import json
import time
import hmac
import hashlib
import uuid
import random
import string
from datetime import datetime
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000"
TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"
ADMIN_LOGIN_URL = f"{BASE_URL}/api/v1/admin/login"

# 测试用客户数据（需要在数据库中存在）
TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

class TokenEndpointTester:
    """
    Token接口测试类
    
    提供完整的token接口测试功能
    """
    
    def __init__(self):
        self.base_url = BASE_URL
        self.token_endpoint = TOKEN_ENDPOINT
        self.test_customer = TEST_CUSTOMER
        self.used_nonces = set()  # 记录已使用的nonce
    
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
            str: 签名值（大写十六进制）
        """
        signature_data = f"{appid}{timestamp}{nonce}"
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    def create_auth_request(self, 
                           appid: str = None, 
                           timestamp: int = None, 
                           nonce: str = None, 
                           secret: str = None,
                           custom_signature: str = None) -> Dict[str, Any]:
        """
        创建认证请求数据
        
        Args:
            appid: 应用ID，默认使用测试客户的app_id
            timestamp: 时间戳，默认使用当前时间
            nonce: 随机字符串，默认自动生成
            secret: 预共享密钥，默认使用测试客户的app_secret
            custom_signature: 自定义签名，用于测试错误签名
            
        Returns:
            Dict[str, Any]: 认证请求数据
        """
        if appid is None:
            appid = self.test_customer["app_id"]
        if timestamp is None:
            timestamp = int(time.time())
        if nonce is None:
            nonce = self.generate_nonce()
        if secret is None:
            secret = self.test_customer["app_secret"]
        
        if custom_signature is None:
            signature = self.generate_signature(appid, timestamp, nonce, secret)
        else:
            signature = custom_signature
        
        return {
            "appid": appid,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature
        }
    
    def send_token_request(self, auth_data: Dict[str, Any]) -> requests.Response:
        """
        发送token请求
        
        Args:
            auth_data: 认证请求数据
            
        Returns:
            requests.Response: HTTP响应对象
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.token_endpoint,
                json=auth_data,
                headers=headers,
                timeout=10
            )
            return response
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {e}")
            raise
    
    def test_normal_authentication(self) -> bool:
        """
        测试正常认证流程
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试正常认证流程 ===")
        
        try:
            # 创建正常的认证请求
            auth_data = self.create_auth_request()
            print(f"请求数据: {json.dumps(auth_data, indent=2)}")
            
            # 发送请求
            response = self.send_token_request(auth_data)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            # 验证响应
            if response.status_code == 200:
                data = response.json()
                required_fields = ["access_token", "data_key", "expires_in"]
                
                for field in required_fields:
                    if field not in data:
                        print(f"❌ 缺少必需字段: {field}")
                        return False
                
                print(f"✅ 正常认证成功")
                print(f"   access_token: {data['access_token'][:50]}...")
                print(f"   data_key: {data['data_key'][:30]}...")
                print(f"   expires_in: {data['expires_in']}")
                return True
            else:
                print(f"❌ 认证失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_time_window_validation(self) -> bool:
        """
        测试时间窗口校验
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试时间窗口校验 ===")
        
        try:
            # 测试过期时间戳（超过5分钟）
            old_timestamp = int(time.time()) - 400  # 6分40秒前
            auth_data = self.create_auth_request(timestamp=old_timestamp)
            
            print(f"使用过期时间戳: {old_timestamp}")
            print(f"当前时间戳: {int(time.time())}")
            print(f"时间差: {int(time.time()) - old_timestamp} 秒")
            
            response = self.send_token_request(auth_data)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            # 应该返回402错误
            if response.status_code == 402:
                print("✅ 时间窗口校验正常，正确拒绝过期请求")
                return True
            else:
                print(f"❌ 时间窗口校验失败，期望402，实际{response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_nonce_replay_protection(self) -> bool:
        """
        测试防重放攻击（nonce校验）
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试防重放攻击 ===")
        
        try:
            # 第一次请求
            nonce = self.generate_nonce()
            timestamp = int(time.time())
            auth_data = self.create_auth_request(timestamp=timestamp, nonce=nonce)
            
            print(f"第一次请求，nonce: {nonce}")
            response1 = self.send_token_request(auth_data)
            print(f"第一次响应状态码: {response1.status_code}")
            
            if response1.status_code != 200:
                print(f"❌ 第一次请求失败: {response1.text}")
                return False
            
            # 等待1秒，然后重复相同的nonce
            time.sleep(1)
            print(f"\n重复使用相同nonce: {nonce}")
            response2 = self.send_token_request(auth_data)
            print(f"第二次响应状态码: {response2.status_code}")
            print(f"第二次响应内容: {response2.text}")
            
            # 应该返回403错误
            if response2.status_code == 403:
                print("✅ 防重放攻击正常，正确拒绝重复nonce")
                return True
            else:
                print(f"❌ 防重放攻击失败，期望403，实际{response2.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_signature_validation(self) -> bool:
        """
        测试签名验证
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试签名验证 ===")
        
        try:
            # 测试错误签名
            wrong_signature = "WRONG_SIGNATURE_12345678901234567890123456789012"
            auth_data = self.create_auth_request(custom_signature=wrong_signature)
            
            print(f"使用错误签名: {wrong_signature}")
            response = self.send_token_request(auth_data)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            # 应该返回401错误
            if response.status_code == 401:
                print("✅ 签名验证正常，正确拒绝错误签名")
                return True
            else:
                print(f"❌ 签名验证失败，期望401，实际{response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_invalid_appid(self) -> bool:
        """
        测试无效appid处理
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试无效appid处理 ===")
        
        try:
            # 使用不存在的appid
            invalid_appid = "invalid_app_id_999"
            auth_data = self.create_auth_request(appid=invalid_appid)
            
            print(f"使用无效appid: {invalid_appid}")
            response = self.send_token_request(auth_data)
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            # 应该返回404错误
            if response.status_code == 404:
                print("✅ 无效appid处理正常，正确拒绝无效appid")
                return True
            else:
                print(f"❌ 无效appid处理失败，期望404，实际{response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False
    
    def test_parameter_validation(self) -> bool:
        """
        测试参数验证
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试参数验证 ===")
        
        test_cases = [
            {
                "name": "缺少appid",
                "data": {
                    "timestamp": int(time.time()),
                    "nonce": self.generate_nonce(),
                    "signature": "test_signature"
                }
            },
            {
                "name": "缺少timestamp",
                "data": {
                    "appid": self.test_customer["app_id"],
                    "nonce": self.generate_nonce(),
                    "signature": "test_signature"
                }
            },
            {
                "name": "缺少nonce",
                "data": {
                    "appid": self.test_customer["app_id"],
                    "timestamp": int(time.time()),
                    "signature": "test_signature"
                }
            },
            {
                "name": "缺少signature",
                "data": {
                    "appid": self.test_customer["app_id"],
                    "timestamp": int(time.time()),
                    "nonce": self.generate_nonce()
                }
            },
            {
                "name": "nonce长度不足",
                "data": {
                    "appid": self.test_customer["app_id"],
                    "timestamp": int(time.time()),
                    "nonce": "short",  # 少于8位
                    "signature": "test_signature"
                }
            },
            {
                "name": "nonce长度过长",
                "data": {
                    "appid": self.test_customer["app_id"],
                    "timestamp": int(time.time()),
                    "nonce": "a" * 20,  # 超过16位
                    "signature": "test_signature"
                }
            }
        ]
        
        all_passed = True
        
        for test_case in test_cases:
            print(f"\n测试: {test_case['name']}")
            try:
                response = self.send_token_request(test_case["data"])
                print(f"响应状态码: {response.status_code}")
                
                # 参数验证错误应该返回422（Unprocessable Entity）
                if response.status_code == 422:
                    print(f"✅ {test_case['name']} - 参数验证正常")
                else:
                    print(f"❌ {test_case['name']} - 期望422，实际{response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print(f"❌ {test_case['name']} - 测试异常: {e}")
                all_passed = False
        
        return all_passed
    
    def test_concurrent_requests(self) -> bool:
        """
        测试并发请求处理
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试并发请求处理 ===")
        
        try:
            import threading
            import queue
            
            results = queue.Queue()
            
            def make_request():
                """发送单个请求"""
                try:
                    auth_data = self.create_auth_request()
                    response = self.send_token_request(auth_data)
                    results.put((response.status_code, response.text[:100]))
                except Exception as e:
                    results.put(("error", str(e)))
            
            # 创建5个并发线程
            threads = []
            for i in range(5):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join()
            
            # 收集结果
            success_count = 0
            while not results.empty():
                status_code, content = results.get()
                if status_code == 200:
                    success_count += 1
                print(f"并发请求结果: {status_code}")
            
            print(f"并发请求成功数: {success_count}/5")
            
            if success_count >= 4:  # 允许1个失败
                print("✅ 并发请求处理正常")
                return True
            else:
                print("❌ 并发请求处理异常")
                return False
                
        except Exception as e:
            print(f"❌ 并发测试异常: {e}")
            return False
    
    def test_concurrent_performance(self) -> bool:
        """
        测试并发性能 - 详细的并发测试，包含性能指标
        
        Returns:
            bool: 测试是否通过
        """
        print("\n=== 测试并发性能 ===")
        
        try:
            import threading
            import time
            
            # 测试配置
            test_configs = [
                {"threads": 5, "requests_per_thread": 2, "name": "轻负载测试"},
                {"threads": 10, "requests_per_thread": 3, "name": "中负载测试"},
                {"threads": 20, "requests_per_thread": 2, "name": "高负载测试"}
            ]
            
            all_passed = True
            
            for config in test_configs:
                print(f"\n--- {config['name']} ---")
                print(f"配置: {config['threads']}线程 x {config['requests_per_thread']}请求")
                
                results = []
                results_lock = threading.Lock()
                
                def worker():
                    """工作线程"""
                    for _ in range(config['requests_per_thread']):
                        start_time = time.time()
                        try:
                            auth_data = self.create_auth_request()
                            response = self.send_token_request(auth_data)
                            response_time = time.time() - start_time
                            
                            with results_lock:
                                results.append({
                                    'status_code': response.status_code,
                                    'response_time': response_time,
                                    'success': response.status_code == 200
                                })
                        except Exception as e:
                            response_time = time.time() - start_time
                            with results_lock:
                                results.append({
                                    'status_code': 0,
                                    'response_time': response_time,
                                    'success': False,
                                    'error': str(e)
                                })
                
                # 记录开始时间
                start_time = time.time()
                
                # 创建并启动线程
                threads = []
                for _ in range(config['threads']):
                    thread = threading.Thread(target=worker)
                    thread.start()
                    threads.append(thread)
                
                # 等待所有线程完成
                for thread in threads:
                    thread.join()
                
                # 记录结束时间
                end_time = time.time()
                total_time = end_time - start_time
                
                # 统计结果
                total_requests = len(results)
                successful_requests = sum(1 for r in results if r['success'])
                failed_requests = total_requests - successful_requests
                response_times = [r['response_time'] for r in results]
                
                # 输出结果
                print(f"总请求数: {total_requests}")
                print(f"成功请求: {successful_requests}")
                print(f"失败请求: {failed_requests}")
                success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
                print(f"成功率: {success_rate:.2f}%")
                print(f"总耗时: {total_time:.2f}秒")
                qps = total_requests / total_time if total_time > 0 else 0
                print(f"QPS: {qps:.2f}")
                
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
                    min_response_time = min(response_times)
                    max_response_time = max(response_times)
                    print(f"平均响应时间: {avg_response_time:.4f}秒")
                    print(f"最小响应时间: {min_response_time:.4f}秒")
                    print(f"最大响应时间: {max_response_time:.4f}秒")
                
                # 判断测试是否通过
                if success_rate < 90:  # 成功率低于90%认为失败
                    print(f"❌ {config['name']} 失败 - 成功率过低")
                    all_passed = False
                elif avg_response_time > 10:  # 平均响应时间超过10秒认为性能不佳
                    print(f"⚠️ {config['name']} 警告 - 响应时间较长")
                else:
                    print(f"✅ {config['name']} 通过")
                
                # 统计错误类型
                error_types = {}
                for result in results:
                    if not result['success']:
                        error_key = f"HTTP_{result['status_code']}"
                        if 'error' in result:
                            error_key += f"_{result['error'][:20]}"
                        error_types[error_key] = error_types.get(error_key, 0) + 1
                
                if error_types:
                    print("错误统计:")
                    for error, count in error_types.items():
                        print(f"  {error}: {count}次")
                
                time.sleep(1)  # 测试间隔
            
            if all_passed:
                print("\n✅ 并发性能测试通过")
            else:
                print("\n❌ 并发性能测试失败")
            
            return all_passed
            
        except Exception as e:
            print(f"❌ 并发性能测试异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """
        运行所有测试
        
        Returns:
            Dict[str, bool]: 测试结果字典
        """
        print(f"\n{'='*60}")
        print(f"开始Token接口完整测试")
        print(f"测试时间: {datetime.now()}")
        print(f"目标接口: {self.token_endpoint}")
        print(f"测试客户: {self.test_customer['app_id']}")
        print(f"{'='*60}")
        
        test_results = {}
        
        # 执行各项测试
        test_methods = [
            ("正常认证流程", self.test_normal_authentication),
            ("时间窗口校验", self.test_time_window_validation),
            ("防重放攻击", self.test_nonce_replay_protection),
            ("签名验证", self.test_signature_validation),
            ("无效appid处理", self.test_invalid_appid),
            ("参数验证", self.test_parameter_validation),
            ("并发请求处理", self.test_concurrent_requests),
            ("并发性能测试", self.test_concurrent_performance)
        ]
        
        for test_name, test_method in test_methods:
            try:
                result = test_method()
                test_results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
                test_results[test_name] = False
        
        # 输出测试总结
        print(f"\n{'='*60}")
        print("测试结果总结:")
        print(f"{'='*60}")
        
        passed_count = 0
        total_count = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_name:<20} {status}")
            if result:
                passed_count += 1
        
        print(f"\n总计: {passed_count}/{total_count} 项测试通过")
        success_rate = (passed_count / total_count) * 100
        print(f"成功率: {success_rate:.1f}%")
        
        if passed_count == total_count:
            print("\n🎉 所有测试通过！Token接口功能正常")
        else:
            print(f"\n⚠️ 有 {total_count - passed_count} 项测试失败，请检查相关功能")
        
        return test_results

def setup_test_customer():
    """
    设置测试客户数据
    
    注意：需要确保数据库中存在测试客户数据
    """
    print("\n=== 设置测试环境 ===")
    print("请确保数据库中存在以下测试客户:")
    print(f"app_id: {TEST_CUSTOMER['app_id']}")
    print(f"app_secret: {TEST_CUSTOMER['app_secret']}")
    print("状态: 启用")
    print("\n如果测试客户不存在，请先创建或修改TEST_CUSTOMER配置")

def main():
    """
    主函数
    """
    # 设置测试环境
    setup_test_customer()
    
    # 创建测试实例
    tester = TokenEndpointTester()
    
    # 运行所有测试
    results = tester.run_all_tests()
    
    # 返回测试结果
    return results

if __name__ == "__main__":
    main()