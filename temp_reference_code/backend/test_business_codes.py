#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务状态码测试脚本

测试新的业务状态码实现是否正常工作

Author: System
Date: 2024
"""

import requests
import json
import time
import hashlib
import hmac
from typing import Dict, Any


class BusinessCodeTester:
    """业务状态码测试器"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token_url = f"{base_url}/api/v1/auth/token"
    
    def generate_signature(self, appid: str, timestamp: int, nonce: str, secret: str) -> str:
        """生成签名"""
        signature_data = f"{appid}{timestamp}{nonce}"
        signature = hmac.new(
            secret.encode('utf-8'),
            signature_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest().upper()
        return signature
    
    def test_param_error(self) -> Dict[str, Any]:
        """测试参数错误 - 应返回业务码1001"""
        print("\n=== 测试参数错误 ===")
        
        # 发送缺少appid的请求
        payload = {
            "timestamp": int(time.time()),
            "nonce": "test1234",
            "signature": "invalid"
        }
        
        response = requests.post(self.token_url, json=payload)
        result = response.json()
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        expected_code = 1001
        actual_code = result.get('code')
        success = response.status_code == 200 and actual_code == expected_code
        
        print(f"测试结果: {'✅ 通过' if success else '❌ 失败'}")
        print(f"期望业务码: {expected_code}, 实际业务码: {actual_code}")
        
        return {
            "test_name": "参数错误",
            "success": success,
            "expected_code": expected_code,
            "actual_code": actual_code,
            "http_status": response.status_code
        }
    
    def test_timestamp_error(self) -> Dict[str, Any]:
        """测试时间窗口错误 - 应返回业务码1003"""
        print("\n=== 测试时间窗口错误 ===")
        
        # 使用过期的时间戳（1小时前）
        old_timestamp = int(time.time()) - 3600
        payload = {
            "appid": "test_app",
            "timestamp": old_timestamp,
            "nonce": "test1234",
            "signature": self.generate_signature("test_app", old_timestamp, "test1234", "test_secret")
        }
        
        response = requests.post(self.token_url, json=payload)
        result = response.json()
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        expected_code = 1003
        actual_code = result.get('code')
        success = response.status_code == 200 and actual_code == expected_code
        
        print(f"测试结果: {'✅ 通过' if success else '❌ 失败'}")
        print(f"期望业务码: {expected_code}, 实际业务码: {actual_code}")
        
        return {
            "test_name": "时间窗口错误",
            "success": success,
            "expected_code": expected_code,
            "actual_code": actual_code,
            "http_status": response.status_code
        }
    
    def test_invalid_appid(self) -> Dict[str, Any]:
        """测试无效appid - 应返回业务码1005"""
        print("\n=== 测试无效appid ===")
        
        timestamp = int(time.time())
        payload = {
            "appid": "invalid_app_id",
            "timestamp": timestamp,
            "nonce": "test1234",
            "signature": self.generate_signature("invalid_app_id", timestamp, "test1234", "test_secret")
        }
        
        response = requests.post(self.token_url, json=payload)
        result = response.json()
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        expected_code = 1005
        actual_code = result.get('code')
        success = response.status_code == 200 and actual_code == expected_code
        
        print(f"测试结果: {'✅ 通过' if success else '❌ 失败'}")
        print(f"期望业务码: {expected_code}, 实际业务码: {actual_code}")
        
        return {
            "test_name": "无效appid",
            "success": success,
            "expected_code": expected_code,
            "actual_code": actual_code,
            "http_status": response.status_code
        }
    
    def test_signature_failed(self) -> Dict[str, Any]:
        """测试签名验证失败 - 应返回业务码1002"""
        print("\n=== 测试签名验证失败 ===")
        
        timestamp = int(time.time())
        # 使用有效的appid，但提供错误的签名
        payload = {
            "appid": "test_app_001",
            "timestamp": timestamp,
            "nonce": "test1234",
            "signature": "wrong_signature"
        }
        
        response = requests.post(self.token_url, json=payload)
        result = response.json()
        
        print(f"HTTP状态码: {response.status_code}")
        print(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        expected_code = 1002
        actual_code = result.get('code')
        success = response.status_code == 200 and actual_code == expected_code
        
        print(f"测试结果: {'✅ 通过' if success else '❌ 失败'}")
        print(f"期望业务码: {expected_code}, 实际业务码: {actual_code}")
        
        return {
            "test_name": "签名验证失败",
            "success": success,
            "expected_code": expected_code,
            "actual_code": actual_code,
            "http_status": response.status_code
        }
    
    def run_all_tests(self) -> None:
        """运行所有测试"""
        print("🚀 开始业务状态码测试...")
        print(f"测试目标: {self.base_url}")
        
        tests = [
            self.test_param_error,
            self.test_timestamp_error,
            self.test_invalid_appid,
            self.test_signature_failed
        ]
        
        results = []
        for test_func in tests:
            try:
                result = test_func()
                results.append(result)
            except Exception as e:
                print(f"❌ 测试执行失败: {e}")
                results.append({
                    "test_name": test_func.__name__,
                    "success": False,
                    "error": str(e)
                })
        
        # 汇总结果
        print("\n" + "="*50)
        print("📊 测试结果汇总")
        print("="*50)
        
        passed = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        for result in results:
            status = "✅ 通过" if result.get('success', False) else "❌ 失败"
            print(f"{result['test_name']}: {status}")
            if 'expected_code' in result:
                print(f"  期望业务码: {result['expected_code']}, 实际: {result.get('actual_code', 'N/A')}")
            if 'error' in result:
                print(f"  错误: {result['error']}")
        
        print(f"\n总计: {passed}/{total} 项测试通过")
        
        if passed == total:
            print("🎉 所有测试通过！业务状态码实现正常。")
        else:
            print(f"⚠️ 有 {total - passed} 项测试失败，请检查实现。")


if __name__ == "__main__":
    tester = BusinessCodeTester()
    tester.run_all_tests()