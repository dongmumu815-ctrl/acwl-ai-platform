#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的Token接口并发测试

Author: System
Date: 2024
"""

import requests
import time
import threading
import hmac
import hashlib
import random
import string
from concurrent.futures import ThreadPoolExecutor

# 测试配置
BASE_URL = "http://localhost:8000"
TOKEN_ENDPOINT = f"{BASE_URL}/api/v1/auth/token"

TEST_CUSTOMER = {
    "app_id": "test_app_001",
    "app_secret": "test_secret_123456789"
}

def generate_nonce(length=12):
    """生成随机nonce"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_signature(appid, timestamp, nonce, secret):
    """生成HMAC-SHA256签名"""
    signature_data = f"{appid}{timestamp}{nonce}"
    signature = hmac.new(
        secret.encode('utf-8'),
        signature_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest().upper()
    return signature

def create_auth_request():
    """创建认证请求"""
    appid = TEST_CUSTOMER["app_id"]
    timestamp = int(time.time())
    nonce = generate_nonce()
    secret = TEST_CUSTOMER["app_secret"]
    
    signature = generate_signature(appid, timestamp, nonce, secret)
    
    return {
        "appid": appid,
        "timestamp": timestamp,
        "nonce": nonce,
        "signature": signature
    }

def send_request():
    """发送单个请求"""
    auth_data = create_auth_request()
    headers = {"Content-Type": "application/json"}
    
    start_time = time.time()
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            json=auth_data,
            headers=headers,
            timeout=10
        )
        response_time = time.time() - start_time
        return response.status_code, response_time, ""
    except Exception as e:
        response_time = time.time() - start_time
        return 0, response_time, str(e)

def test_concurrent(num_threads, requests_per_thread):
    """并发测试"""
    print(f"\n开始并发测试: {num_threads}线程 x {requests_per_thread}请求")
    
    results = []
    results_lock = threading.Lock()
    
    def worker():
        for _ in range(requests_per_thread):
            result = send_request()
            with results_lock:
                results.append(result)
    
    # 记录开始时间
    start_time = time.time()
    
    # 创建并启动线程
    threads = []
    for _ in range(num_threads):
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
    successful_requests = sum(1 for status, _, _ in results if status == 200)
    failed_requests = total_requests - successful_requests
    response_times = [rt for _, rt, _ in results]
    
    # 输出结果
    print(f"\n测试结果:")
    print(f"总请求数: {total_requests}")
    print(f"成功请求: {successful_requests}")
    print(f"失败请求: {failed_requests}")
    print(f"成功率: {(successful_requests/total_requests)*100:.2f}%")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"QPS: {total_requests/total_time:.2f}")
    
    if response_times:
        print(f"平均响应时间: {sum(response_times)/len(response_times):.4f}秒")
        print(f"最小响应时间: {min(response_times):.4f}秒")
        print(f"最大响应时间: {max(response_times):.4f}秒")
    
    # 统计错误
    error_codes = {}
    for status, _, error in results:
        if status != 200:
            key = f"{status}_{error[:20]}" if error else str(status)
            error_codes[key] = error_codes.get(key, 0) + 1
    
    if error_codes:
        print(f"\n错误统计:")
        for error, count in error_codes.items():
            print(f"  {error}: {count}次")

def main():
    """主函数"""
    print("Token接口并发测试")
    print("=" * 40)
    
    # 检查服务器状态
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print(f"✅ 服务器状态正常: {BASE_URL}")
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return
    
    # 运行测试
    test_configs = [
        (5, 2),   # 5线程 x 2请求
        (10, 3),  # 10线程 x 3请求
        (20, 2),  # 20线程 x 2请求
    ]
    
    for threads, req_count in test_configs:
        test_concurrent(threads, req_count)
        time.sleep(1)  # 间隔1秒
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()